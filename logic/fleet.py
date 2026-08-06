"""
Synthetic vehicle fleet for the Control Room's Detect step.

Every vehicle dict has the SAME shape as logic/scenarios.py's SCENARIOS
entries (label, situation, components, component_notes, context_penalty,
context_penalty_reason, interpretations, operational_notes, actions), so
logic/health_score.py's evaluate_scenario() and every renderer in
components/health_ui.py + components/car_diagram.py work on fleet vehicles
completely unchanged.

Generation is deterministic (random.Random(seed)) so the fleet — and every
vehicle's Health Score — stays identical across Streamlit reruns without
needing st.cache or session_state bookkeeping.

interpretations/operational_notes are NOT hand-written: they're assembled
from MODULE_BANDS' existing 운영상 의미(band[3])/기본조치(band[4]) text, so
the generated copy always stays consistent with the spec document instead
of drifting from it.
"""

import copy
import random

from logic.health_score import (
    MODULE_BANDS,
    MODULE_COMPONENTS,
    MODULE_LABELS,
    MODULE_ORDER,
    band_for,
    evaluate_scenario,
)
from logic.scenarios import SCENARIOS

ROUTE_PLACES = [
    ("강남대로", "물류센터 A"),
    ("판교테크노밸리", "정자역 환승센터"),
    ("공단대로", "제2공장"),
    ("신도시순환로", "환승센터"),
    ("송도국제대로", "인천항 배후단지"),
    ("대학로", "학생회관"),
    ("구도심 상가", "중앙시장"),
    ("해안순환로", "요트경기장"),
    ("첨단산업로", "R&D센터"),
    ("신공항대로", "화물터미널"),
    ("강변북로 지선", "복합환승센터"),
    ("테크노파크", "산학협력관"),
]

# (reason, penalty_lo, penalty_hi) — pulled from context tags in this pool
# depending on the vehicle's severity tier.
_HEALTHY_CONTEXT = [
    ("특이사항 없음", 0, 0),
    ("주간 · 맑음 평상 주행", 0, 1),
]
_RISK_CONTEXT = {
    "perception": [("야간 우천 · 시야 저하", 3, 9), ("보행자 밀집 구간 통과", 2, 8)],
    "prediction": [("합류구간 진입 예정", 2, 7), ("주변 차량 급변침 감지", 3, 9)],
    "planning": [("복잡 교차로 접근", 2, 6), ("공사구간 임박", 3, 8)],
    "control": [("노면 마찰력 저하", 2, 7), ("급커브 구간 임박", 3, 8)],
}

_TIER_CUTOFFS = [
    # (name, cumulative_probability)
    ("healthy", 0.78),
    ("mild", 0.92),
    ("moderate", 0.98),
    ("severe", 1.01),
]
_TIER_TARGET_RANGE = {
    "mild": (0.55, 0.72),
    "moderate": (0.40, 0.56),
    "severe": (0.24, 0.42),
}

# Fixed indices get their `components` swapped for the spec-verified
# worked examples (Health Score 68 / 24) so the demo can be cross-checked
# against "자율주행 Health Score 점수체계" 사례 1 / 사례 2 directly.
_PINNED_CASES = {12: "case1", 55: "case2"}


def _healthy_target(rng: random.Random) -> float:
    return rng.uniform(0.87, 0.98)


def _pick_tier(rng: random.Random) -> str:
    roll = rng.random()
    for name, cutoff in _TIER_CUTOFFS:
        if roll <= cutoff:
            return name
    return "healthy"


def _module_components(rng: random.Random, module_key: str, target: float) -> dict:
    values = {}
    for key, _label, _weight in MODULE_COMPONENTS[module_key]:
        v = target + rng.uniform(-0.05, 0.05)
        values[key] = round(min(0.99, max(0.05, v)), 2)
    return values


def _pick_context(rng: random.Random, tier: str, weak_module: str | None) -> tuple:
    if tier == "healthy" or weak_module is None:
        reason, lo, hi = rng.choice(_HEALTHY_CONTEXT)
    else:
        reason, lo, hi = rng.choice(_RISK_CONTEXT[weak_module])
    penalty = rng.randint(lo, hi) if hi > lo else lo
    return reason, penalty


def _build_vehicle(rng: random.Random, idx: int) -> dict:
    tier = _pick_tier(rng)
    weak_module = None
    components = {}

    if tier == "healthy":
        for m in MODULE_ORDER:
            components[m] = _module_components(rng, m, _healthy_target(rng))
    else:
        weak_module = rng.choice(MODULE_ORDER)
        weak_target = rng.uniform(*_TIER_TARGET_RANGE[tier])
        for m in MODULE_ORDER:
            if m == weak_module:
                components[m] = _module_components(rng, m, weak_target)
            else:
                components[m] = _module_components(rng, m, _healthy_target(rng))

    origin, dest = ROUTE_PLACES[idx % len(ROUTE_PLACES)]
    route_label = f"{origin} → {dest}"
    vehicle_id = f"V-{idx:03d}"

    context_reason, penalty = _pick_context(rng, tier, weak_module)

    situation = [f"운행 구간: {route_label}", context_reason]
    if weak_module:
        situation.append(f"{MODULE_LABELS[weak_module]} 모듈 이상 징후 감지")

    return {
        "id": vehicle_id,
        "label": f"{vehicle_id} · {route_label}",
        "route": route_label,
        "situation": situation,
        "components": components,
        "component_notes": {},
        "context_penalty": penalty,
        "context_penalty_reason": context_reason,
        "interpretations": {},
        "operational_notes": [],
        "actions": [],
    }


def _apply_pinned_case(vehicle: dict, case_key: str) -> dict:
    case = SCENARIOS[case_key]
    vehicle["components"] = copy.deepcopy(case["components"])
    vehicle["context_penalty"] = case["context_penalty"]
    vehicle["context_penalty_reason"] = case["context_penalty_reason"]
    vehicle["situation"] = [f"운행 구간: {vehicle['route']}", case["context_penalty_reason"]]
    vehicle["label"] = f"{vehicle['id']} · {vehicle['route']} · 스펙 사례({case['label']})"
    return vehicle


def _finalize(vehicle: dict) -> dict:
    result = evaluate_scenario(vehicle)
    interpretations = {}
    notes = []
    for m in MODULE_ORDER:
        score = result["modules"][m]
        band = band_for(score, MODULE_BANDS[m])
        interpretations[m] = band[3]
        notes.append(f"{MODULE_LABELS[m]}: {band[2]} ({score}점) — {band[3]}")
    vehicle["interpretations"] = interpretations
    vehicle["operational_notes"] = notes
    vehicle["_result"] = result
    vehicle["_weak_module"] = min(MODULE_ORDER, key=lambda m: result["modules"][m])
    return vehicle


def generate_fleet(n: int = 100, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    fleet = []
    for idx in range(n):
        vehicle = _build_vehicle(rng, idx)
        if idx in _PINNED_CASES:
            vehicle = _apply_pinned_case(vehicle, _PINNED_CASES[idx])
        fleet.append(_finalize(vehicle))
    return fleet
