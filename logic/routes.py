"""
Candidate detour routes for the Control Room's route-comparison step.

Deterministic per vehicle (random.Random(f"route-{vehicle_id}") — string
seeds use a hash-independent algorithm, so this is stable across restarts)
so the same vehicle always gets the same 3 candidates across Streamlit
reruns. Mirrors the PPT's route-comparison slides: Route A (최단 경로) runs
straight through the vehicle's weak spot and trends down, Route B (대안
경로 1) is a middling detour, Route C (대안 경로 2) is a longer detour that
tends to stay stable/recover. Whichever ends up with the highest worst-point
score is surfaced as the recommended route — it isn't hardcoded to C.
"""

import random

from logic.health_score import HEALTH_BANDS, band_for

_RISK_TAGS = {
    "perception": ["보행자 밀집", "인도 인접 차선", "야간 시야 저하"],
    "prediction": ["합류구간", "비보호 좌회전", "차량 급변침 잦음"],
    "planning": ["복잡 교차로", "차선 선택지 과다", "공사구간"],
    "control": ["급커브 구간", "좁은 차선", "노면 마찰력 저하"],
}

# key, label, distance factor, eta factor, trend
_ROUTE_DEFS = [
    ("A", "경로 A (최단 경로)", 1.00, 1.00, "decline"),
    ("B", "경로 B (대안 경로 1)", 1.12, 1.15, "flat"),
    ("C", "경로 C (대안 경로 2)", 1.28, 1.35, "recover"),
]

_STEPS = 5
_BASE_DISTANCE_KM = 8.5
_BASE_ETA_MIN = 14


def _trajectory(rng: random.Random, base_score: int, trend: str) -> list[int]:
    scores = [base_score]
    cur = base_score
    for i in range(_STEPS - 1):
        if trend == "decline":
            cur = max(5, cur - (rng.randint(8, 16) + i * 2))
        elif trend == "flat":
            cur = max(20, min(95, cur + rng.randint(-9, 4)))
        else:  # recover
            delta = rng.randint(1, 6) if i == 0 else rng.randint(-3, 6)
            cur = max(base_score - 8, min(95, cur + delta))
        scores.append(cur)
    return scores


def generate_candidate_routes(vehicle_id: str, base_health: float, weak_module: str | None = None):
    """Returns (routes, recommended_key)."""
    rng = random.Random(f"route-{vehicle_id}")
    tags_pool = _RISK_TAGS.get(weak_module, []) if weak_module else []
    base_score = round(base_health)

    routes = []
    for key, label, dist_factor, eta_factor, trend in _ROUTE_DEFS:
        scores = _trajectory(rng, base_score, trend)
        min_score = min(scores)
        band = band_for(min_score, HEALTH_BANDS)
        distance_km = round(_BASE_DISTANCE_KM * dist_factor + rng.uniform(-0.4, 0.4), 1)
        eta_min = round(_BASE_ETA_MIN * eta_factor + rng.uniform(-1, 1))

        risk_factors = []
        if tags_pool and trend == "decline":
            risk_factors = rng.sample(tags_pool, k=min(2, len(tags_pool)))
        elif tags_pool and trend == "flat":
            risk_factors = rng.sample(tags_pool, k=1)

        routes.append(
            {
                "key": key,
                "label": label,
                "distance_km": distance_km,
                "eta_min": eta_min,
                "scores": scores,
                "min_score": min_score,
                "band": band,
                "risk_factors": risk_factors,
            }
        )

    recommended_key = max(routes, key=lambda r: r["min_score"])["key"]
    return routes, recommended_key
