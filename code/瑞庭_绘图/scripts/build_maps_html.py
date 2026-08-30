# -*- coding: utf-8 -*-
"""
HTML map figures — 6-slide spatial block.

- P1 (P1_01): 3D ECharts globe (echarts-gl).  Country fill = log(Mt).
  Top emitters get VERTICAL 3D BARS on top of the country; bar HEIGHT
  encodes per-capita CO₂ (t/person).  This is the headline visual:
  the world is sized by tonnage but the bars show intensity, so
  CHN/IND have big land-mass + short bars, while QAT/KWT have
  tiny land-mass + tall bars.
- P3 (P3_01): 2D ECharts world map. Country fill = dominant fuel (Coal/Oil/Gas).
  Glowing dots on regime leaders (no arcs — they added no meaning). Side panel
  = fuel count cards.

Fully self-contained: only `lib/echarts*.min.js` and `lib/world.geojson` are
loaded locally, so the HTML works in file:// (and offline) without CDN.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

EDA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDA))

import config
from utils.data import concentration_stats, fuel_ok, load_panel, slice_year

NE_CACHE = EDA / "aux" / "ne_110m_admin0.geojson"
NE_URL = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"

LIBS = config.WEB_LIBS
WORLD_GEOJSON = LIBS / "world.geojson"
ECHARTS_JS = LIBS / "echarts.min.js"
ECHARTS_GL_JS = LIBS / "echarts-gl.min.js"

# Make sure the build-time assets exist (download from CDN or copy from
# the project's Natural Earth cache if missing).
need_bootstrap = (
    not ECHARTS_JS.exists() or ECHARTS_JS.stat().st_size < 500_000
    or not WORLD_GEOJSON.exists() or WORLD_GEOJSON.stat().st_size < 100_000
    or not ECHARTS_GL_JS.exists() or ECHARTS_GL_JS.stat().st_size < 300_000
)
if need_bootstrap:
    from _bootstrap_libs import (
        ensure_echarts, ensure_echarts_gl, ensure_world_geojson,
    )
    ensure_echarts()
    ensure_echarts_gl()
    ensure_world_geojson()

CO2_COLOR_RAMP = [
    [0.00, "#E8F1E1"],
    [0.15, "#C8E0A3"],
    [0.30, "#9DCB68"],
    [0.45, "#F4D35E"],
    [0.60, "#EE964B"],
    [0.75, "#D34E29"],
    [0.90, "#A8261C"],
    [1.00, "#5C0F0F"],
]

INTENSITY_HOT = "#C62828"
INTENSITY_COOL = "#2E7D32"

# Per-capita colour ramp (5-stop green → red, used by 3D bar fills and legend).
PC_COLOR_STOPS = [
    (0.00, "#2E7D32"),  # deep green — low per-capita (CHINA / INDIA range)
    (0.25, "#7CB342"),  # light green
    (0.50, "#FDD835"),  # yellow — mid (USA, RUS, JPN range)
    (0.75, "#EF6C00"),  # orange
    (1.00, "#B71C1C"),  # deep red — high per-capita (QAT / KWT / ARE range)
]


def _pc_color(pc: float, pc_max: float) -> str:
    """Map a per-capita value to a colour on the green→red ramp."""
    if pc_max <= 0:
        return PC_COLOR_STOPS[0][1]
    t = max(0.0, min(1.0, pc / pc_max))
    for (t0, c0), (t1, c1) in zip(PC_COLOR_STOPS, PC_COLOR_STOPS[1:]):
        if t <= t1:
            u = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            return _mix(c0, c1, u)
    return PC_COLOR_STOPS[-1][1]


def _ensure_basemap() -> gpd.GeoDataFrame:
    if not NE_CACHE.exists():
        w = gpd.read_file(NE_URL)
        w = w[["ADM0_A3", "ADMIN", "geometry"]].rename(columns={"ADM0_A3": "iso", "ADMIN": "name"})
        w["geometry"] = w.geometry.simplify(0.25, preserve_topology=True)
        NE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        w.to_file(NE_CACHE, driver="GeoJSON")
    return gpd.read_file(NE_CACHE)


def _centroids(y: pd.DataFrame) -> dict:
    w = _ensure_basemap()
    pts = w.geometry.representative_point()
    return {iso: (float(lng), float(lat)) for iso, lng, lat in zip(w["iso"], pts.x, pts.y)}


def _html_doc(title: str, body: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{title}</title>
</head>
<body>
{body}
</body>
</html>
"""


