"""
Health Score calculation engine.

Everything in this file is a REAL implementation of the formulas from
"자율주행 Health Score 점수체계" (2026) — weights, thresholds and the
Savg -> worst-module -> context penalty pipeline are transcribed directly
from the spec. The only thing that is still a stand-in is the *input*:
component health values (0-1) come from hand-picked (logic/scenarios.py)
or procedurally generated (logic/fleet.py) presets instead of live sensor
telemetry. Swapping in real telemetry later doesn't touch this file at
all — only where the `components` dict comes from.
"""

MODULE_LABELS = {
    "perception": "인지",
    "prediction": "예측",
    "planning": "계획",
    "control": "제어",
}

MODULE_ORDER = ["perception", "prediction", "planning", "control"]

# key, label, weight — PDF 2.2 / 3.2 / 4.2 / 5.2
MODULE_COMPONENTS = {
    "perception": [
        ("sensor_quality", "센서 품질", 0.20),
        ("sensor_fusion", "센서 간 일치도", 0.25),
        ("track_stability", "객체 추적 안정성", 0.20),
        ("perception_certainty", "인지 확실성", 0.15),
        ("critical_detection", "중요 객체 검출성", 0.20),
    ],
    "prediction": [
        ("trajectory_certainty", "궤적 확실성", 0.20),
        ("intent_stability", "행동모드 안정성", 0.20),
        ("pred_obs_match", "관측-예측 일치도", 0.20),
        ("path_clearance", "위험경로 교차여유", 0.25),
        ("horizon_margin", "예측시간 여유", 0.15),
    ],
    "planning": [
        ("collision_margin", "충돌 위험여유", 0.30),
        ("stop_feasibility", "정지 가능성", 0.25),
        ("path_feasibility", "경로 실행 가능성", 0.15),
        ("plan_stability", "계획 안정성", 0.15),
        ("fallback_availability", "비상대안 확보", 0.15),
    ],
    "control": [
        ("tracking_accuracy", "경로 추종 정확도", 0.20),
        ("response_speed", "제어 응답성", 0.20),
        ("vehicle_stability", "차량 안정성", 0.20),
        ("braking_margin", "제동 여유", 0.30),
        ("ride_smoothness", "동작 안정성", 0.10),
    ],
}

# (lo, hi, band, 운영상 의미, 기본조치) — PDF 2.3 / 3.3 / 4.3 / 5.3
MODULE_BANDS = {
    "perception": [
        (85, 100, "정상", "주요 객체와 도로환경을 안정적으로 인식", "정상운행"),
        (70, 84, "관찰", "일부 품질 저하가 있으나 중복센서로 보완 가능", "모니터링 강화"),
        (50, 69, "주의", "중요 객체의 인식이 불안정하여 제한운행 필요", "감속, 차선변경 제한, 관제 경고"),
        (30, 49, "위험", "중요 객체를 신뢰성 있게 파악하기 어려움", "진입 보류, 원격관제 전환"),
        (0, 29, "심각", "핵심 인지기능을 운행에 사용할 수 없음", "최소위험상태 또는 운행 중지"),
    ],
    "prediction": [
        (85, 100, "정상", "보행자 행동과 궤적을 안정적으로 예측", "정상계획 유지"),
        (70, 84, "관찰", "복수 행동 가능성이 있으나 안전여유가 충분", "방어적 계획 생성"),
        (50, 69, "주의", "보행자 행동의 불확실성이 커짐", "감속, 정지 가능거리 확보"),
        (30, 49, "위험", "차량 경로와 교차할 가능성이 높거나 예측이 불안정", "정지계획 우선, 관제사 개입 요청"),
        (0, 29, "심각", "돌발행동으로 유효한 미래궤적 예측이 불가능", "즉각적인 긴급제동 또는 안전정지"),
    ],
    "planning": [
        (85, 100, "정상", "충분한 안전여유를 가진 경로를 생성 가능", "정상운행"),
        (70, 84, "관찰", "안전경로는 존재하지만 방어적 운행 필요", "감속계획 적용"),
        (50, 69, "주의", "정상경로의 안전여유가 부족함", "차선 유지, 정지 준비"),
        (30, 49, "위험", "정상운행을 지속할 안전경로가 부족함", "완전 정지 또는 최소위험상태 계획"),
        (0, 29, "심각", "충돌을 피하는 유효한 계획을 생성하기 어려움", "긴급제동 등 독립 안전조치"),
    ],
    "control": [
        (85, 100, "정상", "계획된 조치를 안정적으로 수행 가능", "정상 제어"),
        (70, 84, "관찰", "제어 가능하지만 감속·제동 여유 감소", "속도 제한"),
        (50, 69, "주의", "계획 추종 또는 제동성능이 제한됨", "최소위험상태 우선"),
        (30, 49, "위험", "계획된 회피·정지 조치 수행을 신뢰하기 어려움", "즉시 운행 중지"),
        (0, 29, "심각", "핵심 조향·제동 기능 상실 가능", "비상정지 및 외부 대응"),
    ],
}

