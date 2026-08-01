"""
Landing (promo) page content for AI Hospital — short-and-punchy version.

All sections are rendered as raw HTML blocks (st.markdown(unsafe_allow_html=True))
so the glassmorphism CSS in assets/css/style.css applies directly. Elements
carrying the `reveal` class are animated in on scroll by assets/js/scroll_reveal.js.

IMPORTANT: each section is built as ONE composed HTML string and rendered
with a single `_md()` call. Streamlit mounts every st.markdown() call into
its own isolated DOM container, so an opening tag emitted in one call and
its closing tag emitted in a later call never actually nest in the real
DOM (the browser silently auto-closes the orphaned tag). Wrapper elements
that rely on CSS grid/flex over their children (`.grid`, `.flow-strip`,
`.compact-grid`, `.section`) MUST have their children rendered together.
"""

import streamlit as st

from components.icons import icon
from components.mdutil import md as _md

DEMO_PAGE = "pages/1_🩺_AI_Hospital_체험.py"


def _card(ic: str, title: str, desc: str, delay: int) -> str:
    return (
        f'<div class="glass-card reveal reveal-delay-{delay}">'
        f'<div class="icon">{icon(ic)}</div><h3>{title}</h3><p>{desc}</p></div>'
    )


def _tag_card(tag: str, title: str, desc: str, delay: int) -> str:
    return (
        f'<div class="glass-card reveal reveal-delay-{delay}">'
        f'<div class="tag">{tag}</div><h3>{title}</h3><p>{desc}</p></div>'
    )


def _quote(src: str, text: str, delay: int) -> str:
    return (
        f'<div class="quote-card reveal reveal-delay-{delay}">'
        f'<div class="src">{src}</div><p>{text}</p></div>'
    )


def _chip(ic: str, text: str) -> str:
    return f'<div class="chip"><span class="ic">{icon(ic, 16)}</span>{text}</div>'


def _bullet(ic: str, text: str) -> str:
    return f'<li><span class="ic">{icon(ic, 15)}</span>{text}</li>'


def _navbar():
    _md(
        """
        <div class="navbar">
            <div class="brand"><span class="cross">+</span> AI Hospital</div>
            <div class="nav-links">
                <a href="#problem">문제</a>
                <a href="#solution">솔루션</a>
                <a href="#impact">기대효과</a>
            </div>
        </div>
        """
    )


def _hero():
    _md(
        """
        <div class="hero">
            <div class="bg-orb orb-1"></div>
            <div class="bg-orb orb-2"></div>
            <div class="bg-orb orb-3"></div>

            <div class="hero-badge">
                <span class="dot"></span>
                2026 한국자동차연구원 퓨처모빌리티 아이디어 경진대회 · 1차 중간발표
            </div>

            <h1>AI에게도<br><span class="gradient-text">건강검진</span>이 필요합니다</h1>

            <p class="lead">
                <b>AI Hospital</b>은 다중 AI 모델의 토론(Debate)을 기반으로
                자율주행 AI를 사고 전엔 진단·예방하고, 사고 후엔 원인을 규명해 치료하는
                자율주행 안전 관제 시스템입니다.
            </p>

            <div class="hero-stats">
                <div class="hero-stat"><div class="num">1 : <span>N</span></div><div class="label">관제 효율 회복 목표</div></div>
                <div class="hero-stat"><div class="num">4<span>개</span></div><div class="label">AI 모듈 상시 건강검진</div></div>
                <div class="hero-stat"><div class="num">전<span> 생애주기</span></div><div class="label">사고 전 · 후 통합 관리</div></div>
            </div>
        </div>
        """
    )


def _hero_cta():
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        st.page_link(DEMO_PAGE, label="PoC 체험해보기 →", use_container_width=True)
        _md(
            '<div class="scroll-cue" style="position:static;margin:34px auto 0 auto;">'
            '<span>Scroll</span><span class="chevron"></span></div>'
        )


