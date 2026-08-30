# -*- coding: utf-8 -*-
"""Readable low-angle pseudo-3D trajectory map for the Cobalt Grid deck."""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib as mpl
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
EDA_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(EDA_DIR))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import config
from utils.data import load_panel
from _render_p3_trajectory_revised import DISPLAY_SCALE, TRACKS, YEARS, _trajectory_panel

NE = EDA_DIR / "aux" / "ne_110m_admin0.geojson"
mpl.rcParams["font.sans-serif"] = ["DejaVu Sans"]
mpl.rcParams["axes.unicode_minus"] = False

TRACK_LINE = {
    "Global": "#654316",
    "North America": "#2457A6",
    "South America": "#75429A",
    "Africa": "#9B6A12",
}

Y_SCALE = 0.63
SHEAR = 0.13


def _project(x, y, *, y_scale: float = Y_SCALE, shear: float = SHEAR):
    return np.asarray(x) + shear * np.asarray(y), y_scale * np.asarray(y)


def _total_color(change_pct: float, max_abs: float = 16.0) -> str:
    t = float(np.clip(change_pct / max_abs, -1, 1))
    cmap = mcolors.LinearSegmentedColormap.from_list(
        "total_change", ["#0B8B49", "#D3DAE2", "#D4262C"]
    )
    return mcolors.to_hex(cmap((t + 1) / 2))


def _draw_world(ax, world, *, offset_y: float, face: str,
                edge: str, lw: float, alpha: float, zorder: float,
                y_scale: float = Y_SCALE, shear: float = SHEAR) -> None:
    for _, row in world.iterrows():
        geoms = row.geometry.geoms if row.geometry.geom_type == "MultiPolygon" else [row.geometry]
        for geom in geoms:
            if geom.geom_type != "Polygon":
                continue
            coords = np.asarray(geom.exterior.coords)
            px, py = _project(coords[:, 0], coords[:, 1],
                              y_scale=y_scale, shear=shear)
            ax.fill(px, py + offset_y, facecolor=face, edgecolor=edge,
                    linewidth=lw, alpha=alpha, zorder=zorder)


