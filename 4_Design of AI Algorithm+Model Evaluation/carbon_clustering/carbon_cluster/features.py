"""Validation and country-level trajectory feature engineering."""

from __future__ import annotations

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {
    "country",
    "iso_code",
    "year",
    "co2_per_capita",
    "co2_growth_prct",
    "coal_share",
    "gas_share",
    "is_micro_state",
    "fuel_structure_unreliable",
}

FEATURE_COLUMNS = [
    "log_recent_per_capita",
    "long_term_log_slope",
    "recent_log_slope",
    "slope_acceleration",
    "growth_volatility_mad",
    "peak_timing",
    "post_peak_change",
    "recent_coal_share",
    "recent_gas_share",
    "coal_share_change",
    "gas_share_change",
]


def validate_panel(df: pd.DataFrame) -> None:
    """Raise a clear ValueError when the source panel is unsuitable."""
    missing = sorted(REQUIRED_COLUMNS.difference(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    if df.duplicated(["country", "year"]).any():
        raise ValueError("Duplicate country-year rows found")
    numeric_columns = [
        "year",
        "co2_per_capita",
        "co2_growth_prct",
        "coal_share",
        "gas_share",
    ]
    if df[numeric_columns].isna().any().any():
        raise ValueError("Required numeric columns contain missing values")
    if (df["co2_per_capita"] <= 0).any():
        raise ValueError("co2_per_capita must be positive for logarithmic slopes")
    share_out_of_range = (
        (df[["coal_share", "gas_share"]] < 0)
        | (df[["coal_share", "gas_share"]] > 1)
    ).any().any()
    if share_out_of_range:
        raise ValueError("Fuel shares must be between zero and one")


def _log_slope(group: pd.DataFrame) -> float:
    years = group["year"].to_numpy(dtype=float)
    log_values = np.log(group["co2_per_capita"].to_numpy(dtype=float))
    return float(np.polyfit(years - years.min(), log_values, 1)[0])


def _median_absolute_deviation(values: np.ndarray) -> float:
    median = np.median(values)
    return float(np.median(np.abs(values - median)))


def _cohort_reason(group: pd.DataFrame, expected_years: int) -> str:
    complete = (
        len(group) == expected_years
        and group["year"].nunique() == expected_years
        and int(group["year"].min()) == 1992
        and int(group["year"].max()) == 2021
    )
    if not complete:
        return "incomplete_history"
    if bool(group["is_micro_state"].max()):
        return "micro_state"
    if bool(group["fuel_structure_unreliable"].max()):
        return "unreliable_fuel_structure"
    return "main_cohort"


def _country_feature_row(group: pd.DataFrame) -> dict[str, float | str]:
    group = group.sort_values("year").reset_index(drop=True)
    recent = group[group["year"].between(2017, 2021)]
    recent_trend = group[group["year"].between(2012, 2021)]
    early = group[group["year"].between(1992, 1996)]

    long_slope = _log_slope(group)
    recent_slope = _log_slope(recent_trend)

    growth = group["co2_growth_prct"].to_numpy(dtype=float)
    low, high = np.quantile(growth, [0.01, 0.99])
    clipped_growth = np.clip(growth, low, high)

    smoothed = (
        group.set_index("year")["co2_per_capita"]
        .rolling(window=3, center=True, min_periods=1)
        .median()
    )
    peak_year = int(smoothed.idxmax())
    peak_value = float(smoothed.loc[peak_year])
    last_value = float(smoothed.loc[int(group["year"].max())])
    year_span = int(group["year"].max() - group["year"].min())

    return {
        "country": str(group.loc[0, "country"]),
        "iso_code": str(group.loc[0, "iso_code"]),
        "log_recent_per_capita": float(np.log1p(recent["co2_per_capita"].median())),
        "long_term_log_slope": long_slope,
        "recent_log_slope": recent_slope,
        "slope_acceleration": recent_slope - long_slope,
        "growth_volatility_mad": _median_absolute_deviation(clipped_growth),
        "peak_timing": (peak_year - int(group["year"].min())) / year_span,
        "post_peak_change": (last_value - peak_value) / peak_value,
        "recent_coal_share": float(recent["coal_share"].median()),
        "recent_gas_share": float(recent["gas_share"].median()),
        "coal_share_change": float(
            recent["coal_share"].median() - early["coal_share"].median()
        ),
        "gas_share_change": float(
            recent["gas_share"].median() - early["gas_share"].median()
        ),
    }


def build_country_features(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return main-cohort features and a country-level cohort audit table."""
    validate_panel(df)
    expected_years = 30
    audit_rows: list[dict[str, object]] = []
    feature_rows: list[dict[str, float | str]] = []

    for (country, iso_code), group in df.groupby(
        ["country", "iso_code"], sort=True, dropna=False
    ):
        reason = _cohort_reason(group, expected_years)
        audit_rows.append(
            {
                "country": country,
                "iso_code": iso_code,
                "first_year": int(group["year"].min()),
                "last_year": int(group["year"].max()),
                "n_years": int(group["year"].nunique()),
                "is_micro_state": bool(group["is_micro_state"].max()),
                "fuel_structure_unreliable": bool(
                    group["fuel_structure_unreliable"].max()
                ),
                "cohort_reason": reason,
            }
        )
        if reason == "main_cohort":
            feature_rows.append(_country_feature_row(group))

    features = pd.DataFrame(feature_rows).sort_values("country").reset_index(drop=True)
    audit = pd.DataFrame(audit_rows).sort_values("country").reset_index(drop=True)
    if features.empty:
        raise ValueError("No countries qualify for the main cohort")
    if features[FEATURE_COLUMNS].isna().any().any():
        raise ValueError("Feature engineering produced missing values")
    return features, audit
