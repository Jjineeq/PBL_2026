"""Render helpers for the Control Room's route-comparison step.

Same single-call HTML-string rule as the other components/*_ui.py modules,
except render_leaflet_route_map() which returns a full standalone HTML
document meant for st.components.v1.html() (it needs its own <head> for the
Leaflet CDN assets, so it can't share the page's single st.markdown() call).
Sparklines are hand-rolled inline SVG (no chart library), consistent with
components/car_diagram.py's self-drawn-primitives approach.
"""

import json

from logic.health_score import BAND_COLORS, HEALTH_BANDS, band_for

# ---------------------------------------------------------------------------
# Real-map route view (Leaflet + OpenStreetMap tiles, CSS-inverted to a dark
# basemap — plain OSM tiles stay free/keyless, unlike hosted dark tile sets)
# ---------------------------------------------------------------------------

# Fixed per-route-identity colors for the map (independent of health band) —
# two routes can land in the same band (e.g. both "심각") and would render
# identically if colored by band, making it impossible to tell them apart on
# the map. These stay constant so "경로 A" is always the same color no matter
# how it scores. Chosen away from the red/orange severity spectrum used for
# bands/risk markers elsewhere, so route identity and risk severity never
# read as the same signal.
ROUTE_COLORS = {"A": "#4f9dff", "B": "#a78bfa", "C": "#34d399"}

# One glyph per risk tag (logic/routes.py's _RISK_TAGS pool) so the map shows
# *what kind* of risk a waypoint carries at a glance, not just a generic red
# dot. Keyed by the exact Korean tag text since that's what routes carry.
RISK_TAG_ICONS = {
    "보행자 밀집": "🚶",
    "인도 인접 차선": "🚏",
    "야간 시야 저하": "🌙",
    "합류구간": "🔀",
    "비보호 좌회전": "↩️",
    "차량 급변침 잦음": "🌀",
    "복잡 교차로": "🚦",
    "차선 선택지 과다": "↔️",
    "공사구간": "🚧",
    "급커브 구간": "↪️",
    "좁은 차선": "📏",
    "노면 마찰력 저하": "💧",
}


