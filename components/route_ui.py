"""Render helpers for the Control Room's route-comparison step.

Same single-call HTML-string rule as the other components/*_ui.py modules.
Map + sparklines are hand-rolled inline SVG (no chart library), consistent
with components/car_diagram.py's self-drawn-primitives approach.
"""

from logic.health_score import BAND_COLORS, HEALTH_BANDS, band_for

# ---------------------------------------------------------------------------
# Schematic origin->destination map with the 3 candidate paths
# ---------------------------------------------------------------------------
_MAP_W, _MAP_H = 640, 190
_ORIGIN = (50, 100)
_DEST = (590, 100)
_CONTROL_Y = {"A": 100, "B": 40, "C": 168}


def _bezier_point(p0: tuple, p1: tuple, p2: tuple, t: float) -> tuple:
    x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
    y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
    return x, y


def render_route_map(routes: list[dict], recommended_key: str, origin_label: str, dest_label: str) -> str:
    parts = [
        f'<circle cx="{_ORIGIN[0]}" cy="{_ORIGIN[1]}" r="7" fill="#3ddad7"/>',
        f'<text x="{_ORIGIN[0]}" y="{_ORIGIN[1] - 20}" text-anchor="middle" font-size="16" '
        f'font-weight="700" fill="#e7e9f5">출발 · {origin_label}</text>',
        f'<circle cx="{_DEST[0]}" cy="{_DEST[1]}" r="7" fill="#ff6b4a"/>',
        f'<text x="{_DEST[0]}" y="{_DEST[1] - 20}" text-anchor="middle" font-size="16" '
        f'font-weight="700" fill="#e7e9f5">도착 · {dest_label}</text>',
    ]

    for r in routes:
        key = r["key"]
        is_recommended = key == recommended_key
        color = BAND_COLORS.get(r["band"][2], "#8892a8")
        control = (320, _CONTROL_Y.get(key, 100))
        path_d = f"M {_ORIGIN[0]},{_ORIGIN[1]} Q {control[0]},{control[1]} {_DEST[0]},{_DEST[1]}"
        width = 5 if is_recommended else 2.5
        opacity = 0.95 if is_recommended else 0.4

        parts.append(
            f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="{width}" '
            f'opacity="{opacity}" stroke-linecap="round"/>'
        )

        mx, my = _bezier_point(_ORIGIN, control, _DEST, 0.5)
        check = " ✓" if is_recommended else ""
        parts.append(
            f'<text x="{mx:.0f}" y="{my - 14:.0f}" text-anchor="middle" font-size="16" '
            f'font-weight="800" fill="{color}">{key}{check}</text>'
        )

        if r["min_score"] < 50:
            dx, dy = _bezier_point(_ORIGIN, control, _DEST, 0.65)
            parts.append(
                f'<circle cx="{dx:.0f}" cy="{dy:.0f}" r="17" fill="{color}" opacity="0.18" '
                f'stroke="{color}" stroke-width="1.5" stroke-dasharray="3 3"/>'
                f'<text x="{dx:.0f}" y="{dy + 6:.0f}" text-anchor="middle" font-size="17" '
                f'font-weight="800" fill="{color}">!</text>'
            )

    body = "".join(parts)
    return f"""
    <div class="glass-card reveal route-map-card" style="padding:24px;">
        <div class="route-map-label">경로 후보 미리보기 · 빨간 영역은 예측 위험 구간</div>
        <svg viewBox="0 0 {_MAP_W} {_MAP_H}" width="100%" height="190" preserveAspectRatio="xMidYMid meet">{body}</svg>
    </div>
    """


# ---------------------------------------------------------------------------
# Per-route score-over-time sparkline (labelled points + time axis)
# ---------------------------------------------------------------------------
_SPARK_W = 220
_SPARK_TOP = 26
_SPARK_PLOT_H = 46
_SPARK_AXIS_Y = _SPARK_TOP + _SPARK_PLOT_H + 22
_SPARK_TOTAL_H = _SPARK_AXIS_Y + 6


def _point_color(score: int) -> str:
    band = band_for(score, HEALTH_BANDS)
    return BAND_COLORS.get(band[2], "#8892a8")