# (lo, hi, band, 운영상 의미, 관제 우선순위, 운영조치) — PDF 6.3
HEALTH_BANDS = [
    (85, 100, "정상", "정상 자율주행 가능", "낮음", "정상운행"),
    (70, 84, "주의-관찰", "자체 대응 가능한 경미한 저하", "관찰", "자동 감속·집중 모니터링"),
    (50, 69, "주의-경고", "운행 제한과 관제 확인 필요", "높음", "감속·차선 제한·관제 경고"),
    (30, 49, "위험", "정상운행 지속 불가", "긴급", "안전정지·관제사 개입"),
    (0, 29, "심각", "핵심 안전기능 상실 또는 충돌 임박", "최우선", "즉시 MRM·운행 중지"),
]

# PDF 6.2 예시: 야간 우천 · 보행자 존재 상황의 가중치
HEALTH_WEIGHTS_DEFAULT = {"perception": 0.25, "prediction": 0.30, "planning": 0.30, "control": 0.15}

# Module bands use 정상/관찰/주의/위험/심각; the Health Score band table
# (PDF 6.3) uses its own 5 labels (정상/주의-관찰/주의-경고/위험/심각) — both
# sets are included here so band[2] from either table resolves correctly.
BAND_COLORS = {
    "정상": "#3ddad7",
    "관찰": "#4f9dff",
    "주의": "#ffb140",
    "위험": "#ff6b4a",
    "심각": "#ff3d63",
    "주의-관찰": "#4f9dff",
    "주의-경고": "#ffb140",
}
BAND_STATUS_CLASS = {
    "정상": "normal",
    "관찰": "observe",
    "주의": "caution",
    "위험": "danger",
    "심각": "critical",
    "주의-관찰": "observe",
    "주의-경고": "caution",
}
BAND_EMOJI = {
    "정상": "🟢",
    "관찰": "🔵",
    "주의": "🟡",
    "위험": "🟠",
    "심각": "🔴",
    "주의-관찰": "🔵",
    "주의-경고": "🟡",
}


def compute_module_score(module_key: str, component_values: dict) -> tuple[int, list[dict]]:
    """Weighted-sum score (0-100) for one module, plus the row-by-row
    breakdown (건전성 값 x 가중치 = 기여값) used for the drill-down table.
    """
    weighted = 0.0
    breakdown = []
    for key, label, weight in MODULE_COMPONENTS[module_key]:
        value = component_values[key]
        contribution = weight * value
        weighted += contribution
        breakdown.append(
            {"key": key, "label": label, "value": value, "weight": weight, "contribution": contribution}
        )
    score = round(weighted * 100)
    return score, breakdown


def band_for(score: float, bands: list[tuple]) -> tuple:
    for band in bands:
        lo, hi = band[0], band[1]
        if lo <= score <= hi:
            return band
    return bands[-1] if score < bands[-1][0] else bands[0]


def compute_health(module_scores: dict, health_weights: dict, context_penalty: float) -> dict:
    """PDF 6.2: Savg(상황 가중평균) -> 0.7*Savg + 0.3*최저모듈 -> 상황 페널티 차감."""
    savg = sum(health_weights[m] * module_scores[m] for m in MODULE_ORDER)
    worst_module = min(MODULE_ORDER, key=lambda m: module_scores[m])
    worst_score = module_scores[worst_module]
    health_base = 0.7 * savg + 0.3 * worst_score
    health_final = max(0.0, min(100.0, health_base - context_penalty))
    band = band_for(health_final, HEALTH_BANDS)
    return {
        "savg": round(savg, 2),
        "worst_module": worst_module,
        "worst_score": worst_score,
        "health_base": round(health_base, 2),
        "context_penalty": context_penalty,
        "health_final": health_final,
        "band": band,
    }


def evaluate_scenario(scenario: dict, health_weights: dict | None = None) -> dict:
    """Runs the full pipeline for one scenario preset: 4 module scores +
    breakdowns, then the composite Health Score."""
    weights = health_weights or HEALTH_WEIGHTS_DEFAULT
    modules = {}
    breakdowns = {}
    for key in MODULE_ORDER:
        score, breakdown = compute_module_score(key, scenario["components"][key])
        modules[key] = score
        breakdowns[key] = breakdown
    health = compute_health(modules, weights, scenario["context_penalty"])
    return {"modules": modules, "breakdowns": breakdowns, "health": health}
