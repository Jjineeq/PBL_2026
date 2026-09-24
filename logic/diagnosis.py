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

# What the AI is asking the controller to do, keyed by the same ok/warn/bad
# status this page's fixtures already carry — same "요청" framing as the
# Control Room's AI_REQUEST_BY_BAND (logic/health_score.py), just against
# this page's own 3-tier status instead of the 5-band Health Score system.
STATUS_AI_REQUEST = {
    "ok": "요청 없음 · 자율 운행 중",
    "warn": "🔔 확인 요청",
    "bad": "⚠ 긴급 개입 요청",
}

_HEALTH_FIXTURES = {
    "normal": {
        "overall": 94,
        "status": "ok",
        "situation": "특이 시나리오 없이 주간 · 맑음 조건에서 평이한 도심 구간을 주행 중입니다.",
        "modules": [("인지", 96), ("예측", 95), ("계획", 93), ("제어", 92)],
        "module_notes": {
            "인지": "카메라 · LiDAR 융합 인식률이 96점으로 안정적이며 최근 오탐지 이력이 없습니다.",
            "예측": "주변 차량 · 보행자 궤적 예측 오차가 평균 범위 안에서 유지되고 있습니다.",
            "계획": "표준 경로 계획 로직이 정상 작동하며 재계획 빈도가 낮습니다.",
            "제어": "조향 · 제동 응답 지연이 기준치 이하로 안정적으로 유지되고 있습니다.",
        },
        "issues": [],
        "recommendation": "특이 이상 없음 · 정기 모니터링 주기 유지",
    },
    "night": {
        "overall": 48,
        "status": "bad",
        "situation": "가로등이 드문 야간 도로에서 대비가 낮은 물체를 인식해야 하는 구간을 주행 중입니다.",
        "modules": [("인지", 42), ("예측", 55), ("계획", 61), ("제어", 58)],
        "module_notes": {
            "인지": "저조도 환경에서 카메라 단독 인지 신뢰도가 42점까지 급락했습니다.",
            "예측": "인지 지연이 누적되며 주변 객체 궤적 예측 불확실성이 커졌습니다.",
            "계획": "예측 불확실성 탓에 경로 재계획이 평소보다 잦아지고 있습니다.",
            "제어": "짧은 반응 여유로 인해 급제동 명령 발동이 지연됐습니다.",
        },
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
        "situation": "우천으로 노면이 젖고 시야가 제한된 구간에서 제동 성능 저하가 감지됐습니다.",
        "modules": [("인지", 68), ("예측", 64), ("계획", 60), ("제어", 52)],
        "module_notes": {
            "인지": "빗물 산란으로 차선 인식이 흔들리며 신뢰도가 68점으로 떨어졌습니다.",
            "예측": "젖은 노면 마찰력 추정 오차로 제동 거리 예측이 부정확해졌습니다.",
            "계획": "제동 거리 재계산이 지연되며 감속 시작 시점이 늦어지고 있습니다.",
            "제어": "LiDAR 반사 노이즈 증가로 제어 명령 안정성이 52점까지 하락했습니다.",
        },
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
        "situation": "공사구간 임시 표지판과 협로가 이어지는 구간을 통과하고 있습니다.",
        "modules": [("인지", 71), ("예측", 60), ("계획", 44), ("제어", 55)],
        "module_notes": {
            "인지": "임시 표지판 · 라바콘 배치가 학습 데이터와 달라 인식률이 낮아졌습니다.",
            "예측": "협로 진입 차량 간의 간격 예측 신뢰도가 다소 저하됐습니다.",
            "계획": "경로 재탐색 알고리즘이 대안 경로 산출에 시간이 걸리며 44점까지 하락했습니다.",
            "제어": "협로 통과 시 조향 여유가 줄며 제어 안정성이 낮아졌습니다.",
        },
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
        "situation": "신호가 없는 교차로에서 다수 차량과 진입 우선순위를 조율해야 하는 구간입니다.",
        "modules": [("인지", 74), ("예측", 69), ("계획", 58), ("제어", 62)],
        "module_notes": {
            "인지": "교차 차량 · 보행자 다중 인식은 74점으로 준수한 편입니다.",
            "예측": "타 차량의 진입 의도 예측이 지연되며 신뢰도가 낮아졌습니다.",
            "계획": "우선순위 판단 로직이 보수적으로 작동해 계획 점수가 58점에 머물렀습니다.",
            "제어": "급정지 대응 여유가 줄어 제어 점수가 62점으로 나타났습니다.",
        },
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
    {overall, status, situation, modules, module_notes, issues, recommendation}.
    """
    return _HEALTH_FIXTURES[scenario_key]


# ---------------------------------------------------------------------------
# 사고 후 · 모듈별 소견 종합 기반 원인 진단 (Post-Accident Root Cause)
# ---------------------------------------------------------------------------

ROOT_CAUSE_SCENARIOS = {
    "night_pedestrian": "야간 보행자 인식 실패",
    "rain_braking": "우천 시 제동 지연",
    "construction_avoid": "공사구간 회피 실패",
    "intersection_signal": "교차로 신호 오인식",
}

# All four root-cause scenarios ask the controller for the same kind of
# thing — sign off on the proposed retraining/policy fix before it ships —
# so this stays a single shared phrase rather than one per scenario.
ROOT_CAUSE_AI_REQUEST = "🔔 재학습·정책 변경 승인 요청"

_ROOT_CAUSE_FIXTURES = {
    "night_pedestrian": {
        "situation": "야간 저조도 주택가 도로에서 보행자가 차량 진행 경로로 갑자기 진입한 상황입니다.",
        "timeline": [
            ("Perception", "issue", "T-3.2s"),
            ("Prediction", "issue", "T-2.4s"),
            ("Planning", "normal", "T-1.5s"),
            ("Control", "issue", "T-0.6s"),
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
        "situation": "우천 시 젖은 간선도로에서 선행 차량과의 거리가 급격히 좁혀진 상황입니다.",
        "timeline": [
            ("Perception", "normal", "T-4.0s"),
            ("Prediction", "issue", "T-2.8s"),
            ("Planning", "normal", "T-1.9s"),
            ("Control", "issue", "T-0.9s"),
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
        "situation": "공사구간 임시 차선 통제 구간에서 협로 회피 경로가 필요했던 상황입니다.",
        "timeline": [
            ("Perception", "issue", "T-3.6s"),
            ("Prediction", "normal", "T-2.5s"),
            ("Planning", "issue", "T-1.3s"),
            ("Control", "normal", "T-0.5s"),
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
        "situation": "무신호 교차로에서 교차 방향 차량과 근접 진입이 발생한 상황입니다.",
        "timeline": [
            ("Perception", "normal", "T-3.0s"),
            ("Prediction", "issue", "T-2.2s"),
            ("Planning", "issue", "T-1.1s"),
            ("Control", "normal", "T-0.4s"),
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
    """Returns a fixed multi-module diagnosis result for the given scenario.

    TODO(model swap): replace this lookup with the real multi-module
    diagnosis pipeline call. Keep the return shape identical:
    {situation, timeline, experts, root_cause, treatment}. Each timeline
    entry is (stage, state, time_label).
    """
    return _ROOT_CAUSE_FIXTURES[scenario_key]


# ---------------------------------------------------------------------------
# 사전 건강검진 vs 실제 사고 — 예측 정확도 분석
#
# Each root-cause scenario has a same-situation health-check scenario (both
# "night", both "rain", ...). This cross-checks: of the modules the health
# check flagged as weak *beforehand*, how many actually turn out to be part
# of the real accident's timeline? A module that was called fine but was
# actually involved is a genuine blind spot in the health check — exactly
# the kind of gap human review exists to catch.
# ---------------------------------------------------------------------------

ROOT_CAUSE_TO_HEALTH_SCENARIO = {
    "night_pedestrian": "night",
    "rain_braking": "rain",
    "construction_avoid": "construction",
    "intersection_signal": "intersection",
}

_STAGE_TO_MODULE_LABEL = {"Perception": "인지", "Prediction": "예측", "Planning": "계획", "Control": "제어"}

_VERDICT_META = {
    "hit": {"label": "적중", "tone": "ok", "icon": "check"},
    "correct_clear": {"label": "정상 판단", "tone": "ok", "icon": "check"},
    "blind_spot": {"label": "사각지대", "tone": "bad", "icon": "alert"},
    "false_alarm": {"label": "과잉 경보", "tone": "warn", "icon": "alert"},
}


def analyze_prediction_accuracy(rc_key: str) -> dict | None:
    """Ranks the matching health-check scenario's 4 modules by score — the
    bottom two are what the health check flagged as weak beforehand — then
    compares that flag against whether the real accident's timeline marks
    that module as an "issue". Returns None if there's no matching
    health-check scenario (shouldn't happen for the 4 current fixtures, but
    keeps this safe if scenarios are added asymmetrically later).
    """
    health_key = ROOT_CAUSE_TO_HEALTH_SCENARIO.get(rc_key)
    if not health_key:
        return None

    health = _HEALTH_FIXTURES[health_key]
    timeline = _ROOT_CAUSE_FIXTURES[rc_key]["timeline"]
    involved = {_STAGE_TO_MODULE_LABEL[stage] for stage, state, _ in timeline if state == "issue"}

    ranked = sorted(health["modules"], key=lambda m: m[1])
    flagged_weak = {name for name, _ in ranked[:2]}

    rows = []
    for name, score in health["modules"]:
        was_flagged = name in flagged_weak
        was_involved = name in involved
        if was_flagged and was_involved:
            verdict = "hit"
        elif was_flagged and not was_involved:
            verdict = "false_alarm"
        elif not was_flagged and was_involved:
            verdict = "blind_spot"
        else:
            verdict = "correct_clear"
        rows.append(
            {
                "module": name,
                "score": score,
                "flagged_weak": was_flagged,
                "involved": was_involved,
                "verdict": verdict,
                **_VERDICT_META[verdict],
            }
        )

    return {
        "health_scenario_label": HEALTH_SCENARIOS[health_key],
        "rows": rows,
        "hit_count": sum(1 for r in rows if r["verdict"] in ("hit", "correct_clear")),
        "blind_spots": [r["module"] for r in rows if r["verdict"] == "blind_spot"],
        "false_alarms": [r["module"] for r in rows if r["verdict"] == "false_alarm"],
    }
