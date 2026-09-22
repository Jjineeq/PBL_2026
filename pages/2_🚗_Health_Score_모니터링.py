import streamlit as st

from components.car_diagram import chip_label, render_car_diagram
from components.health_ui import (
    render_comparison,
    render_health_breakdown,
    render_module_drilldown,
    render_report_view,
    report_markdown,
)
from components.mdutil import md
from components.theme import inject_top_markers, load_css, load_scroll_reveal
from logic.health_score import MODULE_LABELS, MODULE_ORDER, evaluate_scenario
from logic.scenarios import SCENARIOS

st.set_page_config(
    page_title="AI Hospital · Health Score 모니터링",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_css()
inject_top_markers()

md(
    """
    <div class="navbar">
        <div class="brand"><span class="cross">+</span> AI Hospital</div>
        <div class="nav-links"><a href="/" target="_self">← 홈으로</a></div>
    </div>
    """
)

md(
    """
    <div class="section section-tight" style="padding-top:110px;">
        <div class="reveal">
            <span class="mock-badge">실제 계산 엔진 · 입력값만 프리셋입니다</span>
            <div class="eyebrow">Health Score</div>
            <div class="section-title">차량 하나를 골라 건강 상태를 들여다봅니다</div>
            <div class="section-sub">
                인지·예측·계획·제어 네 모듈의 점수는 문서에 정의된 가중합 수식으로 실시간 계산됩니다.
                점수 칩을 누르면 어떤 구성요소가 점수를 끌어내렸는지, 어떤 조치가 뒤따르는지 확인할 수 있습니다.
            </div>
        </div>
    </div>
    """
)

if "hs_scenario" not in st.session_state:
    st.session_state["hs_scenario"] = "case1"
if "hs_selected_module" not in st.session_state:
    st.session_state["hs_selected_module"] = None

st.markdown('<div class="demo-shell">', unsafe_allow_html=True)

scenario_key = st.radio(
    "시나리오 선택",
    options=list(SCENARIOS.keys()),
    format_func=lambda k: SCENARIOS[k]["label"],
    horizontal=True,
    label_visibility="collapsed",
    key="hs_scenario",
)

if st.session_state.get("hs_scenario_prev") != scenario_key:
    st.session_state["hs_selected_module"] = None
    st.session_state["hs_scenario_prev"] = scenario_key

scenario = SCENARIOS[scenario_key]
result = evaluate_scenario(scenario)

situation_html = " · ".join(scenario["situation"][:3])
md(f'<p style="color:var(--text-lo);font-size:0.85rem;margin:-6px 0 22px 0;">{situation_html}</p>')

col_car, col_chip = st.columns([1, 1.3], gap="large")

with col_car:
    md(f'<div class="glass-card reveal" style="padding:28px;">{render_car_diagram(result["modules"])}</div>')

with col_chip:
    md(
        '<div class="ph-label" style="color:var(--accent-blue);font-size:0.78rem;font-weight:700;'
        'letter-spacing:0.06em;text-transform:uppercase;margin:30px 0 14px 0;">모듈 점수 · 클릭해서 원인 보기</div>'
    )
    chip_cols = st.columns(2)
    for i, m in enumerate(MODULE_ORDER):
        with chip_cols[i % 2]:
            if st.button(chip_label(m, result["modules"][m]), key=f"chip_{m}", use_container_width=True):
                st.session_state["hs_selected_module"] = m
    if st.session_state["hs_selected_module"] is not None:
        if st.button("Health Score 전체 보기로 돌아가기", key="clear_module"):
            st.session_state["hs_selected_module"] = None
            st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

md('<div class="section section-tight">')
if st.session_state["hs_selected_module"]:
    md(render_module_drilldown(st.session_state["hs_selected_module"], scenario, result))
else:
    md(render_health_breakdown(scenario, result))
md("</div>")

md('<div class="section section-tight">')
md(
    """
    <div class="reveal">
        <div class="eyebrow">Compare</div>
        <div class="section-title" style="font-size:1.4rem;">같은 인지 오류, 다른 결과 — 사례 비교</div>
        <div class="section-sub" style="margin-bottom:20px;">
            인지 점수가 비슷해도 예측·계획 결과와 상황 페널티에 따라 Health Score와 조치가 크게 달라질 수 있습니다.
        </div>
    </div>
    """
)
other_keys = [k for k in SCENARIOS if k != scenario_key]
compare_key = st.radio(
    "비교할 시나리오",
    options=other_keys,
    format_func=lambda k: SCENARIOS[k]["label"],
    horizontal=True,
    label_visibility="collapsed",
    key="hs_compare",
)
compare_result = evaluate_scenario(SCENARIOS[compare_key])
md(render_comparison(scenario, SCENARIOS[compare_key], result, compare_result))
md("</div>")

md('<div class="section section-tight">')
md(
    """
    <div class="reveal">
        <div class="eyebrow">Report</div>
        <div class="section-title" style="font-size:1.4rem;">리포트</div>
        <div class="section-sub" style="margin-bottom:20px;">
            현재 시나리오를 관제 기록용 리포트 형태로 정리합니다.
        </div>
    </div>
    """
)
md(render_report_view(scenario, result))
st.download_button(
    "📄 리포트 Markdown 다운로드",
    data=report_markdown(scenario, result),
    file_name=f"ai_hospital_health_report_{scenario_key}.md",
    mime="text/markdown",
)
md("</div>")

md(
    '<div class="footer-note">2026학년도 한국자동차연구원 퓨처모빌리티 아이디어 경진대회 · '
    "최종발표 · Health Score 산식 출처: 자율주행 Health Score 점수체계</div>"
)

load_scroll_reveal()
