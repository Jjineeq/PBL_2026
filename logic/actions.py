"""
Prevention action catalog for the Control Room's Guide step.

Each module's option list is exactly what the controller can choose from
when that module's score drops out of the "정상" band (< ACTION_MODULE_THRESHOLD,
same cutoff as MODULE_BANDS[m][0][0] in logic/health_score.py). The controller
picks exactly one action per weak module, mirroring how a real operator would
select a single mitigating policy rather than stacking every option.
"""

import copy

from logic.health_score import evaluate_scenario

PREVENTION_ACTIONS = {
    "perception": [
        "보행자 밀집 골목길 회피",
        "인도 인접 차선 회피",
        "속도 상한 하향",
        "안전거리 확대",
        "횡단보도 접근 시 사전 감속",
        "원격 모니터링 준비",
    ],
    "prediction": [
        "추월 제한",
        "차선 변경 최소화",
        "합류구간 회피",
        "비보호 좌회전 회피",
        "주변 차량과의 거리 확대",
        "상호작용 객체가 적은 경로 선택",
    ],
    "planning": [
        "복잡한 교차로 회피",
        "직진 중심의 단순 경로 선택",
        "차선 선택지 축소",
        "유턴·비보호 좌회전 금지",
        "차선 유지 우선",
        "반복 재계획 시 Safe Zone 이동",
    ],
    "control": [
        "최대 속도·가속도 제한",
        "급차선 변경 및 급조향 금지",
        "곡률이 큰 도로 회피",
        "넓은 차선이 있는 도로 선택",
        "제어오차 지속 시 안전지점 이동",
        "심각한 경우 최소위험상태 전환",
    ],
}

# Same cutoff as the "정상" band lower bound in MODULE_BANDS — below this,
# the module needs a controller-selected prevention action.
ACTION_MODULE_THRESHOLD = 85

# The spec doesn't define a numeric action -> score formula, so these are
# illustrative, clearly-labeled recovery estimates (not a validated model) —
# but each action gets its own weight, roughly by how restrictive/direct the
# intervention is, so picking a different option visibly moves the preview
# instead of every option in a module looking identical.
ACTION_EFFECTS = {
    "perception": {
        "보행자 밀집 골목길 회피": 0.22,
        "인도 인접 차선 회피": 0.16,
        "속도 상한 하향": 0.12,
        "안전거리 확대": 0.10,
        "횡단보도 접근 시 사전 감속": 0.14,
        "원격 모니터링 준비": 0.06,
    },
    "prediction": {
        "추월 제한": 0.10,
        "차선 변경 최소화": 0.12,
        "합류구간 회피": 0.16,
        "비보호 좌회전 회피": 0.18,
        "주변 차량과의 거리 확대": 0.14,
        "상호작용 객체가 적은 경로 선택": 0.22,
    },
    "planning": {
        "복잡한 교차로 회피": 0.20,
        "직진 중심의 단순 경로 선택": 0.16,
        "차선 선택지 축소": 0.10,
        "유턴·비보호 좌회전 금지": 0.14,
        "차선 유지 우선": 0.08,
        "반복 재계획 시 Safe Zone 이동": 0.22,
    },
    "control": {
        "최대 속도·가속도 제한": 0.12,
        "급차선 변경 및 급조향 금지": 0.14,
        "곡률이 큰 도로 회피": 0.16,
        "넓은 차선이 있는 도로 선택": 0.10,
        "제어오차 지속 시 안전지점 이동": 0.18,
        "심각한 경우 최소위험상태 전환": 0.24,
    },
}


def simulate_prevention_effect(vehicle: dict, chosen_actions: dict[str, list[str]]) -> dict:
    """Recomputes Health Score assuming each weak module's components are
    boosted by the *sum* of its chosen actions' weights (a controller can
    stack more than one action per module), for the Guide step's live
    before/after preview. Runs through the same evaluate_scenario()
    pipeline as the real score, so the *math* is real — only the size of
    each action's boost is an estimate."""
    sim_vehicle = copy.deepcopy(vehicle)
    for module, actions in chosen_actions.items():
        if not actions:
            continue
        boost = sum(ACTION_EFFECTS[module][a] for a in actions)
        for key, value in sim_vehicle["components"][module].items():
            sim_vehicle["components"][module][key] = min(0.95, value + boost)
    return evaluate_scenario(sim_vehicle)