def render_leaflet_route_map(routes: list[dict], recommended_key: str, origin_label: str, dest_label: str) -> str:
    """Standalone HTML document (own <head>/CDN includes) for
    st.components.v1.html() — draws the real Seoul·Gyeonggi·Incheon-area map
    with each candidate route as a curved polyline between the vehicle's
    origin/destination coordinates (colored by route identity, not band), a
    tagged icon per risk waypoint, and a pale underlay wherever two or more
    routes actually share the same stretch of road."""
    data = {
        "routes": [
            {
                "key": r["key"],
                "label": r["label"],
                "role_label": r.get("role_label", ""),
                "color": ROUTE_COLORS.get(r["key"], "#8892a8"),
                "recommended": r["key"] == recommended_key,
                "coords": r["coords"],
                "scores": r["scores"],
                "time_labels": r["time_labels"],
                "risk_points": r["risk_points"],
                "min_score": r["min_score"],
                "band_label": r["band"][2],
            }
            for r in routes
        ],
        "origin": {"label": origin_label, "coords": routes[0]["coords"][0]},
        "dest": {"label": dest_label, "coords": routes[0]["coords"][-1]},
        "risk_icons": RISK_TAG_ICONS,
    }
    data_json = json.dumps(data, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  html, body {{ height:100%; margin:0; background:transparent; }}
  body {{ font-family:'Malgun Gothic','Noto Sans KR',sans-serif; padding:2px; box-sizing:border-box; }}
  #map {{
    height:calc(100% - 4px); width:calc(100% - 4px); background:#0c1120;
    border-radius:16px; border:1px solid rgba(255,255,255,0.14);
    box-shadow:0 8px 32px rgba(0,0,0,0.45);
    overflow:hidden;
  }}
  /* Plain OpenStreetMap tiles (free, no API key) inverted into a dark
     basemap — the hosted CARTO dark tiles now require a key, this doesn't. */
  .leaflet-tile-pane {{ filter:invert(1) hue-rotate(180deg) brightness(0.92) contrast(0.9) saturate(0.7); }}
  .leaflet-popup-content-wrapper, .leaflet-popup-tip {{ background:#131a2e; color:#e7e9f5; }}
  .leaflet-popup-content-wrapper {{ border-radius:10px; border:1px solid rgba(255,255,255,0.14); }}
  .leaflet-popup-content {{ font-size:13px; line-height:1.5; margin:10px 12px; }}
  .leaflet-container a.leaflet-popup-close-button {{ color:#b7bfd6; }}
  .route-tooltip {{ background:#131a2e; color:#e7e9f5; border:1px solid rgba(255,255,255,0.2); font-weight:700; }}
  .leaflet-control-attribution {{ background:rgba(12,17,32,0.7)!important; color:#7c8399!important; font-size:10px; }}
  .leaflet-control-attribution a {{ color:#8fb4e8!important; }}
  .leaflet-control-zoom a {{ background:#131a2e!important; color:#e7e9f5!important; border-color:rgba(255,255,255,0.14)!important; }}
  .leaflet-control-zoom a:hover {{ background:#1b2440!important; }}
  .leaflet-control-zoom {{ border:1px solid rgba(255,255,255,0.14)!important; }}
  .route-legend {{
    background:#131a2e; color:#e7e9f5; border:1px solid rgba(255,255,255,0.16);
    border-radius:10px; padding:8px 10px; font-size:11px; line-height:1.5;
    box-shadow:0 4px 16px rgba(0,0,0,0.4); max-width:190px;
  }}
  .route-filter {{
    display:flex; gap:3px; background:#131a2e; border:1px solid rgba(255,255,255,0.16);
    border-radius:9px; padding:3px; box-shadow:0 4px 16px rgba(0,0,0,0.4);
  }}
  .route-filter-btn {{
    background:transparent; border:none; color:#b7bfd6; font-size:11.5px; font-weight:700;
    padding:5px 10px; border-radius:6px; cursor:pointer; font-family:inherit; transition:background 0.15s;
  }}
  .route-filter-btn:hover {{ background:rgba(255,255,255,0.1); }}
</style>
</head>
<body>
<div id="map"></div>
<script>
  const DATA = {data_json};
  const map = L.map('map', {{ zoomControl: true, attributionControl: true, scrollWheelZoom: true }});
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
  }}).addTo(map);

  // Origin/destination need to read as origin/destination WITHOUT a click —
  // a same-size same-shape dot distinguished only by color doesn't clear
  // that bar. Each marker is a label chip stacked right above its dot, both
  // baked into one divIcon so the label is always on, not just on hover.
  function endpointIcon(emoji, text, color) {{
      return L.divIcon({{
          className: '',
          html: `<div style="display:flex;flex-direction:column;align-items:center;">` +
                `<div style="background:${{color}};color:#0a0e1a;font-size:11px;font-weight:800;` +
                `padding:3px 10px;border-radius:7px;white-space:nowrap;margin-bottom:4px;` +
                `box-shadow:0 3px 10px rgba(0,0,0,0.5);">${{emoji}} ${{text}}</div>` +
                `<div style="width:20px;height:20px;border-radius:50%;background:${{color}};` +
                `border:3px solid #fff;box-shadow:0 0 10px ${{color}};"></div></div>`,
          iconSize: [140, 50],
          iconAnchor: [70, 33],
      }});
  }}
  const originIcon = endpointIcon('🚩', '출발 · ' + DATA.origin.label, '#3ddad7');
  const destIcon = endpointIcon('🏁', '도착 · ' + DATA.dest.label, '#ff6b4a');
  L.marker(DATA.origin.coords, {{icon: originIcon}}).addTo(map);
  L.marker(DATA.dest.coords, {{icon: destIcon}}).addTo(map);

  // Resamples a polyline down to n evenly-spaced (by arc length) points —
  // used so time/risk markers land at consistent positions whether the line
  // is our 5-point synthetic curve or a real multi-hundred-point road path.
  function resample(points, n) {{
      if (points.length <= n) return points;
      const distKm = (a, b) => {{
          const dLat = (b[0] - a[0]) * 111;
          const dLng = (b[1] - a[1]) * 111 * Math.cos(a[0] * Math.PI / 180);
          return Math.hypot(dLat, dLng);
      }};
      const cum = [0];
      for (let i = 1; i < points.length; i++) cum.push(cum[i - 1] + distKm(points[i - 1], points[i]));
      const total = cum[cum.length - 1];
      const out = [];
      for (let i = 0; i < n; i++) {{
          const target = total * i / (n - 1);
          let j = 0;
          while (j < cum.length - 2 && cum[j + 1] < target) j++;
          const segLen = (cum[j + 1] - cum[j]) || 1;
          const t = (target - cum[j]) / segLen;
          const p0 = points[j], p1 = points[j + 1];
          out.push([p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t]);
      }}
      return out;
  }}

  const routeLayer = L.layerGroup().addTo(map);
  const routeColorByKey = Object.fromEntries(DATA.routes.map(r => [r.key, r.color]));

  // One sub-layer-group per route key (plus one for the shared-corridor
  // underlay) so the filter buttons below can show/hide a single route
  // without having to know which individual polylines/markers belong to it.
  // Rebuilt on every drawRoutes() call; the filter buttons always read the
  // current contents through this same object reference.
  const routeGroups = {{}};
  let overlapGroup = null;
  let activeFilter = 'all';
  // tag -> emoji actually used by each route, filled in by drawRoutes() —
  // applyFilter() re-slices this by whichever route(s) are currently
  // visible, so the legend only ever lists what's actually on screen.
  let usedTagsByRoute = {{}};

  // Small always-on corner panel: which color is which route, which risk
  // icons are actually shown for the currently-visible route(s), and a note
  // about the shared-segment underlay (hidden when filtered to one route,
  // since "overlap" only means something when comparing routes). Content is
  // rebuilt by applyFilter() every time the routes redraw or the filter
  // changes.
  const legendControl = L.control({{position: 'bottomleft'}});
  legendControl.onAdd = function () {{
      const div = L.DomUtil.create('div', 'route-legend');
      div.id = 'route-legend';
      return div;
  }};
  legendControl.addTo(map);

  // Top-right toggle: 전체 / A / B / C — shows just one route at a time (or
  // all three). Built once; drawRoutes() only ever repopulates routeGroups,
  // so these handlers keep working across the later real-route redraw.
  const filterControl = L.control({{position: 'topright'}});
  filterControl.onAdd = function () {{
      const div = L.DomUtil.create('div', 'route-filter');
      L.DomEvent.disableClickPropagation(div);
      [['all', '전체'], ...DATA.routes.map(r => [r.key, r.key])].forEach(([key, label]) => {{
          const btn = document.createElement('button');
          btn.className = 'route-filter-btn';
          btn.dataset.key = key;
          btn.textContent = label;
          btn.addEventListener('click', () => {{ activeFilter = key; applyFilter(); }});
          div.appendChild(btn);
      }});
      return div;
  }};
  filterControl.addTo(map);

  function applyFilter() {{
      // NOTE: routeGroups/overlapGroup are nested INSIDE routeLayer (not
      // added to the map directly), so membership must be checked against
      // routeLayer.hasLayer(), not map.hasLayer() — the latter only knows
      // about routeLayer itself and would always report these as absent.
      Object.keys(routeGroups).forEach(key => {{
          const shouldShow = activeFilter === 'all' || activeFilter === key;
          const group = routeGroups[key];
          if (shouldShow && !routeLayer.hasLayer(group)) group.addTo(routeLayer);
          if (!shouldShow && routeLayer.hasLayer(group)) routeLayer.removeLayer(group);
      }});
      if (overlapGroup) {{
          if (activeFilter === 'all' && !routeLayer.hasLayer(overlapGroup)) overlapGroup.addTo(routeLayer);
          if (activeFilter !== 'all' && routeLayer.hasLayer(overlapGroup)) routeLayer.removeLayer(overlapGroup);
      }}

      document.querySelectorAll('.route-filter-btn').forEach(btn => {{
          const isActive = btn.dataset.key === activeFilter;
          const activeColor = btn.dataset.key === 'all' ? '#e7e9f5' : (routeColorByKey[btn.dataset.key] || '#e7e9f5');
          btn.style.background = isActive ? activeColor : 'transparent';
          btn.style.color = isActive ? '#0c1120' : '#b7bfd6';
      }});

      let legendHtml = '';
      DATA.routes.forEach(r => {{
          const dim = activeFilter !== 'all' && activeFilter !== r.key;
          legendHtml += `<div style="display:flex;align-items:center;gap:6px;margin:2px 0;opacity:${{dim ? 0.35 : 1}};">` +
              `<span style="width:14px;height:4px;border-radius:2px;background:${{r.color}};display:inline-block;flex-shrink:0;"></span>` +
              `<span>${{r.label}}${{r.role_label ? ' · ' + r.role_label : ''}}</span></div>`;
      }});
      const visibleKeys = activeFilter === 'all' ? DATA.routes.map(r => r.key) : [activeFilter];
      const visibleTags = new Map();
      visibleKeys.forEach(k => {{
          Object.entries(usedTagsByRoute[k] || {{}}).forEach(([tag, emoji]) => visibleTags.set(tag, emoji));
      }});
      if (visibleTags.size) {{
          legendHtml += '<div style="margin:6px 0 2px 0;border-top:1px solid rgba(255,255,255,0.14);padding-top:6px;">';
          visibleTags.forEach((emoji, tag) => {{
              legendHtml += `<div style="margin:2px 0;">${{emoji}} ${{tag}}</div>`;
          }});
          legendHtml += '</div>';
      }}
      if (activeFilter === 'all') {{
          legendHtml += '<div style="margin-top:6px;color:#8892a8;">— 굵은 회색 구간 = 경로 겹침</div>';
      }}
      const legendEl = document.getElementById('route-legend');
      if (legendEl) legendEl.innerHTML = legendHtml;
  }}

  // Same arc-length resampling as resample() below, but WITHOUT the
  // short-circuit for short inputs — always returns exactly n points, so a
  // 5-point synthetic curve can be densified (not just a long real polyline
  // downsampled) for the point-by-point overlap comparison in
  // findOverlapRuns().
  function densify(points, n) {{
      if (points.length < 2) return points;
      const distKm = (a, b) => {{
          const dLat = (b[0] - a[0]) * 111;
          const dLng = (b[1] - a[1]) * 111 * Math.cos(a[0] * Math.PI / 180);
          return Math.hypot(dLat, dLng);
      }};
      const cum = [0];
      for (let i = 1; i < points.length; i++) cum.push(cum[i - 1] + distKm(points[i - 1], points[i]));
      const total = cum[cum.length - 1] || 1;
      const out = [];
      for (let i = 0; i < n; i++) {{
          const target = total * i / (n - 1);
          let j = 0;
          while (j < cum.length - 2 && cum[j + 1] < target) j++;
          const segLen = (cum[j + 1] - cum[j]) || 1;
          const t = (target - cum[j]) / segLen;
          const p0 = points[j], p1 = points[j + 1];
          out.push([p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t]);
      }}
      return out;
  }}

  // For each route, finds the index runs (into its own densified points)
  // that fall within ~35m of ANY other route's densified points — i.e. the
  // stretches where they're actually driving over the same road, most
  // commonly right at the shared origin/destination. Drawn as a pale
  // underlay so a shared corridor reads as "one road, three routes use it"
  // instead of three colored lines stacked on top of each other.
  function findOverlapRuns(lineCoordsList) {{
      const OVERLAP_KM = 0.035;
      const dense = lineCoordsList.map(pts => densify(pts, 60));
      const distKm = (a, b) => {{
          const dLat = (b[0] - a[0]) * 111;
          const dLng = (b[1] - a[1]) * 111 * Math.cos(a[0] * Math.PI / 180);
          return Math.hypot(dLat, dLng);
      }};
      return dense.map((pts, i) => {{
          const shared = pts.map(pt => dense.some((other, j) => j !== i && other.some(op => distKm(pt, op) < OVERLAP_KM)));
          const runs = [];
          let start = null;
          for (let k = 0; k < shared.length; k++) {{
              if (shared[k]) {{
                  if (start === null) start = k;
              }} else if (start !== null) {{
                  runs.push([start, k - 1]);
                  start = null;
              }}
          }}
          if (start !== null) runs.push([start, shared.length - 1]);
          return {{ points: pts, runs }};
      }});
  }}

  function drawRoutes(lineCoordsList) {{
      routeLayer.clearLayers();
      Object.keys(routeGroups).forEach(k => delete routeGroups[k]);
      usedTagsByRoute = {{}};
      const bounds = [DATA.origin.coords, DATA.dest.coords];

      // Shared-corridor underlay — its own group so applyFilter() can hide
      // it entirely when only one route is showing.
      overlapGroup = L.layerGroup();
      findOverlapRuns(lineCoordsList).forEach(info => {{
          info.runs.forEach(([s, e]) => {{
              if (e - s < 1) return;
              L.polyline(info.points.slice(s, e + 1), {{
                  color: '#e7e9f5', weight: 11, opacity: 0.16, lineCap: 'round'
              }}).addTo(overlapGroup);
          }});
      }});

      DATA.routes.forEach((r, idx) => {{
          const group = L.layerGroup();
          usedTagsByRoute[r.key] = {{}};
          const lineCoords = lineCoordsList[idx];
          lineCoords.forEach(p => bounds.push(p));
          const line = L.polyline(lineCoords, {{
              color: r.color,
              weight: r.recommended ? 5 : 3,
              opacity: r.recommended ? 0.95 : 0.75
          }}).addTo(group);
          line.bindTooltip(r.label + (r.role_label ? ' · ' + r.role_label : ''), {{sticky:true, className:'route-tooltip'}});

          const markerPts = resample(lineCoords, r.coords.length);
          markerPts.forEach((c, i) => {{
              if (i === 0 || i === markerPts.length - 1) return;
              const risk = r.risk_points.find(rp => rp.idx === i);
              if (risk) {{
                  const emoji = DATA.risk_icons[risk.tag] || '⚠';
                  usedTagsByRoute[r.key][risk.tag] = emoji;
                  const icon = L.divIcon({{
                      className: '',
                      html: `<div style="width:24px;height:24px;border-radius:50%;background:${{r.color}};` +
                            `border:2px solid #fff;box-shadow:0 0 8px ${{r.color}};display:flex;` +
                            `align-items:center;justify-content:center;font-size:12px;line-height:1;">${{emoji}}</div>`,
                      iconSize: [24, 24], iconAnchor: [12, 12]
                  }});
                  const marker = L.marker(c, {{icon}}).addTo(group);
                  marker.bindPopup(
                      `<b>${{r.label}}</b><br>${{r.time_labels[i]}} 지점 · 예상 점수 ${{r.scores[i]}}` +
                      `<br><b style="color:#ff6b7d;">${{emoji}} ${{risk.tag}}</b>`
                  );
              }} else {{
                  const marker = L.circleMarker(c, {{
                      radius: 4.5, color: r.color, fillColor: r.color, fillOpacity: 0.9, weight: 2
                  }}).addTo(group);
                  marker.bindPopup(`<b>${{r.label}}</b><br>${{r.time_labels[i]}} 지점 · 예상 점수 ${{r.scores[i]}}`);
              }}
          }});

          routeGroups[r.key] = group;
      }});

      applyFilter();
      map.fitBounds(bounds, {{padding: [36, 36]}});
  }}

  // First paint: our synthetic bowed curves, so the map is never blank.
  drawRoutes(DATA.routes.map(r => r.coords));

  // Then try to upgrade every route to real road-following geometry via
  // OSRM's public routing demo server (free, no key) — never leaves a route
  // as a pure geometric offset, because that can cut across water/terrain
  // for coastal pairs. alternatives=true asks for more than one path
  // between the same two points; when there aren't enough real alternatives
  // for all candidates, the rest are fetched as a route THROUGH a via-point
  // near our synthetic curve's midpoint — OSRM snaps any coordinate to the
  // nearest real road, so the result always stays on the actual road
  // network even if the via-point itself lands in the sea. If a request
  // fails for any reason (offline, rate-limited), that route just keeps its
  // synthetic curve — no error shown to the user.
  async function fetchJson(url) {{
      try {{
          const res = await fetch(url);
          if (!res.ok) return null;
          return await res.json();
      }} catch (e) {{
          return null;
      }}
  }}

  async function fetchRealRoutes(origin, dest) {{
      const url = `https://router.project-osrm.org/route/v1/driving/${{origin[1]}},${{origin[0]}};${{dest[1]}},${{dest[0]}}?overview=full&geometries=geojson&alternatives=true`;
      const data = await fetchJson(url);
      if (!data || !data.routes || !data.routes.length) return null;
      const sorted = [...data.routes].sort((a, b) => a.distance - b.distance);
      return sorted.map(rt => rt.geometry.coordinates.map(c => [c[1], c[0]]));
  }}

  async function fetchViaRoute(origin, viaPoint, dest) {{
      const url = `https://router.project-osrm.org/route/v1/driving/${{origin[1]}},${{origin[0]}};${{viaPoint[1]}},${{viaPoint[0]}};${{dest[1]}},${{dest[0]}}?overview=full&geometries=geojson`;
      const data = await fetchJson(url);
      if (!data || !data.routes || !data.routes.length) return null;
      return data.routes[0].geometry.coordinates.map(c => [c[1], c[0]]);
  }}

  (async () => {{
      const real = await fetchRealRoutes(DATA.origin.coords, DATA.dest.coords);
      const lineCoordsList = [];
      for (let idx = 0; idx < DATA.routes.length; idx++) {{
          if (real && real[idx]) {{
              lineCoordsList.push(real[idx]);
              continue;
          }}
          const synthetic = DATA.routes[idx].coords;
          const viaPoint = synthetic[Math.floor(synthetic.length / 2)];
          const viaRoute = await fetchViaRoute(DATA.origin.coords, viaPoint, DATA.dest.coords);
          lineCoordsList.push(viaRoute || synthetic);
      }}
      drawRoutes(lineCoordsList);
  }})();
</script>
</body>
</html>"""


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


_ROLE_BADGE_HTML = {
    "ai_optimal": '<div class="recommended-badge">🎯 AI 최적 경로 · 점수 최대화</div>',
    "shortest": '<div class="role-badge role-shortest">📍 최단 경로</div>',
    "compromise": '<div class="role-badge role-compromise">⚖️ 관제사 절충안</div>',
}


def render_route_cards(routes: list[dict], recommended_key: str) -> str:
    cards = []
    for r in routes:
        color = BAND_COLORS.get(r["band"][2], "#8892a8")
        route_color = ROUTE_COLORS.get(r["key"], "#8892a8")
        is_recommended = r["key"] == recommended_key
        badge = _ROLE_BADGE_HTML.get(r.get("role"), "")
        if r["risk_factors"]:
            tags = "".join(
                f'<span class="chip route-tag">{RISK_TAG_ICONS.get(t, "⚠")} {t}</span>' for t in r["risk_factors"]
            )
        else:
            tags = '<span class="route-tag-empty">특이 위험요인 없음</span>'
        spark = _sparkline_svg(r["scores"], r["eta_min"])

        cards.append(
            f"""
            <div class="route-card{' recommended' if is_recommended else ''}">
                {badge}
                <div class="route-card-label">
                    <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{route_color};margin-right:7px;vertical-align:middle;"></span>
                    {r['label']}
                </div>
                <div class="route-card-meta">{r['distance_km']}km · 약 {r['eta_min']}분</div>
                <div class="sparkline">{spark}</div>
                <div class="route-card-score" style="color:{color};">
                    최저 예측 점수 {r['min_score']}
                    <span class="band-name">({r['band'][2]})</span>
                </div>
                <div class="route-score-track"><div class="route-score-fill" style="width:{r['min_score']}%;background:{color};"></div></div>
                <div class="route-tags-label">위험 요인 · 이 점수가 나온 이유</div>
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


def render_route_tradeoff(tradeoff: dict, routes: list[dict]) -> str:
    """Makes the "AI optimizes for score, controller can push back" concept
    concrete with actual numbers instead of just a badge: how much extra
    distance/time the AI's score-maximizing pick costs over the shortest
    route, what score gain that buys, and which named risk factors it
    avoids. Returns "" when the AI's pick already IS the shortest route —
    there's no detour to justify, so nothing to show."""
    if not tradeoff["has_tradeoff"]:
        return ""

    route_by_key = {r["key"]: r for r in routes}
    optimal = route_by_key[tradeoff["ai_optimal_key"]]
    compromise = route_by_key[tradeoff["compromise_key"]]

    avoided_html = (
        "".join(f'<span class="chip route-tag">{RISK_TAG_ICONS.get(t, "⚠")} {t}</span>' for t in tradeoff["avoided_risks"])
        if tradeoff["avoided_risks"]
        else '<span class="route-tag-empty">회피한 위험 요인 없음</span>'
    )

    extreme_note = (
        f'<p style="color:var(--accent-red-2);font-weight:700;font-size:0.92rem;margin-top:12px;">'
        f'⚠ 최단 경로 대비 {tradeoff["extra_pct"]}% 더 우회하는 경로입니다 — '
        f'절충안({compromise["label"]})도 함께 검토해보세요.</p>'
        if tradeoff["is_extreme"]
        else ""
    )

    return f"""
    <div class="verdict-panel reveal" style="margin-top:18px;">
        <div class="vlabel">AI 최적화 트레이드오프</div>
        <p>
            AI는 예측 Health Score를 최대화하는 경로({optimal['label']})를 우선 제안합니다.
            최단 경로 대비 <b>{tradeoff['extra_km']}km(+{tradeoff['extra_pct']}%) · {tradeoff['extra_min']}분</b> 더 걸리지만,
            최저 예측 점수는 <b style="color:var(--accent-teal);">+{tradeoff['score_gain']}점</b> 높습니다.
        </p>
        <div class="route-tags-label" style="margin-top:12px;">회피한 위험 요인</div>
        <div class="chip-row route-tags">{avoided_html}</div>
        {extreme_note}
    </div>
    """
