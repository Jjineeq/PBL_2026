"""Render helpers for the Health Score monitoring page.

Same rule as components/diagnosis_ui.py: each function returns a single
HTML string meant for exactly one mdutil.md() call — see
components/landing.py's module docstring for why partial/split calls
break CSS grid & table layouts under Streamlit.
"""

from logic.health_score import (
    BAND_COLORS,
    BAND_STATUS_CLASS,
    HEALTH_BANDS,
    HEALTH_WEIGHTS_DEFAULT,
    MODULE_BANDS,
    MODULE_LABELS,
    MODULE_ORDER,
    band_for,
)


def _status_class(band_label: str) -> str:
    return BAND_STATUS_CLASS.get(band_label, "normal")


def render_module_drilldown(module_key: str, scenario: dict, result: dict) -> str:
    label = MODULE_LABELS[module_key]
    score = result["modules"][module_key]
    breakdown = result["breakdowns"][module_key]
    band = band_for(score, MODULE_BANDS[module_key])
    notes = scenario.get("component_notes", {}).get(module_key, {})
    interpretation = scenario["interpretations"].get(module_key, "")

    rows = "".join(
        f"<tr><td>{b['label']}</td><td>{b['value']:.2f}</td><td>{b['weight']:.2f}</td>"
        f"<td>{b['contribution']:.3f}</td><td class=\"note\">{notes.get(b['key'], '')}</td></tr>"
        for b in breakdown
    )

    band_rows = "".join(
        f"<tr class=\"{'current' if bd[0] <= score <= bd[1] else ''}\">"
        f"<td>{bd[0]}–{bd[1]}</td><td>{bd[2]}</td><td>{bd[3]}</td><td>{bd[4]}</td></tr>"
        for bd in MODULE_BANDS[module_key]
    )

    return f"""
    <div class="glass-card reveal" style="padding:32px;">
        <div class="gauge-status {_status_class(band[2])}">{label} 점수 드릴다운 · {band[2]} ({score}점)</div>
        <table class="score-table">
            <thead><tr><th>구성요소</th><th>건전성 값</th><th>가중치</th><th>기여값</th><th>비고</th></tr></thead>
            <tbody>{rows}</tbody>
        </table>
        <div class="verdict-panel" style="margin-top:20px;">
            <div class="vlabel">해석</div>
            <p>{interpretation}</p>
        </div>
        <table class="band-table" style="margin-top:20px;">
            <thead><tr><th>점수</th><th>상태</th><th>운영상 의미</th><th>기본조치</th></tr></thead>
            <tbody>{band_rows}</tbody>
        </table>
    </div>
    """


def render_health_breakdown(scenario: dict, result: dict) -> str:
    health = result["health"]
    modules = result["modules"]
    band = health["band"]
    weights = HEALTH_WEIGHTS_DEFAULT
    terms = " + ".join(f"{weights[m]:.2f}×{modules[m]}" for m in MODULE_ORDER)
    worst_label = MODULE_LABELS[health["worst_module"]]
    final_display = int(round(health["health_final"]))

    band_rows = "".join(
        f"<tr class=\"{'current' if bd[0] <= health['health_final'] <= bd[1] else ''}\">"
        f"<td>{bd[0]}–{bd[1]}</td><td>{bd[2]}</td><td>{bd[3]}</td><td>{bd[4]}</td><td>{bd[5]}</td></tr>"
        for bd in HEALTH_BANDS
    )

    return f"""
    <div class="glass-card reveal" style="padding:34px;">
        <div class="gauge-status {_status_class(band[2])}">{scenario['label']} · Health Score {band[2]}</div>
        <div class="gauge-wrap">
            <div class="gauge" style="--pct:{health['health_final']};--gauge-color:{BAND_COLORS[band[2]]};">
                <div class="gauge-inner"><div class="score">{final_display}</div><div class="of100">/ 100</div></div>
            </div>
            <div style="flex:1;min-width:260px;">
                <div class="calc-step">
                    <span>① 상황 가중평균 (Savg)</span>
                    <code>{terms} = {health['savg']}</code>
                </div>
                <div class="calc-step">
                    <span>② 최저 모듈 반영 · 병목 = {worst_label} {health['worst_score']}점</span>
                    <code>0.7 × {health['savg']} + 0.3 × {health['worst_score']} = {health['health_base']}</code>
                </div>
                <div class="calc-step">
                    <span>③ 상황 페널티 적용 · {scenario['context_penalty_reason']}</span>
                    <code>{health['health_base']} − {health['context_penalty']} ≈ {final_display}</code>
                </div>
            </div>
        </div>
        <table class="band-table" style="margin-top:26px;">
            <thead><tr><th>Health Score</th><th>표시 구간</th><th>운영상 의미</th><th>관제 우선순위</th><th>운영조치</th></tr></thead>
            <tbody>{band_rows}</tbody>
        </table>
    </div>
    """


