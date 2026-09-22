import streamlit as st

from components.health_ui import (
    render_human_impact_panel,
    render_prevention_preview,
    render_report_view,
    report_markdown,
)
from components.mdutil import md
from components.theme import inject_top_markers, load_css, load_scroll_reveal
from logic.actions import ACTION_MODULE_THRESHOLD, PREVENTION_ACTIONS, simulate_prevention_effect
from logic.fleet import generate_fleet
from logic.health_score import MODULE_BANDS, MODULE_LABELS, MODULE_ORDER, band_for
from logic.routes import generate_candidate_routes

CONTROL_ROOM_PAGE = "pages/1_🚦_관제_센터.py"

st.set_page_config(
    page_title="AI Hospital · 예방 조치",
    page_icon="🛡",
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

# ---------------------------------------------------------------------------
# 관제 센터에서 넘어온 선택(차량, 경로)을 복원 — 둘 다 결정론적으로 생성되므로
# id/key 두 문자열만 있으면 동일한 결과를 다시 만들 수 있습니다. 전체 dict를
# session_state로 직렬화해 들고 다닐 필요가 없습니다.
# ---------------------------------------------------------------------------
selected_id = st.session_state.get("cc_active_vehicle_id")
chosen_route_key = st.session_state.get("cc_chosen_route_key")

if not selected_id or not chosen_route_key:
    md(
        """
        <div class="section section-tight" style="padding-top:110px;">
            <div class="verdict-panel reveal">
                <div class="vlabel">Status</div>
                <p>아직 선택된 차량·경로가 없습니다. 관제 센터에서 차량을 진단하고 경로를 먼저 선택해주세요.</p>
            </div>
        </div>
        """
    )
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        st.page_link(CONTROL_ROOM_PAGE, label="← 관제 센터로 이동", use_container_width=True)
    load_scroll_reveal()
    st.stop()

fleet = generate_fleet()
vehicle = next((v for v in fleet if v["id"] == selected_id), None)

if vehicle is None:
    md(
        """
        <div class="section section-tight" style="padding-top:110px;">
            <div class="verdict-panel reveal">
                <div class="vlabel">Status</div>
                <p>선택된 차량을 찾을 수 없습니다. 관제 센터에서 차량을 다시 선택해주세요.</p>
            </div>
        </div>
        """
    )
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        st.page_link(CONTROL_ROOM_PAGE, label="← 관제 센터로 이동", use_container_width=True)
    load_scroll_reveal()
    st.stop()

result = vehicle["_result"]
weak_module = vehicle["_weak_module"]
origin_label, dest_label = vehicle["route"].split(" → ", 1)
routes, recommended_key = generate_candidate_routes(vehicle, weak_module, origin_label, dest_label)
chosen_route = next((r for r in routes if r["key"] == chosen_route_key), routes[0])

md(
    f"""
    <div class="section section-tight" style="padding-top:110px;">
        <div class="reveal">
            <span class="mock-badge">PoC · 차량 데이터는 시뮬레이션, 점수 산식은 실제 계산 엔진입니다</span>
            <div class="eyebrow">Control Room · 2/2</div>
            <div class="section-title">예방 조치를 선택하고 운행계획을 적용합니다</div>
            <div class="section-sub">
                {vehicle['label']} · 선택된 경로 {chosen_route['label']}{' · 추천 경로' if chosen_route_key == recommended_key else ''}
                에 적용할 예방 조치를 고릅니다.
            </div>
        </div>
    </div>
    """
)
_, mid, _ = st.columns([1, 1, 1])
with mid:
    st.page_link(CONTROL_ROOM_PAGE, label="← 다른 차량·경로 선택하기", use_container_width=True)

# ---------------------------------------------------------------------------
# 4. Guide — 예방 조치 선택
# ---------------------------------------------------------------------------
md('<div class="section section-tight">')
md(
    """
    <div class="reveal">
        <div class="eyebrow">Guide</div>
        <div class="section-title" style="font-size:1.4rem;">예방 조치 선택</div>
        <div class="section-sub" style="margin-bottom:8px;">정상 구간을 벗어난 모듈마다 적용할 예방 조치를 하나 이상 선택하세요. 여러 개를 함께 선택하면 효과가 합산됩니다.</div>
    </div>
    """
)

weak_modules = [m for m in MODULE_ORDER if result["modules"][m] < ACTION_MODULE_THRESHOLD]
chosen_actions = {}
st.markdown('<div class="demo-shell">', unsafe_allow_html=True)
for m in weak_modules:
    score = result["modules"][m]
    band = band_for(score, MODULE_BANDS[m])
    md(
        f'<div class="ph-label" style="color:var(--accent-blue);font-size:0.78rem;font-weight:700;'
        f'letter-spacing:0.06em;text-transform:uppercase;margin:22px 0 4px 0;">'
        f"{MODULE_LABELS[m]} · {score}점 · {band[2]}</div>"
        f'<p style="color:var(--text-lo);font-size:0.82rem;margin:0 0 10px 0;">시스템 기본 권고: {band[4]}</p>'
    )
    chosen_actions[m] = st.multiselect(
        f"{MODULE_LABELS[m]} 예방 조치",
        options=PREVENTION_ACTIONS[m],
        default=[PREVENTION_ACTIONS[m][0]],
        key=f"cc_action_{selected_id}_{m}",
        label_visibility="collapsed",
    )
st.markdown("</div>", unsafe_allow_html=True)

# Live before/after preview — recomputes on every widget change, no need to
# press Apply first. The recovery amount is an illustrative estimate (the
# spec has no numeric action->score formula); the Health Score math itself
# is the real evaluate_scenario() pipeline.
sim_result = simulate_prevention_effect(vehicle, chosen_actions)
cur_final = int(round(result["health"]["health_final"]))
sim_final = int(round(sim_result["health"]["health_final"]))
md(render_prevention_preview(cur_final, sim_final, weak_modules, result["modules"], sim_result["modules"]))
md("</div>")

# ---------------------------------------------------------------------------
# 5. Apply — 예방 운행계획 적용
# ---------------------------------------------------------------------------
md('<div class="section section-tight">')
md(
    """
    <div class="reveal">
        <div class="eyebrow">Apply</div>
        <div class="section-title" style="font-size:1.4rem;">예방 운행계획 적용</div>
    </div>
    """
)

applied_key = f"cc_applied_{selected_id}"
total_actions = sum(len(chosen_actions[m]) for m in weak_modules)
st.markdown('<div class="demo-shell">', unsafe_allow_html=True)
md(render_human_impact_panel(routes[0], chosen_route, cur_final, sim_final, total_actions))
st.markdown('<div style="height:22px;"></div>', unsafe_allow_html=True)
if st.button("✅ 예방 운행계획 적용", key=f"cc_apply_{selected_id}", type="primary"):
    vehicle["actions"] = (
        [f"우회 경로 적용: {chosen_route['label']} (예상 최저 점수 {chosen_route['min_score']}, {chosen_route['distance_km']}km · 약 {chosen_route['eta_min']}분)"]
        + [
            f"{MODULE_LABELS[m]} 모듈 예방 조치: {', '.join(chosen_actions[m]) if chosen_actions[m] else '없음'}"
            for m in weak_modules
        ]
        + [f"예상 개선 효과(참고용 추정): Health Score {cur_final}점 → {sim_final}점"]
    )
    st.session_state[applied_key] = True
st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.get(applied_key):
    md(render_report_view(vehicle, result))
    st.download_button(
        "📄 예방 운행계획 Markdown 다운로드",
        data=report_markdown(vehicle, result),
        file_name=f"ai_hospital_prevention_plan_{selected_id}.md",
        mime="text/markdown",
        key=f"cc_download_{selected_id}",
    )
else:
    st.caption("경로와 예방 조치를 선택한 뒤 '예방 운행계획 적용'을 눌러보세요.")
md("</div>")

md('<div class="footer-note">2026학년도 한국자동차연구원 퓨처모빌리티 아이디어 경진대회 · 최종발표</div>')

load_scroll_reveal()
