# -*- coding: utf-8 -*-
"""Paths & tokens — maps (HTML) vs non-maps (SCI journal)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDA = Path(__file__).resolve().parent
DATA_CSV = (
    ROOT
    / "0_data_数据集和预处理过程"
    / "Final_data"
    / "co2_panel_1992_2021.csv"
)
AUX = EDA / "aux"

# Generated figures are kept beside the Exploration deliverables.  This
# prevents the retired project-level Figs directory from being recreated.
EXPLORATION_DIR = ROOT / "1_Exploration of Dataset"
FIGURE_DIR = EXPLORATION_DIR / "Figures"
FIGS_ROOT = FIGURE_DIR / "_Generated_by_Scripts"
FIGS_P1 = FIGS_ROOT / "point1"
FIGS_P2 = FIGS_ROOT / "point2"
FIGS_P3 = FIGS_ROOT / "point3"
FIGURE_HTML_SOURCES = EXPLORATION_DIR / "Figure_HTML_Sources"
WEB_LIBS = AUX / "web_libs"

YEAR = 2021
DPI = 300

# --- SCI journal (non-map PNG) ---
INK = "#1B1F24"
INK_SOFT = "#3C4654"
MUTED = "#6B7785"
PAPER = "#FFFFFF"
PAPER_CARD = "#FAFBFC"
GRID = "#E6EAF0"
GRID_SOFT = "#F0F3F7"
ACCENT = "#B83A1A"
ACCENT_SOFT = "#D4896A"
ACCENT_LINE = "#9A3218"

# Sequential green→red (shared semantic for emissions)
CO2_SCALE = [
    "#1B7F3A",
    "#4CAF50",
    "#8BC34A",
    "#CDDC39",
    "#FFC107",
    "#FF9800",
    "#F4511E",
    "#D32F2F",
    "#B71C1C",
]
PC_SCALE = list(CO2_SCALE)
HEAT_SCALE = list(CO2_SCALE)

FUEL_COLORS = {
    "Coal": "#5D4E37",
    "Oil": "#C4471A",
    "Gas": "#2B7A9B",
}

REGION_COLORS = {
    "Africa": "#C47A3A",
    "Asia": "#C0392B",
    "Europe": "#2E6B8A",
    "North America": "#1F7A72",
    "South America": "#4F8A3C",
    "Oceania": "#A08A2E",
    "Other": "#7A8794",
}

STORY_ISO_TOTAL = ["CHN", "USA", "IND", "RUS", "JPN", "IRN", "DEU", "SAU"]
STORY_ISO_PC = ["QAT", "KWT", "ARE", "SAU", "USA", "AUS", "CHN", "IND"]

FONT_FAMILY = "Segoe UI, DejaVu Sans, Arial, Helvetica, sans-serif"

for d in (AUX, FIGS_P1, FIGS_P2, FIGS_P3, FIGURE_HTML_SOURCES, WEB_LIBS):
    d.mkdir(parents=True, exist_ok=True)
