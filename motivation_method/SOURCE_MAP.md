# 论点、实验与来源

本稿整理已有工作，不新增模型运行。证据分为已归档实验报告、同环境 Fisher 配对原始记录、以及本次提供的跨设定主实验说明。第三类结果未在本次写作中逐项回查全部运行日志；不把原文中的概括自动当作数据结论。

## 主线对应关系

| 本稿位置 | 实验如何支持论点 | 对应来源 |
|---|---|---|
| §1 图 1a：测量位置 | 同一初始化、任务、数据、ordinary-Fisher 定义、求解与选步，只切换 A/G 所在网络；保留全部预设步长，首轮尚未涉及后续刷新 | [五点原始表](data/fisher_first_round.json)、[完整配对记录](data/fisher_pair_summary.json)；[Issue #8](https://github.com/euyis1019/INK/issues/8#issuecomment-5648267989) 为相关讨论 |
| §1 图 1b：继续迭代与重测 | 刷新/冻结从共享第一轮状态出发，都继续 CG 与选步；另列单次 CG400 | [Issue #7](https://github.com/euyis1019/INK/issues/7#issuecomment-5648265839)；R2/R4 |
| §1 同状态干预、附录 A 图 2 | 固定同一待更新状态交换统计，并保留跨 block 与等幅负结果 | R2 的三份数据文件；这些干预属于 KL-G，不与图 1a 混用 |
| §2 公式与算法 | 沿用提供的 a、hat-a、u、G 和 AXG 公式；区分输入 h 与输出 y，补齐 bar-s；说明统计处理、CG、留出选步及重测 | [提供的方法说明](sources/coexist_method_results_20260912.md) §1；下方实现链接 |
| §3 主实验与适用范围 | 摘录 CLIP/T5 主表、LLM 起点对照，保留实现差异、T5 扩展和负结果 | [提供的主实验说明](sources/coexist_method_results_20260912.md) §2–5；[机器可读表格](data/main_results.json) |
| §3、附录 A 起点性质 | Average/RegMean 诊断差距 22.36→0.15 pp；保留未拉平起点的终态差异 | [Issue #6](https://github.com/euyis1019/INK/issues/6#issuecomment-5648265351)；R1/R3 |
| §2、附录 A/B 归一化 | 同机归一化消融、Fisher 相对预算与条件性风险界 | [Issue #5](https://github.com/euyis1019/INK/issues/5#issuecomment-5648435999)；R5 |

## 本次加入的原始材料

- `data/fisher_first_round.json`：原 `first_round_proposals.json` 的逐字节副本；与完整配对汇总和逐行线搜索日志的首轮五点交叉核对。
- `data/fisher_pair_summary.json`：原 `paired_summary.json` 的逐字节副本，保留初始状态哈希、环境、资产指纹、配置摘要、首轮提案及各轮记录。
- `sources/coexist_method_results_20260912.md`：本次提供文本的逐字节副本。保留原文是为了追溯；原文第 6 节“所有基线”等强结论没有被正文采用。
- `data/main_results.json`：从该文本的 Markdown 表格直接抽取，包含来源 SHA-256 和主表所用行；不手工补造未运行项。
- `data/source_checks.json`：本次使用材料的哈希与配对核对结果；跨设定主表明确标为提供的汇总数据，而非本次复跑。

首轮全局步长 0.5 的学生/专家 KL 为 0.161849/0.246323；完整首轮选步结束后测试为 87.1999%/85.1609%。这两种指标对应不同阶段。最终复跑选择结果为 87.2941%/85.1807%，不替换为历史学生 87.2704%。

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
| `data/fisher_first_round.json → student/expert.trials` | 图 1a：原有全部五个全局候选点，纵轴为留出教师 KL |
| `evidence.json → refresh.Average.trajectory` | 图 1b、附录冻结表：完整测试准确率，原有同状态和预算对照 |
| `evidence.json → refresh.*.moment_hook_summary / cross_block` | 正文统计变化、同状态干预与附录图 2 |
| `evidence.json → multistart` | §3 初始化性质与附录四起点表；原图中的初始化轨迹未再占用主图面板 |
| `data/main_results.json → clip_main / t5_main` | 主文表 1，T5-base 含目标插值扩展，large 选择原版 |
| `data/main_results.json → llama / gemma` | 主文表 2，所选行含收益与下降，不能解释为所有基线排名 |
| `data/main_results.json → clip_scaling` | 九格收益范围；工作台实现与正式 CLIP 结果分开 |
| `evidence.json → normalization` | 87.0451%/86.6652% 直接消融，已有独立运行 |

准确率差为百分点；KL/JS 不是百分数。位置对照和刷新诊断都是 seed 0，不能借主表的多 seed 数量为机制实验声明跨 seed 显著性。校准与留出分离；诊断测试从未用于接受、选步和选轮。

## 固定版本实现和原始数据链接

| 本地字段 | 固定版本文件 | 用途 |
|---|---|---|
| `multistart.accuracy`、`multistart.pairs` | [derived_results.json](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/cm_motivation_2pages/data/derived_results.json) | 附录四起点表及功能距离诊断 |
| `refresh.Average` | [Average.json](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/klg_iteration_motivation_paper/data/Average.json) | 图 1b、附录图 2 和冻结表、同状态/等幅干预 |
| `refresh.Iso-C` | [Iso-C.json](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/klg_iteration_motivation_paper/data/Iso-C.json) | 附录冻结表与统计变化 |
| `refresh.RegMean` | [RegMean.json](https://github.com/euyis1019/INK/blob/984679b6455c353fa9321684f2738a9a292ce1f8/reports/latex/klg_iteration_motivation_paper/data/RegMean.json) | 附录冻结表与统计变化 |
| `normalization.normalized` | [coexist_inkrl_seed0.json](https://github.com/euyis1019/INK/blob/b36c1f611516db15d3f65dac20365337fb35bc84/results/same_machine_4090/coexist_inkrl_seed0.json) | 87.0451%、最终留出 KL 0.155523 |
| `normalization.unnormalized` | [ablation_unnorm_inkrl_seed0.json](https://github.com/euyis1019/INK/blob/b36c1f611516db15d3f65dac20365337fb35bc84/results/same_machine_4090/ablation_unnorm_inkrl_seed0.json) | 86.6652%、最终留出 KL 0.169934 |

## 方法实现核对

方法按 [coexist_merge.py](https://github.com/euyis1019/INK/blob/b36c1f611516db15d3f65dac20365337fb35bc84/src/ink_model_merging/model_merging_methods/coexist_merge.py) 中的默认归一化 KL-G 路径整理；二阶矩处理与线性系统见 [activation_based.py](https://github.com/euyis1019/INK/blob/b36c1f611516db15d3f65dac20365337fb35bc84/src/ink_model_merging/model_merging_methods/activation_based.py)。没有修改模型实现。

附录的 Fisher 恒等式要求正概率与精确算术。实际实现使用 float32、`epsilon=1e-8`、停止分母梯度及数值 clamp，因此本文没有把理想恒等式解释为每个浮点样本上的精确认证。二次风险边界明确固定参考目标、精确求解且无输出收缩；它不取代实际网络消融。
