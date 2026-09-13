# 论点、实验与来源

本稿使用归一化 KL-G 的机制实验及本次提供的跨设定主实验说明，不新增模型运行。普通 Fisher 的学生/专家实验已移出稿件；附录的 Fisher 相对界仅作归一化的数学参照。跨设定主表在本次写作中没有逐项回查全部运行日志。

## 主线对应关系

| 本稿位置 | 实验或定义如何支持论点 | 对应来源 |
|---|---|---|
| §1 当前模型上的测量参照 | G 由教师目标、学生预测与当前传播共同定义；直接用同一教师替换学生会使该残差归零 | [提供的方法说明](sources/coexist_method_results_20260912.md) §1；正文 §2 估计式；不据此声称专家统计的普遍劣势 |
| 图 1a：起点适配 | 相同后续流程从三种常用起点出发；Average/RegMean 诊断差距 22.36→0.15 pp；附录保留未拉平对照 | [Issue #6](https://github.com/euyis1019/INK/issues/6#issuecomment-5648265351)；R1/R3 |
| 图 1b：继续迭代与重测 | 刷新/冻结共享第一轮状态，都继续 CG 与选步；另列单轮 CG400 | [Issue #7](https://github.com/euyis1019/INK/issues/7#issuecomment-5648265839)；R2/R4 |
| 图 1c：相邻轮度量变化 | 固定校准图像，比较按求解规则处理后的矩阵的方向；曲线只描述统计变化与趋稳 | R2 的 `moment_hook_summary`；[定义与数值](data/source_checks.json) |
| §1 同状态干预、附录 A 图 2 | 同一待更新状态交换统计，并保留跨 block、等幅负结果 | R2 的三份数据文件；用于判断重测的效果 |
| §2 公式与算法 | 沿用 a、hat-a、u、G 和 AXG 公式；输入 h 与输出 y 分开，补齐 bar-s | [提供的方法说明](sources/coexist_method_results_20260912.md) §1；下方实现链接 |
| §3 主实验与适用范围 | 摘录 CLIP/T5 主表、LLM 起点对照，保留实现差异、T5 扩展和负结果 | [主实验说明](sources/coexist_method_results_20260912.md) §2–5；[机器可读表格](data/main_results.json) |
| §2、附录 A/B 归一化 | 同机归一化消融、Fisher 相对预算与条件性风险界 | [Issue #5](https://github.com/euyis1019/INK/issues/5#issuecomment-5648435999)；R5 |

## 图 1c 的精确定义

令 `M_t^(ell,r) = G_t^(ell,r) ⊗ A_t^(ell,r)`，其中 A/G 已按正文规则统一尺度并收缩。在每对相邻状态上，计算各有效层/任务的矩阵余弦，再取 `median(1 - cosine)`。原始记录名为 `H_used_cosine`；H 是历史字段命名，不表示真实 Hessian 或 Fisher。绘图使用 `1 - median(cosine)`，与前述量相同。

该余弦等于输入侧、输出侧处理后矩阵余弦的乘积，因此不必显式构造 Kronecker 大矩阵。C 比较的是方向，忽略整体倍数；不是 raw A/G 的余弦、参数距离、更新效果或误差曲线。横轴 0–1、1–2、2–3、3–4 是相邻学生状态；对数纵轴只为显示后期的小变化。曲线趋小支持度量趋稳，不能单独证明重测提高准确率。

## 本次提供的材料

- `sources/coexist_method_results_20260912.md`：提供文本的逐字节副本，保留原文用于追溯；超出数值表支持范围的强结论没有被正文采用。
- `data/main_results.json`：从该文本的 Markdown 表格抽取，包含来源 SHA-256 和正文所选行。
- `data/source_checks.json`：来源哈希、现成公式的数值代数检查，以及 C 面板的明确含义与逐轮值。
- `evidence.json`：本稿原有 KL-G 起点、刷新、干预及归一化记录，本次未修改。

## 报告 PDF 与对应 LaTeX

| 编号 | PDF | LaTeX 主入口 | 本稿用途 |
|---|---|---|---|
| R1 | [精简版_2.pdf](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/精简版_2.pdf) | [cm_motivation_2pages/main.tex](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/cm_motivation_2pages/main.tex) | 多起点的主线与适用边界 |
| R2 | [精简版.pdf](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/精简版.pdf) | [klg_iteration_motivation_paper/main.tex](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/klg_iteration_motivation_paper/main.tex) | 刷新动机与配对轨迹 |
| R3 | [cm_multistart_motivation.pdf](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/cm_multistart_motivation.pdf) | [cm_multistart_motivation/main.tex](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/cm_multistart_motivation/main.tex) | 多起点完整诊断与对照；正文选择其中结果 |
| R4 | [report.pdf](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/report.pdf) | [vitb32_isoc_iteration_report/report.tex](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/vitb32_isoc_iteration_report/report.tex) | Iso-C 专项迭代诊断，作交叉核对 |
| R5 | [chi2_normalization_theory.pdf](https://github.com/euyis1019/INK/blob/81c54885dd9653f91be8dfe4262d88b13da5b24f/reports/chi2_normalization_theory.pdf) | [chi2_normalization_theory/main.tex](https://github.com/euyis1019/INK/blob/81c54885dd9653f91be8dfe4262d88b13da5b24f/reports/latex/chi2_normalization_theory/main.tex) | 本稿附录 B 选取其几何与二次风险证明；未照搬整份报告 |

## 图表与数据映射

| 数据字段 | 使用位置与说明 |
|---|---|
| `evidence.json → multistart.accuracy.*.diagnostic` | 图 1a，固定独立诊断集，八任务宏平均准确率 |
| `evidence.json → refresh.Average.trajectory` | 图 1b、附录冻结表，完整测试准确率 |
| `evidence.json → refresh.*.moment_hook_summary.*.vs_previous.H_used_cosine` | 图 1c，各层/任务按求解规则处理后的度量余弦的中位数，绘图取 1 减该值 |
| `evidence.json → refresh.*.cross_block` | 附录图 2，固定本块权重的状态干预 |
| `data/main_results.json → clip_main / t5_main` | 主文表 1，T5-base 含目标插值扩展，large 选择原版 |
| `data/main_results.json → llama / gemma` | 主文表 2，所选行含收益与下降，非所有方法排名 |
| `data/main_results.json → clip_scaling` | 九格收益范围，工作台实现与正式 CLIP 结果分开 |
| `evidence.json → normalization` | 已有独立归一化消融 |

准确率差为百分点，KL/JS 和矩阵余弦都不是百分数。三个动机面板均为 seed 0，不能借主表的多 seed 数量声明机制实验的跨 seed 显著性。校准、留出与诊断各有用途，测试不参与接受、选步与选轮。

## 固定版本实现和原始数据链接

| 本地字段 | 固定版本文件 | 用途 |
|---|---|---|
| `multistart.accuracy`、`multistart.pairs` | [derived_results.json](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/cm_motivation_2pages/data/derived_results.json) | 图 1a、附录四起点表及功能距离诊断 |
| `refresh.Average` | [Average.json](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/klg_iteration_motivation_paper/data/Average.json) | 图 1b/c、附录图 2 和冻结表、同状态/等幅干预 |
| `refresh.Iso-C` | [Iso-C.json](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/klg_iteration_motivation_paper/data/Iso-C.json) | 图 1c、附录冻结表与统计变化 |
| `refresh.RegMean` | [RegMean.json](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/klg_iteration_motivation_paper/data/RegMean.json) | 图 1c、附录冻结表与统计变化 |
| `normalization.normalized` | [coexist_inkrl_seed0.json](https://github.com/euyis1019/INK/blob/b36c1f611516db15d3f65dac20365337fb35bc84/results/same_machine_4090/coexist_inkrl_seed0.json) | 87.0451%、最终留出 KL 0.155523 |
| `normalization.unnormalized` | [ablation_unnorm_inkrl_seed0.json](https://github.com/euyis1019/INK/blob/b36c1f611516db15d3f65dac20365337fb35bc84/results/same_machine_4090/ablation_unnorm_inkrl_seed0.json) | 86.6652%、最终留出 KL 0.169934 |

## 方法实现核对

方法按 [coexist_merge.py](https://github.com/euyis1019/INK/blob/b36c1f611516db15d3f65dac20365337fb35bc84/src/ink_model_merging/model_merging_methods/coexist_merge.py) 中的默认归一化 KL-G 路径整理；二阶矩处理与线性系统见 [activation_based.py](https://github.com/euyis1019/INK/blob/b36c1f611516db15d3f65dac20365337fb35bc84/src/ink_model_merging/model_merging_methods/activation_based.py)。没有修改模型实现。

附录的 Fisher 恒等式要求正概率与精确算术。实际实现使用 float32、`epsilon=1e-8`、停止分母梯度及数值 clamp，因此本文没有把理想恒等式解释为每个浮点样本上的精确认证。二次风险边界明确固定参考目标、精确求解且无输出收缩；它不取代实际网络消融。
