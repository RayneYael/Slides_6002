# -*- coding: utf-8 -*-
"""Load Final_data and attach region / derived fields."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

EDA = Path(__file__).resolve().parents[1]
if str(EDA) not in sys.path:
    sys.path.insert(0, str(EDA))

import config
from utils.regions import region_of


def load_panel() -> pd.DataFrame:
    df = pd.read_csv(config.DATA_CSV)
    df["region"] = df["iso_code"].map(region_of)
    return df


def slice_year(df: pd.DataFrame, year: int | None = None) -> pd.DataFrame:
    year = year or config.YEAR
    out = df[df["year"] == year].copy()
    out["log_co2"] = np.log10(out["co2"].clip(lower=0.01))
    shares = out[["coal_share", "oil_share", "gas_share"]]
    out["dominant_fuel"] = shares.idxmax(axis=1).str.replace("_share", "").str.title()
    out.loc[out["fuel_structure_unreliable"], "dominant_fuel"] = np.nan
    return out


def fuel_ok(df: pd.DataFrame) -> pd.DataFrame:
    return df[~df["fuel_structure_unreliable"]].copy()


def write_region_lookup(df: pd.DataFrame) -> Path:
    path = config.AUX / "iso_to_region.csv"
    tab = (
        df.groupby(["iso_code", "country"], as_index=False)["region"]
        .first()
        .sort_values("iso_code")
    )
    tab.to_csv(path, index=False)
    return path


def concentration_stats(y: pd.DataFrame) -> dict:
    total = y["co2"].sum()
    ranked = y.sort_values("co2", ascending=False)
    return {
        "n": len(y),
        "global_mt": float(total),
        "top10_share": float(ranked.head(10)["co2"].sum() / total),
        "top20_share": float(ranked.head(20)["co2"].sum() / total),
        "region_share": (y.groupby("region")["co2"].sum() / total).sort_values(ascending=False),
    }

