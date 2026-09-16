# CM 起点实验清单

由 update_results.py 从核验快照生成。CM + X 表示先用 X 初始化，再运行 CM。主配置是 **CM + Iso-C**，CLIP 与 T5 默认初始化尺度为 1.3。

“原型 / 正式”是实现记录的来源；“4 seeds”是四次校准随机种子的重复，均不是新的方法名。不同实现、目标设定和轮数分别比较。Delta 使用百分点，负值表示低于 Individual FT。

## CLIP：固定基准实现，ViT-B/32 八任务

四种子主实验与单种子起点研究是独立运行记录。后者按留出集选中第 4 轮。

| 配置 | seeds | test 宏平均 | Delta vs. FT |
| --- | --- | --- | --- |
| Individual FT | — | 89.96 | 0.00 |
| CM + Iso-C | 1 | 87.06 | -2.91 |
| CM + WeightAvg | 1 | 85.31 | -4.65 |
| CM + RegMean | 1 | 85.55 | -4.41 |
| CM + 未拉平控制 | 1 | 78.80 | -11.16 |
| CM + Iso-C（主实验） | 4 | 87.059（样本标准差 0.021） | -2.90 |

## CLIP：工作台同配置换起点，ViT-B/32 八任务

均为 seed 0、四轮预算；正文规模表使用留出集选轮后的结果。末轮分数单列供追溯。

| 配置 | 起点 | 留出选轮 | 末轮 | Delta vs. FT |
| --- | --- | --- | --- | --- |
| CM + Iso-C | 81.40 | 86.60 | 86.65 | -3.36 |
| CM + TSV-M | 79.64 | 86.38 | 86.40 | -3.58 |
| CM + RegMean | 80.53 | 85.32 | 85.32 | -4.65 |
| CM + Zero-shot | 46.70 | 85.25 | 85.25 | -4.71 |
| CM + WeightAvg | 62.10 | 85.12 | 85.12 | -4.85 |
| CM + Task Arithmetic | 65.54 | 85.09 | 85.09 | -4.88 |

## T5：同一 seed 0 的起点对照

FeatCal 起点先由 Task Arithmetic 合并再进行 FeatCal。原始目标与目标插值是不同 CM 配置。缺测留空；缺少完整的 Individual FT 对角参考，因此不推算八任务 FT 差距。

| 配置 | base 起点 | base 原始目标 | base 插值 0.3 | large 起点 | large 原始目标 |
| --- | --- | --- | --- | --- | --- |
| CM + Iso-C | 79.64 | 84.85 | 85.59 | 82.42 | 88.99 |
| CM + FeatCal (TA) | 84.56 | 84.82 | 85.44 | 89.06 | 89.10 |
| CM + RegMean | 83.80 | 84.78 | 85.57 | 88.24 | — |
| CM + TSV-M | 82.76 | — | 85.48 | 88.09 | 89.07 |
| CM + Task Arithmetic | 78.89 | — | 85.50 | 87.30 | — |

另有相反顺序的后处理：先 CM，再 FeatCal；这些不计作 CM 初始化实验。

| 模型 | 前序 CM 配置 | 再做 FeatCal 的八任务分数 |
| --- | --- | --- |
| base | original | 84.64 |
| base | target0.3 | 84.78 |
| large | original | 89.32 |

## LLM：已完成的十组起点对照

下面是 GSM8K；IFEval 及 Llama 三域结果见论文附录和完整快照。起点增益与 FT 差距不是同一指标。

