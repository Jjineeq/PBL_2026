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


def render_leaflet_route_map(routes: list[dict], recommended_key: str, origin_label: str, dest_label: str) -> str:
    """Standalone HTML document (own <head>/CDN includes) for
    st.components.v1.html() — draws the real Seoul·Gyeonggi·Incheon-area map
    with each candidate route as a curved polyline between the vehicle's
    origin/destination coordinates, and a marker per time-step waypoint
    (colored red + tooltip where that step has a risk factor)."""
    data = {
        "routes": [
            {
                "key": r["key"],
                "label": r["label"],
                "color": BAND_COLORS.get(r["band"][2], "#8892a8"),
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

  const originIcon = L.divIcon({{className:'', html:'<div style="width:14px;height:14px;border-radius:50%;background:#3ddad7;border:2px solid #fff;box-shadow:0 0 8px #3ddad7;"></div>', iconSize:[14,14], iconAnchor:[7,7]}});
  const destIcon = L.divIcon({{className:'', html:'<div style="width:14px;height:14px;border-radius:50%;background:#ff6b4a;border:2px solid #fff;box-shadow:0 0 8px #ff6b4a;"></div>', iconSize:[14,14], iconAnchor:[7,7]}});
  L.marker(DATA.origin.coords, {{icon: originIcon}}).addTo(map).bindPopup('출발 · ' + DATA.origin.label);
  L.marker(DATA.dest.coords, {{icon: destIcon}}).addTo(map).bindPopup('도착 · ' + DATA.dest.label);

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

  function drawRoutes(lineCoordsList) {{
      routeLayer.clearLayers();
      const bounds = [DATA.origin.coords, DATA.dest.coords];
      DATA.routes.forEach((r, idx) => {{
          const lineCoords = lineCoordsList[idx];
          lineCoords.forEach(p => bounds.push(p));
          const line = L.polyline(lineCoords, {{
              color: r.color,
              weight: r.recommended ? 5 : 3,
              opacity: r.recommended ? 0.95 : 0.55,
              dashArray: r.recommended ? null : '7 7'
          }}).addTo(routeLayer);
          line.bindTooltip((r.recommended ? '✓ ' : '') + r.label, {{sticky:true, className:'route-tooltip'}});

          const markerPts = resample(lineCoords, r.coords.length);
          markerPts.forEach((c, i) => {{
              if (i === 0 || i === markerPts.length - 1) return;
              const risk = r.risk_points.find(rp => rp.idx === i);
              const marker = L.circleMarker(c, {{
                  radius: risk ? 7 : 4.5,
                  color: risk ? '#ff3d63' : r.color,
                  fillColor: risk ? '#ff3d63' : r.color,
                  fillOpacity: 0.9,
                  weight: 2
              }}).addTo(routeLayer);
              const riskHtml = risk ? `<br><b style="color:#ff6b7d;">⚠ ${{risk.tag}}</b>` : '';
              marker.bindPopup(
                  `<b>${{r.label}}</b><br>${{r.time_labels[i]}} 지점 · 예상 점수 ${{r.scores[i]}}${{riskHtml}}`
              );
          }});
      }});
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
