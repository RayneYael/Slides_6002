# -*- coding: utf-8 -*-
"""
P3_01 — 2D world map with country fill = dominant fuel,
plus small pie-chart overlays on the top emitter countries
showing their actual (coal, oil, gas) split.

This is a real-data pie chart for each labelled country, drawn
from `coal_share / oil_share / gas_share` in the panel data.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import pandas as pd
from matplotlib.patches import Polygon, Wedge, Rectangle, Circle
import geopandas as gpd

# Project layout: this file lives in code/scripts/; config.py owns all
# current data and generated-figure paths.
EDA = Path(__file__).resolve().parent.parent
ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(EDA))

import config
from utils.data import fuel_ok, load_panel, slice_year

NE_CACHE = EDA / "aux" / "ne_110m_admin0.geojson"
NE_URL = "https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip"

# CJK font (use DejaVu Sans for full Unicode coverage, including CO₂ subscript)
mpl.rcParams["font.sans-serif"] = ["DejaVu Sans"]
mpl.rcParams["axes.unicode_minus"] = False

# 3 fuel colors
COAL_C = "#5d4e37"
OIL_C = "#c4471a"
GAS_C = "#2b7a9b"
FUEL_COLORS = {"Coal": COAL_C, "Oil": OIL_C, "Gas": GAS_C}


def _ensure_basemap() -> gpd.GeoDataFrame:
    if not NE_CACHE.exists():
        w = gpd.read_file(NE_URL)
        w = w[["ADM0_A3", "ADMIN", "geometry"]].rename(
            columns={"ADM0_A3": "iso", "ADMIN": "name"})
        w["geometry"] = w.geometry.simplify(0.25, preserve_topology=True)
        NE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        w.to_file(NE_CACHE, driver="GeoJSON")
    return gpd.read_file(NE_CACHE)


def render_p3_map(out_path: Path, year: int = 2021, *, compact: bool = False) -> None:
    y = slice_year(load_panel(), year=year)
    d = fuel_ok(y).dropna(subset=["dominant_fuel", "coal_share",
                                  "oil_share", "gas_share"]).copy()
    w = _ensure_basemap()

    iso_to_fuel = dict(zip(d["iso_code"], d["dominant_fuel"]))
    iso_to_country = dict(zip(y["iso_code"], y["country"]))
    iso_to_pc = dict(zip(y["iso_code"], y["co2_per_capita"]))

    # Hand-tuned centroid offsets (degrees) so labels for adjacent emitters
    # (notably KOR / JPN, SAU / ARE, RUS / CHN / KOR) don't overlap.  The
    # map only has so much room; pushing a label off the dense cluster
    # keeps the chart readable.
    CUSTOM_OFFSET = {
        "RUS": (60.0, 64.0),    # Russia — pull far north
        "CHN": (110.0, 38.0),   # China — push east into ocean
        "IND": (78.0, 18.0),    # India — pull south
        "JPN": (152.0, 47.0),   # Japan — push way up-right
        "KOR": (130.0, 30.0),   # S. Korea — south of Japan
        "SAU": (45.0, 22.0),    # S. Arabia
        "IRN": (50.0, 32.0),    # Iran
        "USA": (-100.0, 38.0),  # USA
        "DEU": (10.0, 51.0),    # Germany
        "GBR": (-2.0, 53.5),    # UK
        "FRA": (2.0, 47.0),     # France
        "IDN": (118.0, -5.0),   # Indonesia — push right
        "BRA": (-55.0, -10.0),  # Brazil — pull up
        "AUS": (135.0, -28.0),  # Australia — pull up off the country
        "CAN": (-95.0, 60.0),   # Canada — pull up
    }

    # Lighter background colour — much easier on the eye than near-black.
    BG_MAP = "#EDF6F1" if compact else "#f7f8fa"
    BG_FIG = "#EDF6F1" if compact else "#eef0f3"
    BG_PANEL = "#F7FBF8" if compact else "#ffffff"
    INK_DARK = "#1f2a3a"
    INK_MED = "#4b576a"
    INK_LIGHT = "#8b95a7"
    BORDER = "#d0d6df"

    # Wider map (was 0.80), narrower legend (was 0.18).  Map gets the
    # extra space the user asked for.
    fig_size = (16.0, 6.8) if compact else (15.5, 9.0)
    fig = plt.figure(figsize=fig_size, dpi=140, facecolor=BG_FIG)
    ax = fig.add_axes([0.003, 0.012 if compact else 0.025,
                       0.925 if compact else 0.930,
                       0.976 if compact else 0.95], facecolor=BG_MAP)
    ax_leg = fig.add_axes([0.935 if compact else 0.940,
                           0.012 if compact else 0.025,
                           0.060 if compact else 0.055,
                           0.976 if compact else 0.95], facecolor=BG_PANEL)
    ax.set_xlim(-180, 180)
    ax.set_ylim((-70, 83) if compact else (-62, 80))
    ax.set_aspect("equal")
    ax.set_axis_off()

    # ----- Choropleth (country fill = dominant fuel) -----
    for _, r in w.iterrows():
        iso = r["iso"]
        fuel = iso_to_fuel.get(iso)
        if fuel is None or pd.isna(fuel):
            col = "#e3e7ed"
        else:
            col = FUEL_COLORS.get(str(fuel), "#e3e7ed")
        for geom in (r["geometry"].geoms if r["geometry"].geom_type == "MultiPolygon"
                     else [r["geometry"]]):
            if geom.geom_type == "Polygon":
                xs, ys = geom.exterior.xy
                ax.fill(xs, ys, facecolor=col, edgecolor="#ffffff",
                        linewidth=0.30, zorder=1)
                for interior in geom.interiors:
                    xs, ys = interior.coords.xy
                    ax.fill(xs, ys, facecolor=BG_MAP,
                            edgecolor="none", zorder=1.5)

    # ----- Small pie charts on top emitter countries -----
    # Take the top 12 by tonnage, then force-add Australia (the user
    # called it out — it's a major emitter and shouldn't be missing).
    top12 = d.nlargest(12, "co2").reset_index(drop=True)
    extra_isos = [iso for iso in ("AUS",) if iso not in top12["iso_code"].values
                  and iso in d["iso_code"].values]
    if extra_isos:
        extras = d[d["iso_code"].isin(extra_isos)]
        top12 = pd.concat([top12, extras], ignore_index=True)
    pies_to_draw = top12.reset_index(drop=True)

    SHORT_NAME = {
        "United States": "U.S.A.",
        "Saudi Arabia": "S. Arabia",
        "United Arab Emirates": "UAE",
        "South Korea": "S. Korea",
        "United Kingdom": "U.K.",
    }

    for _, r in pies_to_draw.iterrows():
        iso = r["iso_code"]
        try:
            row = w[w["iso"] == iso].iloc[0]
            c = row.geometry.representative_point()
            lng0, lat0 = float(c.x), float(c.y)
        except Exception:
            continue
        # Apply hand-tuned offset
        if iso in CUSTOM_OFFSET:
            lng0, lat0 = CUSTOM_OFFSET[iso]
        coal = float(r["coal_share"])
        oil = float(r["oil_share"])
        gas = float(r["gas_share"])
        s = coal + oil + gas
        if s <= 0:
            continue
        coal /= s; oil /= s; gas /= s

        r_geo = 4.0 + 2.6 * (np.log10(r["co2"]) - 2) / 2
        ax.add_patch(Circle((lng0, lat0), r_geo + 0.4,
                            facecolor="white", edgecolor="#b8bfca",
                            linewidth=0.6, zorder=4))
        start = 90.0
        for share, color in [(coal, COAL_C), (oil, OIL_C), (gas, GAS_C)]:
            if share <= 0: continue
            end = start - 360 * share
            ax.add_patch(Wedge((lng0, lat0), r_geo, end, start,
                               facecolor=color, edgecolor="white",
                               linewidth=0.8, zorder=5))
            start = end
        # Country label — short, with light bbox.  Some labels need to
        # sit ABOVE the pie (e.g. China, Russia) so they don't crash into
        # adjacent country labels below.
        country_name = SHORT_NAME.get(r["country"], r["country"])
        label_above = iso in ("RUS", "CHN", "USA", "DEU", "GBR", "FRA",
                              "CAN", "AUS", "IRN", "JPN")
        if label_above:
            ax.text(lng0, lat0 + r_geo + 1.6, country_name,
                    ha="center", va="bottom", fontsize=8.8, color=INK_DARK,
                    fontweight="bold", zorder=6,
                    bbox=dict(facecolor="white", alpha=0.88,
                              edgecolor="#cfd5e0", linewidth=0.5, pad=1.5))
        else:
            ax.text(lng0, lat0 - r_geo - 1.6, country_name,
                    ha="center", va="top", fontsize=8.8, color=INK_DARK,
                    fontweight="bold", zorder=6,
                    bbox=dict(facecolor="white", alpha=0.88,
                              edgecolor="#cfd5e0", linewidth=0.5, pad=1.5))

    # ----- Right legend panel (compact) -----
    ax_leg.set_xticks([]); ax_leg.set_yticks([])
    for sp in ax_leg.spines.values():
        sp.set_visible(False)

    # Fuel swatches
    ax_leg.text(0.10, 0.94, "Fuel", fontsize=10.5, color=INK_DARK,
                fontweight="bold", transform=ax_leg.transAxes)
    for i, (label, col) in enumerate([("Coal", COAL_C),
                                       ("Oil", OIL_C),
                                       ("Gas", GAS_C)]):
        y = 0.84 - i * 0.10
        ax_leg.add_patch(Rectangle((0.10, y - 0.026), 0.13, 0.052,
                                   facecolor=col, edgecolor="none",
                                   transform=ax_leg.transAxes))
        ax_leg.text(0.31, y, label, fontsize=9.5, color=INK_DARK,
                    fontweight="bold", va="center", transform=ax_leg.transAxes)

    # Keep only the single useful denominator; the former counts and demo
    # panel repeated information and made the map unnecessarily small.
    counts = d["dominant_fuel"].value_counts()
    ax_leg.text(0.10, 0.48, "Pie", fontsize=10.5, color=INK_DARK,
                fontweight="bold", transform=ax_leg.transAxes)
    ax_leg.text(0.10, 0.43, "actual mix", fontsize=8.5,
                color=INK_LIGHT, transform=ax_leg.transAxes)
    sample = d[d["country"] == "China"].iloc[0]
    ax_pie_demo = fig.add_axes([0.947, 0.315, 0.036, 0.060],
                                facecolor=BG_PANEL, zorder=2)
    start = 90.0
    for share, col in [(float(sample["coal_share"]), COAL_C),
                       (float(sample["oil_share"]), OIL_C),
                       (float(sample["gas_share"]), GAS_C)]:
        if share <= 0: continue
        end = start - 360 * share
        ax_pie_demo.add_patch(Wedge((0, 0), 1.0, end, start,
                                     facecolor=col, edgecolor="white",
                                     linewidth=1.2, zorder=3))
        start = end
    ax_pie_demo.set_xlim(-1.15, 1.15)
    ax_pie_demo.set_ylim(-1.15, 1.15)
    ax_pie_demo.set_aspect("equal")
    ax_pie_demo.set_xticks([]); ax_pie_demo.set_yticks([])
    for sp in ax_pie_demo.spines.values():
        sp.set_visible(False)
    ax_leg.text(0.50, 0.20, f"n = {int(counts.sum())}", fontsize=8.5,
                color=INK_MED, fontweight="bold", ha="center",
                transform=ax_leg.transAxes)
    ax_leg.text(0.50, 0.12, "reliable\nfuel profiles", fontsize=7.8,
                color=INK_LIGHT, ha="center", va="center",
                transform=ax_leg.transAxes)

    fig.savefig(out_path, dpi=150 if compact else 140, facecolor=fig.get_facecolor(),
                bbox_inches=None if compact else "tight",
                pad_inches=0 if compact else 0.05)
    plt.close(fig)
    print(f"  saved {out_path.parent.name}/{out_path.name}  "
          f"({out_path.stat().st_size:,} B)")


if __name__ == "__main__":
    out = config.FIGS_P3 / "P3_01_map_dominant_fuel_2021_cobalt.png"
    render_p3_map(out, year=2021)
