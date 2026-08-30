图片分类说明

1_Exploration of Dataset/Figures
- 01_Emissions Concentration：Exploration 第 1 页的 Treemap（PPT 原图与 HTML 导出图）。
- 02_Scale vs Intensity：Exploration 第 2 页的总排放/人均排放地图及两个渐变图例。
- 03_Fuel Mix Geography：Exploration 第 3 页的主要燃料类型地图。

3_Visual Storytelling/Figures
- 01_Group Profiles_Blueprint：国家分组特征散点图蓝图。
- 02_Group Geography_Blueprint：国家分组空间分布地图蓝图的参考图。
- 03_Group Trajectories_Blueprint：分组空间中心变化地图蓝图。
- 注意：上述三张是当前《Visual Storytelling_空间域_备选蓝图》已使用的画面，其中第 2 页仍是重绘参考，不应视为最终 K-means 分组地图。

_未入选图片_保留
- 保留 31 张未进入当前 Exploration PPT 或 Visual Storytelling 蓝图的候选图、旧版本和替代设计。
- 仍按 point1 / point2 / point3 主题细分，便于回溯。

1_Exploration of Dataset/Figure_HTML_Sources
- 保存两个单图可交互 HTML 源文件。

code/_cleanup_archive_20260827/reviews/figs_qa_20260829
- 仅保存 PPT 整页渲染、拆分检查和版式 QA 截图，不是正式插图。

Code 说明
- 当前已有 config.py、scripts、utils、aux 和 _cleanup_archive_20260827 的基本分层。
- 当前核心生成脚本已改为输出至 1_Exploration of Dataset/Figures/_Generated_by_Scripts，不再创建项目级 Figs 目录。
