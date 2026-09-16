# 中文 motivation → method 稿件

主入口为仓库根目录的 [motivation_method.tex](../motivation_method.tex)，预览为 [motivation_method.pdf](../motivation_method.pdf)。沿用本仓库 ICLR 2027 模板、匿名页眉、字号和页边距。这是一份可接入完整论文的聚焦稿件，未替换旧版全文。

2026-09-16 已回填 CM 实测数据。表 1 只展示三个 ViT、三种任务规模均有结果的九格对照；主配置标为 **CM + Iso-C**，增加相对 Individual FT 的 Delta 行。ViT-B/32 八任务的四种子结果与起点消融另表呈现，种子数单列。T5-base 逐任务表、附录 T5-large、LLM 和起点对照同步更新。详见 [回填记录](RESULTS_UPDATE.md) 和 [CM 起点清单](INITIALIZATIONS.md)。灰底只用于突出 CM 行，不再表示随机占位。

## 内容与编辑位置

| 内容 | 文件 | 写作作用 |
|---|---|---|
| Motivation | [sections/motivation.tex](sections/motivation.tex) | 从当前师生分歧定义度量，再解释继续迭代与接受后的重测 |
| Method | [sections/method.tex](sections/method.tex) | 沿用本次提供的逐类修正、归一化方向、A/G 与 AXG 正规方程，补齐估计和伪代码 |
| 效果与适用范围 | [sections/experiments.tex](sections/experiments.tex) | 用精简主表和跨设定结果验证效果；初始化作为附加性质 |
| 附录 A | [sections/appendix.tex](sections/appendix.tex) | 度量变化的定义、完整起点与冻结对照、同状态和跨 block 干预、直接归一化消融 |
| 附录 B | 同上 | Fisher 几何界、方向重加权恒等式、二次合并的条件性风险边界及反例 |

主文恢复一张三联图：(a) Average、RegMean、Iso-C 的起点适配，(b) Average 的刷新/冻结轨迹和单轮 CG400，(c) 三种起点的相邻轮度量变化。全部来自本方法的归一化 KL 纠正统计。附录保留跨 block 图与负结果；系统规模对照、单设定重复和起点消融分别呈现。

C 的纵轴是按求解规则处理后的度量在相邻两轮之间的 `1 - 余弦相似度`，再在有效层/任务上取中位数。度量指尺度处理与收缩后的 `M = G ⊗ A`，采用正文的转置权重约定。数值越小，度量方向越接近；不表示参数距离、KL 降低量或准确率。Average 从 0→1 轮约 0.447，降到 3→4 轮约 0.007。纵轴为对数尺度，颜色与 A 面板一致。

正文仅用简短设计直觉说明当前学生上的测量参照；机制实验集中于迭代、统计重测与起点适配。两份 Fisher 实验数据副本及其论证已移出此稿；原始实验档案和历史提交保留。附录中的 Fisher 相对界是归一化的数学参照，不属于该测量实验。

主线为“当前师生修正需求 → 逐层求解 → 接受后重测”。任务适用性和初始化适配作为性质验证，不预设所有任务都提升或任意起点同解收敛。

## 编译与图表复现

已提交矢量图及表格，编译只需 XeLaTeX、BibTeX、latexmk，以及 ctex/Fandol、algorithm2e 等常用 TeX 包：

```bash
bash motivation_method/build.sh
```

脚本从仓库根目录编译，将辅助文件写入 `build-motivation/`，成功后更新根目录 `motivation_method.pdf`。Overleaf 直接选择新主入口即可，不必运行脚本。

重画图表需要 Python 3.10+、NumPy、Matplotlib。动机图从 [evidence.json](evidence.json) 读取，结果表从 [data/verified_results.json](data/verified_results.json) 读取；不会访问服务器或运行模型：

```bash
python3 motivation_method/make_figures.py
bash motivation_method/build.sh
```

只重新生成数值表格无需绘图库：`python3 motivation_method/update_results.py`。若该论文仓库放在实验工作区的 `INK-ICLR/` 下，可用 `python3 motivation_method/update_results.py --workspace ..` 从原始结果重新导入。导入会核验任务宏平均、配对种子、缺测、指标定义与 LLM 差值，并记录每个输入文件的 SHA-256。

默认图中文字使用 TeX 自带 Fandol。也可通过 `--font /path/to/chinese-font.ttf` 指定中文 TrueType 字体；提交版本使用 macOS 自带的 Arial Unicode 字体生成，字体文件未打包。不同字体可能改变外观，不改变数据与坐标。矢量 PDF 用于正文，同名 PNG 便于预览。

## 与现成公式及证据的关系

[最初提供的方法与主结果说明](sources/coexist_method_results_20260912.md) 按原文归档。正文沿用其公式链，不采用原说明中比数值表更强的概括。当前结果表以 2026-09-16 回查的运行 JSON 为准，旧说明中的均值、误差与种子数不能覆盖核验快照。T5 原版与目标插值扩展分行；LLM 保留部分指标下降。回填没有重跑模型。

只作必要的记号澄清：

- 层输入为 `h`，层输出为 `y`；A 使用输入，score 与 KL 梯度对输出求导。
- 权重采用输入维度 × 输出维度，正规方程为 `sum A X G = sum A W_t G`，与实现转置权重一致。
- `bar s = E_q[s]` 明确定义；u 的分母停止梯度，反传得到的负号不影响外积。
- 求解式中的 A/G 指尺度统一和收缩后的矩阵；归一化证明作用于处理前的纠正外积。
- 用有限 CG 求解 Kronecker 和，不把“未显式求逆”写成数学上不存在形式解。

T5 目标插值扩展在本稿中仅标明其结果归属，未把原说明中输入/输出混用的交叉矩公式直接移入主方法。主方法给出原版专家锚点 AXG 方程。

[来源索引](SOURCE_MAP.md) 区分已归档的 KL-G 机制实验与日志回填的跨设定结果。图 1a 使用独立诊断集，图 1b 使用完整测试集，图 1c 使用固定校准图像；不同面板的数值各按其协议解释。

校准图像固定，状态依赖来自内部输入、预测与下游传播的改变；本文没有把这一流程定义为强化学习的 on-policy 采样。
