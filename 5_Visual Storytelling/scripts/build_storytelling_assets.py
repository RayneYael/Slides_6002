#!/usr/bin/env python3
"""Build the self-contained data bundle used by the Visual Storytelling draft."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PANEL_PATH = ROOT / "2_data_数据集和预处理过程/Final_data/co2_panel_1992_2021.csv"
FEATURE_PATH = ROOT / "2_data_数据集和预处理过程/K-means_K=2_分组标签好的数据集/country_features_with_clusters.csv"
TOPOLOGY_PATH = ROOT / "5_Visual Storytelling/assets/countries-110m.json"
GEOGRAPHY_PATH = ROOT / "5_Visual Storytelling/assets/iso3_geography.json"
OUTPUT_PATH = ROOT / "5_Visual Storytelling/assets/storytelling_data.js"


def rounded(value: float, digits: int = 3) -> float:
    return round(float(value), digits)


def main() -> None:
    panel = pd.read_csv(PANEL_PATH)
    features = pd.read_csv(FEATURE_PATH)
    geography = json.loads(GEOGRAPHY_PATH.read_text())
    topology = json.loads(TOPOLOGY_PATH.read_text())

    model = features[
        ["iso_code", "cluster", "recent_log_slope", "long_term_log_slope"]
    ].copy()
    joined = panel.merge(model, on="iso_code", how="inner")

    recent = (
        joined.loc[joined["year"].between(2017, 2021)]
        .groupby(["iso_code", "country", "cluster"], as_index=False)
        .agg(
            co2=("co2", "mean"),
            per_capita=("co2_per_capita", "mean"),
            population=("population", "mean"),
            recent_slope=("recent_log_slope", "first"),
        )
    )
    recent = recent.loc[(recent["co2"] > 0) & (recent["per_capita"] > 0)].copy()

    scatter = []
    for row in recent.itertuples(index=False):
        scatter.append(
            {
                "country": row.country,
                "iso": row.iso_code,
                "cluster": int(row.cluster),
                "co2": rounded(row.co2),
                "perCapita": rounded(row.per_capita),
                "population": round(float(row.population)),
                "recentSlope": rounded(row.recent_slope * 100, 2),
            }
        )

    base = (
        joined.loc[joined["year"] == 1992, ["iso_code", "co2"]]
        .rename(columns={"co2": "base_co2"})
        .drop_duplicates("iso_code")
    )
    indexed = joined.merge(base, on="iso_code", how="inner")
    indexed = indexed.loc[indexed["base_co2"] > 0].copy()
    indexed["index"] = indexed["co2"] / indexed["base_co2"] * 100
    trajectory = (
        indexed.groupby(["cluster", "year"])["index"]
        .agg(
            median="median",
            q25=lambda values: values.quantile(0.25),
            q75=lambda values: values.quantile(0.75),
        )
        .reset_index()
    )
    trajectories = {"0": [], "1": []}
    for row in trajectory.itertuples(index=False):
        trajectories[str(int(row.cluster))].append(
            {
                "year": int(row.year),
                "median": rounded(row.median, 1),
                "q25": rounded(row.q25, 1),
                "q75": rounded(row.q75, 1),
            }
        )

    cluster_by_numeric = {}
    for row in features[["iso_code", "cluster"]].itertuples(index=False):
        geo = geography.get(row.iso_code)
        if geo:
            cluster_by_numeric[geo["numeric"]] = int(row.cluster)

    emissions = recent.groupby("cluster")["co2"].sum()
    emissions_share = emissions / emissions.sum() * 100

    region_mix = []
    region_frame = features[["iso_code", "cluster"]].copy()
    region_frame["region"] = region_frame["iso_code"].map(
        lambda code: geography.get(code, {}).get("region", "")
    )
    for region, values in region_frame.loc[region_frame["region"] != ""].groupby("region"):
        pathway_zero_share = (values["cluster"] == 0).mean() * 100
        region_mix.append(
            {"region": region, "pathway0Share": rounded(pathway_zero_share, 1)}
        )

    bundle = {
        "meta": {
            "panelPeriod": "1992–2021",
            "recentWindow": "2017–2021 mean",
            "indexBaseline": "1992 = 100",
        },
        "scatter": scatter,
        "trajectories": trajectories,
        "clusterByNumeric": cluster_by_numeric,
        "topology": topology,
        "regionMix": region_mix,
        "summary": {
            "pathway0Index2021": trajectories["0"][-1]["median"],
            "pathway1Index2021": trajectories["1"][-1]["median"],
            "pathway0EmissionsShare": rounded(emissions_share.loc[0], 1),
            "pathway1EmissionsShare": rounded(emissions_share.loc[1], 1),
        },
        "comparison": {
            "left": "Indonesia",
            "right": "Brazil",
        },
    }
    OUTPUT_PATH.write_text(
        "window.STORY_DATA=" + json.dumps(bundle, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_PATH.relative_to(ROOT)}")
    print(json.dumps(bundle["summary"], indent=2))


if __name__ == "__main__":
    main()
