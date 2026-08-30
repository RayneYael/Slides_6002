# -*- coding: utf-8 -*-
"""Bootstrap the local ECharts + world.geojson assets used by the HTML map builders.

The code/aux/web_libs folder is treated as a *build-time cache*.  After this runs, the
`build_maps_html.py` and `build_headline.py` scripts can find their inputs.
"""
from __future__ import annotations

import json
import ssl
import urllib.request
from pathlib import Path

EDA = Path(__file__).resolve().parents[1]
LIBS = (EDA / "aux" / "web_libs").resolve()
LIBS.mkdir(parents=True, exist_ok=True)

ECHARTS_URL = "https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"
ECHARTS_GL_URL = "https://cdn.jsdelivr.net/npm/echarts-gl@2.0.9/dist/echarts-gl.min.js"
WORLD_SRC = EDA / "aux" / "ne_110m_admin0.geojson"
WORLD_DST = LIBS / "world.geojson"


def _http_get(url: str) -> bytes:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60, context=ctx) as r:
        return r.read()


def ensure_echarts() -> Path:
    out = LIBS / "echarts.min.js"
    if out.exists() and out.stat().st_size > 500_000:
        return out
    print(f"  downloading ECharts 5.4.3 → {out}")
    out.write_bytes(_http_get(ECHARTS_URL))
    return out


def ensure_echarts_gl() -> Path:
    out = LIBS / "echarts-gl.min.js"
    if out.exists() and out.stat().st_size > 300_000:
        return out
    print(f"  downloading echarts-gl 2.0.9 → {out}")
    out.write_bytes(_http_get(ECHARTS_GL_URL))
    return out


def ensure_world_geojson() -> Path:
    if WORLD_DST.exists() and WORLD_DST.stat().st_size > 100_000:
        return WORLD_DST
    if not WORLD_SRC.exists():
        raise FileNotFoundError(f"missing source: {WORLD_SRC}")
    print(f"  copying world GeoJSON → {WORLD_DST}")
    gj = json.loads(WORLD_SRC.read_text(encoding="utf-8"))
    # ECharts maps work when each feature's `properties.name` is the matching
    # key for `data[i].name`.  We override the Natural Earth `name` with the
    # ISO-3 code so data lookup is unambiguous.
    for f in gj.get("features", []):
        props = f.setdefault("properties", {})
        props["iso"] = props.get("iso", props.get("ADM0_A3", ""))
        props["name"] = props.get("iso", props.get("name", ""))
    WORLD_DST.write_text(json.dumps(gj, ensure_ascii=False), encoding="utf-8")
    return WORLD_DST


def main() -> None:
    ensure_echarts()
    ensure_echarts_gl()
    ensure_world_geojson()
    print("  build assets ready in:", LIBS)


if __name__ == "__main__":
    main()
