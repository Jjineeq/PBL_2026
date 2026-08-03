"""Self-contained SVG top-down car diagram with live module-score badges.

No external image assets — the car is drawn from primitives, and each
badge's number/color is injected live from the current scenario's
module scores, so the diagram itself already shows "which score is
where" at a glance (drilling into *why* happens in components/health_ui.py).
"""

from logic.health_score import BAND_COLORS, MODULE_BANDS, MODULE_LABELS, band_for

# module -> (badge center x, badge center y, leader line target x, y)
_ANCHORS = {
    "perception": (30, 55, 78, 46),
    "prediction": (190, 55, 122, 6),
    "planning": (30, 235, 66, 160),
    "control": (190, 235, 190, 220),
}


def render_car_diagram(module_scores: dict) -> str:
    badges = []
    for key, (bx, by, lx, ly) in _ANCHORS.items():
        score = module_scores[key]
        band = band_for(score, MODULE_BANDS[key])
        color = BAND_COLORS[band[2]]
        label = MODULE_LABELS[key]
        badges.append(
            f'<line x1="{bx}" y1="{by}" x2="{lx}" y2="{ly}" stroke="{color}" '
            f'stroke-width="1.5" stroke-dasharray="3 4" opacity="0.65"/>'
            f'<circle cx="{bx}" cy="{by}" r="23" fill="{color}" opacity="0.16" '
            f'stroke="{color}" stroke-width="2"/>'
            f'<text x="{bx}" y="{by + 6}" text-anchor="middle" font-size="17" '
            f'font-weight="800" fill="{color}">{score}</text>'
            f'<text x="{bx}" y="{by + 38}" text-anchor="middle" font-size="11" '
            f'font-weight="700" fill="rgba(237,239,251,0.8)">{label}</text>'
        )
    badges_svg = "".join(badges)

    return f"""
    <svg viewBox="-15 -20 250 330" width="100%" height="100%"
         style="max-width:280px;display:block;margin:0 auto;overflow:visible;">
      <defs>
        <linearGradient id="carBody" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="rgba(255,255,255,0.10)"/>
          <stop offset="100%" stop-color="rgba(255,255,255,0.03)"/>
        </linearGradient>
      </defs>
      <line x1="122" y1="0" x2="122" y2="42" stroke="#4f9dff" stroke-width="3"
            stroke-dasharray="6 6" opacity="0.5"/>
      <polygon points="114,10 130,10 122,-8" fill="#4f9dff" opacity="0.5"/>
      <rect x="52" y="42" width="140" height="240" rx="34" fill="url(#carBody)"
            stroke="rgba(255,255,255,0.22)" stroke-width="2"/>
      <rect x="72" y="70" width="100" height="50" rx="14" fill="rgba(79,157,255,0.22)"
            stroke="rgba(255,255,255,0.18)"/>
      <rect x="72" y="207" width="100" height="42" rx="14" fill="rgba(255,255,255,0.05)"
            stroke="rgba(255,255,255,0.14)"/>
      <rect x="36" y="82" width="16" height="50" rx="6" fill="rgba(255,255,255,0.22)"/>
      <rect x="192" y="82" width="16" height="50" rx="6" fill="rgba(255,255,255,0.22)"/>
      <rect x="36" y="202" width="16" height="50" rx="6" fill="rgba(255,255,255,0.22)"/>
      <rect x="192" y="202" width="16" height="50" rx="6" fill="rgba(255,255,255,0.22)"/>
      <circle cx="90" cy="52" r="4" fill="#ff6b4a"/>
      <circle cx="154" cy="52" r="4" fill="#ff6b4a"/>
      <circle cx="122" cy="46" r="3.5" fill="#3ddad7"/>
      {badges_svg}
    </svg>
    """


def chip_label(module_key: str, score: int) -> str:
    from logic.health_score import BAND_EMOJI

    band = band_for(score, MODULE_BANDS[module_key])
    emoji = BAND_EMOJI[band[2]]
    label = MODULE_LABELS[module_key]
    return f"{emoji} {label} {score}"
