import streamlit as st

from components.diagnosis_ui import render_health_result, render_root_cause_result
from components.mdutil import md
from components.theme import inject_top_markers, load_css, load_scroll_reveal
from logic.diagnosis import (
    HEALTH_SCENARIOS,
    ROOT_CAUSE_SCENARIOS,
    run_health_check,
    run_root_cause,
)

st.set_page_config(
    page_title="AI Hospital · PoC 체험",
    page_icon="🩺",
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
            <span class="mock-badge">PoC · 지금은 고정된 시나리오 답변입니다</span>
            <div class="eyebrow">Live Demo</div>
            <div class="section-title">상황을 선택하면 AI Hospital이 진단합니다</div>
            <div class="section-sub">
                지금은 미리 준비한 시나리오별 결과를 보여주는 목업 단계이며,
                이후 이 부분을 실제 다중 AI 모델 파이프라인으로 교체할 예정입니다.
            </div>
        </div>
    </div>
    """
)

tab1, tab2 = st.tabs(["🩺 AI 건강검진 · 사고 전", "🔍 원인 진단 · 사고 후"])

with tab1:
    st.markdown('<div class="demo-shell">', unsafe_allow_html=True)
    scenario_key = st.radio(
        "상황 선택",
        options=list(HEALTH_SCENARIOS.keys()),
        format_func=lambda k: HEALTH_SCENARIOS[k],
        horizontal=True,
        label_visibility="collapsed",
        key="health_scenario",
    )
    run = st.button("건강검진 실행", key="run_health", type="primary")

    if run:
        st.session_state["health_result"] = run_health_check(scenario_key)
        st.session_state["health_result_label"] = HEALTH_SCENARIOS[scenario_key]

    if "health_result" in st.session_state:
        md(render_health_result(st.session_state["health_result"], st.session_state["health_result_label"]))
    else:
        st.caption("상황을 고른 뒤 '건강검진 실행'을 눌러보세요.")
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="demo-shell">', unsafe_allow_html=True)
    rc_key = st.radio(
        "사고 시나리오 선택",
        options=list(ROOT_CAUSE_SCENARIOS.keys()),
        format_func=lambda k: ROOT_CAUSE_SCENARIOS[k],
        horizontal=True,
        label_visibility="collapsed",
        key="rc_scenario",
    )
    run_rc = st.button("원인 진단 실행", key="run_rc", type="primary")

    if run_rc:
        st.session_state["rc_result"] = run_root_cause(rc_key)
        st.session_state["rc_result_label"] = ROOT_CAUSE_SCENARIOS[rc_key]

    if "rc_result" in st.session_state:
        md(render_root_cause_result(st.session_state["rc_result"], st.session_state["rc_result_label"]))
    else:
        st.caption("사고 시나리오를 고른 뒤 '원인 진단 실행'을 눌러보세요.")
    st.markdown("</div>", unsafe_allow_html=True)

md('<div class="footer-note">2026학년도 한국자동차연구원 퓨처모빌리티 아이디어 경진대회 · 1차 중간발표</div>')

load_scroll_reveal()
