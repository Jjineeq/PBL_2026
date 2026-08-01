"""Minimal hand-built line-icon set (no external icon font / CDN).

Each entry is the *inner* SVG markup (paths/shapes only); `icon()` wraps it
in an <svg> tag sized/colored via CSS. Keeping icons as inline SVG avoids
external asset dependencies and renders crisp at any size, unlike emoji.
"""

_ICONS = {
    "bolt": '<path d="M13 3 4 14h6l-1 7 9-11h-6l1-7z"/>',
    "message": '<path d="M4 6a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H9l-4 4V6z"/>',
    "refresh": '<path d="M4 12a8 8 0 0 1 14-5.3"/><path d="M20 12a8 8 0 0 1-14 5.3"/>'
    '<path d="M18 3v5h-5"/><path d="M6 21v-5h5"/>',
    "pulse": '<path d="M3 12h4l2-7 4 14 2-7h6"/>',
    "cloud-rain": '<path d="M7 16a4 4 0 1 1 1-7.9A5 5 0 0 1 18 10a3.5 3.5 0 0 1-1 6.9H7z"/>'
    '<path d="M8 19v2M12 19v2M16 19v2"/>',
    "alert": '<path d="M12 3 2 20h20L12 3z"/><path d="M12 10v4"/><path d="M12 17h.01"/>',
    "shield": '<path d="M12 3l7 3v6c0 5-3.5 7.5-7 9-3.5-1.5-7-4-7-9V6l7-3z"/><path d="M9 12l2 2 4-4"/>',
    "radio": '<circle cx="12" cy="12" r="2"/>'
    '<path d="M8.5 8.5a5 5 0 0 0 0 7M15.5 8.5a5 5 0 0 1 0 7M5.5 5.5a9 9 0 0 0 0 13M18.5 5.5a9 9 0 0 1 0 13"/>',
    "layers": '<path d="M12 3 2 8l10 5 10-5-10-5z"/><path d="M2 13l10 5 10-5"/>',
    "search": '<circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/>',
    "rocket": '<path d="M12 2c3 3 4 7 4 11l-4 4-4-4c0-4 1-8 4-11z"/><path d="M8 15l-3 5M16 15l3 5"/>',
    "trend": '<path d="M3 17l6-6 4 4 8-8"/><path d="M15 7h6v6"/>',
    "users": '<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6"/>'
    '<circle cx="17" cy="9" r="2.5"/><path d="M15.5 14.2c2.6.4 4.5 2.6 4.5 5.3"/>',
    "cpu": '<rect x="6" y="6" width="12" height="12" rx="2"/>'
    '<path d="M9 2v3M15 2v3M9 19v3M15 19v3M2 9h3M2 15h3M19 9h3M19 15h3"/>',
    "monitor": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 21h8M12 16v5"/>',
    "eye": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="3"/>',
    "sliders": '<line x1="4" y1="6" x2="20" y2="6"/><circle cx="15" cy="6" r="2"/>'
    '<line x1="4" y1="12" x2="20" y2="12"/><circle cx="9" cy="12" r="2"/>'
    '<line x1="4" y1="18" x2="20" y2="18"/><circle cx="17" cy="18" r="2"/>',
    "map": '<path d="M9 3 3 5v16l6-2 6 2 6-2V3l-6 2-6-2z"/><path d="M9 3v16M15 5v16"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "database": '<ellipse cx="12" cy="5" rx="8" ry="3"/>'
    '<path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/>'
    '<path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/>',
    "target": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><circle cx="12" cy="12" r=".5"/>',
}


def icon(name: str, size: int = 22, cls: str = "") -> str:
    inner = _ICONS.get(name, _ICONS["target"])
    klass = f' class="{cls}"' if cls else ""
    return (
        f'<svg{klass} width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="currentColor" stroke-width="1.7" '
        f'stroke-linecap="round" stroke-linejoin="round">{inner}</svg>'
    )
