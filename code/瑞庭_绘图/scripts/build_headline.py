# -*- coding: utf-8 -*-
"""
Headline summary figure — 1×3 mini-maps of the THREE geographies.

  panel 1 : log10 CO₂ (Mt)  — green→red sequential
  panel 2 : log10 per-capita — green→red sequential
  panel 3 : dominant fuel   — Coal / Oil / Gas categorical

Fully self-contained: only lib/echarts.min.js + lib/world.geojson, no CDN.
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
from utils.data import fuel_ok, load_panel, slice_year

NE_CACHE = EDA / "aux" / "ne_110m_admin0.geojson"
LIBS = config.WEB_LIBS
WORLD_GEOJSON = LIBS / "world.geojson"
ECHARTS_JS = LIBS / "echarts.min.js"

OUT_DIR = config.FIGURE_HTML_SOURCES / "headline"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Bootstrap missing assets on first run.
if not ECHARTS_JS.exists() or ECHARTS_JS.stat().st_size < 500_000 \
   or not WORLD_GEOJSON.exists() or WORLD_GEOJSON.stat().st_size < 100_000:
    from _bootstrap_libs import ensure_echarts, ensure_world_geojson
    ensure_echarts()
    ensure_world_geojson()


def _ensure_basemap() -> gpd.GeoDataFrame:
    if not NE_CACHE.exists():
        raise FileNotFoundError(NE_CACHE)
    return gpd.read_file(NE_CACHE)


def _load_echarts_inline() -> str:
    return f"<script>\n{ECHARTS_JS.read_text(encoding='utf-8', errors='ignore')}\n</script>"


def _load_world_inline() -> str:
    return json.dumps(json.loads(WORLD_GEOJSON.read_text(encoding="utf-8")), ensure_ascii=False)


COLOR_SEQ = [
    [0.00, "#E8F1E1"], [0.15, "#C8E0A3"], [0.30, "#9DCB68"],
    [0.45, "#F4D35E"], [0.60, "#EE964B"], [0.75, "#D34E29"],
    [0.90, "#A8261C"], [1.00, "#5C0F0F"],
]


def _build_html(y: pd.DataFrame) -> str:
    co2_z = y["log_co2"].dropna()
    pc_z = y["co2_per_capita"].dropna()
    pc_z = np.log10(pc_z.clip(lower=0.01))

    def map_data_for(value_col, value_range, scale_kind="continuous"):
        rows = []
        for _, r in y.iterrows():
            v = r.get(value_col)
            if pd.isna(v):
                continue
            if scale_kind == "log_pc":
                v2 = float(np.log10(max(0.01, float(v))))
            elif scale_kind == "categorical":
                v2 = str(v)
            else:
                v2 = float(v)
            rows.append({"name": r["iso_code"], "value": v2,
                         "country": r["country"],
                         "fuel": r.get("dominant_fuel")})
        return rows

    map_tonnes = map_data_for("log_co2", (0, 4.2), "continuous")
    map_pc = map_data_for("co2_per_capita", None, "log_pc")
    map_fuel = map_data_for("dominant_fuel", None, "categorical")

    FUEL_IDX = {"Coal": 0, "Oil": 1, "Gas": 2}
    for d in map_fuel:
        f = d.get("fuel")
        d["value"] = FUEL_IDX.get(f, 3) if pd.notna(f) else 3

    map_tonnes_js = json.dumps(map_tonnes, ensure_ascii=False)
    map_pc_js = json.dumps(map_pc, ensure_ascii=False)
    map_fuel_js = json.dumps(map_fuel, ensure_ascii=False)
    world_js = _load_world_inline()
    echarts_js = _load_echarts_inline()

    co2_st = (float(np.percentile(co2_z, 5)), float(co2_z.max()))
    pc_st = (float(np.percentile(pc_z, 5)), float(pc_z.max()))

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Three geographies of 2021 emissions</title>
<style>
  :root {{ --ink:#121820; --muted:#5c6b7a; --page:#eceef1; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; font-family:"Segoe UI","Helvetica Neue",Arial,sans-serif;
         color:var(--ink); background:var(--page); }}
  .wrap {{ max-width:1500px; margin:0 auto; padding:14px 18px 20px; }}
  h1 {{ margin:0 0 4px; font-size:18px; font-weight:700; color:#243040; }}
  .sub {{ margin:0 0 12px; font-size:12px; color:var(--muted); }}
  .grid {{ display:grid; grid-template-columns: 1fr 1fr 1fr; gap:10px; }}
  .panel {{ position:relative; border-radius:14px; overflow:hidden;
            background:linear-gradient(168deg,#eef1f4 0%,#f4f6f8 50%,#f8f9fb 100%);
            border:1px solid rgba(255,255,255,.85); height:430px; }}
  .panel .label {{ position:absolute; top:8px; left:12px; z-index:5;
                   font-size:13px; font-weight:700; color:#243040;
                   background:rgba(255,255,255,.85); padding:4px 9px;
                   border-radius:10px; backdrop-filter:blur(8px);
                   border:1px solid rgba(255,255,255,.95); }}
  .panel .sub2 {{ position:absolute; top:40px; left:12px; z-index:5;
                  font-size:10.5px; color:var(--muted); max-width:80%;
                  line-height:1.35; background:rgba(255,255,255,.78);
                  padding:5px 8px; border-radius:8px;
                  backdrop-filter:blur(6px); }}
  .chart {{ width:100%; height:100%; }}
  .foot {{ margin-top:10px; font-size:11px; color:var(--muted); text-align:center; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Three geographies of 2021 emissions — same world, three readings</h1>
  <p class="sub">From the same Final_data panel (213 countries · 2021). Same colour scale on 1 and 2, categorical on 3.</p>
  <div class="grid">
    <div class="panel">
      <div class="label">①  Total CO₂ (log₁₀ Mt)</div>
      <div class="sub2">Who emits the most tonnes? China/USA/India dominate; Asia = 60% of world.</div>
      <div id="m1" class="chart"></div>
    </div>
    <div class="panel">
      <div class="label">②  Per capita (log₁₀ t/person)</div>
      <div class="sub2">Who is hottest per person? Gulf states spike; CHN/IND are surprisingly cool.</div>
      <div id="m2" class="chart"></div>
    </div>
    <div class="panel">
      <div class="label">③  Dominant fuel</div>
      <div class="sub2">A third geography — Asia leans coal, Americas oil, Europe gas.</div>
      <div id="m3" class="chart"></div>
    </div>
  </div>
  <p class="foot">Drag any map to pan · scroll to zoom · offline (no CDN).</p>
</div>
{echarts_js}
<script>
const WORLD = {world_js};
echarts.registerMap('world', WORLD);
const map1 = {map_tonnes_js};
const map2 = {map_pc_js};
const map3 = {map_fuel_js};

function build(id, data, vm) {{
  const dom = document.getElementById(id);
  const c = echarts.init(dom, null, {{renderer:'canvas'}});
  c.setOption({{
    visualMap: vm,
    tooltip: {{ trigger:'item', backgroundColor:'rgba(255,255,255,0.96)',
                borderColor:'#cdd5e0', textStyle:{{color:'#243040'}},
                formatter: p => {{
                  const v = p.data;
                  if (!v) return p.name;
                  return `<b>${{v.country}}</b>`;
                }} }},
    geo: {{ map:'world', roam:true, zoom:1.15,
            itemStyle:{{areaColor:'#f0f3f7', borderColor:'#aab4c2', borderWidth:0.6}},
            emphasis:{{itemStyle:{{areaColor:'#dbe4ee'}}, label:{{show:false}}}} }},
    series: [{{ name: id, type:'map', geoIndex:0, data:data,
                label:{{show:false}}, emphasis:{{label:{{show:false}}}} }}],
  }});
  return c;
}}

const c1 = build('m1', map1, {{
  type:'continuous', min:{co2_st[0]}, max:{co2_st[1]}, show:false, seriesIndex:0,
  inRange:{{ color:['#E8F1E1','#C8E0A3','#9DCB68','#F4D35E','#EE964B','#D34E29','#A8261C','#5C0F0F'] }}
}});
const c2 = build('m2', map2, {{
  type:'continuous', min:{pc_st[0]}, max:{pc_st[1]}, show:false, seriesIndex:0,
  inRange:{{ color:['#E8F1E1','#C8E0A3','#9DCB68','#F4D35E','#EE964B','#D34E29','#A8261C','#5C0F0F'] }}
}});
const c3 = build('m3', map3, {{
  type:'piecewise', show:false, seriesIndex:0,
  pieces:[
    {{value:0, label:'Coal', color:'#5D4E37'}},
    {{value:1, label:'Oil',  color:'#C4471A'}},
    {{value:2, label:'Gas',  color:'#2B7A9B'}},
    {{value:3, label:'None', color:'#3a4150'}},
  ]
}});

window.addEventListener('resize', () => {{ c1.resize(); c2.resize(); c3.resize(); }});
</script>
</body>
</html>
"""


def main() -> None:
    print("Loading panel…", flush=True)
    y = slice_year(load_panel())
    print("  2021 rows:", len(y), flush=True)

    html = _build_html(y)
    out_html = OUT_DIR / "H0_01_three_geographies.html"
    out_html.write_text(html, encoding="utf-8")
    print(f"  saved {out_html.relative_to(EDA.parent)}  ({len(html):,} bytes)", flush=True)


if __name__ == "__main__":
    main()