def _problem():
    quotes = [
        (
            "한국교통연구원(KOTI) · 2026.04",
            "특정 영역 내 무인 주행이 가능한 '레벨4 자율주행 모빌리티 서비스'에 대한 수요가 급증하고 있다.",
        ),
        (
            "뉴스1 · 2026.02",
            "정부는 8개 지자체 대상 '2026년 자율차 시범운행지구 서비스 지원사업'에 총 30억 원을 투입한다.",
        ),
        (
            "아시아경제 · 2026.06",
            "자율주행 사고의 주요 원인은 하드웨어 결함보다 복합적인 시스템 상호작용 오류로 분석됐다.",
        ),
    ]
    cards_html = "".join(_quote(src, text, i) for i, (src, text) in enumerate(quotes, start=1))

    chips = [
        ("bolt", "AI 오류 = 즉각적 사고 직결"),
        ("message", "사람-AI 소통 오류까지 원인"),
        ("refresh", "원인 분석 없는 재발"),
    ]
    chips_html = "".join(_chip(ic, text) for ic, text in chips)

    _md(
        f"""
        <div id="problem" class="section">
            <div class="reveal">
                <div class="eyebrow">Problem</div>
                <div class="section-title">자율주행 상용화 속도를<br>안전 관제 체계가 따라가지 못하고 있습니다</div>
                <div class="section-sub">
                    수요와 예산은 빠르게 느는데, 사고 원인은 단순 결함이 아닌
                    <b>복합적인 시스템 상호작용 오류</b>로 지목되고 있습니다.
                </div>
            </div>
            <div class="grid grid-3">{cards_html}</div>
            <div class="reveal" style="margin-top:22px;">
                <div class="chip-row">{chips_html}</div>
            </div>
            <div class="reveal stat-line">
                <span class="ic">{icon('target', 18)}</span>
                기대했던 <b>관제사 1 : 차량 N대</b> 구조는, AI 판단을 믿을 수 없어
                결국 <b>관제사 1 : 차량 1대</b>의 상시 감시로 되돌아가고 있습니다.
            </div>
        </div>
        """
    )


def _solution():
    steps = [
        ("1", "모빌리티 AI", "자율주행차 · 셔틀 · 배송로봇"),
        ("2", "사고 전", "건강검진 & 예방"),
        ("3", "AI HOSPITAL", "다중 AI 토론 진단·치료"),
        ("4", "사고 후", "원인 진단 & 치료"),
        ("5", "최종 목표", "안전성 · 신뢰성 향상"),
    ]
    step_html = []
    for i, (n, title, desc) in enumerate(steps):
        step_html.append(f'<div class="flow-step"><div class="n">{n}</div><h4>{title}</h4><p>{desc}</p></div>')
        if i < len(steps) - 1:
            step_html.append('<div class="flow-arrow">→</div>')
    flow_html = "".join(step_html)

    pre_items = "".join(
        _bullet(ic, t)
        for ic, t in [
            ("pulse", "센서/모듈별 AI 건강검진 실시"),
            ("cloud-rain", "야간·우천 등 취약 시나리오 분석"),
            ("alert", "사고 발생 가능성 Top 시나리오 예측"),
            ("shield", "모델 업데이트 등 예방 조치"),
        ]
    )
    post_items = "".join(
        _bullet(ic, t)
        for ic, t in [
            ("radio", "카메라·LiDAR·로그 등 사고 데이터 수집"),
            ("layers", "Vision·Control·Planning 전문가 AI 토론"),
            ("search", "타임라인 기반 Root Cause 진단"),
            ("rocket", "재학습·검증 후 안전하게 재배포"),
        ]
    )

    _md(
        f"""
        <div id="solution" class="section">
            <div class="reveal">
                <div class="eyebrow">Solution</div>
                <div class="section-title">AI도 사람처럼, <span class="gradient-text">전 생애주기</span> 건강 관리가 필요합니다</div>
                <div class="section-sub">
                    사고 전엔 예방하고, 사고 후엔 원인을 진단·치료해 안전하게 재배포하는 순환 구조입니다.
                </div>
            </div>
            <div class="flow-strip reveal">{flow_html}</div>
            <div class="compact-grid reveal" style="margin-top:24px;">
                <div class="compact-panel">
                    <div class="ph-label">사고 전 · Pre-Accident</div>
                    <h4>AI 건강검진 &amp; 사고 예방</h4>
                    <ul>{pre_items}</ul>
                </div>
                <div class="compact-panel">
                    <div class="ph-label">사고 후 · Post-Accident</div>
                    <h4>원인 진단 &amp; 치료</h4>
                    <ul>{post_items}</ul>
                </div>
            </div>
        </div>
        """
    )


