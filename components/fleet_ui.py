"""Render helpers for the Control Room's Detect step (fleet-wide view).

Same single-call HTML-string rule as the other components/*_ui.py modules,
except fleet_dataframe() which returns a pandas DataFrame for st.dataframe()
— that's what gives the Detect step real click-to-select rows (with
built-in scroll/sort) instead of a static HTML table plus a separate
dropdown to actually pick a vehicle.
"""

import pandas as pd

from components.icons import icon
from logic.health_score import AI_REQUEST_BY_BAND, BAND_EMOJI, HEALTH_BANDS, MODULE_LABELS


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


def fleet_dataframe(ordered: list[dict]) -> pd.DataFrame:
    """One row per vehicle, already sorted (caller passes `ordered`, worst
    Health Score first) — feeds st.dataframe(..., on_select="rerun",
    selection_mode="single-row") so clicking a row IS the vehicle picker,
    with native scroll/sort over the whole fleet instead of a capped static
    table plus a separate dropdown.

    Column order puts the highest-signal columns (state, id, score, what the
    AI is asking for) first — on a narrow phone the table can't show all 6
    columns without horizontal scroll, so the two longer/lower-priority text
    columns (route, weakest module) are pushed to the end instead of sitting
    between Health Score and AI 요청 and forcing an extra swipe to reach it."""
    rows = [
        {
            "상태": f"{BAND_EMOJI.get(v['_result']['health']['band'][2], '⚪')} {v['_result']['health']['band'][2]}",
            "차량": v["id"],
            "Health Score": int(round(v["_result"]["health"]["health_final"])),
            "AI 요청": AI_REQUEST_BY_BAND.get(v["_result"]["health"]["band"][2], ""),
            "운행 구간": v["route"],
            "최저 모듈": MODULE_LABELS[v["_weak_module"]],
        }
        for v in ordered
    ]
    return pd.DataFrame(rows)


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
