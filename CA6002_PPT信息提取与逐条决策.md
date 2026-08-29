# CA6002 PPT 信息提取与逐条决策台账

> 状态：逐条审议中，不是最终实施方案。  
> 目的：隔离 PPT 中的硬性要求、事实、作者建议、占位符和未经验证假设，防止新 agent 将建议稿误当成定案。  
> 使用规则：后续 agent 只能直接实施标记为 **已确认** 的条目；**待讨论**、**待验证**、**蓝图假设** 不得进入最终页面。

---

## 1. 分类标准

| 标签 | 含义 | 是否可直接实施 |
|---|---|---|
| 硬性要求 | 老师 Brief/模板明确要求 | 可以，但仍需适配最终内容 |
| 数据事实 | 来自数据、脚本或已验证计算 | 核验版本后可以 |
| 作者解释 | 当前制作者对事实的解释 | 不可以，需逐条讨论 |
| 设计建议 | 对图形、布局、页数或叙事的建议 | 不可以，需逐条讨论 |
| 蓝图假设 | 等待模型或派生计算验证的故事方向 | 不可以 |
| 占位符 | 模板提示、示例、临时数字或待替换内容 | 必须删除或替换 |
| 已否决 | 用户已明确不要 | 不得再次提出或实施 |

决策状态：

- **已确认**：可以进入最终方案；
- **待讨论**：需要用户逐条决定；
- **待验证**：需要数据或代码证据；
- **已否决**：不得进入最终演示；
- **仅内部**：可供计算/开发核对，但不得展示。

---

## 2. 老师模板逐条提取

来源：[`1_assignment具体要求和ppt模板/CA6002 Assignment_Group no - Template.pptx`](1_assignment具体要求和ppt模板/CA6002%20Assignment_Group%20no%20-%20Template.pptx)

### 2.1 标题页和目录页

| ID | PPT 原始信息 | 分类 | 当前决策 |
|---|---|---|---|
| T01 | Use this PPTX template for your assignment | 硬性要求 | **已确认**：最终提交以老师 PPTX 为基础 |
| T02 | 填写 Group Number | 硬性要求 | **已确认** |
| T03 | 填写组长和成员邮箱 | 硬性要求 | **已确认** |
| T04 | 填写 Assignment Title 和成员信息 | 硬性要求 | **已确认** |
| T05 | 标题页不计入 maximum 20 slide limit | 硬性要求 | **已确认** |
| T06 | Contents 页列出 Introduction、Exploration、Algorithm、Evaluation、Storytelling、Conclusions | 硬性要求 | **已确认** |
| T07 | Contents 页不计入 maximum 20 slide limit | 硬性要求 | **已确认** |

### 2.2 全部正文页的共同要求

| ID | PPT 原始信息 | 分类 | 当前决策 |
|---|---|---|---|
| T08 | Delete description in blue in submitted slides | 硬性要求 | **已确认**：蓝色指导文字必须删除 |
| T09 | Write name of person(s) responsible for slide | 硬性要求 | **已确认**：每页底部保留责任人 |
| T10 | Avoid going below 20 point font | 硬性/强指导 | **已确认** |
| T11 | Use adequate figures; assignment focuses on data visualisation | 硬性/强指导 | **已确认** |
| T12 | Sequencing only when it significantly improves clarity | 设计指导 | **已确认**：不为动画而动画 |
| T13 | 总正文不超过 20 页 | 硬性要求 | **已确认** |
| T14 | Replicate template slides when more pages are needed | 硬性要求 | **已确认** |
| T15 | 每页 notes 应充分描述；可按演讲稿方式书写 | 硬性/强指导 | **已确认** |
| T16 | Notes 尽量不超过一页；最低约 10pt | 设计指导 | **已确认** |

### 2.3 Introduction 模板页

| ID | PPT 原始信息 | 分类 | 当前决策 |
|---|---|---|---|
| T17 | 可覆盖 project objectives、motivation、process overview | 内容建议 | **待讨论**：最终 Introduction 内容尚未逐条确定 |
| T18 | Bullet 1–4 | 占位符/指导语 | **已确认**：不作为最终 bullet 原样保留 |

### 2.4 Exploration of Dataset 模板页

| ID | PPT 原始信息 | 分类 | 当前决策 |
|---|---|---|---|
| T19 | 可覆盖 dataset description、strengths/weaknesses、feature selection、conditioning | 内容要求/建议 | **待讨论**：逐条映射现有内容 |
| T20 | Include only the most pertinent and interesting findings | 强指导 | **已确认** |
| T21 | Exploration could take 2–3 slides | 页数建议 | **待讨论**：不是硬上限 |
| T22 | Group is free to allocate slides among stages | 硬性说明 | **已确认** |
| T23 | Bullet 1–3 | 占位符/指导语 | **已确认**：不作为最终正文 |

