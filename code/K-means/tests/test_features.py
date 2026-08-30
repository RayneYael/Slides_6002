import unittest

import numpy as np
import pandas as pd

from carbon_cluster.features import FEATURE_COLUMNS, build_country_features, validate_panel


def make_country(
    country: str,
    iso_code: str,
    *,
    micro: bool = False,
    unreliable: bool = False,
    start_year: int = 1992,
    end_year: int = 2021,
    annual_multiplier: float = 1.03,
) -> pd.DataFrame:
    rows = []
    previous_co2 = None
    for i, year in enumerate(range(start_year, end_year + 1)):
        per_capita = 1.0 * annual_multiplier**i
        population = 1_000_000 + i * 10_000
        co2 = per_capita * population / 1_000_000
        growth_abs = 0.0 if previous_co2 is None else co2 - previous_co2
        growth_pct = 0.0 if previous_co2 is None else growth_abs / previous_co2 * 100
        coal_share = 0.60 - i * 0.005
        gas_share = 0.10 + i * 0.003
        oil_share = 1.0 - coal_share - gas_share
        rows.append(
            {
                "country": country,
                "iso_code": iso_code,
                "year": year,
                "population": population,
                "co2": co2,
                "co2_per_capita": per_capita,
                "co2_growth_abs": growth_abs,
                "co2_growth_prct": growth_pct,
                "oil_co2": co2 * oil_share,
                "coal_co2": co2 * coal_share,
                "gas_co2": co2 * gas_share,
                "coal_co2_filled": co2 * coal_share,
                "gas_co2_filled": co2 * gas_share,
                "coal_source": "owid",
                "gas_source": "owid",
                "oil_source": "owid",
                "coal_share": coal_share,
                "oil_share": oil_share,
                "gas_share": gas_share,
                "is_micro_state": micro,
                "is_high_per_capita": False,
                "fuel_structure_unreliable": unreliable,
            }
        )
        previous_co2 = co2
    return pd.DataFrame(rows)


class FeatureEngineeringTests(unittest.TestCase):
    def setUp(self):
        self.panel = pd.concat(
            [
                make_country("Alpha", "ALP", annual_multiplier=1.04),
                make_country("Beta", "BET", micro=True, annual_multiplier=0.99),
                make_country("Gamma", "GAM", start_year=1995),
            ],
            ignore_index=True,
        )

    def test_validate_panel_rejects_duplicate_country_year(self):
        duplicate = pd.concat([self.panel, self.panel.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "Duplicate country-year"):
            validate_panel(duplicate)

    def test_build_features_filters_main_cohort_and_audits_exclusions(self):
        features, audit = build_country_features(self.panel)
        self.assertEqual(features["country"].tolist(), ["Alpha"])
        reasons = audit.set_index("country")["cohort_reason"].to_dict()
        self.assertEqual(reasons["Alpha"], "main_cohort")
        self.assertEqual(reasons["Beta"], "micro_state")
        self.assertEqual(reasons["Gamma"], "incomplete_history")

    def test_positive_monotonic_path_has_positive_long_term_slope(self):
        features, _ = build_country_features(self.panel)
        self.assertGreater(features.loc[0, "long_term_log_slope"], 0)
        self.assertAlmostEqual(features.loc[0, "long_term_log_slope"], np.log(1.04), places=5)

    def test_feature_set_omits_oil_share_and_scale_variables(self):
        forbidden = {"oil_share", "population", "co2", "co2_growth_abs"}
        self.assertTrue(forbidden.isdisjoint(FEATURE_COLUMNS))
        self.assertEqual(len(FEATURE_COLUMNS), 11)


if __name__ == "__main__":
    unittest.main()
