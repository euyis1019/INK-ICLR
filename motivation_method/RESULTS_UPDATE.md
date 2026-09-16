# CM 结果回填记录

日期：2026-09-16。论文基于克隆时的 `main` 提交 `0cb6f41` 修改；目标是 `motivation_method.tex` 及其 PDF。只报告 CM、明确命名的 CM 扩展和外部参照，未运行模型实验。

## 已回填

- **CLIP 表 1：**仅纳入三个骨干、三种任务规模均有宏平均结果的方法；CM 行统一为 `CM + Iso-C`，紧接一行相对各列 Individual FT 的 Delta。九格来自工作台规模扫描，不加入只有一格的四种子行。归一化逐任务使用对应环境的专家分母。
- **单设定重复与起点表：**固定基准实现的 ViT-B/32 八任务单独成表；CM + Iso-C 四种子均值 87.059，样本标准差 0.021，相对 FT 为 -2.90 个百分点。独立 seed 0 起点研究中，CM + WeightAvg 为 85.31、CM + RegMean 为 85.55、CM + Iso-C 为 87.06；保留未拉平控制。四种子重复与单种子起点研究不混为同一运行。
- **方法命名：**`CM + X` 表示先 X 合并再运行 CM；CLIP 与 T5 默认均为 Iso-C，初始化尺度固定为 1.3。“原型 / 正式”改为实现来源说明，种子数单列，不当作方法名称。未覆盖全规模的 ESM、SVC (ESM) 移到附录，已有八格数值全部保留。
- **T5-base 逐任务表：**替换所有随机数字，报告八专家一次性合并后的 GLUE validation 结果；原来的“持续合并”表述不适用。缺测以横线表示。
- **T5 版本与重复：**原版 base 五种子；目标插值 0.3 四种子，0.6 三种子；large 原版与 0.3 扩展均单种子并分别列行。FeatCal 五种子的样本标准差为 0.22，原来的 0.19 是总体标准差。所有种子误差统一为样本标准差。
- **LLM：**正文独立段落和两张表完整展示 Llama 六组、Gemma 四组起点对照，附录保留参考点与校准种子重复。结果从 GSM8K、IFEval 和已完成的 multilingual 原始评测重算；起点增益先用未舍入数相减，再显示两位小数，保留负向结果。缺少完整评测的 coding、safety 和 Gemma multilingual 不补数，也不计算五域宏平均。
- **起点附表：**CLIP 工作台六起点同时列留出选轮分数、末轮分数和 FT 差距；按选轮分数，CM + WeightAvg 为 85.12、CM + RegMean 为 85.32、CM + TSV-M 为 86.38。T5 分列原始目标与插值 0.3，补入原始目标的 FeatCal、RegMean 起点。默认 base 插值 0.3 使用配对 seed 0 的 85.59，不以四种子均值 85.64 替换。
- **起点索引：**[INITIALIZATIONS.md](INITIALIZATIONS.md) 汇总 CLIP、T5、LLM 起点与额外尺度、轮数记录；[CSV](data/cm_initializations.csv) 保存完整精度分数及逐项来源。尺度和轮数敏感性单列，不伪装成新的方法。
- **反方向后处理更正：**先原始目标 CM 再 FeatCal 的 T5-base 为 84.64；84.78 对应先目标插值 0.3 CM 再 FeatCal。二者均不属于“从 FeatCal 初始化 CM”的实验。

## 仍缺的实测格

| 内容 | 处理 |
|---|---|
| 固定基准实现除 B/32 八任务外的八个规模格 | 单设定结果另表，不在表 1 增加八个空格；表 1 使用完整工作台规模扫描 |
| L/14 二十任务的 ESM 和 SVC (ESM) | 移至附录规模补充表，其余八格保留，缺测格留空 |
| L/14 二十任务的 Iso-C、Iso-CTS、TSV-M 逐任务分数 | 只有从日志恢复的两位小数宏平均；保留绝对分，下标留空，不推算归一化 |
| T5-base 零样本后四任务 | 已有前四任务填入，八任务均值留空 |
| T5 独立专家的完整对角评测 | 只填 CoLA 专家在 CoLA 上的结果，不能将同一个专家的跨任务测试误当作八专家参考 |
| T5-large 目标插值 0.6 | 未找到完成的八任务评测，留空 |
| T5 的其他视觉基线适配 | 未完成的行不展示随机数，也不从视觉结果迁移数值 |
| Llama 从 RegMean 0.9 开始的 CM | 只有合并命令与完成标记，未找到可配对的完整评测，不填数字 |

机制图和理论部分沿用已有归档，本次没有改变数学推导或把单种子机制结果升级为多种子结论。

## 复现与来源

`data/verified_results.json` 保存完整数值、每条记录的来源路径与选点口径，`sources` 保存输入文件 SHA-256；路径均相对实验工作区。源文件名称中的历史标识不改变结果的方法归属。

从本仓库自带快照重建表格：

```bash
python3 motivation_method/update_results.py
bash motivation_method/build.sh
```

从父目录实验工作区重新核验并回填：

```bash
python3 motivation_method/update_results.py --workspace ..
bash motivation_method/build.sh
```

`make_figures.py` 也调用同一表格生成器，重画机制图不会恢复旧汇总或占位表。最初提供的 Markdown 与抽取 JSON 保留在 `sources/`，只用于追溯。
