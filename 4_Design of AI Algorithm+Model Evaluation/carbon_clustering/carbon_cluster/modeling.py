"""Unsupervised model fitting, selection, and stability checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import RobustScaler

from .features import FEATURE_COLUMNS


@dataclass
class ClusteringResult:
    selected_k: int
    metrics: pd.DataFrame
    labels: np.ndarray
    pca_scores: np.ndarray
    explained_variance: float
    gmm_probabilities: np.ndarray
    gmm_labels: np.ndarray
    cluster_profiles: pd.DataFrame
    scaler: RobustScaler
    pca: PCA


def _validate_features(features: pd.DataFrame, k_values: list[int]) -> None:
    missing = sorted(set(FEATURE_COLUMNS).difference(features.columns))
    if missing:
        raise ValueError(f"Missing model features: {missing}")
    if features[FEATURE_COLUMNS].isna().any().any():
        raise ValueError("Model features contain missing values")
    if not np.isfinite(features[FEATURE_COLUMNS].to_numpy(dtype=float)).all():
        raise ValueError("Model features contain non-finite values")
    if not k_values:
        raise ValueError("At least one candidate K is required")
    if min(k_values) < 2 or max(k_values) >= len(features):
        raise ValueError("Candidate K values must be between 2 and n_samples - 1")


def _choose_k(metrics: pd.DataFrame) -> int:
    ranked = metrics.copy()
    ranked["silhouette_rank"] = ranked["silhouette"].rank(
        method="min", ascending=False
    )
    ranked["davies_bouldin_rank"] = ranked["davies_bouldin"].rank(
        method="min", ascending=True
    )
    ranked["calinski_harabasz_rank"] = ranked["calinski_harabasz"].rank(
        method="min", ascending=False
    )
    ranked["composite_rank"] = ranked[
        ["silhouette_rank", "davies_bouldin_rank", "calinski_harabasz_rank"]
    ].sum(axis=1)
    best = ranked.sort_values(
        ["composite_rank", "silhouette", "k"],
        ascending=[True, False, True],
    ).iloc[0]
    return int(best["k"])


def _order_labels_by_current_emissions(
    features: pd.DataFrame, labels: np.ndarray
) -> np.ndarray:
    ordering = (
        pd.DataFrame(
            {
                "cluster": labels,
                "level": features["log_recent_per_capita"].to_numpy(),
            }
        )
        .groupby("cluster")["level"]
        .median()
        .sort_values()
        .index.tolist()
    )
    mapping = {old: new for new, old in enumerate(ordering)}
    return np.asarray([mapping[int(label)] for label in labels], dtype=int)


def fit_clustering(
    features: pd.DataFrame,
    k_values: Iterable[int] = range(2, 9),
    seed: int = 42,
    variance_threshold: float = 0.85,
) -> ClusteringResult:
    """Fit the PCA/K-Means model, select K, and fit a GMM check."""
    k_values = sorted(set(int(k) for k in k_values))
    _validate_features(features, k_values)
    if not 0 < variance_threshold <= 1:
        raise ValueError("variance_threshold must be in (0, 1]")

    matrix = features[FEATURE_COLUMNS].to_numpy(dtype=float)
    scaler = RobustScaler()
    scaled = scaler.fit_transform(matrix)
    pca = PCA(n_components=variance_threshold, svd_solver="full")
    pca_scores = pca.fit_transform(scaled)

    metric_rows = []
    fitted_models: dict[int, KMeans] = {}
    for k in k_values:
        model = KMeans(n_clusters=k, n_init=50, random_state=seed)
        labels = model.fit_predict(pca_scores)
        fitted_models[k] = model
        metric_rows.append(
            {
                "k": k,
                "inertia": float(model.inertia_),
                "silhouette": float(silhouette_score(pca_scores, labels)),
                "davies_bouldin": float(davies_bouldin_score(pca_scores, labels)),
                "calinski_harabasz": float(
                    calinski_harabasz_score(pca_scores, labels)
                ),
            }
        )

    metrics = pd.DataFrame(metric_rows).sort_values("k").reset_index(drop=True)
    selected_k = _choose_k(metrics)
    raw_labels = fitted_models[selected_k].labels_.astype(int)
    labels = _order_labels_by_current_emissions(features, raw_labels)

    profile_source = features[FEATURE_COLUMNS].copy()
    profile_source["cluster"] = labels
    cluster_profiles = (
        profile_source.groupby("cluster")[FEATURE_COLUMNS]
        .median()
        .sort_index()
    )

    gmm = GaussianMixture(
        n_components=selected_k,
        covariance_type="full",
        n_init=10,
        random_state=seed,
        reg_covar=1e-6,
    )
    gmm.fit(pca_scores)
    gmm_probabilities = gmm.predict_proba(pca_scores)
    gmm_labels = gmm_probabilities.argmax(axis=1).astype(int)

    return ClusteringResult(
        selected_k=selected_k,
        metrics=metrics,
        labels=labels,
        pca_scores=pca_scores,
        explained_variance=float(pca.explained_variance_ratio_.sum()),
        gmm_probabilities=gmm_probabilities,
        gmm_labels=gmm_labels,
        cluster_profiles=cluster_profiles,
        scaler=scaler,
        pca=pca,
    )


def estimate_stability(
    pca_scores: np.ndarray,
    reference_labels: np.ndarray,
    selected_k: int,
    seed: int = 42,
    repeats: int = 100,
    sample_fraction: float = 0.80,
) -> pd.DataFrame:
    """Measure K-Means label stability on repeated country subsamples."""
    scores = np.asarray(pca_scores, dtype=float)
    reference = np.asarray(reference_labels, dtype=int)
    if scores.ndim != 2 or len(scores) != len(reference):
        raise ValueError("pca_scores and reference_labels must align")
    if repeats < 1:
        raise ValueError("repeats must be at least one")
    if not 0 < sample_fraction <= 1:
        raise ValueError("sample_fraction must be in (0, 1]")

    rng = np.random.default_rng(seed)
    sample_size = max(selected_k + 1, int(np.floor(len(scores) * sample_fraction)))
    rows = []
    for repeat in range(repeats):
        indices = np.sort(rng.choice(len(scores), size=sample_size, replace=False))
        model = KMeans(
            n_clusters=selected_k,
            n_init=30,
            random_state=seed + repeat + 1,
        )
        sampled_labels = model.fit_predict(scores[indices])
        ari = adjusted_rand_score(reference[indices], sampled_labels)
        rows.append(
            {
                "repeat": repeat + 1,
                "sample_size": sample_size,
                "adjusted_rand_index": float(ari),
            }
        )
    return pd.DataFrame(rows)
