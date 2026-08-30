# -*- coding: utf-8 -*-
"""
P1_01 — 2D world map + real 3D vertical bars on top-15 emitters.

The world map is drawn as a 2D choropleth (equirectangular projection, no
rotation).  On top of the top-15 emitter countries we draw 3D vertical
bars with:

  - HEIGHT ∝ per-capita CO2 (t / person)
  - COLOUR ∝ per-capita (green → red)
  - SIDE / TOP faces visible (true 3D, not flat 2D rectangles)

This produces a clean 2D + 3D composite: the world reads as a flat
choropleth (the "scale"), the bars stand up in 3D (the "intensity"),
and the contrast — China red on the ground but a short green bar;
Qatar pale on the ground but a tall red bar — is the story.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, Normalize, to_rgba
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection, PolyCollection
import geopandas as gpd

# Project layout: this file lives in code/scripts/; config.py owns all
# current data and generated-figure paths.
EDA = Path(__file__).resolve().parent.parent
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(EDA))

import config
from utils.data import concentration_stats, load_panel, slice_year

NE_CACHE = EDA / "aux" / "ne_110m_admin0.geojson"
NE_URL = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"

# CJK font (use DejaVu Sans for full Unicode coverage, including CO₂ subscript)
mpl.rcParams["font.sans-serif"] = ["DejaVu Sans"]
mpl.rcParams["axes.unicode_minus"] = False

# Per-capita green→red ramp
PC_CMAP = LinearSegmentedColormap.from_list("pc", [
    (0.00, "#2E7D32"),
    (0.25, "#7CB342"),
    (0.50, "#FDD835"),
    (0.75, "#EF6C00"),
    (1.00, "#B71C1C"),
])

# Log-Mt choropleth (green→dark red)
LOG_CMAP = LinearSegmentedColormap.from_list("log", [
    (0.00, "#E8F1E1"),
    (0.18, "#C8E0A3"),
    (0.36, "#9DCB68"),
    (0.50, "#F4D35E"),
    (0.65, "#EE964B"),
    (0.82, "#D34E29"),
    (1.00, "#5C0F0F"),
])


def _ensure_basemap() -> gpd.GeoDataFrame:
    if not NE_CACHE.exists():
        w = gpd.read_file(NE_URL)
        w = w[["ADM0_A3", "ADMIN", "geometry"]].rename(
            columns={"ADM0_A3": "iso", "ADMIN": "name"})
        w["geometry"] = w.geometry.simplify(0.25, preserve_topology=True)
        NE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        w.to_file(NE_CACHE, driver="GeoJSON")
    return gpd.read_file(NE_CACHE)


def render_p1_3d(out_path: Path, year: int = 2021, *, map_only: bool = False) -> None:
    y = slice_year(load_panel(), year=year)
    st = concentration_stats(y)
    w = _ensure_basemap()

    iso_to_log = dict(zip(y["iso_code"], y["log_co2"]))
    iso_to_pc = dict(zip(y["iso_code"], y["co2_per_capita"]))
    iso_to_co2 = dict(zip(y["iso_code"], y["co2"]))
    iso_to_country = dict(zip(y["iso_code"], y["country"]))

    zmin, zmax = float(y["log_co2"].min()), float(y["log_co2"].max())
    pc_max = float(y["co2_per_capita"].max())

    bg = "#EAF4F8" if map_only else "#eceef1"
    fig_size = (16.0, 6.8) if map_only else (16.0, 9.6)
    fig, ax = plt.subplots(figsize=fig_size, dpi=140, facecolor=bg)
    ax.set_facecolor(bg)
    ax.set_xlim(-180, 180)
    ax.set_ylim((-70, 90) if map_only else (-62, 80))
    ax.set_aspect("equal")
    ax.set_axis_off()
    # Top padding gives the bar top-labels breathing room (so the
    # "Canada / Russia / S. Arabia" tags aren't pinned against the
    # card edge).  Bottom margin trimmed to ~9 % — legend gets smaller.
    if map_only:
        fig.subplots_adjust(left=0.003, right=0.997, top=0.995, bottom=0.005)
    else:
        fig.subplots_adjust(left=0.003, right=0.997, top=0.982, bottom=0.078)

    # ----- Choropleth (2D world) -----
    norm_log = Normalize(vmin=zmin, vmax=zmax)
    for _, r in w.iterrows():
        v = iso_to_log.get(r["iso"])
        if v is None or pd.isna(v):
            col = "#dbe0e6"
        else:
            col = LOG_CMAP(norm_log(v))
        for geom in (r["geometry"].geoms if r["geometry"].geom_type == "MultiPolygon"
                     else [r["geometry"]]):
            if geom.geom_type == "Polygon":
                xs, ys = geom.exterior.xy
                ax.fill(xs, ys, facecolor=col, edgecolor="white",
                        linewidth=0.30, zorder=1)
                for interior in geom.interiors:
                    xs, ys = interior.coords.xy
                    ax.fill(xs, ys, facecolor=bg, edgecolor="none", zorder=1.5)

    # ----- 3D bars (manual isometric projection) -----
    # We project (lng, lat) → (x, y) on screen, then draw the bar in 3D by
    # stacking: top face, right face, front face, left face (visible from
    # the camera angle).  Bar "depth" offset = (cos(θ), -sin(θ)) * depth.
    θ = np.deg2rad(28)         # 28° "camera" tilt from straight-down
    depth = 5.0                # bar depth in screen degrees
    bar_w = 2.6                # bar width in lng-degrees (square cross-section)
    bar_d = 2.6                # bar depth in lat-degrees (square cross-section)

    # x-axis offset for "back" face
    bx_off = depth * np.cos(θ)   # in screen units (degrees)
    by_off = -depth * np.sin(θ)  # negative = upward in screen y

    norm_pc = Normalize(vmin=0, vmax=pc_max if pc_max > 0 else 1)
    # Major emitters plus three story countries.  Iran is intentionally
    # omitted from this presentation map; Qatar establishes the global
    # per-capita extreme, while Australia and Singapore add useful context.
    selected_isos = [
        iso for iso in y.nlargest(12, "co2")["iso_code"] if iso != "IRN"
    ]
    for iso in ("AUS", "QAT", "SGP"):
        if iso not in selected_isos:
            selected_isos.append(iso)
    top = y.set_index("iso_code").loc[selected_isos].reset_index()
    _label_isos = set(selected_isos)
    # Short English names for chart labels
    SHORT = {"United States": "U.S.A.",
             "Saudi Arabia": "S. Arabia",
             "South Korea": "S. Korea"}

    # Local offsets keep each name beside its own bar.  No connector lines.
    LABEL_OFFSET = {
        "USA": (-10, 4), "CAN": (8, 4), "BRA": (-12, 4),
        "RUS": (10, 3), "DEU": (-8, 3),
        "SAU": (-14, -2), "QAT": (10, 0), "IND": (9, -2),
        "CHN": (9, 4), "JPN": (10, 1), "KOR": (9, -4),
        "IDN": (10, -4), "AUS": (10, -3), "SGP": (-18, -5),
    }

    # Natural Earth 1:110m omits some small states.  These fixed country
    # coordinates restore the real Qatar and Singapore bar locations.
    FALLBACK_COORDS = {
        "QAT": (51.18, 25.30),
        "SGP": (103.82, 1.35),
    }

    H_MAX = 45.0  # keeps Qatar, the global maximum, inside the map frame
    label_z = []  # collected label boxes for dedup / overlap fix

    for _, r in top.iterrows():
        iso = r["iso_code"]
        try:
            row = w[w["iso"] == iso].iloc[0]
            c = row.geometry.representative_point()
            lng0, lat0 = float(c.x), float(c.y)
        except Exception:
            if iso not in FALLBACK_COORDS:
                continue
            lng0, lat0 = FALLBACK_COORDS[iso]
        pc = float(r["co2_per_capita"]) if pd.notna(r["co2_per_capita"]) else 0.0
        h = H_MAX * (pc / pc_max) if pc_max > 0 else 1.0
        h = max(h, 1.5)
        col = PC_CMAP(norm_pc(pc))
        col_dark = PC_CMAP(norm_pc(pc))
        # Make the right & back faces slightly darker
        rgba = to_rgba(col)
        rgba_dark = (rgba[0]*0.7, rgba[1]*0.7, rgba[2]*0.7, rgba[3])

        # Base rectangle (front face on the ground)
        x0, x1 = lng0 - bar_w/2, lng0 + bar_w/2
        y0, y1 = lat0 - bar_d/2, lat0 + bar_d/2
        # Top rectangle, offset by depth
        tx0, tx1 = x0 + bx_off, x1 + bx_off
        ty0, ty1 = y0 + by_off, y1 + by_off

        # Front face: (x0..x1, y0..y1) ground to height h
        front = Polygon([(x0, y0), (x1, y0), (x1, y0), (x1, y0+h),
                        (x0, y0+h), (x0, y0+h), (x0, y0)],
                       closed=True)
        # Right face: x1 edge, lifted
        right = Polygon([(x1, y0), (x1+0+ bx_off, y0+by_off),
                         (x1+ bx_off, y0+by_off+h),
                         (x1, y0+h)], closed=True)
        # Back face: full offset
        back = Polygon([(tx0, ty0), (tx1, ty0), (tx1, ty0+h),
                        (tx0, ty0+h)], closed=True)
        # Left face: x0 edge, offset
        # Top face: (tx0..tx1, ty0..ty0+h)
        top_face = Polygon([(tx0, ty0+h), (tx1, ty0+h),
                            (x1, y0+h), (x0, y0+h)], closed=True)
        # Shadow on the ground
        sh_off_x = bx_off * 0.6
        sh_off_y = by_off * 0.6
        shadow = Polygon([(x0, y0), (x1, y0), (x1+sh_off_x, y0+sh_off_y),
                          (x0+sh_off_x, y0+sh_off_y)], closed=True,
                         facecolor="#1a1f26", alpha=0.15, zorder=2)

        ax.add_patch(shadow)
        # Order: back, right, front, top (so top is on top).  No edgecolor
        # — clean flat-shaded faces.
        edge = "none"
        edge_w = 0.0
        ax.add_patch(Polygon([(x0+ bx_off, y0+by_off),
                              (x1+ bx_off, y0+by_off),
                              (x1+ bx_off, y0+by_off+h),
                              (x0+ bx_off, y0+by_off+h)],
                             closed=True, facecolor=rgba_dark,
                             edgecolor=edge, linewidth=edge_w, zorder=3))
        # Right face
        ax.add_patch(Polygon([(x1, y0), (x1+ bx_off, y0+by_off),
                              (x1+ bx_off, y0+by_off+h),
                              (x1, y0+h)], closed=True, facecolor=rgba_dark,
                             edgecolor=edge, linewidth=edge_w, zorder=4))
        # Front face
        ax.add_patch(Polygon([(x0, y0), (x1, y0),
                              (x1, y0+h), (x0, y0+h)],
                             closed=True, facecolor=rgba,
                             edgecolor=edge, linewidth=edge_w, zorder=5))
        # Top face (slightly lighter, the "lit" face)
        ax.add_patch(Polygon([(x0+ bx_off, y0+by_off+h),
                              (x1+ bx_off, y0+by_off+h),
                              (x1, y0+h), (x0, y0+h)],
                             closed=True, facecolor=col,
                             edgecolor=edge, linewidth=edge_w, zorder=6))

        # Label: country + per-capita
        if iso in _label_isos:
            short = r["country"]
            for trunc in (" of Great Britain and Northern Ireland",
                          " (Plurinational State of)"):
                short = short.replace(trunc, "")
            short = SHORT.get(short, short)
            # One-line label (avoids bbox-split glitches in dense clusters)
            label = short
            # Place label well above the bar.  For the EAST-ASIA cluster
            # (Japan, S. Korea, China) we use extra vertical padding so
            # the labels clear the neighbouring bars — the figure has
            # many labels in a small area here.
            east_asia = iso in ("JPN", "KOR", "CHN", "IND", "RUS")
            pad = 5.0 if east_asia else 3.0
            label_z.append((iso, lng0, y0 + h - by_off + pad, label))

    # Sort labels: lowest first so high ones draw on top (avoid label
    # stacking), then place.  Simple approach: jitter overlapping labels
    # by their x to spread them out.
    for iso, lx, ly, lbl in label_z:
        dx, dy = LABEL_OFFSET.get(iso, (7, 2))
        ax.text(
            lx + dx, ly + dy, lbl,
            fontsize=9.2, fontweight="bold", ha="center", va="center",
            color="#0d1117", zorder=20,
            bbox=dict(facecolor="white", alpha=0.97,
                      edgecolor="#9aa4b3", linewidth=0.7, pad=1.6),
        )

    if map_only:
        fig.savefig(out_path, dpi=150, facecolor=fig.get_facecolor(),
                    bbox_inches=None, pad_inches=0)
        plt.close(fig)
        print(f"  saved {out_path.parent.name}/{out_path.name}  "
              f"({out_path.stat().st_size:,} B)")
        return

    # ----- Compact legend BELOW the map (figure coordinates, horizontal) -----
    # Two color bars side by side, just under the map so the data area is
    # not blocked.  Tighter, professional legend.
    fig = ax.figure
    from matplotlib.patches import FancyBboxPatch

    # Background panel for the legend (fully opaque so the text is always
    # readable regardless of the map content behind it).  Tighter than
    # before — the user asked for more space for the map.
    LEG_H = 0.054
    LEG_Y = 0.010
    BAR_H = 0.012
    LEG_TXT_Y = LEG_Y + LEG_H * 0.78   # title text vertical position
    LEG_LBL_Y = LEG_Y + LEG_H * 0.22   # tick label vertical position
    leg_bg = FancyBboxPatch((0.030, LEG_Y), 0.940, LEG_H,
                             boxstyle="round,pad=0.004,rounding_size=0.004",
                             transform=fig.transFigure,
                             facecolor="white", edgecolor="#9aa4b3",
                             linewidth=0.8, alpha=1.0, zorder=8)
    fig.patches.append(leg_bg)

    # Bar 1 — per-capita
    fig.text(0.050, LEG_TXT_Y, "Bar  =  per-capita (t / person)",
             fontsize=11.0, color="#0d1117", fontweight="bold", zorder=10)
    bar1_w = 0.220
    cax1 = fig.add_axes([0.275, LEG_TXT_Y - BAR_H - 0.004, bar1_w, BAR_H], zorder=10)
    grad = np.linspace(0, 1, 256).reshape(1, -1)
    cax1.imshow(grad, aspect="auto", cmap=PC_CMAP)
    cax1.set_xticks([]); cax1.set_yticks([])
    for s in cax1.spines.values(): s.set_visible(False)
    for frac, lbl in [(0.0, "0"), (0.50, "10"), (1.00, f"{pc_max:.0f}+")]:
        fig.text(0.275 + bar1_w * frac, LEG_LBL_Y, lbl,
                 fontsize=9.0, color="#0d1117", ha="center", zorder=10)

    # Bar 2 — log CO₂ (Mt) — explicit "(CO₂)" using a unicode \u2082 subscript
    fig.text(0.560, LEG_TXT_Y, "Land  =  log CO\u2082 (Mt)",
             fontsize=11.0, color="#0d1117", fontweight="bold", zorder=10)
    bar2_w = 0.220
    cax2 = fig.add_axes([0.715, LEG_TXT_Y - BAR_H - 0.004, bar2_w, BAR_H], zorder=10)
    cax2.imshow(grad, aspect="auto", cmap=LOG_CMAP)
    cax2.set_xticks([]); cax2.set_yticks([])
    for s in cax2.spines.values(): s.set_visible(False)
    for frac, lbl in [(0.0, f"{zmin:.1f}"),
                       (1.00, f"{zmax:.1f}")]:
        fig.text(0.715 + bar2_w * frac, LEG_LBL_Y, lbl,
                 fontsize=9.0, color="#0d1117", ha="center", zorder=10)

    fig.savefig(out_path, dpi=140, facecolor=fig.get_facecolor(),
                bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)
    print(f"  saved {out_path.parent.name}/{out_path.name}  "
          f"({out_path.stat().st_size:,} B)")


if __name__ == "__main__":
    out = config.FIGS_P1 / "P1_01_map_bars_total_co2_2021_cobalt.png"
    render_p1_3d(out, year=2021)
