# 数据处理说明

本目录存放 1992–2021 CO₂ 面板数据的处理结果。  
**变量含义与国家/地区对照**见 [`co2_panel_1992_2021_数据字典.md`](co2_panel_1992_2021_数据字典.md)。

## 目录文件

| 文件 | 说明 |
|------|------|
| `co2_panel_1992_2021.csv` | 主数据集（6,378 行 × 22 列） |
| `co2_panel_1992_2021_数据字典.md` | 字段定义、口径说明、国家/地区 ISO 对照表 |
| `scripts/merge_and_preprocess.py` | 合并 OWID 与 GCB，导出 CSV |
| `scripts/generate_data_dictionary.py` | 根据 CSV 与 OWID codebook 生成数据字典 |

## 原始数据来源

| 角色 | 路径 | 说明 |
|------|------|------|
| **主表** | `data/co2-data-master/co2-data-master/owid-co2-data.csv` | Our World in Data；排放数据主要来自 Global Carbon Budget 2025 |
| **补充表** | `data/archive_kaggle/GCB2022v27_MtCO2_flat.csv` | Global Carbon Project GCB 2022（v27）；仅填补 OWID 缺失的煤/气/油分项 |

**引用**

- OWID: Hannah Ritchie, Pablo Rosado and Max Roser (2024) — *CO₂ and Greenhouse Gas Emissions*. https://ourworldindata.org/co2-and-greenhouse-gas-emissions
- GCB 2022: Friedlingstein, P. et al. (2022). *Global Carbon Budget 2022*. Earth System Science Data. GCP version 2022v27.

## 处理流程

1. 读取 OWID 主表。
2. 保留 1992–2021 且 `iso_code` 非空的国家/地区记录。
3. 剔除 `Monaco`、`San Marino`、`Vatican`（1992–2021 无有效 co2）。
4. 以 `iso_code + year` 为键，左连接 GCB 2022（以 OWID 为主表）。
5. 对煤/气/油分项按优先级填补：`OWID 原值 → GCB 值 → gcb_total=0 时补 0 → 最终兜底补 0`。
6. 删除 `co2`、`population`、`co2_per_capita` 任一缺失的记录。
7. 构造燃料占比、`is_micro_state`、`is_high_per_capita` 及 `fuel_structure_unreliable` 质量标记列。
8. 删除 `co2_growth_abs` 或 `co2_growth_prct` 任一缺失的记录（共 8 行；首年或缺上一年基准，无法计算增长率）。
9. 导出 CSV。运行脚本时会在终端打印简要 QA 摘要。

## 筛选与剔除

| 名称 | ISO | 原因 |
|------|-----|------|
| Monaco | MCO | 1992–2021 无有效 co2，脚本剔除 |
| San Marino | SMR | 同上 |
| Vatican | VAT | 同上 |
| Antarctica | ATA | 核心字段缺失 |
| Christmas Island | CXR | 核心字段缺失 |

**增长率缺失（整行剔除，共 8 行）**

| 国家 | ISO | 年份 | 原因 |
|------|-----|------|------|
| East Timor | TLS | 1994–1998 | OWID 缺增长率或百分比不可定义 |
| Eritrea | ERI | 1994 | 缺上一年 co2 基准 |
| Marshall Islands | MHL | 1992 | 面板首年，无同比 |
| Micronesia | FSM | 1992 | 面板首年，无同比 |

OWID 中 `iso_code` 为空的聚合实体（World、Africa、EU 等）已在步骤 2 过滤。

## GCB 2022 原始字段（合并用，未直接导出）

来源：`GCB2022v27_MtCO2_flat_metadata.json`

