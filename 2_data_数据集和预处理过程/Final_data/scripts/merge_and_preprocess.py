"""Merge OWID CO2 with GCB 2022 (Kaggle) and produce a single 1992-2021 panel."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PROCESSED_DIR = Path(__file__).resolve().parent.parent
ROOT = PROCESSED_DIR.parent.parent
DATA = ROOT / "data"
OUT_DIR = PROCESSED_DIR

OWID_PATH = DATA / "co2-data-master" / "co2-data-master" / "owid-co2-data.csv"
GCB_PATH = DATA / "archive_kaggle" / "GCB2022v27_MtCO2_flat.csv"

DROP_COUNTRIES = {"Monaco", "San Marino", "Vatican"}
YEAR_MIN, YEAR_MAX = 1992, 2021
OUTPUT_FILE = OUT_DIR / "co2_panel_1992_2021.csv"

OUTPUT_COLS = [
    "country",
    "iso_code",
    "year",
    "population",
    "co2",
    "co2_per_capita",
    "co2_growth_abs",
    "co2_growth_prct",
    "oil_co2",
    "coal_co2",
    "gas_co2",
    "coal_co2_filled",
    "gas_co2_filled",
    "coal_source",
    "gas_source",
    "oil_source",
    "coal_share",
    "oil_share",
    "gas_share",
    "is_micro_state",
    "is_high_per_capita",
    "fuel_structure_unreliable",
]


def load_owid() -> pd.DataFrame:
    return pd.read_csv(OWID_PATH, low_memory=False)


def prepare_gcb(gcb: pd.DataFrame) -> pd.DataFrame:
    gcb = gcb.rename(
        columns={
            "ISO 3166-1 alpha-3": "iso_code",
            "Year": "year",
            "Coal": "gcb_coal",
            "Oil": "gcb_oil",
            "Gas": "gcb_gas",
            "Total": "gcb_total",
            "Cement": "gcb_cement",
            "Flaring": "gcb_flaring",
            "Other": "gcb_other",
        }
    )
    value_cols = ["gcb_coal", "gcb_gas", "gcb_oil", "gcb_total"]
    gcb["_completeness"] = gcb[value_cols].notna().sum(axis=1)
    gcb = gcb.sort_values(["iso_code", "year", "_completeness"], ascending=[True, True, False])
    gcb = gcb.drop_duplicates(subset=["iso_code", "year"], keep="first")
    return gcb.drop(columns=["_completeness"])


def load_gcb() -> pd.DataFrame:
    return prepare_gcb(pd.read_csv(GCB_PATH))


def fill_fuel_col(
    df: pd.DataFrame,
    owid_col: str,
    gcb_col: str,
    *,
    zero_total_col: str = "gcb_total",
) -> tuple[pd.Series, pd.Series]:
    """Fill fuel column: OWID > GCB > zero when GCB total=0 > final 0."""
    filled = df[owid_col].copy()
    source = pd.Series("", index=df.index, dtype="object")

    has_owid = df[owid_col].notna()
    filled.loc[has_owid] = df.loc[has_owid, owid_col]
    source.loc[has_owid] = "owid"

    gcb_fill = df[owid_col].isna() & df[gcb_col].notna()
    filled.loc[gcb_fill] = df.loc[gcb_fill, gcb_col]
    source.loc[gcb_fill] = "gcb"

    zero_total = (
        filled.isna()
        & df[zero_total_col].notna()
        & (df[zero_total_col] == 0)
    )
    filled.loc[zero_total] = 0.0
    source.loc[zero_total] = "gcb_zero"

    still_missing = filled.isna()
    filled.loc[still_missing] = 0.0
    source.loc[still_missing & (source == "")] = "imputed_zero"

    return filled, source


def missing_rate(series: pd.Series) -> float:
    return float(series.isna().mean())


def to_native(obj):
    """Convert numpy scalars to native Python types for JSON."""
    if isinstance(obj, dict):
        return {k: to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_native(v) for v in obj]
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return obj


def run_pipeline() -> dict:
    qa: dict = {"steps": {}, "checks": {}, "missing_rates": {}}

    owid_raw = load_owid()
    gcb_file = pd.read_csv(GCB_PATH)
    gcb_raw = prepare_gcb(gcb_file)
    qa["steps"]["owid_raw_rows"] = len(owid_raw)
    qa["steps"]["gcb_raw_rows"] = len(gcb_file)
    qa["steps"]["gcb_rows_after_dedup"] = len(gcb_raw)

    # Step 1-2: time + entity filter
    df = owid_raw[
        (owid_raw["year"] >= YEAR_MIN)
        & (owid_raw["year"] <= YEAR_MAX)
        & owid_raw["iso_code"].notna()
    ].copy()
    qa["steps"]["after_time_entity_filter"] = len(df)

    # Step 3: drop invalid countries
    df = df[~df["country"].isin(DROP_COUNTRIES)].copy()
    qa["steps"]["after_drop_invalid_countries"] = len(df)
    qa["steps"]["dropped_countries"] = sorted(DROP_COUNTRIES)

    pre_mask = df["co2"].notna()
    qa["missing_rates"]["before_merge"] = {
        "coal_co2": missing_rate(df.loc[pre_mask, "coal_co2"]),
        "gas_co2": missing_rate(df.loc[pre_mask, "gas_co2"]),
        "oil_co2": missing_rate(df.loc[pre_mask, "oil_co2"]),
        "fuel_complete_raw": float(
            df.loc[pre_mask, ["coal_co2", "oil_co2", "gas_co2"]].notna().all(axis=1).mean()
        ),
    }

    # Step 4: left join GCB
    gcb_cols = [
        "iso_code",
        "year",
        "gcb_coal",
        "gcb_gas",
        "gcb_oil",
        "gcb_total",
        "gcb_cement",
        "gcb_flaring",
    ]
    df = df.merge(gcb_raw[gcb_cols], on=["iso_code", "year"], how="left")
    gcb_match_mask = df["gcb_coal"].notna()
    qa["steps"]["gcb_match_rate"] = float(gcb_match_mask.mean())

    # Step 5: conditional fill coal / gas / oil (no nulls in output)
    df["coal_owid_orig"] = df["coal_co2"]
    df["gas_owid_orig"] = df["gas_co2"]
    df["oil_owid_orig"] = df["oil_co2"]

    df["coal_co2_filled"], df["coal_source"] = fill_fuel_col(df, "coal_co2", "gcb_coal")
    df["gas_co2_filled"], df["gas_source"] = fill_fuel_col(df, "gas_co2", "gcb_gas")
    df["oil_co2"], df["oil_source"] = fill_fuel_col(df, "oil_co2", "gcb_oil")

    coal_gcb_fill = df["coal_owid_orig"].isna() & (df["coal_source"] == "gcb")
    gas_gcb_fill = df["gas_owid_orig"].isna() & (df["gas_source"] == "gcb")
    coal_zero_fill = df["coal_source"] == "gcb_zero"
    gas_zero_fill = df["gas_source"] == "gcb_zero"
    oil_zero_fill = df["oil_source"] == "gcb_zero"
    qa["steps"]["gcb_coal_fill_count"] = int(coal_gcb_fill.sum())
    qa["steps"]["gcb_gas_fill_count"] = int(gas_gcb_fill.sum())
    qa["steps"]["gcb_zero_coal_fill_count"] = int(coal_zero_fill.sum())
    qa["steps"]["gcb_zero_gas_fill_count"] = int(gas_zero_fill.sum())
    qa["steps"]["gcb_zero_oil_fill_count"] = int(oil_zero_fill.sum())
    qa["steps"]["gcb_coal_fill_all_zero"] = (
        bool((df.loc[coal_gcb_fill, "coal_co2_filled"] == 0).all()) if coal_gcb_fill.any() else True
    )
    qa["steps"]["gcb_gas_fill_all_zero"] = (
        bool((df.loc[gas_gcb_fill, "gas_co2_filled"] == 0).all()) if gas_gcb_fill.any() else True
    )

    # Align raw coal/gas columns with filled values for a null-free export
    df["coal_co2"] = df["coal_co2_filled"]
    df["gas_co2"] = df["gas_co2_filled"]

    # Step 6: drop core missing
    core_cols = ["co2", "population", "co2_per_capita"]
    before_drop = len(df)
    df = df.dropna(subset=core_cols).copy()
    qa["steps"]["after_drop_core_missing"] = len(df)
    qa["steps"]["dropped_core_missing_rows"] = before_drop - len(df)

    # Step 7: flags
    pop_2021 = df.loc[df["year"] == 2021].set_index("iso_code")["population"]
    micro_iso = set(pop_2021[pop_2021 < 50_000].index)
    df["is_micro_state"] = df["iso_code"].isin(micro_iso)

    pc_2021 = df.loc[df["year"] == 2021].set_index("iso_code")["co2_per_capita"]
    high_iso = set(pc_2021[pc_2021 > 20].index)
    df["is_high_per_capita"] = df["iso_code"].isin(high_iso)

    # Step 8: fuel shares (all rows complete after fill)
    fuel_total = df["coal_co2_filled"] + df["oil_co2"] + df["gas_co2_filled"]
    has_fuel = fuel_total > 0
    for share_col, num_col in [
        ("coal_share", "coal_co2_filled"),
        ("oil_share", "oil_co2"),
        ("gas_share", "gas_co2_filled"),
    ]:
        df[share_col] = 0.0
        df.loc[has_fuel, share_col] = (
            df.loc[has_fuel, num_col] / fuel_total[has_fuel]
        )

    # Step 8b: drop rows with missing growth (first year / undefined pct change)
    growth_cols = ["co2_growth_abs", "co2_growth_prct"]
    growth_missing = df[growth_cols].isna().any(axis=1)
    before_growth_drop = len(df)
    df = df[~growth_missing].copy()
    qa["steps"]["after_drop_growth_missing"] = len(df)
    qa["steps"]["dropped_growth_missing_rows"] = before_growth_drop - len(df)

    # Row-level quality flag for downstream filtering.
    df["fuel_structure_unreliable"] = (df["co2"] > 0) & (fuel_total == 0)

    fuel_imputed_mask = (
        (df["coal_source"] != "owid")
        | (df["gas_source"] != "owid")
        | (df["oil_source"] != "owid")
    )
    qa["missing_rates"]["after_merge"] = {
        "coal_co2_filled": missing_rate(df["coal_co2_filled"]),
        "gas_co2_filled": missing_rate(df["gas_co2_filled"]),
        "oil_co2": missing_rate(df["oil_co2"]),
    }
    qa["steps"]["fuel_imputed_rows"] = int(fuel_imputed_mask.sum())
    qa["steps"]["fuel_structure_unreliable_rows"] = int(df["fuel_structure_unreliable"].sum())

    # Step 9: export single final table
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = df[OUTPUT_COLS].copy()
    panel.to_csv(OUTPUT_FILE, index=False)

    qa["output"] = {
        "file": str(OUTPUT_FILE.name),
        "year_range": [YEAR_MIN, YEAR_MAX],
        "rows": len(panel),
        "countries": int(panel["iso_code"].nunique()),
    }

    # Step 10: QA checks
    dup = panel.duplicated(subset=["iso_code", "year"], keep=False).sum()
    qa["checks"]["no_country_year_duplicates"] = dup == 0
    qa["checks"]["all_iso_code_non_null"] = bool(panel["iso_code"].notna().all())
    qa["checks"]["invalid_countries_removed"] = not panel["country"].isin(DROP_COUNTRIES).any()
    qa["checks"]["year_range_ok"] = panel["year"].min() == YEAR_MIN and panel["year"].max() == YEAR_MAX
    null_counts = panel.isna().sum()
    qa["checks"]["no_nulls_in_output"] = bool(null_counts.sum() == 0)
    qa["checks"]["null_counts"] = {k: int(v) for k, v in null_counts.items() if v > 0}

    overlap = df[df["coal_owid_orig"].notna() & df["gcb_coal"].notna()]
    if len(overlap) > 0:
        coal_diff = (overlap["coal_co2"] - overlap["gcb_coal"]).abs()
        qa["checks"]["overlap_coal_median_abs_diff"] = float(coal_diff.median())
        qa["checks"]["overlap_coal_pearson_r"] = float(
            overlap["coal_co2"].corr(overlap["gcb_coal"])
        )

    overlap_gas = df[df["gas_owid_orig"].notna() & df["gcb_gas"].notna()]
    if len(overlap_gas) > 0:
        gas_diff = (overlap_gas["gas_co2"] - overlap_gas["gcb_gas"]).abs()
        qa["checks"]["overlap_gas_median_abs_diff"] = float(gas_diff.median())
        qa["checks"]["overlap_gas_pearson_r"] = float(
            overlap_gas["gas_co2"].corr(overlap_gas["gcb_gas"])
        )

    owid_coal_mask = df["coal_source"] == "owid"
    owid_gas_mask = df["gas_source"] == "owid"
    owid_oil_mask = df["oil_source"] == "owid"
    owid_coal_unchanged = (
        df.loc[owid_coal_mask, "coal_co2_filled"] == df.loc[owid_coal_mask, "coal_owid_orig"]
    ).all()
    owid_gas_unchanged = (
        df.loc[owid_gas_mask, "gas_co2_filled"] == df.loc[owid_gas_mask, "gas_owid_orig"]
    ).all()
    owid_oil_unchanged = (
        df.loc[owid_oil_mask, "oil_co2"] == df.loc[owid_oil_mask, "oil_owid_orig"]
    ).all()
    qa["checks"]["owid_coal_not_overwritten"] = bool(owid_coal_unchanged)
    qa["checks"]["owid_gas_not_overwritten"] = bool(owid_gas_unchanged)
    qa["checks"]["owid_oil_not_overwritten"] = bool(owid_oil_unchanged)
    qa["checks"]["growth_fields_complete"] = bool(
        panel[["co2_growth_abs", "co2_growth_prct"]].notna().all().all()
    )

    return to_native(qa)


if __name__ == "__main__":
    report = run_pipeline()
    print(json.dumps(report, indent=2, ensure_ascii=False))
