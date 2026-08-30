# -*- coding: utf-8 -*-
"""Render the five-slide deck's enlarged chart assets.

The map-only variants deliberately omit legends that are already native
PowerPoint objects.  Their canvases match the data region's landscape aspect,
so the useful geographic content fills the slide without bitmap distortion.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EDA = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(EDA))
sys.path.insert(0, str(SCRIPTS))

import config
from utils.data import load_panel, slice_year
from run_all_spatial import fig_p1_03_treemap_concentration
from _render_p1_3d import render_p1_3d
from _render_p3_map import render_p3_map
from _render_p3_trajectory_pseudo3d_cobalt import render as render_trajectory


def require_new(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite: {path.relative_to(ROOT)}")


def main() -> None:
    outputs = [
        config.FIGS_P1 / "P1_03_combo_top20_bars_cumshare_cobalt_wide.png",
        config.FIGS_P1 / "P1_01_map_bars_total_co2_2021_map_only.png",
        config.FIGS_P3 / "P3_01_map_dominant_fuel_2021_compact.png",
        config.FIGS_P3 / "P3_06_trajectory_map_only_enlarged.png",
    ]
    for path in outputs:
        require_new(path)

    panel_2021 = slice_year(load_panel(), year=2021)
    fig_p1_03_treemap_concentration(panel_2021, wide=True)
    render_p1_3d(outputs[1], year=2021, map_only=True)
    render_p3_map(outputs[2], year=2021, compact=True)
    render_trajectory(outputs[3], map_only=True)

    for path in outputs:
        print(f"ASSET={path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