| 模型 | 配置 | 起点 | CM 后 | 起点增益 |
| --- | --- | --- | --- | --- |
| Llama-3.2-3B | CM + Model Soup | 39.95 | 54.06 | +14.10 |
| Llama-3.2-3B | CM + Task Arith. 0.4 | 40.71 | 51.86 | +11.14 |
| Llama-3.2-3B | CM + TIES 0.3/0.4 | 42.53 | 50.27 | +7.73 |
| Llama-3.2-3B | CM + TSV-M | 54.13 | 55.04 | +0.91 |
| Llama-3.2-3B | CM + RegMean 0.5 | 53.53 | 52.39 | -1.14 |
| Llama-3.2-3B | CM + Iso-C 1.3 | 52.84 | 55.65 | +2.81 |
| Gemma-2-2B | CM + Model Soup | 35.25 | 48.07 | +12.81 |
| Gemma-2-2B | CM + Task Arith. 0.4 | 39.88 | 47.46 | +7.58 |
| Gemma-2-2B | CM + TIES 0.3/0.4 | 42.91 | 46.93 | +4.02 |
| Gemma-2-2B | CM + TSV-M | 41.17 | 46.32 | +5.16 |

另外找到 Llama 的 RegMean 0.9 合并命令及完成标记，未找到可配对的完整评测，故不填成绩。命令记录为 experiments/github_runs/logs/llm_coexist_from_regmean0.9.cmd.sh。

## CLIP：起点尺度与轮数补充

这是参数敏感性记录，不作为新的起点方法，也不混入四轮默认对照。

| 记录 | 起点 | 尺度 | 轮数预算 | 留出选轮分数 | 末轮分数 |
| --- | --- | --- | --- | --- | --- |
| abl_budget_coexist_average_r12 | WeightAvg | 默认 | 12 | 85.15 | 85.18 |
| abl_budget_coexist_iso_c_r12 | Iso-C | 默认 | 12 | 86.60 | 86.33 |
| abl_budget_coexist_regmean_r12 | RegMean | 默认 | 12 | 85.32 | 85.24 |
| abl_budget_coexist_ta_r12 | Task Arithmetic | 默认 | 12 | 85.19 | 85.19 |
| abl_budget_coexist_zeroshot_r12 | Zero-shot | 默认 | 12 | 85.38 | 85.38 |
| abl_hp_coexist_isoalpha1.0 | Iso-C | 1.0 | 4 | 85.82 | 85.82 |
| abl_hp_coexist_isoalpha1.6 | Iso-C | 1.6 | 4 | 86.99 | 87.03 |
| abl_hp_coexist_isoalpha1.8 | Iso-C | 1.8 | 4 | 87.18 | 87.18 |
| abl_hp_coexist_isoalpha2.0 | Iso-C | 2.0 | 4 | 87.25 | 87.29 |
| abl_hp_coexist_isoalpha2.4 | Iso-C | 2.4 | 4 | 87.30 | 87.36 |
| abl_hp_coexist_isoalpha2.7 | Iso-C | 2.7 | 4 | 87.43 | 87.44 |
| abl_hp_coexist_isoalpha3.0 | Iso-C | 3.0 | 4 | 87.46 | 87.46 |
| abl_hp_coexist_isoalpha3.0_r8 | Iso-C | 3.0 | 8 | 87.46 | 87.35 |
| abl_hp_coexist_isoalpha3.3 | Iso-C | 3.3 | 4 | 87.41 | 87.41 |
| abl_hp_coexist_isoalpha4.0 | Iso-C | 4.0 | 4 | 86.72 | 86.72 |
| abl_hp_coexist_isoalpha6.0 | Iso-C | 6.0 | 4 | 86.65 | 86.65 |
| abl_scale_average_a12.0 | WeightAvg | 12.0 | 4 | 67.79 | 67.79 |
| abl_scale_average_a3.0 | WeightAvg | 3.0 | 4 | 85.09 | 85.09 |
| abl_scale_average_a6.0 | WeightAvg | 6.0 | 4 | 84.94 | 84.94 |
| abl_scale_ta_a0.75 | Task Arithmetic | 0.75 | 4 | 84.94 | 84.94 |
| abl_scale_ta_a1.5 | Task Arithmetic | 1.5 | 4 | 67.79 | 67.79 |

## 逐项来源

[CSV 清单](data/cm_initializations.csv) 保存每项配置、完整精度数值、种子和来源文件；[核验快照](data/verified_results.json) 保存逐任务结果与输入文件 SHA-256。来源路径相对实验工作区，历史文件名不代表另一个方法。
