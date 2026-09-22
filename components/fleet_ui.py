"""Render helpers for the Control Room's Detect step (fleet-wide view).

Same single-call HTML-string rule as the other components/*_ui.py modules.
"""

from components.icons import icon
from logic.health_score import BAND_COLORS, BAND_EMOJI, HEALTH_BANDS, MODULE_LABELS


def render_kpi_strip(fleet: list[dict]) -> str:
    counts = {band[2]: 0 for band in HEALTH_BANDS}
    for v in fleet:
        band_label = v["_result"]["health"]["band"][2]
        counts[band_label] += 1

    total_item = f'<div class="impact-item"><div class="ic">🚘</div><span>총 {len(fleet)}대 운행 중</span></div>'
    band_items = "".join(
        f'<div class="impact-item"><div class="ic">{BAND_EMOJI.get(label, "⚪")}</div>'
        f"<span>{label} {count}대</span></div>"
        for label, count in counts.items()
    )
    return f'<div class="impact-row reveal">{total_item}{band_items}</div>'


def render_fleet_table(fleet: list[dict], limit: int | None = 15) -> str:
    ordered = sorted(fleet, key=lambda v: v["_result"]["health"]["health_final"])
    rows_data = ordered if limit is None else ordered[:limit]

    rows = []
    for v in rows_data:
        health = v["_result"]["health"]
        band = health["band"]
        color = BAND_COLORS.get(band[2], "#8892a8")
        score_display = int(round(health["health_final"]))
        weak_label = MODULE_LABELS[v["_weak_module"]]
        row_cls = "current" if band[2] != "정상" else ""
        rows.append(
            f'<tr class="{row_cls}"><td><span class="risk-dot" style="background:{color};"></span>'
            f"{band[2]}</td><td>{v['id']}</td><td>{v['route']}</td>"
            f"<td>{score_display}</td><td>{weak_label}</td></tr>"
        )
    body = "".join(rows)

    return f"""
    <div class="glass-card reveal" style="padding:26px;">
        <table class="band-table">
            <thead><tr><th>상태</th><th>차량</th><th>운행 구간</th><th>Health Score</th><th>최저 모듈</th></tr></thead>
            <tbody>{body}</tbody>
        </table>
    </div>
    """


def render_situation_panel(vehicle: dict) -> str:
    band = vehicle["_result"]["health"]["band"]
    items = "".join(
        f'<li><span class="ic">{icon("radio", 15)}</span>{s}</li>' for s in vehicle["situation"]
    )
    penalty = vehicle["context_penalty"]
    if penalty:
        items += (
            f'<li><span class="ic">{icon("alert", 15)}</span>'
            f"상황 페널티 적용: −{penalty}점 ({vehicle['context_penalty_reason']})</li>"
        )
    return f"""
    <div class="compact-panel reveal" style="margin-bottom:22px;">
        <div class="ph-label">Situation · 현재 상황</div>
        <h4>{vehicle['route']} 구간 운행 중 · {band[2]}</h4>
        <ul>{items}</ul>
    </div>
    """