| GCB 列 | 含义 | 单位 |
|--------|------|------|
| Country | 国家名称 | — |
| ISO 3166-1 alpha-3 | ISO 三位代码 | — |
| Year | 年份 | 日历年 |
| Total | 化石 CO₂ 排放总量 | Mt CO₂ |
| Coal | 煤 CO₂ | Mt CO₂ |
| Oil | 油 CO₂ | Mt CO₂ |
| Gas | 气 CO₂ | Mt CO₂ |
| Cement | 水泥 CO₂ | Mt CO₂ |
| Flaring | 放空燃烧 CO₂ | Mt CO₂ |
| Other | 其他化石 CO₂ | Mt CO₂ |
| Per Capita | 人均化石 CO₂ | t CO₂/person |

## 燃料分项填补说明

OWID 主表中，部分国家/年份的煤/气/油分项存在缺失。脚本用 **GCB 2022** 补充表按以下优先级填补：

```text
OWID 原值  →  GCB 2022 值  →  gcb_total=0 时补 0  →  最终兜底补 0
```

每项燃料的来源记录在 `coal_source`、`gas_source`、`oil_source` 中：

| 取值 | 含义 |
|------|------|
| `owid` | 直接来自 OWID 原值，未填补 |
| `gcb` | OWID 缺失，使用了 **GCB 2022** 报告的值 |
| `gcb_zero` | OWID 与 GCB 分项均缺失，但 GCB 总量为 0，按规则推为 0 |
| `imputed_zero` | 上述来源均不可用，脚本兜底填 0（当前数据中为 0 行） |

**示例（Angola 2000）**：OWID 缺煤分项，GCB 报 coal=0，故 `coal_source=gcb`；气、油仍来自 OWID（`gas_source=owid`，`oil_source=owid`）。

## 质量标记列（详细说明）

导出 CSV 包含一个布尔质量列，以及三个 `*_source` 字符串列用于标记燃料填补来源。

### `coal_source` / `gas_source` / `oil_source`（燃料分项来源）

| 取值 | 含义 |
|------|------|
| `owid` | 直接来自 OWID 原值，未填补 |
| `gcb` | OWID 缺失，使用了 **GCB 2022** 报告的值 |
| `gcb_zero` | OWID 与 GCB 分项均缺失，但 GCB 总量为 0，按规则推为 0 |
| `imputed_zero` | 上述来源均不可用，脚本兜底填 0（当前数据中为 0 行） |

**当前统计**：约 3,241 行（50.8%）至少有一项 `*_source` 不为 `owid`。分析燃料结构时，可筛选三列均为 `owid` 的子样本（约 3,137 行）做稳健性检验。

### `fuel_structure_unreliable`（燃料结构是否不可信）

| 项目 | 说明 |
|------|------|
| **含义** | 该行 **`co2 > 0`（有总排放）但煤+油+气之和 = 0**，无法合理解释燃料结构 |
| **生成规则** | `co2 > 0` 且 `coal_co2 + gas_co2 + oil_co2 = 0` |
| **当前统计** | True：3 行；False：6,375 行 |
| **“不可信”指什么** | **不是说 co2 总量错了**，而是说 `coal_share` / `oil_share` / `gas_share` 没有分析意义（分母为 0，占比全为 0） |
| **具体案例** | 3 行均为 **East Timor（TLS）1999–2001**：有 co2（可能来自 flaring 等非三燃料来源），但三燃料分项均为 0 |
| **如何使用** | 做燃料结构/占比图时**建议排除**这 3 行；做总量/人均分析时**可保留** |

## 建模与可视化使用建议

- **`co2` / `co2_per_capita` 分析**：通常可保留全部 6,378 行。
- **燃料结构分析**（`coal_share` 等）：建议排除 `fuel_structure_unreliable = True` 的 3 行；视情况筛选 `coal_source = gas_source = oil_source = owid` 做稳健性检验。
- **增长率分析**（`co2_growth_*`）：导出表中增长率均来自 OWID 原值，无缺失、无填补；缺失的 8 行已在步骤 8 剔除。

## 运行方式

```powershell
D:\Anaconda3\python.exe data\Final_data\scripts\merge_and_preprocess.py
D:\Anaconda3\python.exe data\Final_data\scripts\generate_data_dictionary.py
```

先跑 merge 生成 CSV，再跑 dictionary 更新数据字典。