### 2.5 Design of AI Algorithm 模板页

| ID | PPT 原始信息 | 分类 | 当前决策 |
|---|---|---|---|
| T24 | 说明算法选择、参数、调优、学习曲线、可解释可视化（如适用） | 内容要求/建议 | **待讨论**：按无监督聚类实际情况取舍 |
| T25 | 避免深入讨论机器学习技术细节 | 强指导 | **已确认** |
| T26 | 重点展示可视化如何帮助算法设计 | 强指导 | **已确认** |
| T27 | Algorithm Design 可与 Evaluation 迭代衔接 | 内容建议 | **待讨论**：需要决定页面边界 |
| T28 | 使用 Gen AI 生成代码需在相关 slide notes 说明 | 硬性要求 | **已确认** |

### 2.6 Model Evaluation 模板页

| ID | PPT 原始信息 | 分类 | 当前决策 |
|---|---|---|---|
| T29 | 使用可视化突出模型评价和表现 | 内容要求 | **已确认** |
| T30 | 突出显著影响模型表现的因素 | 内容要求 | **待讨论**：需与现有证据核对 |
| T31 | 强调不同 plots 如何帮助评价模型 | 强指导 | **已确认** |
| T32 | 使用视觉感知和心理原则改善图形 | 强指导 | **已确认** |

### 2.7 Visual Storytelling 模板页

| ID | PPT 原始信息 | 分类 | 当前决策 |
|---|---|---|---|
| T33 | 面向 bosses 讲数据和模型揭示的有趣、相关洞察 | 内容要求 | **已确认** |
| T34 | 使用视觉感知原则沟通洞察 | 强指导 | **已确认** |
| T35 | 可使用 sequencing、animations、transitions、shapes | 可选设计建议 | **待讨论**：不是必须使用 |
| T36 | Use the right chart for the message | 强指导 | **已确认** |

### 2.8 Conclusions 模板页

| ID | PPT 原始信息 | 分类 | 当前决策 |
|---|---|---|---|
| T37 | 总结团队贡献，重点突出 novel/original contributions | 内容要求 | **已确认** |
| T38 | 避免重复前页内容 | 强指导 | **已确认** |
| T39 | 花更多时间总结团队原创贡献 | 强指导 | **已确认** |

---

## 3. 数据集介绍与预处理 PPT 提取

来源：[`3_Exploration of Dataset/01_Exploration_of_Dataset_数据集介绍与预处理.pptx`](3_Exploration%20of%20Dataset/01_Exploration_of_Dataset_数据集介绍与预处理.pptx)

### 3.1 Slide 1 — Data Sources

| ID | 提取内容 | 分类 | 当前决策 |
|---|---|---|---|
| D01 | OWID 是 country-year analytical backbone | 数据事实/作者概括 | **待验证**：与预处理脚本一致后确认 |
| D02 | GCB 2022 只补充缺失的 coal/oil/gas | 数据事实 | **待验证**：与脚本核对 |
| D03 | Existing OWID values are never replaced | 数据事实 | **待验证**：与脚本核对 |
| D04 | OWID raw file: 50,411 rows、79 variables、1750–2024、218 ISO entities | 数据事实 | **仅内部/待讨论**：是否值得出现在最终页 |
| D05 | GCB raw file: 63,104 rows、11 variables、1750–2021、225 ISO entities | 数据事实 | **仅内部/待讨论** |
| D06 | 两个并列大面板、8 个指标卡、WHY COMBINE 流程 | 设计建议 | **已否决**：用户已确认视觉冗余 |
| D07 | 标题 “Two complementary sources make emissions structure visible” | 作者解释 | **待讨论** |

### 3.2 Slide 2 — Data Preparation

| ID | 提取内容 | 分类 | 当前决策 |
|---|---|---|---|
| D08 | Filter 1992–2021 | 数据事实 | **待验证** |
| D09 | Left join on ISO-3 × year | 数据事实 | **待验证** |
| D10 | Priority: observed OWID → GCB → verified zero | 数据事实/规则 | **待验证** |
| D11 | 6,378 entity-year rows | 数据事实 | **待验证** |
| D12 | 213 ISO-coded entities | 数据事实 | **已确认可用于 Exploration** |
| D13 | 30 years | 数据事实 | **待验证** |
| D14 | 22 analysis variables | 数据事实 | **仅内部/待讨论** |
| D15 | 50.8% gain at least one completed/verified component | 数据事实 | **待验证** |
| D16 | 99.8% entity-year coverage、0 missing core measures | 数据事实 | **待验证** |
| D17 | 五步 pipeline + 四个统计卡 + provenance + support + checks | 设计建议 | **已否决**：最终必须压缩 |
| D18 | 数据源介绍和预处理最终占 1 页还是 2 页 | 页数建议 | **待讨论** |