def render(out_path: Path, *, map_only: bool = False) -> None:
    panel = load_panel()
    world = gpd.read_file(NE)
    traj = _trajectory_panel(panel, world)

    bg = "#EAF1F7" if map_only else "#D7E1EB"
    land = "#AFC0D2"
    ink = "#22364C"
    muted = "#60758B"

    fig_size = (15.8, 6.42) if map_only else (17.0, 9.6)
    fig = plt.figure(figsize=fig_size, dpi=150, facecolor=bg)
    ax = fig.add_axes(
        [0.006, 0.012, 0.988, 0.976]
        if map_only else [0.010, 0.095, 0.980, 0.865],
        facecolor=bg,
    )
    ax.set_xlim((-188, 190) if map_only else (-192, 195))
    ax.set_ylim((-66, 88) if map_only else (-50, 58))
    ax.set_aspect("equal")
    ax.set_axis_off()

    # The earlier pseudo-3D version compressed latitude to 63%, which was
    # appropriate for a low-angle standalone figure but made the map look
    # unnaturally flat once its legend moved into PowerPoint.  Map-only mode
    # restores near-standard geographic proportions and lets the map occupy
    # the complete chart area without stretching the bitmap in PowerPoint.
    y_scale = 1.0 if map_only else Y_SCALE
    shear = 0.06 if map_only else SHEAR

    # Three stacked silhouettes create a low, physical map slab.
    _draw_world(ax, world, offset_y=-5.0, face="#71869B", edge="#71869B",
                lw=0.18, alpha=0.92, zorder=1,
                y_scale=y_scale, shear=shear)
    _draw_world(ax, world, offset_y=-2.5, face="#8FA2B6", edge="#8FA2B6",
                lw=0.18, alpha=0.96, zorder=2,
                y_scale=y_scale, shear=shear)
    _draw_world(ax, world, offset_y=0.0, face=land, edge="#EDF3F7",
                lw=0.28, alpha=1.0, zorder=3,
                y_scale=y_scale, shear=shear)

    # Time controls the within-track growth.  Track scale is derived from the
    # 2021 total (log-compressed), so the global chain is visibly largest,
    # followed by North America, while Africa/South America remain smaller.
    time_size = dict(zip(YEARS, [180, 380, 700, 1150, 1800]))
    totals_2021 = (
        traj[traj["year"] == 2021].set_index("track")["total_mt"].astype(float)
    )
    log_totals = np.log10(totals_2021)
    track_factor = 0.72 + 0.43 * (
        (log_totals - log_totals.min()) /
        (log_totals.max() - log_totals.min() + 1e-9)
    )
    opacity = dict(zip(YEARS, [0.88, 0.76, 0.67, 0.58, 0.50]))

    for track in TRACKS:
        sub = traj[traj["track"] == track].sort_values("year").reset_index(drop=True)
        # Plot every centroid at its data-derived geographic position.  The
        # circles grow strongly with time/track scale, but the trajectory
        # itself is never stretched merely to reach a particular country.
        scale = 1.0
        mean_lng = float(sub["lng"].mean())
        mean_lat = float(sub["lat"].mean())
        lng = mean_lng + (sub["lng"].to_numpy() - mean_lng) * scale
        lat = mean_lat + (sub["lat"].to_numpy() - mean_lat) * scale
        px, py = _project(lng, lat, y_scale=y_scale, shear=shear)
        py = py + 4.0  # circles float above the map slab
        sub["px"] = px; sub["py"] = py

        # Drop line + soft shadow reinforce the 3D lift.
        for _, row in sub.iterrows():
            ax.plot([row["px"], row["px"]], [row["py"] - 4.0, row["py"]],
                    color="#50657A", lw=0.75, alpha=0.35, zorder=4)
            ax.scatter([row["px"]], [row["py"] - 2.1],
                       s=time_size[int(row["year"])] * float(track_factor[track]) * 0.70,
                       facecolor="#4D6175", edgecolor="none",
                       alpha=0.13, zorder=4)

        ax.plot(px, py, color=TRACK_LINE[track], lw=2.4,
                alpha=0.88, zorder=5)

        # Entire circle—fill and border—uses the same total-change gradient.
        for _, row in sub.sort_values("year", ascending=False).iterrows():
            col = _total_color(float(row["total_change"]))
            ax.scatter([row["px"]], [row["py"]],
                       s=time_size[int(row["year"])] * float(track_factor[track]),
                       facecolor=col, edgecolor=col, linewidth=3.0,
                       alpha=opacity[int(row["year"])], zorder=6)

        # A fixed-length, semi-transparent arrow communicates direction only.
        # Its length is deliberately NOT proportional to distance: several
        # emissions centroids move only a few kilometres and would otherwise
        # be invisible at world-map scale.
        dx_data = float(px[-1] - px[0])
        dy_data = float(py[-1] - py[0])
        magnitude = float(np.hypot(dx_data, dy_data))
        if magnitude > 1e-9:
            ux, uy = dx_data / magnitude, dy_data / magnitude
            arrow_len = 18.0
            start_x = float(px[-1] - ux * 2.0)
            start_y = float(py[-1] - uy * 2.0)
            end_x = start_x + ux * arrow_len
            end_y = start_y + uy * arrow_len
            arrow_col = _total_color(float(sub.iloc[-1]["total_change"]))
            ax.annotate(
                "", xy=(end_x, end_y), xytext=(start_x, start_y),
                arrowprops=dict(arrowstyle="-|>", color=arrow_col,
                                lw=4.0, alpha=0.48, mutation_scale=18,
                                shrinkA=0, shrinkB=0),
                zorder=8,
            )

        last = sub.iloc[-1]
        name = "WORLD CENTRE" if track == "Global" else track.upper()
        track_label_offset = {
            "Global": (18, 10),
            "North America": (-18, 10),
            "South America": (-18, 8),
            "Africa": (-18, 4),
        }
        dx, dy = track_label_offset[track]
        ax.text(last["px"] + dx, last["py"] + dy, name,
                fontsize=10.5, fontweight="bold", color=TRACK_LINE[track],
                ha="center", va="center", zorder=9,
                bbox=dict(facecolor="#F0EBDE", alpha=0.95,
                          edgecolor=TRACK_LINE[track], linewidth=0.9, pad=1.8))

    if map_only:
        fig.savefig(out_path, dpi=150, facecolor=fig.get_facecolor(),
                    bbox_inches=None, pad_inches=0)
        plt.close(fig)
        print(f"  saved {out_path.parent.name}/{out_path.name} ({out_path.stat().st_size:,} B)")
        return

    # Small overlay legend; no numerical table competes with the map.
    key = fig.add_axes([0.030, 0.025, 0.45, 0.105], facecolor="#F0EBDE")
    key.set_xlim(0, 1); key.set_ylim(0, 1)
    key.set_xticks([]); key.set_yticks([])
    for spine in key.spines.values():
        spine.set_color("#1F2BE0"); spine.set_linewidth(0.75)
    lx = [0.065, 0.155, 0.255, 0.365, 0.485]
    key.scatter(lx, [0.64] * 5, s=[80, 140, 220, 335, 500],
                facecolor="#AEBBC8", edgecolor="#7E90A2", linewidth=0.7,
                alpha=[0.82, 0.76, 0.70, 0.64, 0.58])
    for x0, year in zip(lx, YEARS):
        key.text(x0, 0.19, str(year), fontsize=6.8, fontweight="bold",
                 color=ink, ha="center", va="center")
    key.scatter([0.69, 0.86], [0.61, 0.61], s=[330, 330],
                facecolor=["#D4262C", "#0B8B49"],
                edgecolor=["#D4262C", "#0B8B49"], linewidth=1.4,
                alpha=[0.62, 0.62])
    key.text(0.69, 0.18, "TOTAL ↑", fontsize=6.8, fontweight="bold",
             color=ink, ha="center")
    key.text(0.86, 0.18, "TOTAL ↓", fontsize=6.8, fontweight="bold",
             color=ink, ha="center")

    fig.text(0.985, 0.026,
             "CENTRES = CO₂-WEIGHTED COUNTRY LOCATIONS · ARROW = DIRECTION ONLY, NOT DISTANCE",
             fontsize=8.2, color=muted, ha="right")
    fig.savefig(out_path, dpi=150, facecolor=fig.get_facecolor(),
                bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    print(f"  saved {out_path.parent.name}/{out_path.name} ({out_path.stat().st_size:,} B)")


if __name__ == "__main__":
    render(config.FIGS_P3 / "P3_06_trajectory_pseudo3d_cobalt.png")
