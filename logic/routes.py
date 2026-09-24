"""
Candidate detour routes for the Control Room's route-comparison step.

There is only ONE Health Score system in this app: this module runs the
exact same evaluate_scenario() engine as the Detect/Diagnose steps. What
differs is *where* it's evaluated — Detect/Diagnose reads it at a single
snapshot in time, while here it's re-run at each of 5 waypoints along a
candidate route, with the vehicle's weakest module perturbed by how much
that particular route exposes it along the way. So a route's score isn't a
second, disconnected formula — it's the same formula, viewed across a path
instead of frozen at one moment.

Deterministic per vehicle (random.Random(f"route-{vehicle_id}") — string
seeds use a hash-independent algorithm, so this is stable across restarts)
so the same vehicle always gets the same 3 candidates across Streamlit
reruns. Mirrors the PPT's route-comparison slides: Route A (최단 경로) runs
straight through the vehicle's weak spot and trends down, Route B (대안
경로 1) is a middling detour, Route C (대안 경로 2) is a longer detour that
tends to stay stable/recover.

Roles (shortest / ai_optimal / compromise, see below) are assigned by
distance rank, not by re-comparing scores — that keeps the "AI went the
extra distance for safety" story geometrically consistent every time,
instead of occasionally handing the ai_optimal badge to a route that isn't
actually the longest one just because random severity noise scored it
highest.
"""

import copy
import math
import random

from logic.fleet import PLACE_COORDS
from logic.health_score import HEALTH_BANDS, band_for, evaluate_scenario

_RISK_TAGS = {
    "perception": ["보행자 밀집", "인도 인접 차선", "야간 시야 저하"],
    "prediction": ["합류구간", "비보호 좌회전", "차량 급변침 잦음"],
    "planning": ["복잡 교차로", "차선 선택지 과다", "공사구간"],
    "control": ["급커브 구간", "좁은 차선", "노면 마찰력 저하"],
}

# key, label, distance factor, eta factor, trend, perpendicular bow offset (km)
# — the bow offset is what makes each route visibly diverge on the map: A
# runs close to the straight line, B bows one way, C bows further the other
# way (and is the longest, matching its larger distance factor). Offsets are
# wide enough (multi-km) that even OSRM's via-point fallback (which snaps
# the bow's midpoint to the nearest real road) tends to land on a genuinely
# different corridor instead of drifting back onto the same street.
_ROUTE_DEFS = [
    ("A", "경로 A (최단 경로)", 1.00, 1.00, "decline", 0.5),
    ("B", "경로 B (대안 경로 1)", 1.15, 1.20, "flat", -2.4),
    ("C", "경로 C (대안 경로 2)", 1.35, 1.45, "recover", 3.6),
]

_STEPS = 5
_BASE_DISTANCE_KM = 8.5
_BASE_ETA_MIN = 14


def _severity_trajectory(rng: random.Random, trend: str, steps: int = _STEPS) -> list[float]:
    """0 (no added exposure) .. ~0.85 (heavy degradation) per waypoint. This
    drives how much the weak module's components get knocked down at each
    point — the route's score then comes from re-running the real Health
    Score formula on that degraded state, not from randomizing a final
    number directly."""
    sev = [0.0]
    cur = 0.0
    for i in range(1, steps):
        if trend == "decline":
            cur = min(0.85, cur + rng.uniform(0.15, 0.24))
        elif trend == "flat":
            cur = rng.uniform(0.22, 0.4) if i == 1 else min(0.55, max(0.12, cur + rng.uniform(-0.09, 0.09)))
        else:  # recover
            cur = rng.uniform(0.32, 0.48) if i == 1 else max(0.0, cur - rng.uniform(0.09, 0.19))
        sev.append(round(cur, 3))
    return sev


def _perturbed_health(vehicle: dict, weak_module: str, severity: float) -> dict:
    """Re-runs the real evaluate_scenario() pipeline on a copy of the vehicle
    with its weakest module degraded by `severity` and a matching bump to
    the situational context penalty — the exact same math the Detect/
    Diagnose snapshot uses, just fed a worse (route-exposure-dependent)
    input instead of the vehicle's current state."""
    if severity <= 0:
        return evaluate_scenario(vehicle)
    sim = copy.deepcopy(vehicle)
    for key, value in sim["components"][weak_module].items():
        sim["components"][weak_module][key] = max(0.05, value * (1 - severity))
    sim["context_penalty"] = vehicle["context_penalty"] + round(severity * 6)
    return evaluate_scenario(sim)


def _route_waypoints(origin: tuple, dest: tuple, bow_km: float, steps: int = _STEPS) -> list[tuple]:
    """Interpolates `steps` (lat, lng) points from origin to dest, bowed
    sideways by `bow_km` at the midpoint (a simple flat-plane approximation
    — fine at these short, few-km-to-tens-of-km distances)."""
    lat0, lng0 = origin
    lat1, lng1 = dest
    km_per_deg_lat = 111.0
    km_per_deg_lng = 111.0 * math.cos(math.radians((lat0 + lat1) / 2))

    dx = (lng1 - lng0) * km_per_deg_lng
    dy = (lat1 - lat0) * km_per_deg_lat
    length = math.hypot(dx, dy) or 1.0
    perp_x, perp_y = -dy / length, dx / length

    points = []
    for i in range(steps):
        t = i / (steps - 1)
        base_lat = lat0 + (lat1 - lat0) * t
        base_lng = lng0 + (lng1 - lng0) * t
        bow = math.sin(math.pi * t) * bow_km
        off_lat = (perp_y * bow) / km_per_deg_lat
        off_lng = (perp_x * bow) / km_per_deg_lng
        points.append((round(base_lat + off_lat, 5), round(base_lng + off_lng, 5)))
    return points