def _inject_script(p: Path) -> str:
    """Inline a local JS file into the HTML so the page works on file:// without
    a local web server. ECharts is large but the rest of our scripts are small."""
    return f"<script>\n{p.read_text(encoding='utf-8', errors='ignore')}\n</script>"


def _load_echarts_inline() -> str:
    if not ECHARTS_JS.exists():
        raise FileNotFoundError(f"ECharts library missing: {ECHARTS_JS}")
    return f"<script>\n{ECHARTS_JS.read_text(encoding='utf-8', errors='ignore')}\n</script>"


def _load_world_inline() -> str:
    if not WORLD_GEOJSON.exists():
        raise FileNotFoundError(f"World GeoJSON missing: {WORLD_GEOJSON}")
    gj = json.loads(WORLD_GEOJSON.read_text(encoding="utf-8"))
    return json.dumps(gj, ensure_ascii=False)


def write_html(path: Path, html: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    print(f"  saved {path.parent.name}/{path.name}")


# ═══════════════════════════════════════════════════════════════════════════
# P1 — 3D totals map: 3D land = log(Mt), 3D vertical bars = per-capita
# ═══════════════════════════════════════════════════════════════════════════
def build_total_map(y: pd.DataFrame) -> None:
    """3D world (echarts-gl map3D).  Country land colour = log(Mt).
    On top of the top-15 emitter countries we place VERTICAL 3D BARS whose
    HEIGHT is per-capita CO₂ (t/person).  The result is a single
    "scale vs intensity" picture:

      * China/USA/India:  large land mass (high Mt) + short bars
        (per-capita only middle of the pack) — they're the giant
        smokestacks but the citizens are not the dirtiest.
      * Qatar/Kuwait/UAE:  tiny land mass + the TALLEST bars
        (per-capita 20-37 t/p) — small stacks but extreme intensity.

    Mouse drag rotates, scroll zooms.
    """
    st = concentration_stats(y)
    z = y["log_co2"].dropna()
    zmin, zmax = float(np.percentile(z, 5)), float(z.max())
    pc_max = float(y["co2_per_capita"].max())
    pc_hot = float(y["co2_per_capita"].quantile(0.9))
    centroids = _centroids(y)

    # Map data: value = log Mt (drives colour).  Carry the per-capita for the tooltip.
    map_data = []
    for _, r in y.iterrows():
        if pd.isna(r["co2"]):
            continue
        map_data.append({
            "name": r["iso_code"],
            "value": float(r["log_co2"]),
            "co2": float(r["co2"]),
            "pc": float(r["co2_per_capita"]) if pd.notna(r["co2_per_capita"]) else None,
            "country": r["country"],
        })

    # 3D BARS on the top-15 total emitters.
    # Bar HEIGHT ∝ per-capita, bar COLOR also ∝ per-capita (green→red).
    # This makes the "scale ≠ intensity" split visible at a glance:
    # China/India are red on the land (high total) but their bars are green/short
    # (per-capita only middle), while Gulf states are pale on the land but have
    # tall red bars.
    bars = []
    top_emitters = y.nlargest(15, "co2")
    for _, r in top_emitters.iterrows():
        c = centroids.get(r["iso_code"])
        if not c:
            continue
        lng, lat = c
        pc = float(r["co2_per_capita"]) if pd.notna(r["co2_per_capita"]) else 0.0
        # height in the bar3D series: keep it visually readable.
        # We map per-capita to a height in roughly [0, 14] units.
        if pc_max > 0:
            h = 1.0 + 13.0 * (pc / pc_max)  # shortest bar ≈ 1
        else:
            h = 1.0
        # Color: green (cool, low pc) → yellow (mid) → red (hot, high pc)
        col = _pc_color(pc, pc_max)
        bars.append({
            "name": f"{r['country']} — {pc:.1f} t/person",
            "value": [lng, lat, h],
            "country": r["country"],
            "co2": float(r["co2"]),
            "pc": pc,
            "itemStyle": {"color": col, "opacity": 0.9,
                          "borderColor": "#5a1210", "borderWidth": 0.4},
        })

    # Side-panel cards: top per-capita hotspots (with scale note).
    cards = []
    for iso in config.STORY_ISO_PC:
        row = y[y["iso_code"] == iso]
        if row.empty:
            continue
        r = row.iloc[0]
        pc = float(r["co2_per_capita"])
        role = "hot" if pc >= pc_hot else "cool"
        cards.append((iso, r["country"], pc, float(r["co2"]), role))
    cards_js = json.dumps(cards, ensure_ascii=False)
    map_data_js = json.dumps(map_data, ensure_ascii=False)
    bars_js = json.dumps(bars, ensure_ascii=False)
    world_js = _load_world_inline()
    echarts_js = _load_echarts_inline()
    echarts_gl_js = (
        f"<script>\n{ECHARTS_GL_JS.read_text(encoding='utf-8', errors='ignore')}\n</script>"
    )

    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>P1 3D totals + per-capita bars</title>
<style>
  :root {{ --ink:#121820; --muted:#5c6b7a; --page:#eceef1; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:"Segoe UI","Helvetica Neue",Arial,sans-serif;
         color:var(--ink); background:var(--page); }}
  .wrap {{ max-width:1480px; margin:0 auto; padding:14px 18px 28px; }}
  .kicker {{ font-size:11px; letter-spacing:.14em; text-transform:uppercase;
             color:#7a8b9c; margin:0 0 4px; }}
  h1.file {{ margin:0 0 6px; font-size:18px; font-weight:700; color:#243040; }}
  .sub {{ margin:0 0 12px; font-size:13px; color:var(--muted); line-height:1.5; max-width:960px; }}
  .sub b {{ color:#b71c1c; }}
  .grid {{ display:grid; grid-template-columns: 1.7fr 0.7fr; gap:14px; align-items:start; }}
  .stage {{ position:relative; border-radius:18px; overflow:hidden;
            background: linear-gradient(168deg,#eef1f4 0%,#f4f6f8 50%,#f8f9fb 100%);
            border:1px solid rgba(255,255,255,.85); height:720px; }}
  #map {{ width:100%; height:100%; }}
  .cbar {{ position:absolute; z-index:5; left:14px; top:50%; transform:translateY(-50%);
           display:flex; flex-direction:column; align-items:center; gap:8px;
           padding:12px 10px; border-radius:16px; background:rgba(255,255,255,.86);
           backdrop-filter:blur(12px); border:1px solid rgba(255,255,255,.95);
           box-shadow:0 12px 30px rgba(25,45,70,.12); }}
  .cbar .t {{ font-size:10px; letter-spacing:.12em; color:#3d5166; font-weight:700; }}
  .cbar .track {{ width:14px; height:170px; border-radius:99px;
                   background:linear-gradient(180deg,
                     #E8F1E1 0%, #C8E0A3 14%, #9DCB68 29%, #F4D35E 43%,
                     #EE964B 57%, #D34E29 71%, #A8261C 86%, #5C0F0F 100%);
                   box-shadow:inset 0 0 0 1px rgba(0,0,0,.07); }}
  .cbar .meta {{ display:flex; flex-direction:column; justify-content:space-between;
                 height:170px; }}
  .cbar .meta b {{ font-size:11px; color:#243040; }}
  .cbar .meta span {{ font-size:9px; color:#7a8b9c; }}
  .barLegend {{ position:absolute; z-index:5; right:14px; bottom:14px;
                background:rgba(255,255,255,.88); backdrop-filter:blur(10px);
                border:1px solid rgba(255,255,255,.95); border-radius:14px;
                padding:10px 12px; box-shadow:0 10px 24px rgba(25,45,70,.10);
                font-size:11px; color:var(--muted); line-height:1.5; }}
  .barLegend b {{ color:#243040; font-size:12px; display:block; margin-bottom:4px; }}
  .barLegend .bar {{ display:flex; align-items:flex-end; gap:6px; }}
  .barLegend .col {{ width:10px; background:linear-gradient(180deg,
                     #2E7D32 0%, #7CB342 25%, #FDD835 50%, #EF6C00 75%, #B71C1C 100%);
                     border:1px solid rgba(0,0,0,.18); border-radius:2px; }}
  .side h2 {{ margin:6px 0; font-size:13px; font-weight:700; color:#3d5166; }}
  .blurb {{ font-size:12px; color:var(--muted); line-height:1.45; padding:11px 13px;
            border-radius:14px; background:#fff; border:1px solid rgba(0,0,0,.05);
            box-shadow:0 6px 16px rgba(30,50,70,.05); margin:0 0 10px; }}
  .card {{ border-radius:14px; padding:10px 12px; background:#fff; margin-bottom:8px;
           border:1px solid rgba(0,0,0,.05); box-shadow:0 6px 16px rgba(30,50,70,.05);
           display:grid; grid-template-columns:1fr auto; gap:4px 10px; align-items:center; }}
  .card.hot {{ border-left:4px solid #c62828; }}
  .card.cool {{ border-left:4px solid #2e7d32; }}
  .card .iso {{ font-size:10px; font-weight:700; letter-spacing:.08em; color:#8a9aac; }}
  .card .name {{ font-size:14px; font-weight:700; }}
  .card .role {{ font-size:10px; font-weight:700; padding:2px 8px; border-radius:99px; }}
  .card .role.hot {{ background:#fdecec; color:#c62828; }}
  .card .role.cool {{ background:#e8f4ea; color:#2e7d32; }}
  .card .m {{ font-size:11px; color:var(--muted); }}
  .card .m b {{ color:var(--ink); font-variant-numeric:tabular-nums; font-size:13px; }}
  .foot {{ margin-top:14px; font-size:12px; color:var(--muted); }}
</style>
</head>
<body>
<div class="wrap">
  <p class="kicker">Point 1 · 3D totals + per-capita bars</p>
  <h1 class="file">P1_01_map_bars_total_co2_2021.html</h1>
  <p class="sub">
    <b>Land colour</b> = log₁₀ CO₂ (Mt), 2021  ·  <b>3D bar height &amp; colour</b> = per-capita (green = low, red = high).
    Top10 ≈ <b>{st['top10_share']*100:.0f}%</b> of world · Asia ≈ <b>{st['region_share'].get('Asia',0)*100:.0f}%</b>.
    CHN/IND are red on the land but their bars are <b>green/short</b> — Gulf states are pale on the land but have <b>red/tall</b> bars.
  </p>
  <div class="grid">
    <div class="stage">
      <div id="map"></div>
      <div class="cbar">
        <div class="t">LOG Mt</div>
        <div class="track"></div>
        <div class="meta">
          <b>High</b>
          <span>10k</span>
          <span>1k</span>
          <span>Low</span>
        </div>
      </div>
      <div class="barLegend">
        <b>Bar height &amp; colour = per-capita (t / person)</b>
        <div class="bar">
          <span style="height:6px;  background:#2E7D32"></span>
          <span style="height:14px; background:#7CB342"></span>
          <span style="height:22px; background:#FDD835"></span>
          <span style="height:30px; background:#EF6C00"></span>
          <span style="height:38px; background:#B71C1C"></span>
        </div>
        <div style="font-size:9px; margin-top:4px;">
          cool &nbsp;·&nbsp; CHN/IND ≈ 7  ·  USA ≈ 14  ·  Gulf ≈ 25-37  t / person
        </div>
      </div>
    </div>
    <div class="side">
      <h2>Scale ≠ intensity</h2>
      <p class="blurb">
        The 3D bars make the scale-vs-intensity split obvious.
        Gulf countries (Qatar, Kuwait, UAE, Saudi Arabia) are small
        emitters on the land but the TALLEST bars on the map.
      </p>
      <div id="cards"></div>
    </div>
  </div>
  <p class="foot">Drag to rotate · scroll to zoom · offline (no CDN).</p>
</div>

{echarts_js}
{echarts_gl_js}
<script>
const WORLD = {world_js};
echarts.registerMap('world', WORLD);
const mapData = {map_data_js};
const bars = {bars_js};
const cards = {cards_js};

const dom = document.getElementById('map');
const option = {{
  tooltip: {{
    trigger: 'item',
    backgroundColor: 'rgba(255,255,255,0.96)',
    borderColor: '#cdd5e0', borderWidth: 1,
    textStyle: {{ color: '#243040' }},
    formatter: function(p) {{
      if (p.seriesType === 'map3D') {{
        const v = p.data;
        if (!v || !v.country) return p.name;
        return `<b>${{v.country}}</b><br>CO₂: ${{v.co2.toLocaleString(undefined,{{maximumFractionDigits:0}})}} Mt<br>per capita: ${{v.pc != null ? v.pc.toFixed(1) : 'n/a'}} t/person`;
      }}
      if (p.seriesType === 'bar3D') {{
        const v = p.data;
        return `<b>${{v.country}}</b><br>per capita: ${{v.pc.toFixed(1)}} t/person<br>CO₂: ${{v.co2.toLocaleString(undefined,{{maximumFractionDigits:0}})}} Mt`;
      }}
      return p.name;
    }}
  }},
  visualMap: {{
    show: false,
    min: 0, max: 4.2,
    inRange: {{ color: ['#E8F1E1','#C8E0A3','#9DCB68','#F4D35E','#EE964B','#D34E29','#A8261C','#5C0F0F'] }},
    seriesIndex: 0,
  }},
  // 3D globe base — flat heightmap (no terrain); the story is in the bars
  series3D: [
    {{ name: 'log Mt', type: 'map3D', map: 'world',
       data: mapData,
       boxHeight: 1.2,
       regionHeight: 0.8,
       itemStyle: {{ opacity: 0.92, borderColor: '#ffffff', borderWidth: 0.4 }},
       emphasis: {{ itemStyle: {{ color: '#f7d57f' }}, label: {{ show: false }} }},
       label: {{ show: false }}, zlevel: 1,
    }},
    {{ name: 'Per-capita bars', type: 'bar3D', coordinateSystem: 'map3D',
       data: bars, shading: 'lambert',
       barSize: 1.0,
       minHeight: 0.4,
       itemStyle: {{ color: '#c62828', opacity: 0.85,
                     borderColor: '#7d1810', borderWidth: 0.5 }},
       emphasis: {{ itemStyle: {{ color: '#ff7043' }} }},
       zlevel: 5,
    }},
  ],
  // Camera + interaction
  viewControl: {{
    projection: 'perspective',
    autoRotate: false,
    alpha: 25, beta: 0,
    distance: 180, minDistance: 80, maxDistance: 360,
    center: [10, 0, 20],
    animationDurationUpdate: 600,
  }},
  light: {{
    main: {{ intensity: 1.4, shadow: true, alpha: 40, beta: 30 }},
    ambient: {{ intensity: 0.5 }},
  }},
  postEffect: {{ enable: true, bloom: {{ enable: false }} }},
}};

// Render side cards (DOM-only, doesn't depend on chart)
const host = document.getElementById('cards');
cards.forEach(c => {{
  const div = document.createElement('div');
  div.className = 'card ' + c[4];
  div.innerHTML = `
    <div class="iso">${{c[0]}}</div>
    <div class="role ${{c[4]}}">${{c[4] === 'hot' ? 'HIGH INTENSITY' : 'SCALE ≠ INTENSITY'}}</div>
    <div class="name" style="grid-column:1/2">${{c[1]}}</div>
    <div class="m" style="grid-column:1/2">
      <b>${{c[2].toFixed(1)}}</b> t/person · <b>${{c[3].toLocaleString(undefined,{{maximumFractionDigits:0}})}}</b> Mt
    </div>`;
  host.appendChild(div);
}});

// Initialise the 3D chart.  Defer until the parent grid has laid out
// so the canvas gets a real (non-zero) size.
let chart = null;
function initChart() {{
  const r = dom.getBoundingClientRect();
  if (r.width < 50 || r.height < 50) return false;
  try {{
    chart = echarts.init(dom, null, {{ renderer: 'canvas', width: r.width, height: r.height }});
    chart.setOption(option);
    return true;
  }} catch (e) {{
    console.error('[P1] init error', e);
    return false;
  }}
}}
function attemptInit() {{
  if (initChart()) return;
  setTimeout(attemptInit, 80);
}}
attemptInit();
function safeResize() {{ if (chart) try {{ chart.resize(); }} catch (e) {{}} }}
if (window.ResizeObserver) {{
  const ro = new ResizeObserver(safeResize);
  ro.observe(dom);
}}
window.addEventListener('load', () => setTimeout(safeResize, 200));
setTimeout(safeResize, 600);
setTimeout(safeResize, 1500);
setTimeout(safeResize, 3000);
window.addEventListener('resize', safeResize);
</script>
</body>
</html>
"""
    write_html(config.FIGS_P1 / "P1_01_map_bars_total_co2_2021.html", html=body)


# ═══════════════════════════════════════════════════════════════════════════
# P3 — fuel regimes night-style atlas
# ═══════════════════════════════════════════════════════════════════════════
def build_fuel_map(y: pd.DataFrame) -> None:
    d = fuel_ok(y).dropna(subset=["dominant_fuel"]).copy()
    counts = d["dominant_fuel"].value_counts()
    centroids = _centroids(y)

    fuel_color = config.FUEL_COLORS

    # Country fills (value = fuel index 0/1/2, matched by visualMap pieces)
    map_data = []
    FUEL_IDX = {"Coal": 0, "Oil": 1, "Gas": 2}
    for _, r in y.iterrows():
        f = r.get("dominant_fuel")
        if pd.isna(f) or str(f) not in FUEL_IDX:
            map_data.append({
                "name": r["iso_code"], "value": 3,
                "country": r["country"], "fuel": None,
            })
        else:
            map_data.append({
                "name": r["iso_code"], "value": FUEL_IDX[str(f)],
                "country": r["country"], "fuel": str(f),
            })

    # Glowing dots on the largest same-fuel emitter per regime.
    # (No arcs — the user pointed out arcs between countries are not meaningful.)
    glows = []
    for fuel in ["Coal", "Oil", "Gas"]:
        sub = d[d["dominant_fuel"] == fuel].nlargest(2, "co2")
        for _, r in sub.iterrows():
            c = centroids.get(r["iso_code"])
            if not c:
                continue
            glows.append({
                "name": f"{r['country']} — {fuel} regime leader",
                "value": [c[0], c[1], float(r["co2"])],
                "itemStyle": {"color": fuel_color[fuel], "shadowBlur": 12,
                              "shadowColor": fuel_color[fuel]},
            })

    map_data_js = json.dumps(map_data, ensure_ascii=False)
    glows_js = json.dumps(glows, ensure_ascii=False)
    counts_js = json.dumps({k: int(v) for k, v in counts.items()}, ensure_ascii=False)
    fuel_hex_js = json.dumps(fuel_color, ensure_ascii=False)
    world_js = _load_world_inline()
    echarts_js = _load_echarts_inline()

    body = f"""
<style>
  :root {{ --ink:#e8eef6; --muted:#9aa8b8; --page:#0c1016; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:"Segoe UI","Helvetica Neue",Arial,sans-serif;
         color:var(--ink); background:#0c1016; }}
  .wrap {{ max-width:1480px; margin:0 auto; padding:14px 18px 28px; }}
  .kicker {{ font-size:11px; letter-spacing:.16em; text-transform:uppercase;
             color:#7d8da3; margin:0 0 4px; }}
  h1.file {{ margin:0 0 6px; font-size:18px; font-weight:700; }}
  .sub {{ margin:0 0 12px; font-size:13px; color:var(--muted); line-height:1.5; max-width:960px; }}
  .grid {{ display:grid; grid-template-columns: 1fr 0.55fr; gap:14px; align-items:start; }}
  .stage {{ position:relative; border-radius:20px; overflow:hidden; height:720px;
            background: linear-gradient(155deg,#141c2c 0%,#0e1420 50%,#0a0e16 100%);
            border:1px solid rgba(120,150,190,.18);
            box-shadow:0 30px 80px rgba(0,0,0,.5); }}
  #map {{ width:100%; height:100%; }}
  .orbs {{ display:flex; flex-direction:column; gap:10px; }}
  .orb {{ padding:14px 16px; border-radius:18px; background:rgba(12,18,28,.78);
          border:1px solid rgba(255,255,255,.10); backdrop-filter:blur(16px);
          box-shadow:0 12px 30px rgba(0,0,0,.4); }}
  .orb .head {{ display:flex; align-items:center; gap:10px; font-size:11px; letter-spacing:.1em;
                text-transform:uppercase; color:#aebccd; font-weight:700; }}
  .orb .dot {{ width:11px; height:11px; border-radius:50%; display:inline-block;
               box-shadow:0 0 12px currentColor; }}
  .orb .n {{ font-size:32px; font-weight:700; margin-top:4px; font-variant-numeric:tabular-nums; }}
  .orb .hint {{ font-size:10px; color:#7d8da3; margin-top:2px; }}
  .blurb {{ font-size:12px; color:var(--muted); line-height:1.45; padding:12px 14px;
            border-radius:14px; background:rgba(12,18,28,.6);
            border:1px solid rgba(255,255,255,.06); margin-top:8px; }}
  .foot {{ margin-top:14px; font-size:12px; color:#7d8da3; }}
</style>

<div class="wrap">
  <p class="kicker">Point 3 · fuel regimes · night constellation</p>
  <h1 class="file">P3_01_map_dominant_fuel_2021.html</h1>
  <p class="sub">Third geography: neither tonnes nor intensity. Country fill = <b>dominant fuel</b>
  (Coal / Oil / Gas). Glowing dots on regime leaders. Look at the colour zones.</p>
  <div class="grid">
    <div class="stage"><div id="map"></div></div>
    <div class="orbs" id="orbs"></div>
  </div>
  <p class="blurb">Dominant = max(coal, oil, gas share) · glow on same-regime top emitters · drag to pan</p>
  <p class="foot">Offline (no CDN). Grey = no reliable fuel split.</p>
</div>

{echarts_js}
<script>
const WORLD = {world_js};
echarts.registerMap('world', WORLD);
const mapData = {map_data_js};
const glows = {glows_js};
const counts = {counts_js};
const fuelHex = {fuel_hex_js};

const dom = document.getElementById('map');
const chart = echarts.init(dom, null, {{ renderer: 'canvas' }});
const option = {{
  backgroundColor: 'transparent',
  tooltip: {{
    trigger: 'item',
    backgroundColor: 'rgba(20,28,40,0.95)', borderColor: 'rgba(255,255,255,.1)',
    textStyle: {{ color: '#e8eef6' }},
    formatter: function(p) {{
      if (p.seriesType === 'map') {{
        const v = p.data;
        if (!v) return p.name;
        return `<b>${{v.country}}</b><br>dominant fuel: <b>${{v.fuel || 'n/a'}}</b>`;
      }}
      return p.name;
    }}
  }},
  visualMap: {{
    type: 'piecewise',
    show: false,
    pieces: [
      {{ value: 0, label: 'Coal', color: fuelHex.Coal }},
      {{ value: 1, label: 'Oil',  color: fuelHex.Oil }},
      {{ value: 2, label: 'Gas',  color: fuelHex.Gas }},
      {{ value: 3, label: 'None', color: '#3a4150' }},
    ],
    seriesIndex: 0,
  }},
  geo: {{
    map: 'world', roam: true, zoom: 1.2,
    itemStyle: {{ areaColor: '#1a2230', borderColor: '#0a0e16', borderWidth: 0.5 }},
    emphasis: {{ itemStyle: {{ areaColor: '#2a3548' }}, label: {{ show: false }} }},
  }},
  series: [
    {{ name: 'Dominant fuel', type: 'map', geoIndex: 0, data: mapData,
       label: {{ show: false }},
       emphasis: {{ label: {{ show: false }} }} }},
    {{ name: 'Glow', type: 'effectScatter', coordinateSystem: 'geo', data: glows,
       showEffectOn: 'render', rippleEffect: {{ period: 3, scale: 3.2, brushType: 'stroke' }},
       symbolSize: 9, zlevel: 3,
       label: {{ show: false }} }},
  ],
}};
chart.setOption(option);

const orbs = document.getElementById('orbs');
['Coal','Oil','Gas'].forEach(f => {{
  const n = counts[f] || 0;
  const col = fuelHex[f];
  const div = document.createElement('div');
  div.className = 'orb';
  div.innerHTML = `
    <div class="head"><span class="dot" style="background:${{col}};color:${{col}}"></span>${{f}}</div>
    <div class="n" style="color:${{col}}">${{n}}</div>
    <div class="hint">countries · dominant</div>`;
  orbs.appendChild(div);
}});

window.addEventListener('resize', () => chart.resize());
</script>
"""
    write_html(config.FIGS_P3 / "P3_01_map_dominant_fuel_2021.html", _html_doc("P3 fuel map", body))


def _mix(c0: str, c1: str, u: float) -> str:
    def rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    r0, g0, b0 = rgb(c0)
    r1, g1, b1 = rgb(c1)
    return f"#{int(r0+(r1-r0)*u):02x}{int(g0+(g1-g0)*u):02x}{int(b0+(b1-b0)*u):02x}"


def main() -> None:
    print("Building HTML maps (ECharts 2D, fully offline)…", flush=True)
    y = slice_year(load_panel())
    print("  P1 totals + intensity contrast…", flush=True)
    build_total_map(y)
    print("  P3 fuel atlas…", flush=True)
    build_fuel_map(y)
    print(f"HTML maps → {config.FIGS_P1} · {config.FIGS_P3}", flush=True)


if __name__ == "__main__":
    main()
