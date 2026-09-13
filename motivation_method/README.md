# 中文 motivation → method 稿件

主入口为仓库根目录的 [motivation_method.tex](../motivation_method.tex)，预览为 [motivation_method.pdf](../motivation_method.pdf)。沿用本仓库 ICLR 2027 模板、匿名页眉、字号和页边距。这是一份可接入完整论文的聚焦稿件，未替换旧版全文。

## 内容与编辑位置

| 内容 | 文件 | 写作作用 |
|---|---|---|
| Motivation | [sections/motivation.tex](sections/motivation.tex) | 先检验专家/学生测量位置，再解释继续迭代与接受后的重测 |
| Method | [sections/method.tex](sections/method.tex) | 沿用本次提供的逐类修正、归一化方向、A/G 与 AXG 正规方程，补齐估计和伪代码 |
| 效果与适用范围 | [sections/experiments.tex](sections/experiments.tex) | 用精简主表和跨设定结果验证效果；初始化作为附加性质 |
| 附录 A | [sections/appendix.tex](sections/appendix.tex) | 位置对照的协议、完整起点与冻结对照、同状态和跨 block 干预、直接归一化消融 |
| 附录 B | 同上 | Fisher 几何界、方向重加权恒等式、二次合并的条件性风险边界及反例 |

主文保留一张双联图：(a) 同一起点上 ordinary-Fisher 的学生/专家首轮提案，(b) KL-G 的 Average 刷新/冻结轨迹。两面板对应两个动机，统计定义和指标各自明确。附录保留跨 block 图及负结果。跨设定结果用两张小表呈现，不增加趋势图。

主线是“度量在哪个模型上测 → 接受更新后为何重测 → 如何估计、求解和接受”。采用本次说明中的方法名 Coexist-Merge，保留原稿入口文件名。任务适用性、初始化适配均是需验证的性质，不预设所有任务都提升或任意起点同解收敛。

位置对照的首轮数据支持 ordinary-Fisher 构造中的测量位置选择，并不单独证明最终 KL-G 的全部设计。最终方法用归一化 KL 纠正二阶矩；它与普通 Fisher、真实 KL Hessian 有明确区别。

## 编译与图表复现

已提交矢量图及表格，编译只需 XeLaTeX、BibTeX、latexmk，以及 ctex/Fandol、algorithm2e 等常用 TeX 包：

```bash
bash motivation_method/build.sh
```

脚本从仓库根目录编译，将辅助文件写入 `build-motivation/`，成功后更新根目录 `motivation_method.pdf`。Overleaf 直接选择新主入口即可，不必运行脚本。

重画图表需要 Python 3.10+、NumPy、Matplotlib。图表从 [evidence.json](evidence.json)、[data/fisher_first_round.json](data/fisher_first_round.json) 和 [data/main_results.json](data/main_results.json) 读取；不会访问服务器或运行模型：

```bash
python3 motivation_method/make_figures.py
bash motivation_method/build.sh
```

默认图中文字使用 TeX 自带 Fandol。也可通过 `--font /path/to/chinese-font.ttf` 指定中文 TrueType 字体；提交版本使用 macOS 自带的 Arial Unicode 字体生成，字体文件未打包。不同字体可能改变外观，不改变数据与坐标。矢量 PDF 用于正文，同名 PNG 便于预览。

## 与现成公式及证据的关系

[本次提供的方法与主结果说明](sources/coexist_method_results_20260912.md) 按原文归档。正文沿用其公式链，不采用原说明中比数值表更强的概括。T5-base 明确含目标插值扩展；LLM 保留部分指标下降，不写所有基线均被超越。该说明的主实验表是本节来源，本次没有重跑模型，也未逐项核查其全部实验日志。

只作必要的记号澄清：

- 层输入为 `h`，层输出为 `y`；A 使用输入，score 与 KL 梯度对输出求导。
- 权重采用输入维度 × 输出维度，正规方程为 `sum A X G = sum A W_t G`，与实现转置权重一致。
- `bar s = E_q[s]` 明确定义；u 的分母停止梯度，反传得到的负号不影响外积。
- 求解式中的 A/G 指尺度统一和收缩后的矩阵；归一化证明作用于处理前的纠正外积。
- 用有限 CG 求解 Kronecker 和，不把“未显式求逆”写成数学上不存在形式解。

T5 目标插值扩展在本稿中仅标明其结果归属，未把原说明中输入/输出混用的交叉矩公式直接移入主方法。主方法给出原版专家锚点 AXG 方程。

[来源索引](SOURCE_MAP.md) 区分三种证据：固定版本的报告与原始数据、这次核对的同环境 Fisher 配对记录，以及用户提供的跨设定主实验汇总。历史学生 ordinary-Fisher 87.2704%、同环境复跑 87.2941%、最终 KL-G 正式四 seed 87.06% 不拼接成同一轨迹。

校准图像固定，状态依赖来自内部输入、预测与下游传播的改变；本文没有把这一流程定义为强化学习的 on-policy 采样。
