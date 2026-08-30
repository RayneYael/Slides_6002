import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from run_clustering import run_pipeline
from tests.test_features import make_country


class PipelineTests(unittest.TestCase):
    def test_pipeline_writes_all_required_outputs(self):
        panels = []
        multipliers = [0.975, 1.000, 1.045]
        for group, multiplier in enumerate(multipliers):
            for index in range(4):
                panels.append(
                    make_country(
                        f"Group{group}_Country{index}",
                        f"G{group}{index}",
                        annual_multiplier=multiplier + index * 0.0005,
                    )
                )
        panel = pd.concat(panels, ignore_index=True)

        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            summary = run_pipeline(
                panel,
                output_dir,
                k_values=range(2, 4),
                seed=42,
                stability_repeats=3,
            )
            expected = {
                "country_features_with_clusters.csv",
                "cohort_audit.csv",
                "k_selection_metrics.csv",
                "stability_results.csv",
                "gmm_membership_probabilities.csv",
                "cluster_profiles.csv",
                "run_summary.json",
                "figures/k_selection.png",
                "figures/pca_clusters.png",
                "figures/cluster_feature_heatmap.png",
                "figures/cluster_trajectories.png",
                "figures/fuel_structure.png",
            }
            actual = {
                str(path.relative_to(output_dir))
                for path in output_dir.rglob("*")
                if path.is_file()
            }
            self.assertTrue(expected.issubset(actual))
            self.assertIn(summary["selected_k"], {2, 3})
            on_disk = json.loads((output_dir / "run_summary.json").read_text())
            self.assertEqual(on_disk["main_cohort_countries"], 12)
            for relative_path in expected:
                self.assertGreater((output_dir / relative_path).stat().st_size, 0)


if __name__ == "__main__":
    unittest.main()
