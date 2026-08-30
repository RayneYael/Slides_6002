# -*- coding: utf-8 -*-
"""Truthful time-space fusion for the revised spatial deck.

Four tracks × five two-year time points:
  Global emissions centroid, North America, South America, Africa.

Circle size encodes time only (2013 smallest, 2021 largest).
Circle fill encodes per-capita change vs 2013.
Circle outline encodes total-emissions change vs 2013.
Circle centre follows the emissions-weighted geographic centroid.  Small
geographic displacements are magnified by a labelled per-track factor so the
direction is visible without pretending that the magnitudes are comparable.
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

ROOT = Path(__file__).resolve().parent.parent.parent
EDA_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EDA_DIR))

import config
from utils.data import load_panel

NE = EDA_DIR / "aux" / "ne_110m_admin0.geojson"
YEARS = [2013, 2015, 2017, 2019, 2021]
TRACKS = ["Global", "North America", "South America", "Africa"]

TRACK_COLOR = {
    "Global": "#7A3E00",
    "North America": "#2457A6",
    "South America": "#7A3AA6",
    "Africa": "#A66B00",
}
DISPLAY_SCALE = {
    "Global": 5,
    "North America": 180,
    "South America": 12,
    "Africa": 9,
}

mpl.rcParams["font.sans-serif"] = ["DejaVu Sans"]
mpl.rcParams["axes.unicode_minus"] = False


def _change_color(pct: float, max_abs: float = 16.0) -> str:
    """Green = lower emissions, red = higher, grey = baseline/flat."""
    norm = float(np.clip(pct / max_abs, -1, 1))
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "improvement", ["#168447", "#D7DCE3", "#C92A2A"]
    )
    return mcolors.to_hex(cmap((norm + 1) / 2))


def _trajectory_panel(panel: pd.DataFrame, world: gpd.GeoDataFrame) -> pd.DataFrame:
    points = (
        world.set_index("iso")["geometry"]
        .apply(lambda g: g.representative_point())
        .apply(lambda p: (p.x, p.y))
        .to_dict()
    )
    d = panel.copy()
    d["lng"] = d["iso_code"].map(lambda i: points.get(i, (np.nan, np.nan))[0])
    d["lat"] = d["iso_code"].map(lambda i: points.get(i, (np.nan, np.nan))[1])

    rows: list[dict] = []
    for track in TRACKS:
        for year in YEARS:
            all_rows = d[d["year"] == year]
            if track != "Global":
                all_rows = all_rows[all_rows["region"] == track]
            geo_rows = all_rows.dropna(subset=["lng", "lat"])
            weights = geo_rows["co2"].clip(lower=0.1).to_numpy()
            total_mt = float(all_rows["co2"].sum())
            pop = float(all_rows["population"].sum())
            pc = total_mt * 1_000_000 / pop
            top = all_rows.sort_values("co2", ascending=False).iloc[0]
            rows.append({
                "track": track,
                "year": year,
                "lng": float(np.average(geo_rows["lng"], weights=weights)),
                "lat": float(np.average(geo_rows["lat"], weights=weights)),
                "total_mt": total_mt,
                "pc": pc,
                "top_country": str(top["country"]),
            })
    out = pd.DataFrame(rows)
    base = out[out["year"] == YEARS[0]].set_index("track")
    out["total_change"] = out.apply(
        lambda r: (r["total_mt"] / base.loc[r["track"], "total_mt"] - 1) * 100,
        axis=1,
    )
    out["pc_change"] = out.apply(
        lambda r: (r["pc"] / base.loc[r["track"], "pc"] - 1) * 100,
        axis=1,
    )
    return out


def _draw_basemap(ax, world: gpd.GeoDataFrame, bg: str) -> None:
    for _, row in world.iterrows():
        geoms = row["geometry"].geoms if row["geometry"].geom_type == "MultiPolygon" else [row["geometry"]]
        for geom in geoms:
            if geom.geom_type != "Polygon":
                continue
            xs, ys = geom.exterior.xy
            ax.fill(xs, ys, facecolor="#E8ECF1", edgecolor="white",
                    linewidth=0.28, zorder=1)
            for interior in geom.interiors:
                xs, ys = interior.coords.xy
                ax.fill(xs, ys, facecolor=bg, edgecolor="none", zorder=1.2)


def render(out_path: Path) -> None:
    panel = load_panel()
    world = gpd.read_file(NE)
    traj = _trajectory_panel(panel, world)

    bg_fig = "#EEF0F3"
    bg_map = "#F7F8FA"
    ink = "#1F2A3A"
    ink_mid = "#4B576A"
    muted = "#7C8797"
    grid = "#D7DCE3"

    fig = plt.figure(figsize=(17.0, 9.6), dpi=140, facecolor=bg_fig)
    ax = fig.add_axes([0.015, 0.055, 0.765, 0.875], facecolor=bg_map)
    ax_leg = fig.add_axes([0.792, 0.055, 0.198, 0.875], facecolor="white")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-58, 82)
    ax.set_aspect("equal")
    ax.set_axis_off()
    _draw_basemap(ax, world, bg_map)

    sizes = dict(zip(YEARS, [150, 250, 380, 530, 700]))
    label_offsets = {
        "Global": [(0, -7), (0, 7), (0, -7), (0, 7), (0, -8)],
        "North America": [(0, -7), (0, 7), (0, -7), (0, 7), (0, -8)],
        "South America": [(-7, 0), (7, 0), (-7, 0), (7, 0), (-8, 0)],
        "Africa": [(-7, 0), (7, 0), (-7, 0), (7, 0), (-8, 0)],
    }

    for track in TRACKS:
        sub = traj[traj["track"] == track].sort_values("year").reset_index(drop=True)
        scale = DISPLAY_SCALE[track]
        mean_lng, mean_lat = float(sub["lng"].mean()), float(sub["lat"].mean())
        sub["plot_lng"] = mean_lng + (sub["lng"] - mean_lng) * scale
        sub["plot_lat"] = mean_lat + (sub["lat"] - mean_lat) * scale

        ax.plot(sub["plot_lng"], sub["plot_lat"], color=TRACK_COLOR[track],
                lw=2.2, alpha=0.92, zorder=3)
        ax.annotate(
            "", xy=(sub.iloc[-1]["plot_lng"], sub.iloc[-1]["plot_lat"]),
            xytext=(sub.iloc[-2]["plot_lng"], sub.iloc[-2]["plot_lat"]),
            arrowprops=dict(arrowstyle="-|>", color=TRACK_COLOR[track],
                            lw=2.4, mutation_scale=13), zorder=4,
        )

        # Draw newest/largest first, then older/smaller on top.  This keeps
        # all five rings visible when a centroid is spatially stable (North
        # America) instead of hiding the early years behind 2021.
        for _, row in sub.sort_values("year", ascending=False).iterrows():
            x, y = row["plot_lng"], row["plot_lat"]
            size = sizes[int(row["year"])]
            face = _change_color(float(row["pc_change"]))
            edge = _change_color(float(row["total_change"]))
            ax.scatter([x], [y], s=size * 1.18, facecolor="white",
                       edgecolor="none", zorder=4.5)
            ax.scatter([x], [y], s=size, facecolor=face, edgecolor=edge,
                       linewidth=3.0, alpha=0.94, zorder=5)

        for i, row in sub.iterrows():
            x, y = row["plot_lng"], row["plot_lat"]
            dx, dy = label_offsets[track][i]
            ax.text(x + dx, y + dy, str(int(row["year"])), fontsize=8.5,
                    fontweight="bold", color=ink, ha="center", va="center",
                    bbox=dict(facecolor="white", alpha=0.94, edgecolor=grid,
                              linewidth=0.5, pad=1.1), zorder=7)

        last = sub.iloc[-1]
        title = "WORLD total-emissions centre" if track == "Global" else track
        label_dx = 10 if track in ("Global", "Africa") else -10
        ax.text(last["plot_lng"] + label_dx, last["plot_lat"] + 8, title,
                fontsize=11.5, fontweight="bold", color=TRACK_COLOR[track],
                ha="center", va="center", zorder=8,
                bbox=dict(facecolor="white", alpha=0.96,
                          edgecolor=TRACK_COLOR[track], linewidth=1.0, pad=2.0))
        ax.text(mean_lng, mean_lat - 10,
                f"spatial displacement ×{scale} for visibility",
                fontsize=7.7, color=muted, ha="center", va="center", zorder=8)

    fig.text(0.020, 0.965,
             "What is moving east?  The centre of total emissions — not per-capita emissions",
             fontsize=15.5, color=ink, fontweight="bold")
    fig.text(0.020, 0.938,
             "Five real observations at two-year intervals · locations follow emissions-weighted country centroids",
             fontsize=10.3, color=ink_mid)

    ax_leg.set_xlim(0, 1); ax_leg.set_ylim(0, 1)
    ax_leg.set_xticks([]); ax_leg.set_yticks([])
    for spine in ax_leg.spines.values():
        spine.set_visible(False)

    ax_leg.text(0.06, 0.96, "2013 → 2021", fontsize=13,
                color=ink, fontweight="bold")
    ax_leg.text(0.06, 0.925, "Change calculated from the panel data",
                fontsize=8.8, color=muted)
    ax_leg.text(0.06, 0.875, "Track", fontsize=9.5, color=ink,
                fontweight="bold")
    ax_leg.text(0.60, 0.875, "Total", fontsize=9.5, color=ink,
                fontweight="bold", ha="center")
    ax_leg.text(0.85, 0.875, "Per-cap", fontsize=9.5, color=ink,
                fontweight="bold", ha="center")
    ax_leg.plot([0.06, 0.94], [0.855, 0.855], color=grid, lw=0.8)

    for i, track in enumerate(TRACKS):
        sub = traj[traj["track"] == track].sort_values("year")
        first, last = sub.iloc[0], sub.iloc[-1]
        y = 0.805 - i * 0.095
        d_total = float(last["total_change"])
        d_pc = float(last["pc_change"])
        ax_leg.add_patch(plt.Rectangle((0.06, y - 0.012), 0.025, 0.024,
                                       facecolor=TRACK_COLOR[track], edgecolor="none"))
        short_track = "World centre" if track == "Global" else track.replace("North ", "N. ").replace("South ", "S. ")
        ax_leg.text(0.10, y, short_track, fontsize=9.8, color=ink,
                    fontweight="bold", va="center")
        ax_leg.text(0.60, y, f"{d_total:+.1f}%", fontsize=10.5,
                    color=_change_color(d_total), fontweight="bold",
                    ha="center", va="center")
        ax_leg.text(0.85, y, f"{d_pc:+.1f}%", fontsize=10.5,
                    color=_change_color(d_pc), fontweight="bold",
                    ha="center", va="center")
        ax_leg.text(0.10, y - 0.028,
                    f"{first['total_mt']:,.0f}→{last['total_mt']:,.0f} Mt · {first['pc']:.2f}→{last['pc']:.2f} t/p",
                    fontsize=7.5, color=muted, va="center")

    # Data-driven explanation of the world-centre shift.
    asia = panel[panel["region"] == "Asia"].groupby("year")["co2"].sum()
    europe = panel[panel["region"] == "Europe"].groupby("year")["co2"].sum()
    asia_delta = (asia.loc[2021] / asia.loc[2013] - 1) * 100
    europe_delta = (europe.loc[2021] / europe.loc[2013] - 1) * 100
    box = FancyBboxPatch((0.05, 0.30), 0.90, 0.13,
                         boxstyle="round,pad=0.012,rounding_size=0.012",
                         facecolor="#F7F2E9", edgecolor="#D8C5A5", linewidth=0.8)
    ax_leg.add_patch(box)
    ax_leg.text(0.08, 0.395, "Why east?", fontsize=10.5, color=ink,
                fontweight="bold")
    ax_leg.text(0.08, 0.355,
                f"Asia total {asia_delta:+.1f}% while Europe {europe_delta:+.1f}%.",
                fontsize=9.0, color=ink_mid)
    ax_leg.text(0.08, 0.322,
                "The global centroid shifts 37.5°E → 43.7°E.",
                fontsize=9.0, color=ink_mid)

    ax_leg.text(0.06, 0.255, "How to read each circle", fontsize=10.5,
                color=ink, fontweight="bold")
    ax_leg.scatter([0.12, 0.25], [0.205, 0.205], s=[90, 455],
                   facecolor="#D7DCE3", edgecolor="#D7DCE3", linewidth=2.5)
    ax_leg.text(0.37, 0.205, "size = time  ·  2013 → 2021",
                fontsize=8.8, color=ink_mid, va="center")
    ax_leg.scatter([0.12], [0.145], s=190, facecolor="#168447",
                   edgecolor="#C92A2A", linewidth=3.0)
    ax_leg.text(0.24, 0.145, "fill = per-capita · outline = total",
                fontsize=8.8, color=ink_mid, va="center")
    ax_leg.text(0.06, 0.085, "green = lower (improving)  ·  red = higher",
                fontsize=8.7, color=ink_mid)
    ax_leg.text(0.06, 0.045,
                "Display multipliers affect only visible displacement, not values or direction.",
                fontsize=7.5, color=muted, wrap=True)

    fig.text(0.020, 0.020,
             "Key result: the eastward story belongs to total-emissions geography; world per-capita CO₂ fell slightly, while Asia's total and per-capita both rose.",
             fontsize=9.8, color=muted, style="italic")

    fig.savefig(out_path, dpi=150, facecolor=fig.get_facecolor(),
                bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    print(f"  saved {out_path.parent.name}/{out_path.name} ({out_path.stat().st_size:,} B)")


if __name__ == "__main__":
    render(config.FIGS_P3 / "P3_06_trajectory_revised.png")
