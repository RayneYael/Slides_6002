"""Generate data dictionary MD from official codebooks and processed panel."""

from datetime import date
from pathlib import Path

import pandas as pd

PROCESSED = Path(__file__).resolve().parent.parent
DATA = PROCESSED.parent
OUT_MD = PROCESSED / "co2_panel_1992_2021_数据字典.md"
CODEBOOK = DATA / "co2-data-master" / "co2-data-master" / "owid-co2-codebook.csv"
PANEL = PROCESSED / "co2_panel_1992_2021.csv"

cb = pd.read_csv(CODEBOOK).set_index("column")
panel = pd.read_csv(PANEL)
countries = (
    panel.groupby(["iso_code", "country"], as_index=False)["year"]
    .agg(数据年份数="count", 起始年="min", 结束年="max")
    .sort_values("iso_code")
)
generated_on = date.today().isoformat()
panel_rows = len(panel)
panel_countries = panel["iso_code"].nunique()
panel_cols = len(panel.columns)
fuel_imputed_rows = int(
    (
        (panel["coal_source"] != "owid")
        | (panel["gas_source"] != "owid")
        | (panel["oil_source"] != "owid")
    ).sum()
)
fuel_structure_unreliable_rows = int(panel["fuel_structure_unreliable"].sum())
short_year_countries = countries[countries["数据年份数"] < 30]

TYPE_MAP: dict[str, tuple[str, str]] = {
    "country": ("字符串", "—"),
    "iso_code": ("字符串", "—"),
    "year": ("整数", "—"),
    "coal_source": ("字符串", "—"),
    "gas_source": ("字符串", "—"),
    "oil_source": ("字符串", "—"),
    "is_micro_state": ("布尔", "—"),
    "is_high_per_capita": ("布尔", "—"),
    "fuel_structure_unreliable": ("布尔", "—"),
    "coal_share": ("数值", "比例 (0–1)"),
    "oil_share": ("数值", "比例 (0–1)"),
    "gas_share": ("数值", "比例 (0–1)"),
    "coal_co2": ("数值", "million tonnes (Mt)"),
    "gas_co2": ("数值", "million tonnes (Mt)"),
}


def owid_desc(col: str) -> str:
    return cb.loc[col, "description"]


def col_type_unit(col: str, cb_col: str | None) -> tuple[str, str]:
    if col in TYPE_MAP:
        return TYPE_MAP[col]
    if cb_col and cb_col in cb.index:
        unit = cb.loc[cb_col, "unit"]
        return "数值", (unit if pd.notna(unit) else "—")
    return "数值", "—"


col_docs = [
    ("country", "OWID", "country", "国家/地区英文名称。"),
    ("iso_code", "OWID", "iso_code", "ISO 3166-1 alpha-3 三位字母国家/地区代码。"),
    ("year", "OWID", "year", "观测年份。"),
    ("population", "OWID", "population", None),
    ("co2", "OWID", "co2", None),
    ("co2_per_capita", "OWID", "co2_per_capita", None),
    ("co2_growth_abs", "OWID", "co2_growth_abs", "年度 CO₂ 总量绝对变化量（Mt）。"),
    ("co2_growth_prct", "OWID", "co2_growth_prct", "年度 CO₂ 总量百分比变化。"),
    ("oil_co2", "OWID+GCB", "oil_co2", "油 CO₂ 排放量（Mt）。"),
    ("coal_co2", "OWID+GCB", "coal_co2", "煤 CO₂ 排放量（Mt）；与 `coal_co2_filled` 相同。"),
    ("gas_co2", "OWID+GCB", "gas_co2", "气 CO₂ 排放量（Mt）；与 `gas_co2_filled` 相同。"),
    ("coal_co2_filled", "OWID+GCB", "coal_co2", "煤 CO₂ 最终值（Mt）。"),
    ("gas_co2_filled", "OWID+GCB", "gas_co2", "气 CO₂ 最终值（Mt）。"),
    ("coal_source", "衍生", None, "煤分项来源。`owid`=OWID原值；`gcb`=OWID缺失时用GCB2022补；`gcb_zero`=GCB总量为0推0；`imputed_zero`=兜底填0。"),
    ("gas_source", "衍生", None, "气分项来源，取值含义同 `coal_source`。"),
    ("oil_source", "衍生", None, "油分项来源，取值含义同 `coal_source`。"),
    ("coal_share", "衍生", None, "煤占三燃料（煤+油+气）排放的比例；三燃料之和为 0 时为 0。"),
    ("oil_share", "衍生", None, "油占三燃料排放的比例；三燃料之和为 0 时为 0。"),
    ("gas_share", "衍生", None, "气占三燃料排放的比例；三燃料之和为 0 时为 0。"),
    ("is_micro_state", "衍生", None, "2021 年 population < 50,000 则为 True（该国所有年份相同）。"),
    ("is_high_per_capita", "衍生", None, "2021 年 co2_per_capita > 20 t/person 则为 True（该国所有年份相同）。"),
    ("fuel_structure_unreliable", "衍生", None, "co2>0 但煤+油+气=0 时为 True；总量可用，但燃料占比不可信。"),
]

