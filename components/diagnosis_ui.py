"""Render helpers for the AI Hospital PoC demo page (pages/1_🩺_...).

Pure HTML-string builders — the caller passes the result to a single
st.markdown(unsafe_allow_html=True) call. See components/landing.py's
module docstring for why these must stay single-call, un-split blocks.
"""

from components.icons import icon
from logic.diagnosis import ROOT_CAUSE_AI_REQUEST, STATUS_AI_REQUEST

_STATUS_LABEL = {"ok": "정상", "warn": "주의", "bad": "위험"}
_EXPERT_ICON = {"Vision": "eye", "Control": "sliders", "Planning": "map"}


def gauge_status_color(status: str) -> str:
    return {"ok": "var(--accent-teal)", "warn": "#ffb140", "bad": "var(--accent-red-2)"}[status]


def render_health_result(result: dict, scenario_label: str) -> str:
    status = result["status"]
    color = gauge_status_color(status)
    modules_html = "".join(
        f"""
        <div class="module-bar-row">
            <div class="m-label">{name}</div>
            <div class="module-bar-track"><div class="module-bar-fill" style="width:{score}%;"></div></div>
            <div class="m-val">{score}</div>
        </div>
        """
        for name, score in result["modules"]
    )

    if result["issues"]:
        issues_html = "".join(
            f"""
            <li><span class="rank">{i}</span>{name}<span class="drop">{drop}%</span></li>
            """
            for i, (name, drop) in enumerate(result["issues"], start=1)
        )
    else:
        issues_html = '<li><span class="rank">✓</span>이상 징후가 발견되지 않았습니다.</li>'

    return f"""
    <div class="glass-card reveal" style="padding:34px;">
        <div class="gauge-status {status}">{scenario_label} · {_STATUS_LABEL[status]}</div>
        <div class="ai-request-badge {status}">{STATUS_AI_REQUEST[status]}</div>
        <p style="color:var(--text-mid);font-size:1rem;line-height:1.7;margin:2px 0 0 0;">{result['situation']}</p>
        <div class="gauge-wrap" style="margin-top:22px;">
            <div class="gauge" style="--pct:{result['overall']};--gauge-color:{color};">
                <div class="gauge-inner">
                    <div class="score">{result['overall']}</div>
                    <div class="of100">/ 100</div>
                </div>
            </div>
            <div style="flex:1;min-width:220px;">
                <div class="module-bars">{modules_html}</div>
            </div>
        </div>
        <ul class="issue-list">{issues_html}</ul>
        <div class="verdict-panel" style="margin-top:22px;">
            <div class="vlabel">Recommendation</div>
            <p>{result['recommendation']}</p>
        </div>
    </div>
    """


_TONE_COLOR = {"ok": "var(--accent-teal)", "warn": "#ffb140", "bad": "var(--accent-red-2)"}


def render_prediction_accuracy(analysis: dict) -> str:
    """Cross-check panel: did the matching pre-accident health check's
    weak-module call actually predict what went wrong? Reuses the
    compact-panel/icon-list pattern (single wrapping <span> per row) rather
    than a bare flex row with loose text + <b> siblings — that combination
    is what fragmented the stat-line text on mobile (see style.css), so
    every row's description + verdict badge stays inside one span."""
    rows_html = "".join(
        f'<li><span class="ic" style="color:{_TONE_COLOR[r["tone"]]};">{icon(r["icon"], 15)}</span>'
        f'<span>{r["module"]} {r["score"]}점 · 사전 판정 {"취약" if r["flagged_weak"] else "양호"} · '
        f'실제 사고 {"관여함" if r["involved"] else "관여 안 함"} '
        f'— <b style="color:{_TONE_COLOR[r["tone"]]};">{r["label"]}</b></span></li>'
        for r in analysis["rows"]
    )

    parts = [
        f"4개 모듈 중 {analysis['hit_count']}개는 사전 건강검진 판단과 실제 사고 원인이 일치했습니다."
    ]
    if analysis["blind_spots"]:
        parts.append(
            f"{', '.join(analysis['blind_spots'])} 모듈은 사전 검진에서 양호로 판단됐지만 실제로는 사고에 관여했습니다 "
            "— 건강검진만으로는 잡아내지 못한 사각지대입니다."
        )
    if analysis["false_alarms"]:
        parts.append(
            f"{', '.join(analysis['false_alarms'])} 모듈은 사전에 취약 신호가 있었지만 "
            "이번 사고에는 직접 관여하지 않았습니다."
        )
    summary = " ".join(parts)

    return f"""
    <div class="compact-panel reveal" style="margin-top:22px;">
        <div class="ph-label">Predictive Accuracy · 사전 건강검진 vs 실제 사고</div>
        <h4>{analysis['health_scenario_label']} 사전 검진이 실제 원인을 얼마나 맞췄을까요</h4>
        <ul>{rows_html}</ul>
        <p style="color:var(--text-mid);font-size:0.94rem;line-height:1.7;margin-top:14px;padding-top:14px;border-top:1px solid rgba(255,255,255,0.08);">
            {summary}
        </p>
    </div>
    """


def render_module_note(module_name: str, note: str) -> str:
    return f"""
    <div class="verdict-panel reveal" style="margin-top:16px;">
        <div class="vlabel">{module_name} 모듈 상세</div>
        <p>{note}</p>
    </div>
    """


def render_root_cause_result(result: dict, scenario_label: str) -> str:
    nodes = []
    for i, (stage, state, time_label) in enumerate(result["timeline"]):
        cls = "active" if state == "issue" else ""
        nodes.append(
            f'<div class="timeline-node {cls}"><div class="dot"></div>'
            f'<div class="t-label">{stage}</div><div class="t-time">{time_label}</div></div>'
        )
        if i < len(result["timeline"]) - 1:
            nodes.append('<div class="timeline-line"></div>')
    timeline_html = "".join(nodes)

    experts_html = "".join(
        f"""
        <div class="expert-bubble">
            <div class="avatar">{icon(_EXPERT_ICON.get(name, 'search'), 18)}</div>
            <div>
                <div class="name">{name} Expert</div>
                <p>{text}</p>
            </div>
        </div>
        """
        for name, _icon_name, text in result["experts"]
    )

    treatment_html = "".join(f"<li>{t}</li>" for t in result["treatment"])

    return f"""
    <div class="glass-card reveal" style="padding:34px;">
        <div class="ph-label" style="color:var(--accent-blue);font-size:0.78rem;font-weight:700;letter-spacing:0.06em;text-transform:uppercase;">
            {scenario_label}
        </div>
        <p style="color:var(--text-mid);font-size:1rem;line-height:1.7;margin:10px 0 0 0;">{result['situation']}</p>
        <div class="timeline-row">{timeline_html}</div>
        <div class="expert-row">{experts_html}</div>
        <div class="verdict-panel">
            <div class="vlabel">Root Cause</div>
            <div class="ai-request-badge warn" style="margin-bottom:10px;">{ROOT_CAUSE_AI_REQUEST}</div>
            <h4>{result['root_cause']}</h4>
            <ul class="issue-list" style="margin-top:14px;">{treatment_html}</ul>
            <p style="color:var(--text-lo);font-size:0.82rem;margin-top:14px;line-height:1.6;">
                ※ 관제사는 원인 진단과 조치 방향을 확인·승인하는 역할이며, 실제 재학습·모델 배포는
                검증을 거쳐 별도 ML 파이프라인에서 진행됩니다.
            </p>
        </div>
    </div>
    """
