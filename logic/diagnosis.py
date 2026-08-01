"""
Mock diagnosis engine for the AI Hospital PoC demo page.

`run_health_check()` and `run_root_cause()` are the ONLY two functions the
UI (pages/1_🩺_AI_Hospital_체험.py) calls. Today they look up a fixed
scenario -> canned-response table below. When a real model/pipeline is
ready, swap the body of these two functions for the actual inference
call — the UI and fixture data shapes are already what the real system
should return, so nothing else needs to change.
"""

# ---------------------------------------------------------------------------
# 사고 전 · AI 건강검진 (Pre-Accident Health Check)
# ---------------------------------------------------------------------------

HEALTH_SCENARIOS = {
    "normal": "평상시 주행",
    "night": "야간 주행",
    "rain": "우천 환경",
    "construction": "공사구간",
    "intersection": "무신호 교차로",
}

_HEALTH_FIXTURES = {
    "normal": {
        "overall": 94,
        "status": "ok",
        "modules": [("인지", 96), ("예측", 95), ("계획", 93), ("제어", 92)],
        "issues": [],
        "recommendation": "특이 이상 없음 · 정기 모니터링 주기 유지",
    },
    "night": {
        "overall": 48,
        "status": "bad",
        "modules": [("인지", 42), ("예측", 55), ("계획", 61), ("제어", 58)],
        "issues": [
            ("야간 인지 신뢰도 저하", -20),
            ("예측 불확실성 증가", -12),
            ("제어 계획 불안정", -8),
        ],
        "recommendation": "야간 카메라 게인 보정 및 저조도 인지 모델 재학습 권장",
    },
    "rain": {
        "overall": 61,
        "status": "warn",
        "modules": [("인지", 68), ("예측", 64), ("계획", 60), ("제어", 52)],
        "issues": [
            ("우천 시 제동 거리 예측 오차", -16),
            ("차선 인식 흔들림", -10),
            ("LiDAR 반사 노이즈 증가", -7),
        ],
        "recommendation": "우천 조건 제동 정책 재보정 및 LiDAR 노이즈 필터 업데이트 권장",
    },
    "construction": {
        "overall": 57,
        "status": "warn",
        "modules": [("인지", 71), ("예측", 60), ("계획", 44), ("제어", 55)],
        "issues": [
            ("공사구간 경로 재탐색 지연", -18),
            ("임시 표지판 인식률 저하", -11),
            ("협로 통과 판단 지연", -6),
        ],
        "recommendation": "공사구간 시나리오 학습 데이터 확충 및 경로 재탐색 로직 개선 권장",
    },
    "intersection": {
        "overall": 65,
        "status": "warn",
        "modules": [("인지", 74), ("예측", 69), ("계획", 58), ("제어", 62)],
        "issues": [
            ("무신호 교차로 우선순위 판단 오류", -14),
            ("타 차량 진입 예측 지연", -9),
            ("급정지 대응 여유 부족", -5),
        ],
        "recommendation": "교차로 다중 객체 예측 모델 고도화 및 안전 여유거리 정책 조정 권장",
    },
}


def run_health_check(scenario_key: str) -> dict:
    """Returns a fixed diagnosis for the given scenario.

    TODO(model swap): replace this lookup with a call into the real
    multi-module health-check pipeline. Keep the return shape identical:
    {overall, status, modules, issues, recommendation}.
    """
    return _HEALTH_FIXTURES[scenario_key]


# ---------------------------------------------------------------------------
# 사고 후 · 다중 AI 토론 기반 원인 진단 (Post-Accident Root Cause Debate)
# ---------------------------------------------------------------------------

ROOT_CAUSE_SCENARIOS = {
    "night_pedestrian": "야간 보행자 인식 실패",
    "rain_braking": "우천 시 제동 지연",
    "construction_avoid": "공사구간 회피 실패",
    "intersection_signal": "교차로 신호 오인식",
}

