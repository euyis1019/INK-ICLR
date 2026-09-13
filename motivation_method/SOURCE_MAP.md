# 论点、实验与来源

本稿整理已有结果，没有新增模型运行。精简报告与完整报告往往共享实验，不能当作独立复现。以下报告/数据链接固定到已核查版本；issue 链接用于阅读实验解释。

## 主线对应关系

| 本稿位置 | 实验如何支持论点 | 对应讨论与报告 |
|---|---|---|
| §1，图 1a，附录 A 表 1 | 四起点使用同一后续流程；正文选取 Average/RegMean 的诊断准确率差距从 22.36 缩到 0.15 pp，附录保留未拉平对照的 8.25 pp 终态差距 | [Issue #6](https://github.com/euyis1019/INK/issues/6#issuecomment-5648265351)；下方 R1、R3 |
| §1，图 1b，附录 A 表 2 | 从共享 W1 分叉，刷新与冻结都继续求解/选步；另列单轮 CG400，将继续更新与重测的作用分开 | [Issue #7](https://github.com/euyis1019/INK/issues/7#issuecomment-5648265839)；R2、R4 |
| §1，图 1c，附录 A 图 2 | 固定图像的 hook、实际求解矩阵变化、同 checkpoint 交换统计、固定本块权重的跨 block 干预；保留等幅提案和 block 0 的负结果 | [Issue #7](https://github.com/euyis1019/INK/issues/7#issuecomment-5648265839)；R2 的三份数据文件 |
| §1 → §2 的过渡 | 从起点差距可修复、继续更新和统计变化，逐步引出当前状态上的修正；以当前 A/G 构造专家锚点回归代理，接受后重估 | [Issue #8](https://github.com/euyis1019/INK/issues/8#issuecomment-5648267989)；由 #6/#7 综合，不当作额外实验 |
| §2.1、附录 A/B | 同机归一化/未归一化消融；Fisher 相对预算、方向重加权、条件性二次风险界 | [Issue #5](https://github.com/euyis1019/INK/issues/5#issuecomment-5648435999)；R5 和下方归一化数据 |

## 报告 PDF 与对应 LaTeX

| 编号 | PDF | LaTeX 主入口 | 本稿用途 |
|---|---|---|---|
| R1 | [精简版_2.pdf](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/精简版_2.pdf) | [cm_motivation_2pages/main.tex](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/cm_motivation_2pages/main.tex) | 多起点的主线与适用边界 |
| R2 | [精简版.pdf](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/精简版.pdf) | [klg_iteration_motivation_paper/main.tex](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/klg_iteration_motivation_paper/main.tex) | 刷新动机与配对轨迹 |
| R3 | [cm_multistart_motivation.pdf](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/cm_multistart_motivation.pdf) | [cm_multistart_motivation/main.tex](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/cm_multistart_motivation/main.tex) | 多起点完整诊断与对照；正文选择其中结果 |
| R4 | [report.pdf](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/report.pdf) | [vitb32_isoc_iteration_report/report.tex](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/vitb32_isoc_iteration_report/report.tex) | Iso-C 专项迭代诊断，作交叉核对 |
| R5 | [chi2_normalization_theory.pdf](https://github.com/euyis1019/INK/blob/81c54885dd9653f91be8dfe4262d88b13da5b24f/reports/chi2_normalization_theory.pdf) | [chi2_normalization_theory/main.tex](https://github.com/euyis1019/INK/blob/81c54885dd9653f91be8dfe4262d88b13da5b24f/reports/latex/chi2_normalization_theory/main.tex) | 本稿附录 B 选取其几何与二次风险证明；未照搬整份报告 |

## 图表与关键数字的数据映射

| 本地 evidence.json 字段 | 固定版本原始文件 | 使用位置 |
|---|---|---|
| `multistart.accuracy`、`multistart.pairs` | [derived_results.json](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/cm_motivation_2pages/data/derived_results.json) | 图 1a、表 1、参数距离；更多预测分布诊断见原报告 |
| `refresh.Average` | [Average.json](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/klg_iteration_motivation_paper/data/Average.json) | 图 1b/c、图 2、表 2、同状态/等幅干预 |
| `refresh.Iso-C` | [Iso-C.json](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/klg_iteration_motivation_paper/data/Iso-C.json) | 图 1c、表 2 |
| `refresh.RegMean` | [RegMean.json](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/klg_iteration_motivation_paper/data/RegMean.json) | 图 1c、表 2 |
| `normalization.normalized` | [coexist_inkrl_seed0.json](https://github.com/euyis1019/INK/blob/b36c1f611516db15d3f65dac20365337fb35bc84/results/same_machine_4090/coexist_inkrl_seed0.json) | 87.0451%、最终留出 KL 0.155523 |
| `normalization.unnormalized` | [ablation_unnorm_inkrl_seed0.json](https://github.com/euyis1019/INK/blob/b36c1f611516db15d3f65dac20365337fb35bc84/results/same_machine_4090/ablation_unnorm_inkrl_seed0.json) | 86.6652%、最终留出 KL 0.169934 |

图 1a 使用多起点研究的固定 validation 前 256 张图像，图 1b 使用完整测试，图 1c 使用校准集的实际求解度量。刷新研究的独立诊断集另行固定随机抽取；图 2 及同状态干预使用该诊断集。准确率为八任务宏平均百分数，准确率差为百分点，KL/JS 均不是百分数。统计刷新复用同一批图像。正文中所有数值均为 seed 0，不把样本级区间或多轮记录当作跨 seed 重复。

## 方法实现核对

方法按 [coexist_merge.py](https://github.com/euyis1019/INK/blob/b36c1f611516db15d3f65dac20365337fb35bc84/src/ink_model_merging/model_merging_methods/coexist_merge.py) 中的默认归一化 KL-G 路径整理；二阶矩处理与线性系统见 [activation_based.py](https://github.com/euyis1019/INK/blob/b36c1f611516db15d3f65dac20365337fb35bc84/src/ink_model_merging/model_merging_methods/activation_based.py)。没有修改模型实现。

附录的 Fisher 恒等式要求正概率与精确算术。实际实现使用 float32、`epsilon=1e-8`、停止分母梯度及数值 clamp，因此正文没有把理想恒等式解释为每个浮点样本上的精确认证。二次风险边界明确固定参考目标、精确求解且无输出收缩；它不取代实际网络消融。
