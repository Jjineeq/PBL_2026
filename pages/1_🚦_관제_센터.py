import streamlit as st
import streamlit.components.v1 as st_components

from components.car_diagram import chip_label, render_car_diagram
from components.fleet_ui import render_fleet_table, render_kpi_strip, render_situation_panel
from components.health_ui import (
    render_health_breakdown,
    render_human_impact_panel,
    render_module_drilldown,
    render_prevention_preview,
    render_report_view,
    report_markdown,
)
from components.mdutil import md
from components.route_ui import render_leaflet_route_map, render_route_cards, render_route_delta
from components.theme import inject_top_markers, load_css, load_scroll_reveal
from logic.actions import ACTION_MODULE_THRESHOLD, PREVENTION_ACTIONS, simulate_prevention_effect
from logic.fleet import generate_fleet
from logic.health_score import MODULE_BANDS, MODULE_LABELS, MODULE_ORDER, band_for
from logic.routes import generate_candidate_routes

st.set_page_config(
    page_title="AI Hospital · 관제 센터",
    page_icon="🚦",
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
            <span class="mock-badge">PoC · 차량 데이터는 시뮬레이션, 점수 산식은 실제 계산 엔진입니다</span>
            <div class="eyebrow">Control Room</div>
            <div class="section-title">관제사 관점에서 위험 차량을 선별하고 예방 조치를 적용합니다</div>
            <div class="section-sub">
                AI가 전체 차량 상태를 먼저 진단하고(Detect), 위험 차량의 원인을 모듈별로 분석한 뒤(Diagnose),
                경로 후보와 예방 조치를 관제사가 검토·선택합니다(Guide).
            </div>
        </div>
    </div>
    """
)

fleet = generate_fleet()
ordered = sorted(fleet, key=lambda v: v["_result"]["health"]["health_final"])

# ---------------------------------------------------------------------------
# 1. Detect — 위험 차량 선별
# ---------------------------------------------------------------------------
md('<div class="section section-tight">')
md(
    """
    <div class="reveal">
        <div class="eyebrow">Detect</div>
        <div class="section-title" style="font-size:1.4rem;">위험 차량 선별</div>
        <div class="section-sub" style="margin-bottom:20px;">
            전체 차량을 Health Score 낮은 순으로 정렬합니다. 관제사는 모든 차량이 아니라 이 목록만 확인하면 됩니다.
        </div>
    </div>
    """
)
md(render_kpi_strip(fleet))

st.markdown('<div class="demo-shell" style="margin-top:22px;">', unsafe_allow_html=True)
show_all = st.checkbox(f"전체 {len(fleet)}대 보기", value=False, key="cc_show_all")
md(render_fleet_table(fleet, limit=None if show_all else 15))

label_map = {
    v["id"]: f"{v['id']} · {v['route']} · {int(round(v['_result']['health']['health_final']))}점"
    for v in fleet
}
with st.container(border=True):
    st.markdown(
        '<div class="picker-label"><span class="picker-arrow">▸</span> 드릴다운할 차량 선택'
        '<span class="picker-hint">Health Score 낮은 순 · 여기서 고른 차량을 아래에서 진단합니다</span></div>',
        unsafe_allow_html=True,
    )
    selected_id = st.selectbox(
        "드릴다운할 차량 선택 (Health Score 낮은 순)",
        options=[v["id"] for v in ordered],
        format_func=lambda vid: label_map[vid],
        key="cc_selected_vehicle",
        label_visibility="collapsed",
    )
st.markdown("</div>", unsafe_allow_html=True)
md("</div>")

vehicle = next(v for v in fleet if v["id"] == selected_id)
result = vehicle["_result"]
band_label = result["health"]["band"][2]

# ---------------------------------------------------------------------------
# 2. Diagnose — 차량 상태 진단
# ---------------------------------------------------------------------------
md('<div class="section section-tight">')
md(
    f"""
    <div class="reveal">
        <div class="eyebrow">Diagnose</div>
        <div class="section-title" style="font-size:1.4rem;">{vehicle['label']}</div>
        <div class="section-sub" style="margin-bottom:20px;">인지·예측·계획·제어 네 모듈의 현재 상태입니다.</div>
    </div>
    """
)

st.markdown('<div class="demo-shell">', unsafe_allow_html=True)
md(render_situation_panel(vehicle))
col_car, col_chip = st.columns([1, 1.3], gap="large")

with col_car:
    md(f'<div class="glass-card reveal" style="padding:28px;">{render_car_diagram(result["modules"])}</div>')

module_key_state = f"cc_module_{selected_id}"
st.session_state.setdefault(module_key_state, None)

with col_chip:
    md(
        '<div class="ph-label" style="color:var(--accent-blue);font-size:0.78rem;font-weight:700;'
        'letter-spacing:0.06em;text-transform:uppercase;margin:30px 0 14px 0;">모듈 점수 · 클릭해서 원인 보기</div>'
    )
    chip_cols = st.columns(2)
    for i, m in enumerate(MODULE_ORDER):
        with chip_cols[i % 2]:
            if st.button(chip_label(m, result["modules"][m]), key=f"cc_chip_{selected_id}_{m}", use_container_width=True):
                st.session_state[module_key_state] = m
    if st.session_state[module_key_state] is not None:
        if st.button("Health Score 전체 보기로 돌아가기", key=f"cc_clear_{selected_id}"):
            st.session_state[module_key_state] = None
            st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

if st.session_state[module_key_state]:
    md(render_module_drilldown(st.session_state[module_key_state], vehicle, result))
else:
    md(render_health_breakdown(vehicle, result))
md("</div>")

# ---------------------------------------------------------------------------
# 정상 차량은 여기서 종료
# ---------------------------------------------------------------------------
if band_label == "정상":
    md('<div class="section section-tight">')
    md(
        """
        <div class="verdict-panel reveal">
            <div class="vlabel">Status</div>
            <p>정상 운행 중입니다 — 예방 조치가 필요하지 않습니다. 인지·예측·계획·제어를 AI가 자율적으로 안정적으로 수행합니다.</p>
        </div>
        """
    )
    md("</div>")
    md('<div class="footer-note">2026학년도 한국자동차연구원 퓨처모빌리티 아이디어 경진대회 · 최종발표</div>')
    load_scroll_reveal()
    st.stop()

weak_module = vehicle["_weak_module"]

# ---------------------------------------------------------------------------
# 3. 후보 경로 비교
# ---------------------------------------------------------------------------
md('<div class="section section-tight">')
md(
    f"""
    <div class="reveal">
        <div class="eyebrow">Route Comparison</div>
        <div class="section-title" style="font-size:1.4rem;">후보 경로 비교 · 최적 우회 경로 추천</div>
        <div class="section-sub" style="margin-bottom:8px;">
            별도의 경로 점수 산식이 아니라, 위에서 쓴 것과 같은 Health Score 계산식을
            {MODULE_LABELS[weak_module]} 모듈 저하를 가정해 경로의 각 지점마다 다시 계산합니다 —
            한 시점의 스냅샷이 아니라 경로 전체에 걸쳐 다각도로 봅니다.
        </div>
    </div>
    """
)
origin_label, dest_label = vehicle["route"].split(" → ", 1)
routes, recommended_key = generate_candidate_routes(vehicle, weak_module, origin_label, dest_label)
md('<div class="route-map-label">실시간 경로 지도 · 마커를 클릭하면 그 지점의 상황을 볼 수 있습니다</div>')
st_components.html(render_leaflet_route_map(routes, recommended_key, origin_label, dest_label), height=430)
md(render_route_cards(routes, recommended_key))

route_label_map = {r["key"]: r["label"] for r in routes}
route_options = [r["key"] for r in routes]
st.markdown('<div class="demo-shell" style="padding-top:18px;">', unsafe_allow_html=True)
chosen_route_key = st.radio(
    "적용할 경로 선택",
    options=route_options,
    format_func=lambda k: route_label_map[k] + (" · 추천" if k == recommended_key else ""),
    index=route_options.index(recommended_key),
    horizontal=True,
    key=f"cc_route_{selected_id}",
)
chosen_route = next(r for r in routes if r["key"] == chosen_route_key)
md(render_route_delta(chosen_route, routes[0]))
st.markdown("</div>", unsafe_allow_html=True)
md("</div>")

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

# Live before/after preview — recomputes on every radio change, no need to
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