def _ecosystem():
    eco = [
        ("TRACK RECORD", "건강 기록부", "Health score·사고·모델 업데이트 이력을 축적합니다."),
        ("FEDERATED LEARNING", "연합학습", "모델 업데이트만 공유해 전체 AI 성능을 높입니다."),
        ("MLLM DEBATE", "다중 전문가 토론", "다중 AI 협업으로 진단 정확도·신뢰성을 높입니다."),
        ("DIGITAL TWIN", "디지털 트윈", "가상 환경에서 시나리오를 안전하게 검증합니다."),
        ("KNOWLEDGE BASE", "지식 베이스", "축적된 경험을 전 모빌리티 AI에 공유합니다."),
    ]
    cards_html = "".join(
        _tag_card(tag, title, desc, ((i - 1) % 3) + 1) for i, (tag, title, desc) in enumerate(eco, start=1)
    )

    _md(
        f"""
        <div class="section section-tight">
            <div class="reveal">
                <div class="eyebrow">Continuous Learning</div>
                <div class="section-title">사고 경험이 축적될수록 더 똑똑해지는 시스템</div>
            </div>
            <div class="grid grid-3">{cards_html}</div>
        </div>
        """
    )


def _impact_cta():
    impacts = [
        ("trend", "안전성 향상"),
        ("users", "신뢰성 확보"),
        ("cpu", "설명 가능성 강화"),
        ("monitor", "관제 효율 회복"),
    ]
    impact_html = "".join(
        f'<div class="impact-item"><div class="ic">{icon(ic, 20)}</div><span>{label}</span></div>'
        for ic, label in impacts
    )

    _md(
        f"""
        <div id="impact" class="section">
            <div class="reveal">
                <div class="eyebrow">Expected Impact</div>
                <div class="section-title">AI Hospital이 만드는 변화</div>
            </div>
            <div class="impact-row reveal">{impact_html}</div>
        </div>
        """
    )

    _md(
        """
        <div class="section section-tight" style="padding-bottom:0;">
            <div class="cta-panel reveal">
                <span class="mock-badge">PoC · Proof of Concept</span>
                <h2>지금 바로 AI Hospital을 체험해보세요</h2>
                <p>상황을 선택하면 AI 건강검진과 다중 AI 토론 기반 원인 진단을
                   미리 만든 시나리오로 보여드립니다.</p>
            </div>
        </div>
        """
    )
    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        st.page_link(DEMO_PAGE, label="PoC 체험해보기 →", use_container_width=True)
    _md('<div class="section section-tight" style="padding-top:0;"></div>')


def _footer():
    _md(
        """
        <div class="footer-note">
            2026학년도 한국자동차연구원 퓨처모빌리티 아이디어 경진대회 · 1차 중간발표<br>
            김다빈 · 김수림 · 장성호
        </div>
        """
    )


def render():
    _navbar()
    _hero()
    _hero_cta()
    _problem()
    _solution()
    _ecosystem()
    _impact_cta()
    _footer()
