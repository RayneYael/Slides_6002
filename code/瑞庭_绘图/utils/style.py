# -*- coding: utf-8 -*-
"""SCI journal styling for non-map figures."""
from __future__ import annotations

from typing import Optional, Sequence

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap, Normalize

import config

CO2_CMAP = LinearSegmentedColormap.from_list("co2_gr", config.CO2_SCALE)
PC_CMAP = LinearSegmentedColormap.from_list("pc_gr", config.PC_SCALE)
HEAT_CMAP = LinearSegmentedColormap.from_list("heat_gr", config.HEAT_SCALE)


def apply_mpl_style() -> None:
    mpl.rcParams.update(
        {
            "figure.facecolor": config.PAPER,
            "axes.facecolor": config.PAPER_CARD,
            "axes.edgecolor": config.GRID,
            "axes.labelcolor": config.INK_SOFT,
            "axes.titlecolor": config.INK,
            "axes.titlesize": 14,
            "axes.titleweight": "bold",
            "axes.labelsize": 13,
            "xtick.color": config.MUTED,
            "ytick.color": config.MUTED,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "text.color": config.INK,
            "font.family": "sans-serif",
            "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial", "Helvetica"],
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "legend.frameon": False,
            "savefig.dpi": config.DPI,
            "savefig.bbox": "tight",
            "savefig.facecolor": config.PAPER,
            "figure.dpi": 120,
        }
    )


def save_fig(fig: plt.Figure, folder, name: str) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / name
    fig.savefig(out, dpi=config.DPI, bbox_inches="tight", facecolor=config.PAPER, pad_inches=0.18)
    plt.close(fig)
    print(f"  saved {folder.name}/{out.name}")


def journal_figure(
    figsize=(11.2, 7.4),
    *,
    main=(0.08, 0.26, 0.84, 0.62),
    legend=(0.08, 0.04, 0.84, 0.15),
    cbar_side: Optional[str] = None,
):
    """
    White canvas + bottom legend band.
    Legend band uses the SAME left/width as the main plot area.
    """
    fig = plt.figure(figsize=figsize, facecolor=config.PAPER)
    # Force legend width == main width
    legend = (main[0], legend[1], main[2], legend[3])
    ax = fig.add_axes(list(main), facecolor=config.PAPER_CARD)
    ax_leg = fig.add_axes(list(legend), facecolor="#F5F6F8")
    for sp in ax_leg.spines.values():
        sp.set_color(config.GRID)
        sp.set_linewidth(0.7)
    ax_leg.set_xticks([])
    ax_leg.set_yticks([])
    cax = None
    if cbar_side == "right":
        x = main[0] + main[2] + 0.012
        cax = fig.add_axes([x, main[1], 0.014, main[3]])
    elif cbar_side == "left":
        x = main[0] - 0.028
        cax = fig.add_axes([x, main[1], 0.014, main[3]])
    return fig, ax, ax_leg, cax


def title_filename(fig, filename: str, subtitle: str = "") -> None:
    """Deprecated for PPT figs — titles live with the Exploration figure assets."""
    return


def clear_legend_band(ax_leg) -> None:
    ax_leg.cla()
    ax_leg.set_facecolor("#F5F6F8")
    for sp in ax_leg.spines.values():
        sp.set_color(config.GRID)
        sp.set_linewidth(0.7)
    ax_leg.set_xticks([])
    ax_leg.set_yticks([])
    ax_leg.set_xlim(0, 1)
    ax_leg.set_ylim(0, 1)


def thin_colorbar(cax, cmap, norm, *, label: str = "", ticks=None, ticklabels=None) -> None:
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = cax.figure.colorbar(sm, cax=cax, orientation="vertical")
    if ticks is not None:
        cbar.set_ticks(list(ticks))
    if ticklabels is not None:
        cbar.set_ticklabels(list(ticklabels))
    if label:
        cbar.set_label(label, fontsize=9, color=config.INK_SOFT, labelpad=6)
    cbar.ax.tick_params(labelsize=8, colors=config.MUTED, length=2.5, width=0.5)
    cbar.outline.set_edgecolor(config.GRID)
    cbar.outline.set_linewidth(0.5)


def legend_handles(ax_leg, handles, labels, *, note: str = "", ncol: Optional[int] = None) -> None:
    """Full-width legend band; icons + text centered (not left-aligned)."""
    clear_legend_band(ax_leg)
    n = max(1, len(handles))
    if ncol is None:
        ncol = min(n, 6)
    y_leg = 0.58 if note else 0.50
    leg = ax_leg.legend(
        handles,
        labels,
        loc="center",
        bbox_to_anchor=(0.5, y_leg),
        ncol=ncol,
        frameon=False,
        fontsize=11.5,
        handlelength=1.4,
        columnspacing=1.5,
        handletextpad=0.5,
        borderaxespad=0.0,
        alignment="center",
    )
    for t in leg.get_texts():
        t.set_color(config.INK_SOFT)
        t.set_ha("center")
    if note:
        ax_leg.text(0.5, 0.14, note, color=config.MUTED, fontsize=11, va="center", ha="center")


def style_axes(ax, *, ygrid: bool = True) -> None:
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color(config.GRID)
        ax.spines[spine].set_linewidth(0.85)
    ax.tick_params(colors=config.MUTED, labelsize=12, length=3)
    gkw = dict(color=config.GRID_SOFT, lw=0.6, zorder=0)
    if ygrid:
        ax.yaxis.grid(True, **gkw)
    else:
        ax.xaxis.grid(True, **gkw)
    ax.set_axisbelow(True)


def format_mt_label(mt: float) -> str:
    if mt < 1:
        return f"{mt:.1f}"
    if mt < 1000:
        return f"{mt:.0f}"
    if mt < 10000:
        return f"{mt/1000:.1f}k"
    return f"{mt/1000:.0f}k"


def log_mt_tick_labels(vmin: float, vmax: float, n: int = 5):
    ticks = np.linspace(vmin, vmax, n)
    return ticks, [format_mt_label(10**t) for t in ticks]