def _sparkline_svg(scores: list[int], eta_min: int) -> str:
    n = len(scores)
    step = _SPARK_W / (n - 1)

    def _y(s):
        return _SPARK_TOP + (1 - max(0, min(100, s)) / 100) * _SPARK_PLOT_H

    segments = [
        f'<line x1="{i * step:.1f}" y1="{_y(scores[i]):.1f}" x2="{(i + 1) * step:.1f}" '
        f'y2="{_y(scores[i + 1]):.1f}" stroke="{_point_color(scores[i])}" stroke-width="2.5" '
        f'stroke-linecap="round"/>'
        for i in range(n - 1)
    ]

    dots, labels, time_labels = [], [], []
    for i, s in enumerate(scores):
        x = i * step
        y = _y(s)
        color = _point_color(s)
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="{color}"/>')
        warn = " !" if s < 50 else ""
        labels.append(
            f'<text x="{x:.1f}" y="{y - 11:.1f}" text-anchor="middle" font-size="12" '
            f'font-weight="700" fill="{color}">{s}{warn}</text>'
        )
        t_label = "출발" if i == 0 else ("도착" if i == n - 1 else f"+{round(eta_min * i / (n - 1))}분")
        time_labels.append(
            f'<text x="{x:.1f}" y="{_SPARK_AXIS_Y}" text-anchor="middle" font-size="10.5" '
            f'fill="rgba(237,239,251,0.55)">{t_label}</text>'
        )

    svg_body = "".join(segments) + "".join(dots) + "".join(labels) + "".join(time_labels)
    return f'<svg viewBox="0 0 {_SPARK_W} {_SPARK_TOTAL_H}" width="100%" height="{_SPARK_TOTAL_H}">{svg_body}</svg>'


def render_route_cards(routes: list[dict], recommended_key: str) -> str:
    cards = []
    for r in routes:
        color = BAND_COLORS.get(r["band"][2], "#8892a8")
        is_recommended = r["key"] == recommended_key
        badge = '<div class="recommended-badge">✓ 추천 경로</div>' if is_recommended else ""
        if r["risk_factors"]:
            tags = "".join(f'<span class="chip route-tag">{t}</span>' for t in r["risk_factors"])
        else:
            tags = '<span class="route-tag-empty">특이 위험요인 없음</span>'
        spark = _sparkline_svg(r["scores"], r["eta_min"])

        cards.append(
            f"""
            <div class="route-card{' recommended' if is_recommended else ''}">
                {badge}
                <div class="route-card-label">{r['label']}</div>
                <div class="route-card-meta">{r['distance_km']}km · 약 {r['eta_min']}분</div>
                <div class="sparkline">{spark}</div>
                <div class="route-card-score" style="color:{color};">
                    최저 예측 점수 {r['min_score']}
                    <span class="band-name">({r['band'][2]})</span>
                </div>
                <div class="chip-row route-tags">{tags}</div>
            </div>
            """
        )

    return f'<div class="route-grid reveal">{"".join(cards)}</div>'


def render_route_delta(chosen: dict, baseline: dict) -> str:
    """Immediate feedback line shown right under the route radio — updates
    on every rerun as soon as the controller picks a different candidate."""
    delta = chosen["min_score"] - baseline["min_score"]
    sign = "+" if delta > 0 else ""
    tone = "var(--accent-teal)" if delta > 0 else ("var(--text-lo)" if delta == 0 else "var(--accent-red-2)")
    color = BAND_COLORS.get(chosen["band"][2], "#8892a8")
    same_route = chosen["key"] == baseline["key"]
    compare = (
        "이미 최단 경로가 선택되어 있습니다."
        if same_route
        else f'최단 경로({baseline["label"]}) 대비 <b style="color:{tone};">{sign}{delta}점</b>'
    )
    return (
        f'<div class="stat-line reveal" style="justify-content:flex-start;text-align:left;">'
        f'선택한 경로 적용 시 최저 예측 점수 '
        f'<b style="color:{color};">{chosen["min_score"]}점 ({chosen["band"][2]})</b> · {compare}'
        f"</div>"
    )
