"""Presentation-ready static plots for the clustering workflow."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .features import FEATURE_COLUMNS


COLORS = ["#3B4CC0", "#2C7FB8", "#41AB5D", "#F0A202", "#E85D04", "#9D4EDD", "#6C757D", "#D62828"]

FEATURE_LABELS = {
    "log_recent_per_capita": "Current per-capita level (log)",
    "long_term_log_slope": "Long-term trend",
    "recent_log_slope": "Recent trend",
    "slope_acceleration": "Trend acceleration",
    "growth_volatility_mad": "Growth volatility",
    "peak_timing": "Peak timing",
    "post_peak_change": "Post-peak change",
    "recent_coal_share": "Current coal share",
    "recent_gas_share": "Current gas share",
    "coal_share_change": "Coal-share change",
    "gas_share_change": "Gas-share change",
}


def _save(fig: plt.Figure, path: Path) -> None:
    fig.savefig(path, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_k_selection(metrics: pd.DataFrame, selected_k: int, path: Path) -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    specifications = [
        ("silhouette", "Silhouette (higher is better)"),
        ("davies_bouldin", "Davies-Bouldin (lower is better)"),
        ("calinski_harabasz", "Calinski-Harabasz (higher is better)"),
    ]
    for axis, (column, title) in zip(axes, specifications):
        axis.plot(metrics["k"], metrics[column], marker="o", color="#345995")
        axis.axvline(selected_k, color="#D1495B", linestyle="--", linewidth=1.5)
        axis.set_title(title, fontsize=10)
        axis.set_xlabel("Number of clusters (K)")
        axis.grid(alpha=0.2)
    fig.suptitle(f"Model selection supports K = {selected_k}", fontsize=14, fontweight="bold")
    fig.tight_layout()
    _save(fig, path)


def plot_pca_clusters(
    pca_scores: np.ndarray,
    labels: np.ndarray,
    explained_ratio: np.ndarray,
    path: Path,
) -> None:
    x = pca_scores[:, 0]
    y = pca_scores[:, 1] if pca_scores.shape[1] > 1 else np.zeros(len(x))
    fig, axis = plt.subplots(figsize=(8.5, 6))
    for cluster in sorted(np.unique(labels)):
        mask = labels == cluster
        axis.scatter(
            x[mask],
            y[mask],
            s=42,
            alpha=0.78,
            label=f"Cluster {cluster}",
            color=COLORS[cluster % len(COLORS)],
            edgecolor="white",
            linewidth=0.4,
        )
    pc1 = explained_ratio[0] * 100
    pc2 = explained_ratio[1] * 100 if len(explained_ratio) > 1 else 0
    axis.set_xlabel(f"PC1 ({pc1:.1f}% variance)")
    axis.set_ylabel(f"PC2 ({pc2:.1f}% variance)")
    axis.set_title("Countries separate into distinct carbon-transition pathways", fontweight="bold")
    axis.axhline(0, color="#bbbbbb", linewidth=0.6)
    axis.axvline(0, color="#bbbbbb", linewidth=0.6)
    axis.legend(frameon=False, ncol=2)
    axis.grid(alpha=0.15)
    _save(fig, path)


def plot_cluster_feature_heatmap(profiles: pd.DataFrame, path: Path) -> None:
    values = profiles[FEATURE_COLUMNS]
    medians = values.median(axis=0)
    iqrs = values.quantile(0.75) - values.quantile(0.25)
    safe_iqrs = iqrs.mask(iqrs.abs() < 1e-12, 1.0)
    robust_scores = (values - medians) / safe_iqrs
    robust_scores = robust_scores.rename(columns=FEATURE_LABELS)
    fig, axis = plt.subplots(figsize=(11, max(3.8, len(profiles) * 0.65)))
    limit = max(1.0, float(np.nanmax(np.abs(robust_scores.to_numpy()))))
    image = axis.imshow(
        robust_scores.to_numpy(),
        cmap="coolwarm",
        vmin=-limit,
        vmax=limit,
        aspect="auto",
    )
    axis.set_xticks(np.arange(len(robust_scores.columns)))
    axis.set_xticklabels(robust_scores.columns)
    axis.set_yticks(np.arange(len(robust_scores.index)))
    axis.set_yticklabels(robust_scores.index)
    colorbar = fig.colorbar(image, ax=axis, shrink=0.8)
    colorbar.set_label("Relative to cluster median (robust score)")
    axis.set_xticks(np.arange(-0.5, len(robust_scores.columns), 1), minor=True)
    axis.set_yticks(np.arange(-0.5, len(robust_scores.index), 1), minor=True)
    axis.grid(which="minor", color="white", linewidth=0.5)
    axis.tick_params(which="minor", bottom=False, left=False)
    axis.set_ylabel("Cluster")
    axis.set_xlabel("")
    axis.set_title("Each pathway has a distinct level, trend, and fuel profile", fontweight="bold")
    axis.tick_params(axis="x", rotation=40)
    _save(fig, path)


def plot_cluster_trajectories(panel_with_cluster: pd.DataFrame, path: Path) -> None:
    trajectories = (
        panel_with_cluster.groupby(["cluster", "year"], as_index=False)["co2_per_capita"]
        .median()
    )
    fig, axis = plt.subplots(figsize=(10, 5.8))
    for cluster, group in trajectories.groupby("cluster"):
        axis.plot(
            group["year"],
            group["co2_per_capita"],
            linewidth=2.6,
            label=f"Cluster {cluster}",
            color=COLORS[int(cluster) % len(COLORS)],
        )
    axis.set_yscale("log")
    axis.set_xlabel("Year")
    axis.set_ylabel("Median CO2 per capita (tonnes, log scale)")
    axis.set_title("The clusters follow different 30-year emissions trajectories", fontweight="bold")
    axis.grid(alpha=0.2, which="both")
    axis.legend(frameon=False, ncol=2)
    _save(fig, path)


def summarize_fuel_structure(panel_with_cluster: pd.DataFrame) -> pd.DataFrame:
    recent = panel_with_cluster[panel_with_cluster["year"].between(2017, 2021)]
    shares = recent.groupby("cluster")[["coal_share", "oil_share", "gas_share"]].median()
    totals = shares.sum(axis=1)
    if (totals <= 0).any():
        raise ValueError("Fuel-share medians must have a positive row total")
    return shares.div(totals, axis=0)


def plot_fuel_structure(panel_with_cluster: pd.DataFrame, path: Path) -> None:
    shares = summarize_fuel_structure(panel_with_cluster)
    fig, axis = plt.subplots(figsize=(8.5, 5.2))
    bottom = np.zeros(len(shares))
    for column, label, color in [
        ("coal_share", "Coal", "#4D4D4D"),
        ("oil_share", "Oil", "#D97706"),
        ("gas_share", "Gas", "#2A9D8F"),
    ]:
        axis.bar(
            shares.index.astype(str),
            shares[column] * 100,
            bottom=bottom * 100,
            label=label,
            color=color,
        )
        bottom += shares[column].to_numpy()
    axis.set_ylim(0, 100)
    axis.set_xlabel("Cluster")
    axis.set_ylabel("Median fuel share (%)")
    axis.set_title("Current fuel structures explain important pathway differences", fontweight="bold")
    axis.legend(frameon=False, ncol=3, loc="upper center")
    axis.grid(axis="y", alpha=0.2)
    _save(fig, path)
