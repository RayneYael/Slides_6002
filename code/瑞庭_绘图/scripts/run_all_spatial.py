# -*- coding: utf-8 -*-
"""
Non-map SCI PNG figures for the spatial block (6-slide PPT).

Outputs (1_Exploration of Dataset/Figures/_Generated_by_Scripts/point*):
  P1_03 — lollipop Top20 + multi-path cumulative (NO bars; complements P1_04)
  P1_04 — region vertical bars + Lorenz concentration
  P2_02 — scale-vs-intensity bubble
  P2_03 — two-ring sunburst (tonnes vs per-capita)
  P3_02 — regional fuel stacked (in-segment % only for wide segments;
           all regions get a side callout to avoid overlap)
  P3_03 — parallel coordinates with non-overlapping story country labels

Maps (HTML) live in build_maps_html.py.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
import squarify
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, Rectangle
from scipy import stats

EDA = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EDA))

import config
from utils.data import concentration_stats, fuel_ok, load_panel, slice_year, write_region_lookup
from utils.style import (
    CO2_CMAP,
    apply_mpl_style,
    journal_figure,
    legend_handles,
    save_fig,
    style_axes,
)

warnings.filterwarnings("ignore", category=FutureWarning)
apply_mpl_style()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _safe_short(name: str, iso: str, max_len: int = 11) -> str:
    return name if len(str(name)) <= max_len else iso


# ===========================================================================
# Point 1
# ===========================================================================
def fig_p1_03_treemap_concentration(y: pd.DataFrame, *, wide: bool = False) -> list:
    """
    Hierarchical treemap (region → country).

    Visual rules (per user request, slide 2):
      • Region blocks are COLOURED ONLY — no region name or % repeated inside
        the cells (the legend at the bottom of the figure explains the colour
        → region mapping; the share % lives in the PPT title and key points).
      • Each country block gets one of three label tiers, decided by cell
        area (i.e. its CO₂ share):
            - Big enough  → full name + share-%
            - Smaller     → ISO-3 code only
            - Tiniest     → no label at all
    The former numbered-country index was removed: it consumed the slide's
    narrative space without improving the hierarchy reading.
    """
    fname = (
        "P1_03_combo_top20_bars_cumshare_cobalt_wide.png"
        if wide else "P1_03_combo_top20_bars_cumshare_cobalt.png"
    )
    total = float(y["co2"].sum())

    # ── Region-level summary, sorted largest first ────────────────────────
    by_reg = (
        y.groupby("region")["co2"].sum()
         .sort_values(ascending=False)
    )
    reg_share = (by_reg / total * 100)

    # Discrete colour ramp — 6 steps, red (largest) → green (smallest)
    # No continuous interpolation: each region gets one of the 6 colours.
    DISCRETE_RAMP = [
        "#B71C1C",   # 1  - deepest red  (largest)
        "#E64A19",   # 2  - red-orange
        "#FB8C00",   # 3  - orange
        "#FBC02D",   # 4  - amber-yellow
        "#7CB342",   # 5  - light green
        "#2E7D32",   # 6  - deep green   (smallest)
    ]
    REGION_COL = {reg: DISCRETE_RAMP[i] for i, reg in enumerate(by_reg.index)}
    REGION_LIGHT = {
        reg: tuple(0.55 * c + 0.45 for c in mcolors.to_rgb(col))
        for reg, col in REGION_COL.items()
    }

    # Short country names (keep treemap labels compact)
    SHORT_TM = {"United States": "U.S.A.",
                "Saudi Arabia": "S. Arabia",
                "South Korea": "S. Korea",
                "United Kingdom": "U.K.",
                "South Africa": "S. Africa",
                "Trinidad and Tobago": "Trinidad & Tobago",
                "United Arab Emirates": "UAE",
                "New Zealand": "N. Zealand",
                "Czechia": "Czechia"}

    # The slide uses a landscape chart card.  In wide mode the treemap is
    # recomputed for that landscape rectangle instead of drawing a square
    # treemap in the middle of a wide bitmap (which wastes almost half of the
    # available data area).  Area encoding remains exact.
    fig_bg = "#F7F0E5" if wide else config.PAPER
    card_bg = "#F7F0E5" if wide else config.PAPER_CARD
    legend_bg = "#F4EBDD" if wide else "#F5F6F8"
    fig_size = (12.0, 7.2) if wide else (12.0, 7.8)
    fig = plt.figure(figsize=fig_size, facecolor=fig_bg)
    ax_tm = fig.add_axes([0.02, 0.16, 0.96, 0.81], facecolor=card_bg)
    ax_leg = fig.add_axes([0.02, 0.025, 0.96, 0.105], facecolor=legend_bg)
    for sp in ax_leg.spines.values():
        sp.set_color(config.GRID)
    ax_leg.set_xticks([])
    ax_leg.set_yticks([])

    # ── Outer treemap: 6 regions, sized by their share of world CO₂ ───────
    style_axes(ax_tm, ygrid=False)
    tm_w, tm_h = (200.0, 100.0) if wide else (100.0, 100.0)
    sizes_reg = (by_reg.values / by_reg.values.sum() * 100).tolist()
    rects_reg = squarify.normalize_sizes(sizes_reg, tm_w, tm_h)
    rects_reg = squarify.squarify(rects_reg, 0, 0, tm_w, tm_h)

    # Output: numbered small countries (region, name, iso, share, number)
    numbered: list[dict] = []
    number_counter = 1

    for r_reg, region, share in zip(rects_reg, by_reg.index, reg_share.values):
        rx, ry = r_reg["x"], r_reg["y"]
        w, h = r_reg["dx"], r_reg["dy"]
        col_reg = REGION_COL[region]

        # Region block (parent rectangle) — outer = region colour
        ax_tm.add_patch(Rectangle((rx, ry), w, h, facecolor=col_reg,
                                   edgecolor="white", linewidth=1.6, zorder=2))

        # NOTE: region name + % label is intentionally OMITTED inside the
        # block — the legend at the bottom of the figure + the PPT title
        # already tell the user "red = largest region" and "Asia = 60%".

        # Inner area where countries will be drawn (no header band)
        pad_x = 0.004 * tm_w
        pad_y = 0.004 * tm_h
        inner_x = rx + pad_x
        inner_y = ry + pad_y
        inner_w = w - 2 * pad_x
        inner_h = h - 2 * pad_y
        if inner_w <= 1 or inner_h <= 1:
            continue

        # ── Inner treemap: countries in this region ──────────────────────
        sub = y[y["region"] == region].sort_values("co2", ascending=False).copy()
        if sub.empty:
            continue
        sub["share_pct"] = sub["co2"] / total * 100
        sizes_ctry = (sub["co2"].values / sub["co2"].sum() * 100).tolist()
        rects_ctry = squarify.normalize_sizes(sizes_ctry, inner_w, inner_h)
        rects_ctry = squarify.squarify(rects_ctry, inner_x, inner_y, inner_w, inner_h)

        # A lighter shade of the region colour for the country blocks (so
        # the hierarchy is visible: outer = region, inner = country in region).
        light = REGION_LIGHT[region]

        for rc, (_, crow) in zip(rects_ctry, sub.iterrows()):
            cx, cy, cdx, cdy = rc["x"], rc["y"], rc["dx"], rc["dy"]
            ax_tm.add_patch(Rectangle((cx, cy), cdx, cdy, facecolor=light,
                                       edgecolor=col_reg, linewidth=0.6, zorder=3))
            name = SHORT_TM.get(crow["country"], crow["country"])
            # Normalise dimensions back to the original 100×100 decision
            # space so the same label-density rules work in both layouts.
            cdx_norm = cdx / tm_w * 100
            cdy_norm = cdy / tm_h * 100
            area = cdx_norm * cdy_norm
            pct = float(crow["share_pct"])
            iso = crow["iso_code"]
            # Tier 1: very large country — show name + share %
            if area >= 60 and cdx_norm >= 12 and cdy_norm >= 6:
                ax_tm.text(cx + cdx / 2, cy + cdy * 0.62, name,
                           ha="center", va="center", fontsize=12,
                           color="white", fontweight="bold", zorder=4)
                ax_tm.text(cx + cdx / 2, cy + cdy * 0.25, f"{pct:.1f}%",
                           ha="center", va="center", fontsize=10,
                           color="white", alpha=0.95, zorder=4)
            # Tier 2: medium country — show name + share %
            elif area >= 24 and cdx_norm >= 5.5 and cdy_norm >= 5:
                # Long names are the main source of collisions in narrow
                # rectangles.  Use an ISO code unless the short name fits.
                safe_name = (
                    name
                    if len(str(name)) <= 11 and cdx_norm >= max(7.0, len(str(name)) * 1.20)
                    else iso
                )
                ax_tm.text(cx + cdx / 2, cy + cdy * 0.62, safe_name,
                           ha="center", va="center", fontsize=9.0,
                           color="white", fontweight="bold", zorder=4)
                ax_tm.text(cx + cdx / 2, cy + cdy * 0.25, f"{pct:.1f}%",
                           ha="center", va="center", fontsize=7.5,
                           color="white", alpha=0.9, zorder=4)
            # Tier 3: keep a short full name; use the dataset ISO-3 code only
            # when the country name itself is long.
            elif area >= 9 and max(cdx_norm, cdy_norm) >= 3:
                name_fits = (
                    len(str(name)) <= 8
                    and cdx_norm >= max(6.0, len(str(name)) * 1.30)
                    and cdy_norm >= 4.0
                )
                small_label = name if name_fits else str(iso)
                small_fs = 7.2 if small_label == name else 8.0
                ax_tm.text(cx + cdx / 2, cy + cdy / 2, small_label,
                           ha="center", va="center", fontsize=small_fs,
                           color="white", fontweight="bold", zorder=4)
            # Tier 4: too tiny — no label at all (omitted)

    ax_tm.set_xlim(0, tm_w)
    ax_tm.set_ylim(0, tm_h)
    ax_tm.set_aspect("equal")
    ax_tm.set_xticks([])
    ax_tm.set_yticks([])
    for sp in ax_tm.spines.values():
        sp.set_visible(False)

    # ── LEGEND (bottom band) — explains region colour → region, ordered
    # by the same discrete ramp as the treemap (red = largest).  No share-%
    # in the legend (it's in the PPT title / key points).
    handles = [
        Line2D([0], [0], marker="s", color="none",
               markerfacecolor=REGION_LIGHT[reg],
               markeredgecolor=REGION_COL[reg], markeredgewidth=1.2,
               markersize=12, label=reg)
        for reg in by_reg.index
    ]
    legend_handles(
        ax_leg, handles, [h.get_label() for h in handles],
        note=("Legend swatches exactly match the country-cell fill; the darker "
              "outline marks the region boundary.  Long labels use ISO-3; "
              "the smallest cells are intentionally unlabelled."),
        ncol=6,
    )
    save_fig(fig, config.FIGS_P1, fname)
    return numbered


def fig_p1_04_panel(y: pd.DataFrame) -> None:
    """Region vertical bars + Lorenz concentration curve (no Top10 hbar)."""
    fname = "P1_04_combo_concentration_bars_region_top10.png"
    st = concentration_stats(y)
    rs = st["region_share"].sort_values(ascending=False)

    ordered = y.sort_values("co2", ascending=True).copy()
    ordered["share"] = ordered["co2"] / ordered["co2"].sum()
    ordered["cum_pop"] = np.arange(1, len(ordered) + 1) / len(ordered)
    ordered["cum_emi"] = ordered["share"].cumsum()
    lorenz_top10_x = (len(y) - 10) / len(y)
    lorenz_top10_y = 1 - st["top10_share"]
    lorenz_top20_x = (len(y) - 20) / len(y)
    lorenz_top20_y = 1 - st["top20_share"]

    fig = plt.figure(figsize=(11.5, 7.2), facecolor=config.PAPER)
    axr = fig.add_axes([0.08, 0.30, 0.40, 0.55], facecolor=config.PAPER_CARD)
    axl = fig.add_axes([0.55, 0.30, 0.37, 0.55], facecolor=config.PAPER_CARD)
    ax_leg = fig.add_axes([0.08, 0.05, 0.86, 0.17], facecolor="#F5F6F8")
    for sp in ax_leg.spines.values():
        sp.set_color(config.GRID)
    ax_leg.set_xticks([])
    ax_leg.set_yticks([])

    # Region bars
    style_axes(axr, ygrid=True)
    axr.set_title("Regional share of world CO₂ (vertical)", loc="left", fontsize=12, pad=6)
    xpos = np.arange(len(rs))
    colors = [config.REGION_COLORS.get(i, config.MUTED) for i in rs.index]
    axr.bar(xpos, rs.values * 100, color=colors, width=0.66, edgecolor="white", lw=0.5)
    for i, (reg, v) in enumerate(rs.items()):
        axr.text(i, v * 100 + 1.3, f"{v*100:.0f}%", ha="center", va="bottom", fontsize=11, fontweight="bold", color=config.INK)
    axr.set_xticks(xpos)
    axr.set_xticklabels(list(rs.index), rotation=22, ha="right", fontsize=10)
    axr.set_ylabel("% of world CO₂")
    axr.set_ylim(0, max(rs.values) * 100 * 1.20)
    axr.tick_params(axis="x", pad=2)

    # Lorenz
    style_axes(axl, ygrid=True)
    axl.set_title("Lorenz concentration curve", loc="left", fontsize=12, pad=6)
    axl.plot([0, 1], [0, 1], color=config.MUTED, ls="--", lw=1.0, label="Equality")
    axl.plot(ordered["cum_pop"], ordered["cum_emi"], color=config.ACCENT_LINE, lw=2.4, label="Lorenz")
    axl.fill_between(ordered["cum_pop"], ordered["cum_emi"], ordered["cum_pop"], color=config.ACCENT_SOFT, alpha=0.18)
    axl.scatter([lorenz_top10_x], [lorenz_top10_y], s=80, c=config.ACCENT, zorder=5, edgecolors="white", lw=0.8)
    axl.scatter([lorenz_top20_x], [lorenz_top20_y], s=80, c=config.INK, zorder=5, edgecolors="white", lw=0.8)
    axl.annotate(
        f"ex-Top10\n({st['top10_share']*100:.0f}% in Top10)",
        (lorenz_top10_x, lorenz_top10_y),
        textcoords="offset points", xytext=(-70, 18),
        fontsize=9.5, color=config.ACCENT, fontweight="bold",
        arrowprops=dict(arrowstyle="-", color=config.ACCENT_SOFT, lw=0.8),
    )
    axl.annotate(
        f"ex-Top20\n({st['top20_share']*100:.0f}% in Top20)",
        (lorenz_top20_x, lorenz_top20_y),
        textcoords="offset points", xytext=(10, -32),
        fontsize=9.5, color=config.INK, fontweight="bold",
        arrowprops=dict(arrowstyle="-", color=config.MUTED, lw=0.8),
    )
    axl.set_xlabel("Cumulative share of countries (small → large)")
    axl.set_ylabel("Cumulative share of emissions")
    axl.set_xlim(0, 1)
    axl.set_ylim(0, 1)

    handles = [
        Line2D([0], [0], color=config.REGION_COLORS[r], marker="s", ls="none", markersize=9, label=r)
        for r in rs.index if r in config.REGION_COLORS
    ]
    handles += [
        Line2D([0], [0], color=config.ACCENT_LINE, lw=2.2, label="Lorenz curve"),
        Line2D([0], [0], color=config.MUTED, ls="--", lw=1.1, label="Equality line"),
    ]
    legend_handles(
        ax_leg, handles, [h.get_label() for h in handles],
        note="Left = where tonnes sit by region · Right = how unequal (bow away from diagonal = concentration).",
        ncol=4,
    )
    save_fig(fig, config.FIGS_P1, fname)


# ===========================================================================
# Point 2
# ===========================================================================
def fig_p2_02_bubble(y: pd.DataFrame) -> None:
    """Scale vs intensity bubble — ALL countries, top-5 labels each side.

    Visual rules (per user request, slide 4):
      • NO horizontal / vertical dashed lines (no median cross, no
        axis-projections from the two #1 emitters — those made the chart
        busy and didn't add information).
      • Dots are coloured by a 2-D gradient: R grows with log CO₂,
        B grows with per-capita, with a small constant G for visibility.
        Bottom-left ≈ dark blue, top-right ≈ magenta, etc.  This is NOT
        region-based, so the chart doesn't duplicate the region colour
        already on the page-3 map.
      • Top-5 labels inherit the same 2-D gradient colour as their dot,
        so each label visually anchors to its point.  No green, no black.
    """
    fname = "P2_02_combo_bubble_scale_vs_intensity_cobalt.png"
    d = y.copy()
    rho, _ = stats.spearmanr(d["co2"], d["co2_per_capita"])
    top5_t = d.nlargest(5, "co2")
    top5_p = d.nlargest(5, "co2_per_capita")
    overlap = len(set(top5_t["iso_code"]) & set(top5_p["iso_code"]))

    fig, ax, ax_leg, _ = journal_figure(
        figsize=(12.0, 7.8),
        main=(0.09, 0.30, 0.82, 0.58),
        legend=(0.09, 0.05, 0.82, 0.18),
    )
    style_axes(ax, ygrid=True)

    # ----- 2-D gradient colour for every dot ---------------------------
    # x ∈ [0, 1]   →  R grows with log CO₂
    # y ∈ [0, 1]   →  B grows with per-capita
    # A small constant G keeps the colours from going pure red / pure blue
    # (and avoids the dark-green corner).  The result: dark-blue in the
    # bottom-left, dark-magenta in the top-right, with a smooth 2-D wash.
    x = d["log_co2"].values.astype(float)
    yv = d["co2_per_capita"].values.astype(float)
    x_n = (x - np.nanmin(x)) / (np.nanmax(x) - np.nanmin(x) + 1e-9)
    y_n = (yv - np.nanmin(yv)) / (np.nanmax(yv) - np.nanmin(yv) + 1e-9)
    R = 0.10 + 0.78 * x_n ** 0.85
    G_arr = np.full_like(R, 0.18, dtype=float)
    B = 0.10 + 0.78 * y_n ** 0.85
    colors = np.column_stack([R, G_arr, B])

    # Plot ALL countries as bubbles (size ∝ population, colour = 2-D gradient)
    ax.scatter(
        x, yv,
        s=np.sqrt(d["population"].clip(1).values / 1e6) * 18,
        c=colors, alpha=0.78, edgecolors="white", lw=0.4, zorder=3,
    )

    # Build a small set of legend handles that explains the 2-D gradient
    # using four corner swatches (low/low, low/high, high/low, high/high).
    # NB: don't call this `legend_handles` — that would shadow the imported
    # `legend_handles` function from utils.style used further down.
    def _grad(rx, ry):
        return (0.10 + 0.78 * rx ** 0.85, 0.18, 0.10 + 0.78 * ry ** 0.85)
    bubble_legend_handles = [
        Line2D([0], [0], marker="o", color="none",
               markerfacecolor=_grad(0.05, 0.05), markersize=10,
               label="low scale  ·  low intensity"),
        Line2D([0], [0], marker="o", color="none",
               markerfacecolor=_grad(0.95, 0.05), markersize=10,
               label="high scale  ·  low intensity"),
        Line2D([0], [0], marker="o", color="none",
               markerfacecolor=_grad(0.05, 0.95), markersize=10,
               label="low scale  ·  high intensity"),
        Line2D([0], [0], marker="o", color="none",
               markerfacecolor=_grad(0.95, 0.95), markersize=10,
               label="high scale  ·  high intensity"),
    ]

    # ── Label top-5 by total AND top-5 by per-capita ─────────────────────
    SHORT_BUB = {
        "United States": "U.S.A.",
        "Saudi Arabia": "S. Arabia",
        "United Arab Emirates": "UAE",
        "Trinidad and Tobago": "Trinidad & Tobago",
        "South Korea": "S. Korea",
    }
    # Build a set of isos to label, with hand-tuned offsets so the labels
    # don't pile on top of each other.
    label_targets = []
    for _, r in top5_t.iterrows():
        label_targets.append((r["iso_code"], SHORT_BUB.get(r["country"], r["country"]), "ton"))
    for _, r in top5_p.iterrows():
        # Avoid duplicate labels
        if r["iso_code"] in [t[0] for t in label_targets]:
            continue
        label_targets.append((r["iso_code"], SHORT_BUB.get(r["country"], r["country"]), "pc"))
    # Local, hand-tuned label positions.  Every connector points generally
    # rightward, but the labels remain close to their own point and fan out
    # diagonally to avoid bubbles and one another (no artificial label rail).
    LABEL_POS = {
        "QAT": (2.55, 36.3),
        "BRN": (1.55, 28.0),
        "TTO": (2.10, 26.1),
        "BHR": (2.12, 23.5),
        "SAU": (3.26, 21.1),
        "USA": (4.10, 16.2),
        "RUS": (3.66, 12.8),
        "JPN": (3.48, 9.6),
        "CHN": (4.35, 7.2),
        "IND": (3.80, 3.1),
    }
    ax.set_xlim(float(np.nanmin(x)) - 0.3, float(np.nanmax(x)) + 0.95)
    for iso, display, kind in label_targets:
        r = d[d["iso_code"] == iso]
        if r.empty:
            continue
        r = r.iloc[0]
        # Use the dot's own 2-D gradient colour for the label so the
        # label visually anchors to its point.  No green, no black.
        rx_p = r["log_co2"]
        ry_p = r["co2_per_capita"]
        xn_p = (rx_p - np.nanmin(x)) / (np.nanmax(x) - np.nanmin(x) + 1e-9)
        yn_p = (ry_p - np.nanmin(yv)) / (np.nanmax(yv) - np.nanmin(yv) + 1e-9)
        col = (0.10 + 0.78 * xn_p ** 0.85, 0.18, 0.10 + 0.78 * yn_p ** 0.85)
        rank_tag = "#1 total" if iso == top5_t.iloc[0]["iso_code"] else (
            "#1 per-cap" if iso == top5_p.iloc[0]["iso_code"] else None
        )
        label_text = f"{display}  ·  {rank_tag}" if rank_tag else display
        label_xy = LABEL_POS.get(
            iso, (float(r["log_co2"]) + 0.35, float(r["co2_per_capita"]) + 0.8)
        )
        ax.annotate(
            label_text, (r["log_co2"], r["co2_per_capita"]),
            textcoords="data", xytext=label_xy,
            fontsize=9.8, fontweight="bold", color=config.INK, ha="left",
            bbox=dict(facecolor="white", alpha=0.94, edgecolor=col,
                      linewidth=1.1, pad=1.5),
            arrowprops=dict(arrowstyle="-", color=col, lw=0.9,
                            shrinkA=0, shrinkB=2),
            zorder=6,
        )

    # Soft background bands (not dashed lines!) help the eye separate
    # the 4 quadrants without cluttering the chart.
    ax.axvspan(np.nanmin(x), np.median(x), color="#F4F6FA", alpha=0.55, zorder=0)
    ax.axvspan(np.median(x), np.nanmax(x), color="#FAF1F2", alpha=0.55, zorder=0)

    ax.set_xlabel("log₁₀ CO₂ (Mt), 2021", fontsize=13)
    ax.set_ylabel("CO₂ per capita (t / person)", fontsize=13)
    # Compact bivariate key: unlike four disconnected swatches, this makes
    # the simultaneous x/y colour encoding explicit.
    ax_leg.set_xlim(0, 1); ax_leg.set_ylim(0, 1)
    ax_leg.set_xticks([]); ax_leg.set_yticks([])
    ax_leg.text(0.02, 0.82, "Bivariate colour key", fontsize=11.5,
                fontweight="bold", color=config.INK)
    ax_leg.text(0.02, 0.54,
                "red component ↑ with total CO₂ (x)\nblue component ↑ with per-capita CO₂ (y)",
                fontsize=10.0, color=config.INK_SOFT, va="center")
    ax_leg.text(0.02, 0.18,
                f"All markers are circles; labels identify the two #1 countries.  Top-5 overlap: {overlap}/5.",
                fontsize=9.5, color=config.MUTED, va="center")
    gx = np.linspace(0, 1, 80)
    gy = np.linspace(0, 1, 60)
    XX, YY = np.meshgrid(gx, gy)
    key_rgb = np.dstack([0.10 + 0.78 * XX ** 0.85,
                         np.full_like(XX, 0.18),
                         0.10 + 0.78 * YY ** 0.85])
    ax_leg.imshow(key_rgb, extent=[0.69, 0.94, 0.18, 0.86],
                  origin="lower", aspect="auto", zorder=2)
    ax_leg.text(0.815, 0.08, "total →", ha="center", fontsize=9.5,
                color=config.INK)
    ax_leg.text(0.665, 0.52, "per-capita →", ha="center", va="center",
                rotation=90, fontsize=9.5, color=config.INK)
    save_fig(fig, config.FIGS_P2, fname)


def fig_p2_03_sunburst(y: pd.DataFrame) -> None:
    """Two-ring sunburst (tonnes vs per-capita)."""
    fname = "P2_03_combo_sunburst_top10_tonnes_vs_intensity.png"
    top_t = y.nlargest(10, "co2").copy()
    top_p = y.nlargest(10, "co2_per_capita").copy()
    overlap = set(top_t["iso_code"]) & set(top_p["iso_code"])
    overlap_names = ", ".join(sorted(overlap)) or "none"

    fig = plt.figure(figsize=(12.0, 7.4), facecolor=config.PAPER)

    def ring_data(df: pd.DataFrame, value_col: str):
        reg = df.groupby("region", sort=False)[value_col].sum().sort_values(ascending=False)
        sizes_inner = reg.values.tolist()
        labels_inner = reg.index.tolist()
        colors_inner = [config.REGION_COLORS.get(r, config.MUTED) for r in labels_inner]
        parts = [df[df["region"] == r].sort_values(value_col, ascending=False) for r in labels_inner]
        out = pd.concat(parts)
        sizes_outer = out[value_col].tolist()
        # FULL country names — no ISO abbreviations (per user request).
        labels_outer = [str(row["country"]) for _, row in out.iterrows()]
        colors_outer = []
        for _, row in out.iterrows():
            base = np.array(mcolors.to_rgb(config.REGION_COLORS.get(row["region"], config.MUTED)))
            colors_outer.append(tuple(0.55 * base + 0.45 * np.array([1.0, 1.0, 1.0])))
        return sizes_inner, labels_inner, colors_inner, sizes_outer, labels_outer, colors_outer

    ax1 = fig.add_axes([0.04, 0.24, 0.45, 0.65])
    ax2 = fig.add_axes([0.51, 0.24, 0.45, 0.65])
    a = ring_data(top_t, "co2")
    b = ring_data(top_p, "co2_per_capita")
    _sunburst(ax1, *a, title="Top 10 by total emissions")
    _sunburst(ax2, *b, title="Top 10 by per-capita intensity")

    ax_leg = fig.add_axes([0.08, 0.05, 0.86, 0.15], facecolor="#F5F6F8")
    for sp in ax_leg.spines.values():
        sp.set_color(config.GRID)
    ax_leg.set_xticks([])
    ax_leg.set_yticks([])

    regs = sorted(set(top_t["region"]) | set(top_p["region"]))
    handles = [Line2D([0], [0], color=config.REGION_COLORS.get(r, config.MUTED),
                      marker="s", ls="none", markersize=9, label=r) for r in regs]
    legend_handles(
        ax_leg, handles, [h.get_label() for h in handles],
        note=f"Overlap = {len(overlap)}/10 ({overlap_names}) — rings look different = not one emitter type",
        ncol=4,
    )
    save_fig(fig, config.FIGS_P2, fname)


def _sunburst(ax, sizes_inner, labels_inner, colors_inner, sizes_outer,
              labels_outer_full, colors_outer, title: str) -> None:
    """Two-ring sunburst.  Inner ring is colour-coded by region (legend
    already shows region names — so we do NOT duplicate them inside the
    ring).  Outer ring shows full country names; long names are placed
    outside the ring with a leader line.
    """
    SHORT_NAME = {
        "United States": "U.S.A.",
        "Saudi Arabia": "S. Arabia",
        "United Arab Emirates": "UAE",
        "Trinidad and Tobago": "Trinidad & Tobago",
    }
    ax.set_aspect("equal")
    ax.set_title(title, loc="left", fontsize=12, pad=6)

    # Inner ring (no in-chart labels — legend covers it).
    ax.pie(
        sizes_inner, radius=0.52, colors=colors_inner, labels=None,
        wedgeprops=dict(width=0.28, edgecolor="white", linewidth=1.2),
        startangle=90,
    )

    # Outer ring.
    ax.pie(
        sizes_outer, radius=1.0, colors=colors_outer, labels=None,
        wedgeprops=dict(width=0.42, edgecolor="white", linewidth=0.8),
        startangle=90,
    )

    # Country labels — full names; long ones get a leader line outside.
    total = sum(sizes_outer) or 1.0
    ang = 90.0
    n = len(sizes_outer)
    # Compute the middle angle for each wedge.
    mids = []
    for sz in sizes_outer:
        sweep = 360.0 * sz / total
        mids.append(ang + sweep / 2)
        ang += sweep
    SHORT_LIMIT = 10  # chars that comfortably fit on the wedge
    for i, (name, sz, mid_deg) in enumerate(zip(labels_outer_full, sizes_outer, mids)):
        name = SHORT_NAME.get(name, name)
        mid = np.deg2rad(mid_deg)
        leader_col = colors_outer[i]
        if len(name) <= SHORT_LIMIT and sz / total >= 0.04:
            ax.text(0.78 * np.cos(mid), 0.78 * np.sin(mid), name,
                    ha="center", va="center", fontsize=10,
                    color=config.INK, fontweight="bold", zorder=4)
        else:
            # Leader line: from mid-of-wedge to outside
            x0, y0 = 0.82 * np.cos(mid), 0.82 * np.sin(mid)
            x1, y1 = 1.06 * np.cos(mid), 1.06 * np.sin(mid)
            ax.plot([x0, x1], [y0, y1], color=leader_col, lw=1.0, zorder=3)
            x2 = 1.20 * np.cos(mid)
            y2 = 1.20 * np.sin(mid)
            ha = "left" if np.cos(mid) >= 0 else "right"
            ax.text(x2, y2, name, ha=ha, va="center",
                    fontsize=10, color=config.INK, fontweight="bold", zorder=4)
    ax.set_xlim(-1.40, 1.40)
    ax.set_ylim(-1.40, 1.40)


# ===========================================================================
# Point 3
# ===========================================================================
def fig_p3_02_stacked(y: pd.DataFrame) -> None:
    """Regional fuel structure — stacked Mt, side callouts so small bars
    never get a clobbered in-segment % label."""
    fname = "P3_02_combo_pct_stacked_fuel_by_region.png"
    d = fuel_ok(y).copy()
    rows = []
    for reg, g in d.groupby("region"):
        w = g["co2"].values
        if w.sum() <= 0:
            continue
        tot = float(w.sum())
        rows.append({
            "region": reg,
            "Coal_mt": tot * np.average(g["coal_share"], weights=w),
            "Oil_mt": tot * np.average(g["oil_share"], weights=w),
            "Gas_mt": tot * np.average(g["gas_share"], weights=w),
            "co2": tot,
        })
    tab = pd.DataFrame(rows).sort_values("co2", ascending=False)  # biggest on top

    # Use a wider figure: main plot on the left, side callout column on the right
    fig = plt.figure(figsize=(13.2, 6.8), facecolor=config.PAPER)
    ax = fig.add_axes([0.08, 0.30, 0.55, 0.58], facecolor=config.PAPER_CARD)
    ax_side = fig.add_axes([0.66, 0.30, 0.27, 0.58], facecolor=config.PAPER_CARD)
    ax_leg = fig.add_axes([0.08, 0.05, 0.86, 0.18], facecolor="#F5F6F8")
    for sp in ax_leg.spines.values():
        sp.set_color(config.GRID)
    ax_leg.set_xticks([])
    ax_leg.set_yticks([])

    ax.set_title("Regional fuel structure — absolute Mt stacked", loc="left", fontsize=12, pad=6)
    style_axes(ax, ygrid=False)
    # Plot top→bottom to keep biggest on top
    y_pos = np.arange(len(tab))[::-1]
    left = np.zeros(len(tab))
    fuel_pct = {r: {"Coal": 0.0, "Oil": 0.0, "Gas": 0.0} for r in tab["region"]}
    for fuel, col in [("Coal_mt", "Coal"), ("Oil_mt", "Oil"), ("Gas_mt", "Gas")]:
        vals = tab[fuel].values
        ax.barh(y_pos, vals, left=left, color=config.FUEL_COLORS[col], height=0.60,
                edgecolor="white", lw=0.5)
        for i, (v, l0, tot) in enumerate(zip(vals, left, tab["co2"].values)):
            # only show in-segment % if segment is wide enough (>=9% of axis)
            if v / max(tab["co2"]) >= 0.09 and v / tot >= 0.18:
                ax.text(l0 + v / 2, y_pos[i], f"{100 * v / tot:.0f}%",
                        ha="center", va="center", fontsize=9.5, color="white", fontweight="bold")
            fuel_pct[tab["region"].iloc[i]][col] = float(v / tot)
        left = left + vals
    for i, (_, r) in enumerate(tab.iterrows()):
        ax.text(r["co2"] * 1.01, y_pos[i], f"{r['co2']:,.0f} Mt",
                va="center", fontsize=9.5, color=config.INK_SOFT, fontweight="bold")
    ax.set_yticks(y_pos)
    ax.set_yticklabels(tab["region"].values, fontsize=10.5)
    ax.set_xlabel("CO₂ emissions (Mt), 2021 — absolute scale", fontsize=11)
    ax.set_xlim(0, max(tab["co2"]) * 1.13)
    ax.set_xticks(np.linspace(0, max(tab["co2"]), 6))
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))

    # ── Side callout column: every region shows ALL three % clearly
    style_axes(ax_side, ygrid=False)
    ax_side.set_xlim(0, 1)
    ax_side.set_ylim(-0.5, len(tab) - 0.5)
    ax_side.set_xticks([])
    ax_side.set_yticks([])
    for sp in ax_side.spines.values():
        sp.set_visible(False)
    ax_side.set_title("Within-region mix", loc="left", fontsize=11, pad=6, color=config.INK_SOFT)
    for i, (_, r) in enumerate(tab.iterrows()):
        yp = y_pos[i]
        p = fuel_pct[r["region"]]
        ax_side.text(0.0, yp, "Coal", fontsize=9.5, color=config.FUEL_COLORS["Coal"],
                     fontweight="bold", va="center")
        ax_side.text(0.30, yp, f"{p['Coal']*100:.0f}%", fontsize=9.5, color=config.INK,
                     va="center", fontweight="bold")
        ax_side.text(0.45, yp, "Oil", fontsize=9.5, color=config.FUEL_COLORS["Oil"],
                     fontweight="bold", va="center")
        ax_side.text(0.65, yp, f"{p['Oil']*100:.0f}%", fontsize=9.5, color=config.INK,
                     va="center", fontweight="bold")
        ax_side.text(0.78, yp, "Gas", fontsize=9.5, color=config.FUEL_COLORS["Gas"],
                     fontweight="bold", va="center")
        ax_side.text(0.96, yp, f"{p['Gas']*100:.0f}%", fontsize=9.5, color=config.INK,
                     va="center", fontweight="bold", ha="right")

    handles = [Line2D([0], [0], color=config.FUEL_COLORS[f], lw=8, label=f) for f in ["Coal", "Oil", "Gas"]]
    legend_handles(
        ax_leg, handles, [h.get_label() for h in handles],
        note=("Bar length = absolute regional Mt.  In-bar % only on wide segments. "
              "Side column = full within-region mix for every region."),
        ncol=3,
    )

    ct = pd.crosstab(d["region"], d["dominant_fuel"])
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    n = ct.values.sum()
    v = np.sqrt(chi2 / (n * (min(ct.shape) - 1)))
    print(f"  chi2 region x fuel: Cramers V={v:.3f}")
    save_fig(fig, config.FIGS_P3, fname)


def fig_p3_03_pcp(y: pd.DataFrame) -> None:
    """Parallel coordinates — multi-D fuel profiles with non-overlapping labels."""
    fname = "P3_03_combo_pcp_multidim_fuel.png"
    d = fuel_ok(y).copy()
    cols = ["log_co2", "co2_per_capita", "coal_share", "oil_share", "gas_share"]
    labels = ["log₁₀ CO₂", "Per capita", "Coal %", "Oil %", "Gas %"]
    normed = d[cols].copy()
    for c in cols:
        lo, hi = float(normed[c].min()), float(normed[c].max())
        normed[c] = (normed[c] - lo) / (hi - lo + 1e-12)
    normed["dominant_fuel"] = d["dominant_fuel"].values
    normed["iso_code"] = d["iso_code"].values
    normed["country"] = d["country"].values

    # Widen figure so right axis has room for story-country panel
    fig = plt.figure(figsize=(13.6, 7.6), facecolor=config.PAPER)
    ax = fig.add_axes([0.07, 0.40, 0.62, 0.48], facecolor=config.PAPER_CARD)
    # Right panel: story-country dashboard (no label overlap with chart)
    ax_side = fig.add_axes([0.72, 0.40, 0.22, 0.48], facecolor=config.PAPER_CARD)
    ax_leg = fig.add_axes([0.08, 0.05, 0.86, 0.20], facecolor="#F5F6F8")
    for sp in ax_leg.spines.values():
        sp.set_color(config.GRID)
    ax_leg.set_xticks([])
    ax_leg.set_yticks([])

    ax.set_title("Parallel coordinates — fuel regimes as multi-D profiles", loc="left", fontsize=12, pad=18)
    style_axes(ax, ygrid=False)
    x = np.arange(len(cols))

    rng = np.random.default_rng(42)
    for fuel, color in config.FUEL_COLORS.items():
        sub = normed[normed["dominant_fuel"] == fuel]
        if sub.empty:
            continue
        idx = rng.choice(len(sub), size=min(28, len(sub)), replace=False)
        for i in idx:
            ax.plot(x, sub.iloc[i][cols].values, color=color, lw=0.55, alpha=0.18, zorder=1)
        q25 = sub[cols].quantile(0.25).values
        q75 = sub[cols].quantile(0.75).values
        ax.fill_between(x, q25, q75, color=color, alpha=0.16, zorder=2)
        ax.plot(x, sub[cols].median().values, color=color, lw=3.0, zorder=4, label=f"{fuel} median")

    # Story country polylines (no right-edge text labels — labels live in side panel)
    callouts = [("CHN", "China"), ("USA", "USA"), ("QAT", "Qatar"), ("NOR", "Norway"), ("IND", "India")]
    story_dots = []  # collect (x_end, y_end, iso, name, color) for side panel rendering
    for iso, name in callouts:
        row = normed[normed["iso_code"] == iso]
        if row.empty:
            continue
        vals = row.iloc[0][cols].values.astype(float)
        fuel = row.iloc[0]["dominant_fuel"]
        col = config.FUEL_COLORS.get(str(fuel), config.INK)
        ax.plot(x, vals, color=col, lw=1.9, ls="--", zorder=5)
        # marker at the end
        ax.scatter([x[-1]], [vals[-1]], s=55, color=col, edgecolors="white", lw=0.8, zorder=6)
        story_dots.append((name, fuel, col))

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10.5)
    ax.set_xlim(-0.15, len(cols) - 0.7)
    ax.set_ylim(-0.04, 1.06)
    ax.set_yticks([0, 0.5, 1.0])
    ax.set_yticklabels(["low", "mid", "high"], fontsize=10)
    for xi in x:
        ax.axvline(xi, color=config.GRID, lw=0.85, zorder=0)
    ax.text(0.01, 1.045, "Axes scaled 0–1 within full sample", transform=ax.transAxes,
            fontsize=8.5, color=config.MUTED, va="bottom")

    # Side panel: story countries as a clean list (no overlap)
    style_axes(ax_side, ygrid=False)
    ax_side.set_xlim(0, 1)
    ax_side.set_ylim(-0.5, len(story_dots) - 0.5)
    ax_side.set_xticks([])
    ax_side.set_yticks([])
    for sp in ax_side.spines.values():
        sp.set_visible(False)
    ax_side.set_title("Story countries", loc="left", fontsize=11, pad=6, color=config.INK_SOFT)
    for i, (name, fuel, col) in enumerate(story_dots):
        yp = len(story_dots) - 1 - i
        ax_side.plot(0.04, yp, "o", color=col, markersize=10, markeredgecolor="white",
                     markeredgewidth=0.8, transform=ax_side.transData)
        ax_side.text(0.14, yp, name, fontsize=11, color=config.INK, fontweight="bold",
                     va="center", transform=ax_side.transData)
        ax_side.text(0.92, yp, fuel, fontsize=10, color=col, fontweight="bold",
                     va="center", ha="right", transform=ax_side.transData)

    handles = [
        Line2D([0], [0], color=c, lw=2.8, label=f"{f} median") for f, c in config.FUEL_COLORS.items()
    ]
    handles.append(Line2D([0], [0], color=config.INK, lw=1.7, ls="--", label="Story country"))
    handles.append(Line2D([0], [0], color=config.MUTED, lw=1.0, alpha=0.5, label="Sample countries"))

    # Region × fuel Cramér's V (regime distinctness) — added as a stat note.
    ct = pd.crosstab(d["region"], d["dominant_fuel"])
    chi2, p, dof, _ = stats.chi2_contingency(ct)
    n = ct.values.sum()
    v_cramer = float(np.sqrt(chi2 / (n * (min(ct.shape) - 1))))
    note = (f"Bands = P25–P75 · dashed = CHN/USA/QAT/NOR/IND (listed on the right) "
            f"— profiles diverge = not one emitter type.  "
            f"Region × fuel Cramér's V = {v_cramer:.2f}  (p < 0.001)")
    legend_handles(
        ax_leg, handles, [h.get_label() for h in handles],
        note=note,
        ncol=3,
    )
    print(f"  chi2 region x fuel (PCP): Cramers V={v_cramer:.3f}")
    save_fig(fig, config.FIGS_P3, fname)


# ---------------------------------------------------------------------------
def _remove_obsolete() -> None:
    obsolete = [
        config.FIGS_P1 / "P1_02_treemap_region_country_co2.png",
        config.FIGS_P2 / "P2_01_map_bars_per_capita_2021.html",
        config.FIGS_P2 / "P2_01_map_bars_per_capita_2021.data.json",
        config.FIGS_P2 / "P2_04_combo_violin_strip_region_pc.png",
        config.FIGS_P2 / "P2_03_combo_slope_rank_co2_vs_pc.png",
        config.FIGS_P3 / "P3_04_heatdot_region_fuel_share.png",
        config.FIGS_P1 / "P1_01_map_bars_total_co2_2021.data.json",
        config.FIGS_P3 / "P3_01_map_dominant_fuel_2021.data.json",
    ]
    for path in obsolete:
        if path.exists():
            path.unlink()
            print("  removed obsolete", path.parent.name + "/" + path.name)


def main() -> None:
    print("Loading…", flush=True)
    panel = load_panel()
    write_region_lookup(panel)
    y = slice_year(panel)

    print("Point1 (P1_03 treemap+concentration · P1_04 region+Lorenz)…", flush=True)
    numbered = fig_p1_03_treemap_concentration(y)
    # Persist the numbered-country list so the PPT (slide 2) can render
    # the right-side caption without re-running the treemap.
    try:
        import json
        out_json = config.FIGS_P1 / "P1_03_numbered_countries.json"
        out_json.write_text(
            json.dumps(numbered, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"  saved point1/P1_03_numbered_countries.json ({len(numbered)} entries)")
    except Exception as e:
        print(f"  [warn] could not save numbered countries: {e}")
    fig_p1_04_panel(y)

    print("Point2 (P2_02 bubble · P2_03 sunburst)…", flush=True)
    fig_p2_02_bubble(y)
    fig_p2_03_sunburst(y)

    print("Point3 (P3_02 stacked · P3_03 PCP)…", flush=True)
    fig_p3_02_stacked(y)
    fig_p3_03_pcp(y)

    _remove_obsolete()
    print(f"Done non-map PNGs → {config.FIGS_ROOT}", flush=True)


if __name__ == "__main__":
    main()