def render_comparison(scenario_a: dict, scenario_b: dict, result_a: dict, result_b: dict) -> str:
    ha, hb = result_a["health"], result_b["health"]
    rows = [
        ("인지 점수", result_a["modules"]["perception"], result_b["modules"]["perception"]),
        ("예측 점수", result_a["modules"]["prediction"], result_b["modules"]["prediction"]),
        ("계획 점수", result_a["modules"]["planning"], result_b["modules"]["planning"]),
        ("제어 점수", result_a["modules"]["control"], result_b["modules"]["control"]),
        ("상황 페널티", scenario_a["context_penalty"], scenario_b["context_penalty"]),
        ("Health Score", int(round(ha["health_final"])), int(round(hb["health_final"]))),
        ("운영구간", ha["band"][2], hb["band"][2]),
        ("관제 우선순위", ha["band"][4], hb["band"][4]),
        ("운영조치", ha["band"][5], hb["band"][5]),
    ]
    body = "".join(f"<tr><td>{k}</td><td>{a}</td><td>{b}</td></tr>" for k, a, b in rows)

    return f"""
    <div class="glass-card reveal" style="padding:30px;">
        <table class="band-table">
            <thead><tr><th>항목</th><th>{scenario_a['label']}</th><th>{scenario_b['label']}</th></tr></thead>
            <tbody>{body}</tbody>
        </table>
    </div>
    """


def render_report_view(scenario: dict, result: dict) -> str:
    health = result["health"]
    band = health["band"]
    final_display = int(round(health["health_final"]))

    situation_html = "".join(f"<li>{s}</li>" for s in scenario["situation"])
    notes_html = "".join(f"<li>{n}</li>" for n in scenario["operational_notes"])
    actions_html = "".join(f"<li>{a}</li>" for a in scenario["actions"])

    module_tables = []
    for key in MODULE_ORDER:
        label = MODULE_LABELS[key]
        score = result["modules"][key]
        rows = "".join(
            f"<tr><td>{b['label']}</td><td>{b['value']:.2f}</td><td>{b['weight']:.2f}</td>"
            f"<td>{b['contribution']:.3f}</td></tr>"
            for b in result["breakdowns"][key]
        )
        module_tables.append(
            f"""
            <h4>{label} 점수 · {score}</h4>
            <table class="score-table">
                <thead><tr><th>구성요소</th><th>건전성 값</th><th>가중치</th><th>기여값</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>
            <p class="report-interp">해석: {scenario['interpretations'].get(key, '')}</p>
            """
        )
    modules_html = "".join(module_tables)

    return f"""
    <div class="glass-card reveal report-doc" style="padding:36px;">
        <div class="gauge-status {_status_class(band[2])}">{scenario['label']} · Health Score {final_display} ({band[2]})</div>
        <h3>1. 상황</h3>
        <ul class="report-list">{situation_html}</ul>
        <h3>2. 모듈별 점수 계산</h3>
        {modules_html}
        <h3>3. Health Score 계산</h3>
        <p>Savg = {health['savg']} → 최저모듈 반영 {health['health_base']} → 상황 페널티 {health['context_penalty']} 적용 → <b>{final_display}점</b></p>
        <h3>4. 운영 의미</h3>
        <ul class="report-list">{notes_html}</ul>
        <h3>5. 조치</h3>
        <ul class="report-list">{actions_html}</ul>
    </div>
    """


def report_markdown(scenario: dict, result: dict) -> str:
    health = result["health"]
    band = health["band"]
    final_display = int(round(health["health_final"]))

    lines = [
        "# AI Hospital · Health Score 리포트",
        f"## 시나리오: {scenario['label']}",
        "",
        "### 1. 상황",
    ]
    lines += [f"- {s}" for s in scenario["situation"]]
    lines.append("")

    for key in MODULE_ORDER:
        label = MODULE_LABELS[key]
        score = result["modules"][key]
        lines.append(f"### {label} 점수: {score}")
        lines.append("")
        lines.append("| 구성요소 | 건전성 값 | 가중치 | 기여값 |")
        lines.append("|---|---|---|---|")
        for b in result["breakdowns"][key]:
            lines.append(f"| {b['label']} | {b['value']:.2f} | {b['weight']:.2f} | {b['contribution']:.3f} |")
        lines.append("")
        lines.append(f"해석: {scenario['interpretations'].get(key, '')}")
        lines.append("")

    lines.append(f"### Health Score: {final_display} ({band[2]})")
    lines.append(f"- Savg = {health['savg']}")
    lines.append(f"- 최저 모듈 반영 후 = {health['health_base']}")
    lines.append(
        f"- 상황 페널티 {health['context_penalty']} ({scenario['context_penalty_reason']}) 적용 → 최종 {final_display}"
    )
    lines.append(f"- 관제 우선순위: {band[4]} / 운영조치: {band[5]}")
    lines.append("")
    lines.append("### 운영 의미")
    lines += [f"- {n}" for n in scenario["operational_notes"]]
    lines.append("")
    lines.append("### 조치")
    lines += [f"- {a}" for a in scenario["actions"]]

    return "\n".join(lines)