_ROLE_LABEL = {"shortest": "최단 경로", "ai_optimal": "AI 최적 경로", "compromise": "관제사 절충안"}


def generate_candidate_routes(
    vehicle: dict,
    weak_module: str,
    origin_label: str | None = None,
    dest_label: str | None = None,
):
    """Returns (routes, recommended_key, tradeoff).

    Each route also carries a `role`/`role_label` — "shortest" (least
    distance), "ai_optimal" (highest min_score = what recommended_key
    points at: the route the health-score formula itself prefers, even if
    it's a long way round), and "compromise" (whichever candidate is left).
    `tradeoff` quantifies what picking ai_optimal over shortest actually
    costs/buys — extra distance/time vs. the score gain and which risk
    tags disappear — so the controller has concrete numbers instead of a
    bare recommendation to weigh against, and the UI can flag it when the
    AI's score-maximizing pick is a disproportionate detour.
    """
    rng = random.Random(f"route-{vehicle['id']}")
    tags_pool = _RISK_TAGS.get(weak_module, [])

    origin_coords = PLACE_COORDS.get(origin_label, (37.45, 126.95)) if origin_label else (37.45, 126.95)
    dest_coords = PLACE_COORDS.get(dest_label, (37.40, 127.05)) if dest_label else (37.40, 127.05)

    routes = []
    for key, label, dist_factor, eta_factor, trend, bow_km in _ROUTE_DEFS:
        severities = _severity_trajectory(rng, trend)
        scores = [round(_perturbed_health(vehicle, weak_module, sev)["health"]["health_final"]) for sev in severities]
        min_score = min(scores)
        band = band_for(min_score, HEALTH_BANDS)
        distance_km = round(_BASE_DISTANCE_KM * dist_factor + rng.uniform(-0.4, 0.4), 1)
        eta_min = round(_BASE_ETA_MIN * eta_factor + rng.uniform(-1, 1))
        coords = _route_waypoints(origin_coords, dest_coords, bow_km * dist_factor)

        # Tag whichever mid-route waypoints actually carry the most exposure
        # for this route (rather than a hardcoded index), so the risk callout
        # always lines up with where the recomputed score actually dips.
        mid_idxs = sorted((i for i in range(1, _STEPS - 1) if severities[i] > 0.25), key=lambda i: -severities[i])
        chosen_tags = rng.sample(tags_pool, k=min(len(mid_idxs), len(tags_pool))) if tags_pool and mid_idxs else []
        tagged_idxs = sorted(mid_idxs[: len(chosen_tags)])
        risk_factors = chosen_tags
        risk_points = [{"idx": idx, "tag": tag} for idx, tag in zip(tagged_idxs, chosen_tags)]

        time_labels = [
            "출발" if i == 0 else ("도착" if i == _STEPS - 1 else f"+{round(eta_min * i / (_STEPS - 1))}분")
            for i in range(_STEPS)
        ]

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
                "risk_points": risk_points,
                "coords": coords,
                "time_labels": time_labels,
            }
        )

    # Roles are assigned by DISTANCE RANK, not by comparing min_score —
    # severity is randomized per waypoint, so picking "whichever scored
    # highest" could occasionally hand the ai_optimal badge to a SHORTER
    # route than the one labeled "compromise", which reads as backwards
    # (the AI supposedly went out of its way for safety, except it didn't
    # go the furthest). Tying roles to distance guarantees the story is
    # always geometrically consistent: longest = AI's furthest detour for
    # safety, middle = the compromise, shortest = the baseline it's being
    # compared against. The bow offsets already make farther routes
    # reliably score better (recover trend vs. decline trend), so this
    # rarely disagrees with the score ranking anyway.
    by_distance = sorted(routes, key=lambda r: (r["distance_km"], r["key"]))
    shortest_key = by_distance[0]["key"]
    compromise_key = by_distance[1]["key"]
    recommended_key = by_distance[2]["key"]

    role_by_key = {shortest_key: "shortest", compromise_key: "compromise", recommended_key: "ai_optimal"}
    for r in routes:
        r["role"] = role_by_key.get(r["key"], "compromise")
        r["role_label"] = _ROLE_LABEL[r["role"]]

    route_by_key = {r["key"]: r for r in routes}
    shortest_route, optimal_route = route_by_key[shortest_key], route_by_key[recommended_key]
    extra_km = round(optimal_route["distance_km"] - shortest_route["distance_km"], 1)
    extra_pct = round((optimal_route["distance_km"] / shortest_route["distance_km"] - 1) * 100) if shortest_route["distance_km"] else 0
    avoided_risks = [t for t in shortest_route["risk_factors"] if t not in optimal_route["risk_factors"]]

    tradeoff = {
        "shortest_key": shortest_key,
        "ai_optimal_key": recommended_key,
        "compromise_key": compromise_key,
        "has_tradeoff": shortest_key != recommended_key,
        "extra_km": extra_km,
        "extra_pct": extra_pct,
        "extra_min": optimal_route["eta_min"] - shortest_route["eta_min"],
        "score_gain": optimal_route["min_score"] - shortest_route["min_score"],
        "avoided_risks": avoided_risks,
        "is_extreme": extra_pct >= 20,
    }

    return routes, recommended_key, tradeoff
