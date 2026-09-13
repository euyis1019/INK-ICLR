# 中文 motivation → method 稿件

主入口为仓库根目录的 [motivation_method.tex](../motivation_method.tex)，预览为 [motivation_method.pdf](../motivation_method.pdf)。沿用本仓库 ICLR 2027 模板、匿名页眉、字号和页边距。这是一份可接入完整论文的聚焦稿件，未替换旧版全文。

## 内容与编辑位置

| 内容 | 文件 | 写作作用 |
|---|---|---|
| Motivation | [sections/motivation.tex](sections/motivation.tex) | 提出专家约束在当前网络中是否仍然合适的问题，解释当前输入、下游传播和师生分歧的作用 |
| Method | [sections/method.tex](sections/method.tex) | 从局部功能影响解释学生 A/G 的测量，以专家为锚点构造回归代理，给出求解、选步和重估流程 |
| 设计检验 | [sections/evidence.tex](sections/evidence.tex) | 方法之后依次检验统计状态依赖、重估价值和起点适配；将数据与设计假设对应 |
| 附录 A | [sections/appendix.tex](sections/appendix.tex) | 划分/预算、完整起点与冻结对照、同状态和跨 block 干预、直接归一化消融 |
| 附录 B | 同上 | Fisher 几何界、方向重加权恒等式、二次合并的条件性风险边界及反例 |
| 文献 | [references.bib](references.bib) | 使用真实论文来源，未使用旧稿的占位结果 |

主文只保留一张三联图：(a) 相邻状态的度量变化、(b) Average 的刷新/冻结轨迹、(c) 初始化轨迹。顺序对应“变化存在 → 处理变化有价值 → 适配效果”。附录保留一张跨 block 干预图，并显示 block 0 的负结果。其余关键结果以数值和两张小表呈现；图表均可独立移入完整论文。

核心设计原则是“专家提供参数目标，当前学生提供衡量这些目标的输入统计和纠正统计”。迭代与刷新由这一原则引出，起点适配是需要验证的效果。正文明确区分 KL 的一阶功能关系与所构造的二次回归代理，未把纠正外积当作 KL Hessian，也未声称由 Taylor 展开严格导出了整个求解器。

“对初始化不敏感”限定为常用合并起点的功能差距可显著缩小，不宣称任意起点同解收敛。刷新收益依赖初始化与阶段。归一化命题针对明确的几何预算或二次代理目标，不是实际网络准确率的无条件优势定理。

## 编译与图表复现

已提交矢量图及表格，编译只需 XeLaTeX、BibTeX、latexmk，以及 ctex/Fandol、algorithm2e 等常用 TeX 包：

```bash
bash motivation_method/build.sh
```

脚本从仓库根目录编译，将辅助文件写入 `build-motivation/`，成功后更新根目录 `motivation_method.pdf`。Overleaf 直接选择新主入口即可，不必运行脚本。

重画图表需要 Python 3.10+、NumPy、Matplotlib。所有数值读自 [evidence.json](evidence.json)，不会访问服务器或运行模型：

```bash
python3 motivation_method/make_figures.py
bash motivation_method/build.sh
```

默认图中文字使用 TeX 自带 Fandol。也可通过 `--font /path/to/chinese-font.ttf` 指定中文 TrueType 字体；提交版本使用 macOS 自带的 Arial Unicode 字体生成，字体文件未打包。不同字体可能改变外观，不改变数据与坐标。矢量 PDF 用于正文，同名 PNG 便于预览。

## 与实现和证据的关系

参见 [SOURCE_MAP.md](SOURCE_MAP.md)，其中链接固定版本的实验报告、LaTeX 和数据，避免仓库更新后来源漂移。`evidence.json` 保留原始数据文件的 SHA-256 及所用字段；图表数值没有手工平滑或插值。

本文的 `G` 是归一化教师到学生 KL 纠正的未中心化二阶矩。历史 ordinary-Fisher 的 87.2704% 属于另一种统计模式，未与本文 KL-G 轨迹混用。`A/G` 都在当前学生测量，教师提供固定分布与参数锚点。这里的状态依赖来自内部激活、预测及 Jacobian 的改变，校准图像固定；文中未把它定义为强化学习的 on-policy 采样。

正文按输出乘输入形状写权重 `W`，正规方程为 `sum G W A = sum G W_t A`；实现以转置权重求解 `sum A W^T G`，两者等价。外积代理不是精确 KL Hessian，真实留出 KL 用于接受提案。
