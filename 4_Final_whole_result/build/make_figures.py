# -*- coding: utf-8 -*-
"""Generate every figure used by the CA6002 Group 30 final deck.

Style contract (kept identical across all figures and the slides themselves):
  Times New Roman, white background, low-saturation palette
    rapid-growth pathway (24)  -> muted amber   #BE7F4E
    plateau/slowdown (169)     -> muted steel   #4F6E96
    boundary edge              -> ink           #2B3138
    accent                     -> deep maroon   #7C2530

Figures
  fig_cover_art          decorative but data-driven cover graphic
  fig_k_selection        K = 2-8 validity metrics
  fig_pca_pathways       PCA projection of the two pathways
  fig_stability_gmm      resampling ARI + GMM soft membership
  fig_pathway_profiles   aggregate decomposition + per-capita trajectories
  fig_burden_growth      current burden x recent momentum scatter
  fig_pathway_map        K = 2 labels on the world map
  fig_pathway_centroids  CO2-weighted centre of gravity per pathway, 1992-2021
                         (reuses the spatial team's centroid method)

Run with the project .venv python (needs geopandas for the maps).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

ROOT = Path(r"C:\Users\user\Desktop\Overall_Data Visual Assignment")
OUT = ROOT / "4_Final_whole_result" / "build" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

LAB = ROOT / r"0_data_数据集和预处理过程/K-means_K=2_分组标签好的数据集/country_features_with_clusters.csv"
PANEL = ROOT / r"0_data_数据集和预处理过程/Final_data/co2_panel_1992_2021.csv"
KMET = ROOT / r"code/K-means/outputs/k_selection_metrics.csv"
STAB = ROOT / r"code/K-means/outputs/stability_results.csv"
GMM = ROOT / r"code/K-means/outputs/gmm_membership_probabilities.csv"
GEO = ROOT / r"code/瑞庭_绘图/aux/ne_110m_admin0.geojson"

C_RAPID = "#BE7F4E"
C_PLAT = "#4F6E96"
C_RAPID_L = "#E4CDB7"
C_PLAT_L = "#BFCBDB"
C_EDGE = "#252B30"
C_RED = "#2F5248"          # aggregate / accent series, matches the deck chrome
C_MUTED = "#6E7672"
C_GREY = "#C6CFC7"
C_LAND = "#E7EBE6"

plt.rcParams.update({
    "font.family": "Times New Roman",
    "font.size": 13,
    "axes.edgecolor": "#8A9490",
    "axes.linewidth": 0.9,
    "axes.titlesize": 16,
    "axes.labelsize": 14,
    "xtick.labelsize": 13,
    "ytick.labelsize": 13,
    "legend.fontsize": 13,
    "legend.facecolor": "white",
    "legend.edgecolor": "#D5DED6",
    "legend.framealpha": 0.85,
    "figure.facecolor": "none",
    "axes.facecolor": "none",
    "axes.unicode_minus": False,
})

lab = pd.read_csv(LAB)
gmm = pd.read_csv(GMM).set_index("iso_code")
lab = lab.set_index("iso_code").join(gmm[["gmm_max_probability"]])
panel = pd.read_csv(PANEL)

RAPID, PLAT = 0, 1
NAME = {RAPID: "Rapid-growth pathway (24)", PLAT: "Plateauing / slowdown pathway (169)"}
COL = {RAPID: C_RAPID, PLAT: C_PLAT}


def save(fig, name):
    # transparent so every chart sits directly on the deck's pale-green wash
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", transparent=True)
    plt.close(fig)
    print("  saved", name, f"{(OUT / (name + '.png')).stat().st_size:,} B")


# ---------------------------------------------------------------- K selection
km = pd.read_csv(KMET)
# figure sizes match the box each figure occupies on its slide, so the type
# inside the charts prints at the same size as the type on the slides
fig, axes = plt.subplots(1, 3, figsize=(9.5, 3.0), dpi=220)
panels = [
    ("silhouette", "Silhouette  (higher = better)"),
    ("davies_bouldin", "Davies-Bouldin  (lower = better)"),
    ("calinski_harabasz", "Calinski-Harabasz  (higher = better)"),
]
for ax, (col, title) in zip(axes, panels):
    ax.plot(km["k"], km[col], "-o", color=C_PLAT, lw=2, ms=7, zorder=2)
    ax.axvline(2, color=C_RED, ls="--", lw=1.6, zorder=1)
    v2 = km.loc[km.k == 2, col].iloc[0]
    ax.plot([2], [v2], "o", color=C_RAPID, ms=11, mec=C_EDGE, mew=1.2, zorder=3)
    off = (14, 10) if col == "davies_bouldin" else (14, -20)
    ax.annotate(f"K=2: {v2:.1f}" if col == "calinski_harabasz" else f"K=2: {v2:.3f}",
                (2, v2), textcoords="offset points", xytext=off,
                fontsize=13, fontweight="bold", color=C_RED)
    ax.set_title(title, fontsize=14)
    ax.set_xlabel("Number of clusters (K)")
    ax.set_xticks(range(2, 9))
    ax.grid(alpha=0.3, lw=0.6)
    ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(w_pad=2.2)
save(fig, "fig_k_selection")

# ---------------------------------------------------------------- PCA projection
fig, ax = plt.subplots(figsize=(8.8, 5.6), dpi=200)
for c in (PLAT, RAPID):
    sub = lab[lab.cluster == c]
    nb = sub[sub["gmm_max_probability"] >= 0.70]
    b = sub[sub["gmm_max_probability"] < 0.70]
    ax.scatter(nb["PC1"], nb["PC2"], s=48, color=COL[c], alpha=0.88,
               edgecolor="white", lw=0.5, label=NAME[c], zorder=3)
    if len(b):
        ax.scatter(b["PC1"], b["PC2"], s=66, facecolor="none", edgecolor=C_EDGE,
                   lw=1.6, zorder=4)
ax.scatter([], [], s=66, facecolor="none", edgecolor=C_EDGE, lw=1.6,
           label="Boundary countries (low confidence)")
ax.axhline(0, color=C_GREY, lw=0.9, zorder=1)
ax.axvline(0, color=C_GREY, lw=0.9, zorder=1)
ax.set_xlabel("PC1  (56.1% of variance)")
ax.set_ylabel("PC2  (14.7% of variance)")
ax.grid(alpha=0.25, lw=0.6)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(loc="upper right", frameon=True, framealpha=0.95, edgecolor="#CCCCCC")
fig.tight_layout()
save(fig, "fig_pca_pathways")

# ---------------------------------------------------------------- stability + GMM
stab = pd.read_csv(STAB)
fig, axes = plt.subplots(1, 2, figsize=(8.9, 3.55), dpi=220,
                         gridspec_kw={"width_ratios": [1, 1.35]})
ax = axes[0]
ax.hist(stab["adjusted_rand_index"], bins=np.linspace(0.75, 1.005, 24),
        color=C_PLAT, edgecolor="white", lw=0.8)
med = stab["adjusted_rand_index"].median()
ax.axvline(med, color=C_RED, ls="--", lw=1.8)
ax.text(med - 0.008, ax.get_ylim()[1] * 0.93, f"median ARI = {med:.3f}",
        ha="right", fontsize=13, fontweight="bold", color=C_RED)
ax.set_xlabel("Adjusted Rand Index vs. full-sample fit")
ax.set_ylabel("Repeats (out of 100)")
ax.set_title("100 x 80% country subsamples", fontsize=14)
ax.grid(alpha=0.25, lw=0.6)
ax.spines[["top", "right"]].set_visible(False)

ax = axes[1]
g = lab.sort_values("gmm_max_probability")["gmm_max_probability"].reset_index(drop=True)
colors = [C_RAPID if v < 0.70 else C_PLAT for v in g]
ax.scatter(np.arange(1, len(g) + 1), g, s=16, c=colors, zorder=3)
ax.axhline(0.70, color=C_RED, ls="--", lw=1.6)
ax.text(len(g) * 0.98, 0.695, "0.70 boundary threshold", ha="right", va="top",
        fontsize=12, color=C_RED, fontweight="bold")
ax.set_xlabel("193 modelled countries, sorted by confidence")
ax.set_ylabel("Max membership probability")
ax.set_ylim(0.45, 1.02)
ax.set_title("Soft membership: 10 countries below 0.70", fontsize=14)
ax.grid(alpha=0.25, lw=0.6)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(w_pad=2.5)
save(fig, "fig_stability_gmm")

# ---------------------------------------------------------------- pathway profiles
# Panel A: the rising sample total, decomposed into the two pathways.
# Panel B: median per-capita trajectory of each pathway, with median peak years.
pl = panel.merge(lab[["cluster"]], left_on="iso_code", right_index=True, how="inner")
agg = pl.pivot_table(index="year", columns="cluster", values="co2", aggfunc="sum")
agg = agg[[RAPID, PLAT]] / 1000.0  # Mt -> Gt
med_pc = pl.pivot_table(index="year", columns="cluster",
                        values="co2_per_capita", aggfunc="median")

fig, axes = plt.subplots(1, 2, figsize=(12.9, 3.15), dpi=220,
                         gridspec_kw={"width_ratios": [1.12, 1]})
ax = axes[0]
ax.stackplot(agg.index, agg[PLAT], agg[RAPID],
             colors=[C_PLAT_L, C_RAPID_L], edgecolor="white", lw=0.6,
             labels=[NAME[PLAT], NAME[RAPID]])
total = agg.sum(axis=1)
ax.plot(agg.index, total, color=C_EDGE, lw=1.8, zorder=5,
        label="Sample-wide total")
ax.annotate(f"{total.iloc[0]:.1f} Gt", (agg.index[0], total.iloc[0]),
            textcoords="offset points", xytext=(6, 8), fontsize=12.5,
            fontweight="bold", color=C_EDGE)
ax.annotate(f"{total.iloc[-1]:.1f} Gt  (+{(total.iloc[-1] / total.iloc[0] - 1) * 100:.1f}%)",
            (agg.index[-1], total.iloc[-1]), textcoords="offset points",
            xytext=(-16, 10), ha="right", fontsize=12.5, fontweight="bold", color=C_RED)
ax.set_xlim(1992, 2021)
ax.set_ylim(0, total.max() * 1.16)
ax.set_xlabel("Year")
ax.set_ylabel("Fossil CO2, 193 countries (Gt)")
ax.set_title("The rising total, split by pathway", fontsize=14)
ax.grid(alpha=0.22, lw=0.6)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(loc="lower right", frameon=True, framealpha=0.95, edgecolor="#CCCCCC")
share = agg.loc[2017:2021].sum() / agg.loc[2017:2021].sum().sum() * 100
ax.text(1993, total.max() * 1.08,
        f"2017-2021 share of emissions\nplateauing {share[PLAT]:.1f}%  ·  rapid-growth {share[RAPID]:.1f}%",
        fontsize=12.5, color=C_PLAT, fontweight="bold", va="center")

ax = axes[1]
for c in (PLAT, RAPID):
    ax.plot(med_pc.index, med_pc[c], color=COL[c], lw=2.6, label=NAME[c])
    pk = int(lab.loc[lab.cluster == c, "peak_timing"].median() * 29 + 1992) \
        if lab["peak_timing"].max() <= 1 else int(lab.loc[lab.cluster == c, "peak_timing"].median())
    if med_pc.index.min() <= pk <= med_pc.index.max():
        ax.plot([pk], [med_pc[c].loc[pk]], "o", ms=11, color="white",
                mec=COL[c], mew=2.6, zorder=5)
        # the plateauing marker sits near the top of the panel, so its label goes
        # below the marker to stay clear of the panel title
        below = c == PLAT
        ax.annotate(f"median peak {pk}", (pk, med_pc[c].loc[pk]),
                    textcoords="offset points", xytext=(0, -22 if below else 14),
                    ha="center", va="top" if below else "bottom",
                    fontsize=11.5, fontweight="bold", color=COL[c])
ax.set_xlim(1992, 2021)
ax.set_xlabel("Year")
ax.set_ylabel("Median CO2 per person (t)")
ax.set_title("Two different transition shapes", fontsize=14)
ax.grid(alpha=0.22, lw=0.6)
ax.spines[["top", "right"]].set_visible(False)
ax.legend(loc="center left", frameon=True, framealpha=0.95, edgecolor="#CCCCCC")
fig.tight_layout(w_pad=2.4)
save(fig, "fig_pathway_profiles")
print("  2017-2021 shares:", share.round(2).to_dict())

# ---------------------------------------------------------------- burden x growth
recent = (panel[(panel.year >= 2017) & (panel.year <= 2021)]
          .groupby("iso_code")["co2"].mean().rename("avg_co2"))
d = lab.join(recent).dropna(subset=["avg_co2"])
d["growth_pct"] = d["recent_log_slope"] * 100

fig, ax = plt.subplots(figsize=(9.3, 5.5), dpi=220)
for c in (PLAT, RAPID):
    sub = d[d.cluster == c]
    nb = sub[sub["gmm_max_probability"] >= 0.70]
    b = sub[sub["gmm_max_probability"] < 0.70]
    ax.scatter(nb["avg_co2"], nb["growth_pct"], s=44, color=COL[c], alpha=0.82,
               edgecolor="white", lw=0.5, label=NAME[c], zorder=3)
    if len(b):
        ax.scatter(b["avg_co2"], b["growth_pct"], s=62, facecolor="none",
                   edgecolor=C_EDGE, lw=1.5, zorder=4)
ax.scatter([], [], s=62, facecolor="none", edgecolor=C_EDGE, lw=1.5,
           label="Boundary countries")
ax.set_xscale("log")
ax.axhline(0, color=C_MUTED, lw=1.0, ls="--", zorder=1)
ax.axvline(100, color=C_GREY, lw=1.0, ls=":", zorder=1)
ax.set_xlabel("Average annual fossil CO2 2017-2021 (Mt, log scale)")
ax.set_ylabel("Recent trend 2012-2021 (% per year)")
ax.grid(alpha=0.22, lw=0.6, which="both")
ax.spines[["top", "right"]].set_visible(False)
ax.legend(loc="lower left", frameon=True, framealpha=0.95, edgecolor="#CCCCCC")
ax.text(105, ax.get_ylim()[1] * 0.97, "high current burden", fontsize=12,
        color=C_MUTED, va="top")
label_spec = {
    "CHN": (10, 4), "USA": (10, -6), "IND": (12, -12), "RUS": (-58, -18),
    "JPN": (10, -6), "VNM": (8, 6), "BGD": (8, 4), "KOR": (-82, 9),
    "IRN": (8, 10), "IDN": (-72, 4), "DEU": (-58, -14),
}
for iso, (dx, dy) in label_spec.items():
    if iso in d.index:
        r = d.loc[iso]
        ax.annotate(r["country"], (r["avg_co2"], r["growth_pct"]),
                    textcoords="offset points", xytext=(dx, dy), fontsize=12,
                    color=C_EDGE, fontweight="bold")
fig.tight_layout()
save(fig, "fig_burden_growth")

# ---------------------------------------------------------------- maps
import geopandas as gpd

world = gpd.read_file(GEO)
world = world[world["iso"] != "ATA"]
w = world.merge(lab[["cluster", "gmm_max_probability"]], left_on="iso",
                right_index=True, how="left")

# Both storytelling maps share the spatial team's pseudo-3D "slab" treatment: the
# world is sheared slightly and drawn three times at descending offsets, which
# gives the map physical thickness instead of a flat fill.
SLAB_DEEP, SLAB_MID, SLAB_TOP = "#6E7C80", "#8E9C9F", "#CBD5D2"
SLAB_EDGE = "#F1F5F1"
Y_SCALE, SHEAR, LIFT = 1.0, 0.06, 4.0


def slab(ax, gdf, offset_y, face, edge, lw, alpha, z):
    for geom in gdf.geometry:
        if geom is None:
            continue
        parts = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
        for part in parts:
            if part.geom_type != "Polygon":
                continue
            c = np.asarray(part.exterior.coords)
            px = c[:, 0] + SHEAR * c[:, 1]
            py = Y_SCALE * c[:, 1] + offset_y
            ax.fill(px, py, facecolor=face, edgecolor=edge, linewidth=lw,
                    alpha=alpha, zorder=z)


fig = plt.figure(figsize=(10.0, 4.85), dpi=220)
ax = fig.add_axes([0.004, 0.01, 0.992, 0.98])
ax.set_xlim(-186, 192)
ax.set_ylim(-62, 90)
ax.set_aspect("equal")
slab(ax, world, -4.6, SLAB_DEEP, SLAB_DEEP, 0.18, 0.92, 1)
slab(ax, world, -2.3, SLAB_MID, SLAB_MID, 0.18, 0.96, 2)
slab(ax, w[w["cluster"].isna()], 0.0, C_LAND, SLAB_EDGE, 0.28, 1.0, 3)
slab(ax, w[w["cluster"] == PLAT], 0.0, C_PLAT, SLAB_EDGE, 0.28, 1.0, 3)
slab(ax, w[w["cluster"] == RAPID], 0.0, C_RAPID, SLAB_EDGE, 0.32, 1.0, 4)
for geom in w[w["gmm_max_probability"] < 0.70].geometry:
    if geom is None:
        continue
    parts = geom.geoms if geom.geom_type == "MultiPolygon" else [geom]
    for part in parts:
        if part.geom_type != "Polygon":
            continue
        c = np.asarray(part.exterior.coords)
        ax.plot(c[:, 0] + SHEAR * c[:, 1], Y_SCALE * c[:, 1], color=C_EDGE,
                lw=1.4, zorder=5)
handles = [
    Patch(facecolor=C_RAPID, edgecolor="white", label="Rapid-growth pathway (24)"),
    Patch(facecolor=C_PLAT, edgecolor="white", label="Plateauing / slowdown pathway (169)"),
    Line2D([0], [0], color=C_EDGE, lw=1.7, label="Boundary country outline (10)"),
    Patch(facecolor=C_LAND, edgecolor="white",
          label="Not modelled (micro states / incomplete history)"),
]
leg = ax.legend(handles=handles, loc="lower left", frameon=True, framealpha=0.95,
                edgecolor=C_RED, facecolor="#F7FAF6")
leg.get_frame().set_linewidth(0.8)
leg.set_zorder(10)
ax.set_axis_off()
save(fig, "fig_pathway_map")
print("  map matched:", w["cluster"].notna().sum(), "of", len(lab))

# ------------------------------------------------- centre of gravity per pathway
# Method reused from the spatial team's trajectory figure
# (code/瑞庭_绘图/scripts/_render_p3_trajectory_revised.py): each country sits at
# the representative point of its polygon and years are averaged with CO2 weights.
# Here the tracks are the two validated pathways instead of continents.
pts = (world.set_index("iso")["geometry"]
       .apply(lambda g: g.representative_point())
       .apply(lambda p: (p.x, p.y)).to_dict())
pl2 = pl.copy()
pl2["lng"] = pl2["iso_code"].map(lambda i: pts.get(i, (np.nan, np.nan))[0])
pl2["lat"] = pl2["iso_code"].map(lambda i: pts.get(i, (np.nan, np.nan))[1])
YEARS = [1992, 2000, 2007, 2014, 2021]

tracks = {"All modelled countries": None, NAME[PLAT]: PLAT, NAME[RAPID]: RAPID}
rows = []
for tname, cl in tracks.items():
    for yr in YEARS:
        sub = pl2[pl2.year == yr]
        if cl is not None:
            sub = sub[sub.cluster == cl]
        geo = sub.dropna(subset=["lng", "lat"])
        wgt = geo["co2"].clip(lower=0.01).to_numpy()
        rows.append({"track": tname, "year": yr,
                     "lng": float(np.average(geo["lng"], weights=wgt)),
                     "lat": float(np.average(geo["lat"], weights=wgt)),
                     "total_mt": float(sub["co2"].sum())})
traj = pd.DataFrame(rows)
base = traj[traj.year == YEARS[0]].set_index("track")
traj["total_change"] = traj.apply(
    lambda r: (r["total_mt"] / base.loc[r["track"], "total_mt"] - 1) * 100, axis=1)

TCOL = {"All modelled countries": C_MUTED, NAME[PLAT]: C_PLAT, NAME[RAPID]: C_RAPID}
# No magnification: the real 1992-2021 displacement is already large enough to read.
# Offsets are in map degrees (the label sits next to its 1992 / 2021 circle).
LBL_OFF = {"All modelled countries": (18, -11), NAME[PLAT]: (30, 13),
           NAME[RAPID]: (-2, -15)}
Y0_OFF = {"All modelled countries": (-4, -7), NAME[PLAT]: (-4, 7),
          NAME[RAPID]: (-13, 8)}

# Same slab treatment as the pathway map, with the trajectory drawn above it:
# centroids float over the surface with drop lines and soft shadows, and the
# circles grow with time (the spatial team's pseudo-3D trajectory figure).
fig = plt.figure(figsize=(8.9, 4.3), dpi=220)
ax = fig.add_axes([0.004, 0.01, 0.992, 0.98])
ax.set_xlim(-16, 148)
ax.set_ylim(-16, 66)
ax.set_aspect("equal")
ax.set_axis_off()

slab(ax, world, -4.6, SLAB_DEEP, SLAB_DEEP, 0.18, 0.92, 1)
slab(ax, world, -2.3, SLAB_MID, SLAB_MID, 0.18, 0.96, 2)
slab(ax, world, 0.0, SLAB_TOP, SLAB_EDGE, 0.30, 1.0, 3)
# the two pathways tint the countries they contain, on top of the slab surface
slab(ax, w[w["cluster"] == PLAT], 0.0, C_PLAT_L, SLAB_EDGE, 0.30, 0.95, 4)
slab(ax, w[w["cluster"] == RAPID], 0.0, C_RAPID_L, SLAB_EDGE, 0.30, 0.95, 4)

time_size = dict(zip(YEARS, [150, 300, 520, 820, 1200]))
opacity = dict(zip(YEARS, [0.88, 0.78, 0.68, 0.58, 0.50]))
AGG = "All modelled countries"
for tname in tracks:
    sub = traj[traj.track == tname].sort_values("year").reset_index(drop=True)
    px = sub["lng"].to_numpy() + SHEAR * sub["lat"].to_numpy()
    py = Y_SCALE * sub["lat"].to_numpy() + LIFT
    col = TCOL[tname]
    # the sample-wide track is the reference, so it stays visually subordinate to
    # the two pathways it is decomposed into
    fac, z0 = (0.45, 0) if tname == AGG else (1.0, 3)
    for x0, y0, yr in zip(px, py, sub["year"]):
        ax.plot([x0, x0], [y0 - LIFT, y0], color="#5C6B62", lw=0.75, alpha=0.35,
                zorder=5 + z0)
        ax.scatter([x0], [y0 - 2.0], s=time_size[int(yr)] * fac * 0.70,
                   facecolor="#57685E", edgecolor="none", alpha=0.13, zorder=5 + z0)
    ax.plot(px, py, color=col, lw=2.4 if fac == 1.0 else 1.6, alpha=0.88,
            zorder=6 + z0, ls="-" if fac == 1.0 else (0, (4, 2)))
    for x0, y0, yr in sorted(zip(px, py, sub["year"]), key=lambda t: -t[2]):
        ax.scatter([x0], [y0], s=time_size[int(yr)] * fac, facecolor=col,
                   edgecolor=col, linewidth=2.6 * fac, alpha=opacity[int(yr)],
                   zorder=7 + z0)
    # fixed-length arrow: direction only, because some centroids barely move
    dx, dy = px[-1] - px[0], py[-1] - py[0]
    mag = float(np.hypot(dx, dy))
    if mag > 1e-9:
        ux, uy = dx / mag, dy / mag
        ax.annotate("", xy=(px[-1] - ux * 2 + ux * 15, py[-1] - uy * 2 + uy * 15),
                    xytext=(px[-1] - ux * 2, py[-1] - uy * 2),
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=3.4 * fac,
                                    alpha=0.5, mutation_scale=16, shrinkA=0,
                                    shrinkB=0),
                    zorder=9 + z0)
    ax.text(px[0] + Y0_OFF[tname][0], py[0] + Y0_OFF[tname][1], str(YEARS[0]),
            fontsize=11, fontweight="bold", color=col, ha="center", va="center",
            zorder=10)
    ax.text(px[-1] + LBL_OFF[tname][0], py[-1] + LBL_OFF[tname][1],
            f"{tname.split(' (')[0].upper()}  {YEARS[-1]}",
            fontsize=11.5, fontweight="bold", color=col, ha="center", va="center",
            zorder=10,
            bbox=dict(facecolor="#F7FAF6", alpha=0.95, edgecolor=col,
                      linewidth=0.9, pad=2.4))

# size key: the circles encode time only
key = fig.add_axes([0.022, 0.035, 0.30, 0.135], facecolor="#F7FAF6")
key.set_xlim(0, 1); key.set_ylim(0, 1)
key.set_xticks([]); key.set_yticks([])
for sp in key.spines.values():
    sp.set_color(C_RED); sp.set_linewidth(0.8)
kx = [0.10, 0.26, 0.45, 0.66, 0.88]
key.scatter(kx, [0.62] * 5, s=[60, 110, 180, 270, 380], facecolor="#B7C3BA",
            edgecolor="#8C9A90", linewidth=0.7,
            alpha=[0.85, 0.78, 0.71, 0.63, 0.55])
for x0, yr in zip(kx, YEARS):
    key.text(x0, 0.17, str(yr), fontsize=8, fontweight="bold", color=C_EDGE,
             ha="center", va="center")
key.text(0.5, 0.90, "CIRCLE SIZE = YEAR", fontsize=8, fontweight="bold",
         color=C_MUTED, ha="center", va="center")
save(fig, "fig_pathway_centroids")
print(traj.round(2).to_string())

# --------------------------------------------- small tinted map (closing slide)
fig, ax = plt.subplots(figsize=(7.4, 5.0), dpi=200)
fig.patch.set_alpha(0)
w[w["cluster"].isna()].plot(ax=ax, color="#EDEEF0", edgecolor="white", lw=0.2)
w[w["cluster"] == PLAT].plot(ax=ax, color=C_PLAT_L, edgecolor="white", lw=0.2)
w[w["cluster"] == RAPID].plot(ax=ax, color=C_RAPID_L, edgecolor="white", lw=0.25)
ax.set_axis_off()
ax.set_facecolor("none")
fig.savefig(OUT / "fig_cover_art.png", bbox_inches="tight", transparent=True)
plt.close(fig)
print("  saved fig_cover_art")

print("done ->", OUT)
