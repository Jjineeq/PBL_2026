"""Render helpers for the AI Hospital PoC demo page (pages/1_🩺_...).

Pure HTML-string builders — the caller passes the result to a single
st.markdown(unsafe_allow_html=True) call. See components/landing.py's
module docstring for why these must stay single-call, un-split blocks.
"""

from components.icons import icon

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
            <h4>{result['root_cause']}</h4>
            <ul class="issue-list" style="margin-top:14px;">{treatment_html}</ul>
        </div>
    </div>
    """
