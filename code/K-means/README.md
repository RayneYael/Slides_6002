# Global Carbon Transition Pathway Clustering

This project converts the supplied 1992-2021 country-year CO2 panel into one trajectory profile per country, then applies robust scaling, PCA, K-Means model selection, a Gaussian Mixture Model check, and repeated-subsample stability analysis.

## Method

The main cohort contains countries with all 30 years of data, excludes micro-states from fitting, and excludes fuel structures flagged as unreliable. The model uses eleven features describing current per-capita emissions, long- and short-term slopes, acceleration, volatility, peak timing, post-peak change, current coal/gas shares, and changes in those shares. Population and total emissions do not enter the clustering model.

Oil share is omitted from the model because coal, oil, and gas shares sum to one. It remains in the interpretation charts. K is evaluated from 2 to 8 using silhouette, Davies-Bouldin, and Calinski-Harabasz metrics. The selected model is checked with GMM soft membership and repeated 80% country subsamples.

## Run

Create an environment and install the dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Run the full analysis:

```bash
.venv/bin/python run_clustering.py \
  --input "/absolute/path/co2_panel_1992_2021.csv" \
  --output outputs \
  --stability-repeats 100
```

Run the tests:

```bash
PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -v
```

## Outputs

- `country_features_with_clusters.csv`: interpretable features, cluster label, and PCA coordinates.
- `cluster_profiles.csv`: median feature profile for each cluster in original units.
- `k_selection_metrics.csv`: K=2 through K=8 metrics and selected K.
- `stability_results.csv`: adjusted Rand index from repeated country subsamples.
- `gmm_membership_probabilities.csv`: soft-membership probabilities and uncertainty.
- `cohort_audit.csv`: why each country was included or excluded.
- `run_summary.json`: reproducibility and headline model statistics.
- `figures/`: five presentation-ready diagnostic and storytelling charts.

## Interpretation limits

The clusters describe similarity, not causal effects or a ranking from best to worst. PCA charts are projections rather than the complete model. The fuel-share fields cover coal, oil, and gas and therefore should not be described as the entire energy system. Cluster names must be assigned only after examining the actual profiles and representative countries.
