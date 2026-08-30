#!/usr/bin/env python3
"""Run the complete carbon trajectory clustering workflow."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from carbon_cluster.features import FEATURE_COLUMNS, build_country_features
from carbon_cluster.modeling import estimate_stability, fit_clustering
from carbon_cluster.plots import (
    plot_cluster_feature_heatmap,
    plot_cluster_trajectories,
    plot_fuel_structure,
    plot_k_selection,
    plot_pca_clusters,
)


def run_pipeline(
    panel: pd.DataFrame,
    output_dir: Path,
    *,
    k_values: Iterable[int] = range(2, 9),
    seed: int = 42,
    stability_repeats: int = 100,
) -> dict[str, int | float | list[int]]:
    output_dir = Path(output_dir)
    figure_dir = output_dir / "figures"
    figure_dir.mkdir(parents=True, exist_ok=True)

    features, audit = build_country_features(panel)
    result = fit_clustering(features, k_values=k_values, seed=seed)
    stability = estimate_stability(
        result.pca_scores,
        result.labels,
        selected_k=result.selected_k,
        seed=seed,
        repeats=stability_repeats,
    )

    country_results = features.copy()
    country_results["cluster"] = result.labels
    for index in range(result.pca_scores.shape[1]):
        country_results[f"PC{index + 1}"] = result.pca_scores[:, index]

    probability_columns = [
        f"gmm_component_{index}_probability" for index in range(result.selected_k)
    ]
    gmm_results = features[["country", "iso_code"]].copy()
    gmm_results[probability_columns] = result.gmm_probabilities
    gmm_results["gmm_component"] = result.gmm_labels
    gmm_results["gmm_max_probability"] = result.gmm_probabilities.max(axis=1)

    metrics = result.metrics.copy()
    metrics["selected"] = metrics["k"].eq(result.selected_k)

    country_results.to_csv(output_dir / "country_features_with_clusters.csv", index=False)
    audit.to_csv(output_dir / "cohort_audit.csv", index=False)
    metrics.to_csv(output_dir / "k_selection_metrics.csv", index=False)
    stability.to_csv(output_dir / "stability_results.csv", index=False)
    gmm_results.to_csv(output_dir / "gmm_membership_probabilities.csv", index=False)
    result.cluster_profiles.to_csv(output_dir / "cluster_profiles.csv", index=True)

    summary: dict[str, int | float | list[int]] = {
        "input_rows": int(len(panel)),
        "countries_and_territories": int(audit.shape[0]),
        "main_cohort_countries": int(features.shape[0]),
        "excluded_countries": int((audit["cohort_reason"] != "main_cohort").sum()),
        "feature_count": len(FEATURE_COLUMNS),
        "selected_k": result.selected_k,
        "pca_components": int(result.pca_scores.shape[1]),
        "pca_explained_variance": result.explained_variance,
        "stability_repeats": int(stability_repeats),
        "median_adjusted_rand_index": float(stability["adjusted_rand_index"].median()),
        "random_seed": int(seed),
        "candidate_k": [int(k) for k in metrics["k"]],
    }
    (output_dir / "run_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    label_lookup = country_results[["country", "iso_code", "cluster"]]
    panel_with_cluster = panel.merge(
        label_lookup,
        on=["country", "iso_code"],
        how="inner",
        validate="many_to_one",
    )
    plot_k_selection(metrics, result.selected_k, figure_dir / "k_selection.png")
    plot_pca_clusters(
        result.pca_scores,
        result.labels,
        result.pca.explained_variance_ratio_,
        figure_dir / "pca_clusters.png",
    )
    plot_cluster_feature_heatmap(
        result.cluster_profiles,
        figure_dir / "cluster_feature_heatmap.png",
    )
    plot_cluster_trajectories(
        panel_with_cluster,
        figure_dir / "cluster_trajectories.png",
    )
    plot_fuel_structure(panel_with_cluster, figure_dir / "fuel_structure.png")
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cluster countries by their 1992-2021 carbon-emission trajectories."
    )
    parser.add_argument("--input", required=True, type=Path, help="Input panel CSV")
    parser.add_argument("--output", type=Path, default=Path("outputs"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--stability-repeats", type=int, default=100)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    panel = pd.read_csv(args.input)
    summary = run_pipeline(
        panel,
        args.output,
        seed=args.seed,
        stability_repeats=args.stability_repeats,
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