### 3.3 已确认视觉方向

当前精简试稿：[`3_Exploration of Dataset/01_Exploration_of_Dataset_数据集介绍与预处理_精简版.html`](3_Exploration%20of%20Dataset/01_Exploration_of_Dataset_数据集介绍与预处理_精简版.html)

该 HTML 只证明用户喜欢这种视觉风格，不代表其中两页结构和所有文案已经成为最终方案。

---

## 4. 空间域 PPT 提取

来源：[`3_Exploration of Dataset/03_Exploration_of_Dataset_空间域可视化_final_v12.pptx`](3_Exploration%20of%20Dataset/03_Exploration_of_Dataset_空间域可视化_final_v12.pptx)

### 4.1 Slide 1 — Emissions Concentration

| ID | 提取内容 | 分类 | 当前决策 |
|---|---|---|---|
| S01 | Asia share = 59.8% | 数据事实 | **待验证** |
| S02 | China share = 31.4% | 数据事实 | **待验证** |
| S03 | Top 20 share = 81.2% | 数据事实 | **待验证** |
| S04 | Treemap：area = country share；colour = region | 图形编码 | **待讨论**：是否进入最终 Exploration |
| S05 | “Asia contributes 59.8%...” 作为标题 | 作者解释 | **待讨论** |
| S06 | 右侧说明段 + 三条 Key Points | 设计建议 | **已否决**：过度重复 |

### 4.2 Slide 2 — Scale vs Intensity

| ID | 提取内容 | 分类 | 当前决策 |
|---|---|---|---|
| S07 | China leads total emissions | 数据事实 | **待验证** |
| S08 | Qatar leads per-capita emissions | 数据事实 | **待验证** |
| S09 | Land colour = log total CO₂；3-D bar = per-capita CO₂ | 图形编码 | **待讨论**：图形是否过载 |
| S10 | Total and per-capita must be read together | 作者解释 | **待讨论** |
| S11 | 169/213 Natural Earth polygon match、约 99.6% emissions coverage | 地图限制 | **仅内部/notes 候选** |
| S12 | 右侧三条 Key Points + HTML 额外 legend | 设计建议 | **已否决**：最终 JPG 不重复 HTML legend |

### 4.3 Slide 3 — Fuel Mix Geography

| ID | 提取内容 | 分类 | 当前决策 |
|---|---|---|---|
| S13 | Country colour = dominant coal/oil/gas | 图形编码 | **待讨论** |
| S14 | Selected pies = actual three-fuel shares | 图形编码 | **待讨论** |
| S15 | White = missing or unreliable profile | 数据限制/编码 | **待验证** |
| S16 | Coal: Asia；Oil: Africa/Middle East/Americas；Gas: Russia/Central Asia | 作者解释 | **待验证**：不可仅凭视觉概括 |
| S17 | Dominant fuel can mask different national mixes | 作者解释 | **待讨论** |
| S18 | 两个底部说明盒 | 设计建议 | **已否决**：改为更轻的信息层级 |

### 4.4 已确认视觉方向

当前精简试稿：[`3_Exploration of Dataset/03_Exploration_of_Dataset_空间域可视化_final_v12_精简版.html`](3_Exploration%20of%20Dataset/03_Exploration_of_Dataset_空间域可视化_final_v12_精简版.html)

该文件只作为视觉风格参考；其 3 页内容尚未全部确认进入最终 PPT。

---

## 5. Visual Storytelling 蓝图提取

来源：[`5_Visual Storytelling/Visual_Storytelling_空间域_备选蓝图.pptx`](5_Visual%20Storytelling/Visual_Storytelling_空间域_备选蓝图.pptx)

### 5.1 总体状态

该 PPT 自己将页面标记为 `REDRAW BLUEPRINT`，notes 反复要求 final labels frozen 后重新生成。因此整份文件当前属于建议/假设，不是最终内容来源。

### 5.2 Slide 1 — Group Profiles

| ID | 提取内容 | 分类 | 当前决策 |
|---|---|---|---|
| V01 | Scale × intensity scatter，bubble area = population，colour = cluster | 设计建议 | **待讨论** |
| V02 | Model groups should reveal what rankings miss | 蓝图假设 | **待验证** |
| V03 | 标注 representative countries | 设计建议 | **待讨论**；必须先定义代表性标准 |
| V04 | 比较 total Top-5、per-capita Top-5 与 groups | 设计建议 | **待讨论** |
| V05 | final labels frozen 后再重绘 | 工作要求 | **已确认** |

