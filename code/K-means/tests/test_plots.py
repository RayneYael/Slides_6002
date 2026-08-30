import unittest

import numpy as np
import pandas as pd

from carbon_cluster.plots import summarize_fuel_structure


class PlotDataTests(unittest.TestCase):
    def test_fuel_structure_rows_are_normalized_to_one(self):
        frame = pd.DataFrame(
            {
                "cluster": [0, 0, 0, 1, 1, 1],
                "year": [2019, 2020, 2021, 2019, 2020, 2021],
                "coal_share": [0.10, 0.20, 0.80, 0.00, 0.10, 0.20],
                "oil_share": [0.80, 0.30, 0.10, 0.80, 0.80, 0.10],
                "gas_share": [0.10, 0.50, 0.10, 0.20, 0.10, 0.70],
            }
        )
        shares = summarize_fuel_structure(frame)
        np.testing.assert_allclose(shares.sum(axis=1), np.ones(len(shares)))


if __name__ == "__main__":
    unittest.main()
