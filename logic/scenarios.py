"""
Scenario presets for the Health Score demo page.

"case1" and "case2" reproduce the two worked examples from
"자율주행 Health Score 점수체계" (PDF 사례 1 / 사례 2) verbatim — same
component health values, same context penalty, same interpretation
text — so the computed numbers in logic/health_score.py can be checked
against the document (Health Score 68 / 24 respectively). "normal" is a
constructed healthy baseline for contrast, not from the document.
"""

SCENARIOS = {
    "normal": {
        "label": "정상 주행",
        "situation": [
            "주간 · 맑음, 평상시 주행 상태",
            "보행자·장애물 없음",
            "전 센서 정상 동작",
        ],
        "components": {
            "perception": {
                "sensor_quality": 0.95,
                "sensor_fusion": 0.95,
                "track_stability": 0.95,
                "perception_certainty": 0.95,
                "critical_detection": 0.95,
            },
            "prediction": {
                "trajectory_certainty": 0.95,
                "intent_stability": 0.95,
                "pred_obs_match": 0.95,
                "path_clearance": 0.95,
                "horizon_margin": 0.95,
            },
            "planning": {
                "collision_margin": 0.95,
                "stop_feasibility": 0.95,
                "path_feasibility": 0.95,
                "plan_stability": 0.95,
                "fallback_availability": 0.95,
            },
            "control": {
                "tracking_accuracy": 0.95,
                "response_speed": 0.95,
                "vehicle_stability": 0.95,
                "braking_margin": 0.95,
                "ride_smoothness": 0.95,
            },
        },
        "component_notes": {},
        "context_penalty": 0,
        "context_penalty_reason": "위험 요인 없음",
        "interpretations": {
            "perception": "센서 품질과 객체 인식이 모두 안정적으로 유지되고 있습니다.",
            "prediction": "주변 객체의 이동 예측이 안정적으로 이뤄지고 있습니다.",
            "planning": "충분한 안전 여유를 가진 경로가 유지되고 있습니다.",
            "control": "계획된 조치를 차량이 정상적으로 수행하고 있습니다.",
        },
        "operational_notes": [
            "네 모듈 모두 안정 구간",
            "특이 이상 징후 없음",
        ],
        "actions": [
            "정상 운행 지속",
            "정기 모니터링 주기 유지",
        ],
    },
    "case1": {
        "label": "사례 1 · 보행자 보도 정지",
        "situation": [
            "야간 우천, 차량 속도 35km/h",
            "보행자: 보도 위에서 정지",
            "카메라: 빗물과 반사광으로 보행자 분류 불안정",
            "LiDAR: 보행자 형태 객체를 간헐적으로 유지",
            "보행자의 차도 방향 움직임 없음",
        ],
        "components": {
            "perception": {
                "sensor_quality": 0.55,
                "sensor_fusion": 0.40,
                "track_stability": 0.50,
                "perception_certainty": 0.55,
                "critical_detection": 0.70,
            },
            "prediction": {
                "trajectory_certainty": 0.65,
                "intent_stability": 0.85,
                "pred_obs_match": 0.75,
                "path_clearance": 0.90,
                "horizon_margin": 0.75,
            },
            "planning": {
                "collision_margin": 0.85,
                "stop_feasibility": 0.90,
                "path_feasibility": 0.95,
                "plan_stability": 0.85,
                "fallback_availability": 0.90,
            },
            "control": {
                "tracking_accuracy": 0.95,
                "response_speed": 0.95,
                "vehicle_stability": 0.92,
                "braking_margin": 0.90,
                "ride_smoothness": 0.90,
            },
        },
        "component_notes": {},
        "context_penalty": 2,
        "context_penalty_reason": "보행자가 보도에 정지",
        "interpretations": {
            "perception": "보행자 존재 자체는 간헐적으로 확인되지만 센서 간 결과와 추적이 불안정하므로, "
            "정상적인 인지 결과로 신뢰하기 어렵습니다.",
            "prediction": "보행자의 위치 인식은 불안정하지만 보도에 정지해 있고 차량 경로와 충분히 분리되어 "
            "있어, 즉각적인 행동위험은 낮습니다.",
            "planning": "감속하고 현재 차선을 유지하면 충분히 안전하게 통과하거나 정지할 수 있습니다.",
            "control": "차량은 자동 감속 및 필요 시 정지를 정상적으로 수행할 수 있습니다.",
        },
        "operational_notes": [
            "인지 결과는 불안정함",
            "그러나 예측·계획·제어는 비교적 정상임",
            "보행자는 차량 경로에 진입하지 않음",
            "차량 자체의 감속과 안전거리 확보로 위험을 통제할 수 있음",
        ],
        "actions": [
            "35km/h에서 20km/h로 자동 감속",
            "차선변경 제한",
            "보행자 집중 추적",
            "관제사에게 경고",
            "관제사는 원인과 자동조치 확인",
            "즉각적인 수동 개입이나 운행 중지는 요구하지 않음",
        ],
    },
    "case2": {
        "label": "사례 2 · 보행자 차도 진입",
        "situation": [
            "야간 우천, 초기 속도 35km/h",
            "보행자가 정지 상태에서 차도 방향으로 갑자기 이동 시작",
            "카메라-LiDAR 불일치 지속",
            "보행자 예상경로가 차량 경로와 교차",
        ],
        "components": {
            "perception": {
                "sensor_quality": 0.50,
                "sensor_fusion": 0.35,
                "track_stability": 0.45,
                "perception_certainty": 0.45,
                "critical_detection": 0.65,
            },
            "prediction": {
                "trajectory_certainty": 0.25,
                "intent_stability": 0.20,
                "pred_obs_match": 0.30,
                "path_clearance": 0.10,
                "horizon_margin": 0.40,
            },
            "planning": {
                "collision_margin": 0.20,
                "stop_feasibility": 0.55,
                "path_feasibility": 0.80,
                "plan_stability": 0.50,
                "fallback_availability": 0.60,
            },
            "control": {
                "tracking_accuracy": 0.92,
                "response_speed": 0.90,
                "vehicle_stability": 0.85,
                "braking_margin": 0.70,
                "ride_smoothness": 0.65,
            },
        },
        "component_notes": {
            "prediction": {
                "trajectory_certainty": "돌발 이동으로 분산 증가",
                "intent_stability": "정지에서 횡단으로 급변",
                "pred_obs_match": "직전 예측과 실제 행동 불일치",
                "path_clearance": "차량 경로와 교차",
                "horizon_margin": "대응 가능한 시간이 짧음",
            },
            "planning": {
                "collision_margin": "TTC 급감",
                "stop_feasibility": "긴급제동 시 정지 가능",
                "path_feasibility": "직선 감속은 실행 가능",
                "plan_stability": "정상주행 계획을 즉시 폐기",
                "fallback_availability": "정지공간은 존재",
            },
            "control": {
                "tracking_accuracy": "차량 경로 정상",
                "response_speed": "제동 응답 정상",
                "vehicle_stability": "우천으로 노면 마찰 일부 저하",
                "braking_margin": "높은 감속 요구",
                "ride_smoothness": "급제동으로 jerk 증가",
            },
        },
        "context_penalty": 15,
        "context_penalty_reason": "보행자 경로가 차량 경로와 교차",
        "interpretations": {
            "perception": "보행자의 존재는 확인되지만 위치와 행동상태를 신뢰성 있게 파악하기 어렵습니다.",
            "prediction": "보행자의 미래 움직임을 안정적으로 예측할 수 없고, 위험한 궤적이 차량 경로와 "
            "직접 교차합니다.",
            "planning": "정상운행을 유지하는 계획은 안전하지 않지만, 긴급제동과 완전 정지는 아직 실행 "
            "가능한 상태입니다.",
            "control": "상황은 위험하지만 차량 제어기와 제동장치는 긴급정지 명령을 수행할 수 있습니다.",
        },
        "operational_notes": [
            "인지 결과가 불안정함",
            "예측모델이 보행자의 행동을 안정적으로 판단하지 못함",
            "보행자 예상경로와 차량 경로가 교차함",
            "정상운행 계획은 더 이상 유효하지 않음",
            "제어기능은 남아 있으므로 긴급정지가 가능함",
        ],
        "actions": [
            "시스템이 관제사 승인 없이 긴급제동",
            "차선변경 및 회피조향 제한",
            "비상등 작동",
            "관제 우선순위를 최우선으로 변경",
            "관제사가 완전 정지 유지 및 운행 재개 여부 판단",
            "인지 상태가 회복되지 않으면 운행 종료 또는 차량 회수",
        ],
    },
}