lines: list[str] = [
    "# CO₂ 面板数据字典（1992–2021）",
    "",
    "> **数据文件**：`data/Final_data/co2_panel_1992_2021.csv`  ",
    f"> **生成日期**：{generated_on}  ",
    f"> **行数**：{panel_rows:,}（{panel_countries} 个国家/地区，1992–2021）  ",
    "> **用途**：字段定义、变量口径、国家/地区 ISO 对照。数据处理流程见 [`README.md`](README.md)。",
    "",
    "---",
    "",
    f"## 1. 字段说明（{panel_cols} 列）",
    "",
    "OWID 字段英文原文见 `owid-co2-codebook.csv`；下表为中文说明。",
    "",
    "| 列名 | 类型 | 单位 | 来源 | 含义 |",
    "|------|------|------|------|------|",
]

for col, src, cb_col, extra in col_docs:
    ctype, unit = col_type_unit(col, cb_col)
    if cb_col and cb_col in cb.index:
        meaning = owid_desc(cb_col)
        if extra:
            meaning = f"{meaning}（{extra}）"
    else:
        meaning = extra or ""
    lines.append(f"| `{col}` | {ctype} | {unit} | {src} | {meaning} |")

lines += [
    "",
    "### 1.1 变量口径",
    "",
    "1. **`co2` 不一定等于煤+油+气。** `co2` 为不含土地利用变化的化石燃料+工业 CO₂ 总量，还可含水泥、flaring、其他工业等。",
    "2. **燃料占比分母** = 煤+油+气，不含 cement / flaring / other。",
    "3. **`coal_share` + `oil_share` + `gas_share`** 在三燃料之和 > 0 时相加为 1；三燃料之和为 0 时三者均为 0。",
    "",
    "### 1.2 质量标记与来源列（简要）",
    "",
    "布尔质量列及燃料来源说明；完整规则见 [`README.md`](README.md)。",
    "",
    f"| 列名 | 含义 | 统计 |",
    f"|------|------|------|",
    f"| `coal_source` / `gas_source` / `oil_source` | 各燃料分项来源（见下表取值） | 约 {fuel_imputed_rows:,} 行至少一项非 `owid` |",
    f"| `fuel_structure_unreliable` | co2>0 但三燃料之和=0，燃料占比不可信 | {fuel_structure_unreliable_rows:,} 行 |",
    "",
    "**`*_source` 取值**：`owid`（OWID原值）/ `gcb`（GCB2022补）/ `gcb_zero`（GCB总量=0推0）/ `imputed_zero`（兜底填0）。",
    "",
    "---",
    "",
    f"## 2. 国家/地区 ISO 对照表（{panel_countries} 个）",
    "",
    "标准：**ISO 3166-1 alpha-3**（OWID / ISO）。",
    "",
    "| ISO | 名称（OWID） | 年份数 | 范围 |",
    "|-----|-------------|--------|------|",
]

for _, r in countries.iterrows():
    lines.append(
        f"| {r['iso_code']} | {r['country']} | {int(r['数据年份数'])} | {int(r['起始年'])}–{int(r['结束年'])} |"
    )

if len(short_year_countries) > 0:
    short_notes = "；".join(
        f"{r['iso_code']}（{r['country']}，{int(r['数据年份数'])} 年，{int(r['起始年'])}–{int(r['结束年'])}）"
        for _, r in short_year_countries.iterrows()
    )
    lines += ["", f"**年份不足 30 年**：{short_notes}。", ""]

lines += [
    "本表不含 Monaco、San Marino、Vatican、Antarctica、Christmas Island 及 OWID 聚合实体（World、Africa、EU 等）；剔除原因见 [`README.md`](README.md)。",
    "",
]

OUT_MD.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {OUT_MD}")