_ROOT_CAUSE_FIXTURES = {
    "night_pedestrian": {
        "timeline": [
            ("Perception", "issue"),
            ("Prediction", "issue"),
            ("Planning", "normal"),
            ("Control", "issue"),
        ],
        "experts": [
            ("Vision", "eye", "야간 저조도 환경에서 보행자 인식 신뢰도가 급락했습니다. 카메라 단독 인지의 한계로 보입니다."),
            ("Control", "sliders", "인지 지연으로 인해 급제동 명령이 충돌 0.6초 전에야 발동됐습니다. 대응 여유가 부족했습니다."),
            ("Planning", "map", "회피 경로 탐색이 제동 판단과 동시에 시작되어 우선순위 조정이 늦었습니다."),
        ],
        "root_cause": "야간 환경 보행자 인식 실패 → 위험 예측 지연 → 제동 실패",
        "treatment": [
            "야간·저조도 보행자 데이터셋 보강 및 인식 모델 재학습",
            "카메라·LiDAR 센서 퓨전 가중치 조정",
            "제동 타이밍 정책 최적화",
        ],
    },
    "rain_braking": {
        "timeline": [
            ("Perception", "normal"),
            ("Prediction", "issue"),
            ("Planning", "normal"),
            ("Control", "issue"),
        ],
        "experts": [
            ("Vision", "eye", "차선·전방 차량 인식 자체는 안정적이었습니다. 우천으로 인한 시야 저하는 크지 않았습니다."),
            ("Control", "sliders", "노면 마찰력 추정치가 실제보다 높게 잡혀 제동 거리가 예측보다 길어졌습니다."),
            ("Planning", "map", "제동 거리 재계산이 늦게 반영되며 감속 시작 시점이 지연됐습니다."),
        ],
        "root_cause": "우천 노면 마찰력 오추정 → 제동거리 예측 오차 → 제동 지연",
        "treatment": [
            "우천·젖은 노면 마찰력 추정 모델 재보정",
            "실시간 노면 상태 센서 데이터 반영 로직 추가",
            "우천 조건 전용 제동 안전 마진 정책 도입",
        ],
    },
    "construction_avoid": {
        "timeline": [
            ("Perception", "issue"),
            ("Prediction", "normal"),
            ("Planning", "issue"),
            ("Control", "normal"),
        ],
        "experts": [
            ("Vision", "eye", "임시 표지판과 라바콘 배치가 학습 데이터와 달라 인식률이 낮았습니다."),
            ("Control", "sliders", "제어 명령 자체는 정상 범위였습니다. 문제는 상위 경로 판단에 있었습니다."),
            ("Planning", "map", "협로 재탐색 알고리즘이 대안 경로를 늦게 산출해 회피가 지연됐습니다."),
        ],
        "root_cause": "임시 표지판 인식 실패 → 경로 재탐색 지연 → 회피 실패",
        "treatment": [
            "공사구간 임시 표지판·라바콘 인식 데이터 확충",
            "협로 경로 재탐색 알고리즘 응답 속도 개선",
            "공사구간 진입 시 사전 감속 정책 강화",
        ],
    },
    "intersection_signal": {
        "timeline": [
            ("Perception", "normal"),
            ("Prediction", "issue"),
            ("Planning", "issue"),
            ("Control", "normal"),
        ],
        "experts": [
            ("Vision", "eye", "신호등 인식 자체는 정확했습니다. 문제는 교차 차량의 진입 의도 예측이었습니다."),
            ("Control", "sliders", "최종 급정지 대응은 규격 내에서 이뤄졌습니다."),
            ("Planning", "map", "무신호 교차로에서 타 차량의 우선순위를 잘못 판단해 진입을 강행했습니다."),
        ],
        "root_cause": "교차 차량 진입 의도 예측 오류 → 우선순위 오판 → 근접 진입",
        "treatment": [
            "다중 객체 진입 의도 예측 모델 고도화",
            "무신호 교차로 우선순위 판단 규칙 재정의",
            "교차로 접근 시 안전 여유거리 정책 강화",
        ],
    },
}


def run_root_cause(scenario_key: str) -> dict:
    """Returns a fixed multi-expert debate result for the given scenario.

    TODO(model swap): replace this lookup with the real multi-agent (MLLM
    Debate) pipeline call. Keep the return shape identical:
    {timeline, experts, root_cause, treatment}.
    """
    return _ROOT_CAUSE_FIXTURES[scenario_key]