### 5.3 Slide 2 — Group Geography

| ID | 提取内容 | 分类 | 当前决策 |
|---|---|---|---|
| V06 | 国家按 cluster 填色的世界地图 | 设计建议 | **待讨论** |
| V07 | Groups may show concentration、dispersion or regional mixing | 蓝图假设 | **待验证** |
| V08 | 选择 representative/surprising countries 标注 | 设计建议 | **待讨论** |
| V09 | 用 outline/transparency 表示 confidence | 设计建议 | **待讨论** |
| V10 | 对未进入模型国家增加 no-model-result 颜色和解释 | 设计建议 | **已否决**：用户要求最终演示完全不提或标注模型样本变化 |

### 5.4 Slide 3 — Group Spatial Trajectories

| ID | 提取内容 | 分类 | 当前决策 |
|---|---|---|---|
| V11 | 按 cluster 计算 emissions-weighted geographic centres | 分析建议 | **待讨论** |
| V12 | 2013→2021，使用五个 two-year observations | 分析建议 | **待讨论**：时间点依据未确认 |
| V13 | point size = time；arrows = direction only | 图形编码建议 | **待讨论** |
| V14 | 标注移动距离和方向 | 设计建议 | **待讨论** |
| V15 | `WORLD ≈585 km ESE` | 占位符/未验证数字 | **已否决**：不得进入最终内容 |
| V16 | 解释哪些国家或区域驱动每组移动 | 蓝图假设 | **待验证** |

### 5.5 Storytelling 尚未确认的核心问题

必须逐条决定：

1. 是否真的需要 scale–intensity bubble scatter？
2. 它相对 Exploration 的 total/per-capita 图增加了什么信息？
3. Cluster geography map 是否能产生明确、非空泛的空间结论？
4. Group temporal trajectories 是否比 spatial centre movement 更易解释？
5. 空间中心移动是否容易被少数大排放国支配？
6. 三页还是四页最适合 15 分钟展示？
7. 哪些观点可以从数据直接支持，哪些只能作为限制或讨论？

---

## 6. 当前已确认的跨文件决策

| ID | 决策 | 状态 |
|---|---|---|
| C01 | 最终使用老师 PPTX 模板结构 | **已确认** |
| C02 | 主体采用浅米色、深色正文、编辑式标题、细分隔线、大留白 | **已确认** |
| C03 | 删除背景网格、glitch、QR、粗边框、重复卡片和无意义装饰 | **已确认** |
| C04 | 图表后续主要以 JPG/PNG 插入；HTML 重点处理位置和大小 | **已确认** |
| C05 | 每页一个核心结论 | **已确认** |
| C06 | Exploration 可显示 213 ISO-coded entities | **已确认** |
| C07 | Algorithm/Evaluation/Storytelling 完全不出现模型样本数量、数量变化、筛选、异常值或排除原因 | **已确认** |
| C08 | 不出现 `193`、`24+169`、`10/193` 等直接或间接计数 | **已确认** |
| C09 | 现有精简 HTML 是风格参考，不是最终页序或最终内容定案 | **已确认** |
| C10 | Visual Storytelling PPT 是候选蓝图，不得直接实施 | **已确认** |

---

## 7. 逐条审议顺序

建议按照以下顺序与用户逐条确认，不一次性决定整套页序：

1. 老师模板中的硬性要求与可选建议；
2. Exploration 数据集介绍：最终 1 页还是 2 页；
3. 时域内容：哪些图真正进入最终 PPT；
4. 空间域 S01–S18：逐页决定保留、合并或删除；
5. Algorithm/Evaluation：另行从 HTML 建立同样的提取台账；
6. Visual Storytelling V01–V16：在模型结果和实际图形可用后逐条决定；
7. 所有条目确认后，才生成最终页序和迁移方案。

---

## 8. 给新 agent 的硬性启动规则

新 agent 开始工作时必须先阅读本文件，并遵守：

1. 不得将任何 PPT 的现有页序视为最终页序；
2. 不得将 PPT 标题、bullet、notes 或图形建议自动视为用户要求；
3. 只能实施标记为 **已确认** 的条目；
4. 遇到 **待讨论** 时必须停下来与用户逐条确认；
5. 遇到 **待验证** 时先找数据/代码证据，不得凭 PPT 文案判断；
6. 遇到 **蓝图假设** 时不得美化或扩写成结论；
7. 遇到 **已否决** 时不得重新加入方案；
8. `CA6002_演示优化与迁移总规划.md` 中的页数和页序仍是 provisional，不得机械执行；
9. 用户明确要求不显示模型样本数量或变化，任何页面、notes 和图例均不得出现；
10. 每确认一项，应更新本台账的当前决策，再进入下一项。

