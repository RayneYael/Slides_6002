import unittest

import numpy as np
import pandas as pd

from carbon_cluster.features import FEATURE_COLUMNS
from carbon_cluster.modeling import estimate_stability, fit_clustering


def make_three_blob_features(seed: int = 7) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    centers = [-6.0, 0.0, 6.0]
    blocks = []
    countries = []
    for cluster_id, center in enumerate(centers):
        block = rng.normal(center, 0.25, size=(30, len(FEATURE_COLUMNS)))
        blocks.append(block)
        countries.extend([f"Country_{cluster_id}_{i:02d}" for i in range(30)])
    values = np.vstack(blocks)
    frame = pd.DataFrame(values, columns=FEATURE_COLUMNS)
    frame.insert(0, "iso_code", [f"X{i:02d}" for i in range(len(frame))])
    frame.insert(0, "country", countries)
    return frame


class ModelingTests(unittest.TestCase):
    def setUp(self):
        self.features = make_three_blob_features()

    def test_fit_selects_three_separated_clusters(self):
        result = fit_clustering(self.features, k_values=range(2, 5), seed=42)
        self.assertEqual(result.selected_k, 3)
        self.assertEqual(set(result.metrics["k"]), {2, 3, 4})
        self.assertEqual(len(result.labels), len(self.features))

    def test_pca_retains_required_variance(self):
        result = fit_clustering(self.features, k_values=range(2, 5), seed=42)
        self.assertGreaterEqual(result.explained_variance, 0.85)
        self.assertGreaterEqual(result.pca_scores.shape[1], 1)
        self.assertLessEqual(result.pca_scores.shape[1], len(FEATURE_COLUMNS))

    def test_gmm_probabilities_sum_to_one(self):
        result = fit_clustering(self.features, k_values=range(2, 5), seed=42)
        totals = result.gmm_probabilities.sum(axis=1)
        np.testing.assert_allclose(totals, np.ones(len(totals)), atol=1e-8)

    def test_cluster_profiles_use_original_feature_units(self):
        result = fit_clustering(self.features, k_values=range(2, 5), seed=42)
        self.assertEqual(set(result.cluster_profiles.columns), set(FEATURE_COLUMNS))
        self.assertEqual(len(result.cluster_profiles), result.selected_k)
        self.assertGreater(result.cluster_profiles.to_numpy().max(), 1.0)

    def test_stability_is_bounded_and_high_for_separated_blobs(self):
        result = fit_clustering(self.features, k_values=range(2, 5), seed=42)
        stability = estimate_stability(
            result.pca_scores,
            result.labels,
            selected_k=result.selected_k,
            seed=42,
            repeats=12,
        )
        self.assertEqual(len(stability), 12)
        self.assertTrue(stability["adjusted_rand_index"].between(0, 1).all())
        self.assertGreater(stability["adjusted_rand_index"].median(), 0.90)


if __name__ == "__main__":
    unittest.main()
