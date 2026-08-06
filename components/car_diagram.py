"""Self-contained SVG side-view car diagram with live module-score badges.

No external image assets — the car is drawn from primitives as a side
profile (nose pointing right, direction of travel), and each badge's
number/color is injected live from the current scenario's module scores.
Anchor points are chosen so each AI function sits where it intuitively
"lives" on a real vehicle, front to back: Perception at the front
sensor/bumper, Prediction at the front roof sensor pod, Planning at the
rear roof/cabin, Control at the wheels (drilling into *why* happens in
components/health_ui.py).
"""

from logic.health_score import BAND_COLORS, MODULE_BANDS, MODULE_LABELS, band_for

_WHEEL_R = 26
_WHEEL_REAR = (128, 196)
_WHEEL_FRONT = (338, 196)

_BODY_PATH = (
    "M70,185 L70,158 Q70,143 85,138 L100,114 Q105,100 125,100 "
    "L295,100 Q315,100 325,115 L349,144 Q354,150 364,150 "
    "L394,150 Q410,150 410,165 L408,180 Q408,185 400,185 Z"
)
_GLASS_PATH = "M108,113 L292,113 L316,133 L124,133 Z"

# module -> (badge center x, badge center y, leader-line target x, y)
# perception = front bumper, prediction = front roof pod, planning = rear
# roof/cabin, control = wheels (control's leader lines fan out separately)
_ANCHORS = {
    "planning": (100, 34, 118, 102),
    "prediction": (335, 28, 322, 102),
    "perception": (452, 140, 404, 163),
    "control": (241, 236, None, None),
}


def render_car_diagram(module_scores: dict) -> str:
    parts = []

    control_band = band_for(module_scores["control"], MODULE_BANDS["control"])
    wheel_color = BAND_COLORS[control_band[2]]

    parts.append(f'<path d="{_BODY_PATH}" fill="url(#carBody)" stroke="rgba(255,255,255,0.24)" stroke-width="2"/>')
    parts.append(f'<path d="{_GLASS_PATH}" fill="rgba(79,157,255,0.20)" stroke="rgba(255,255,255,0.16)"/>')

    for wx, wy in (_WHEEL_REAR, _WHEEL_FRONT):
        parts.append(
            f'<circle cx="{wx}" cy="{wy}" r="{_WHEEL_R}" fill="#12162a" stroke="{wheel_color}" stroke-width="3"/>'
            f'<circle cx="{wx}" cy="{wy}" r="9" fill="rgba(255,255,255,0.18)"/>'
        )
    parts.append('<circle cx="399" cy="152" r="4" fill="#3ddad7"/>')

    cbx, cby, _, _ = _ANCHORS["control"]
    for wx, wy in (_WHEEL_REAR, _WHEEL_FRONT):
        parts.append(
            f'<line x1="{cbx}" y1="{cby}" x2="{wx}" y2="{wy - _WHEEL_R}" stroke="{wheel_color}" '
            f'stroke-width="1.5" stroke-dasharray="3 4" opacity="0.65"/>'
        )

    for key, (bx, by, lx, ly) in _ANCHORS.items():
        score = module_scores[key]
        band = band_for(score, MODULE_BANDS[key])
        color = BAND_COLORS[band[2]]
        label = MODULE_LABELS[key]
        if lx is not None:
            parts.append(
                f'<line x1="{bx}" y1="{by}" x2="{lx}" y2="{ly}" stroke="{color}" '
                f'stroke-width="1.5" stroke-dasharray="3 4" opacity="0.65"/>'
            )
        parts.append(
            f'<circle cx="{bx}" cy="{by}" r="27" fill="{color}" opacity="0.16" '
            f'stroke="{color}" stroke-width="2"/>'
            f'<text x="{bx}" y="{by + 7}" text-anchor="middle" font-size="21" '
            f'font-weight="800" fill="{color}">{score}</text>'
            f'<text x="{bx}" y="{by + 45}" text-anchor="middle" font-size="14" '
            f'font-weight="700" fill="rgba(237,239,251,0.88)">{label}</text>'
        )

    badges_svg = "".join(parts)

    return f"""
    <svg viewBox="-20 -10 520 300" width="100%" height="100%"
         style="max-width:460px;display:block;margin:0 auto;overflow:visible;">
      <defs>
        <linearGradient id="carBody" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="rgba(255,255,255,0.10)"/>
          <stop offset="100%" stop-color="rgba(255,255,255,0.03)"/>
        </linearGradient>
      </defs>
      {badges_svg}
    </svg>
    """


def chip_label(module_key: str, score: int) -> str:
    from logic.health_score import BAND_EMOJI

    band = band_for(score, MODULE_BANDS[module_key])
    emoji = BAND_EMOJI[band[2]]
    label = MODULE_LABELS[module_key]
    return f"{emoji} {label} {score}"
