# Coexist-Merge manuscript (ICLR 2027 template)

## CM 结果回填（2026-09-16）

当前编辑入口为 [motivation_method.tex](motivation_method.tex)，输出为 [motivation_method.pdf](motivation_method.pdf)。表 1 保留三个 ViT、三种任务规模的完整九格对照，主配置明确命名为 **CM + Iso-C**，并增加相对 Individual FT 的 Delta 行。只覆盖单一设定的四种子结果与起点消融单独成表，覆盖未齐的基线移至附录。T5、LLM 及其他起点详见 [CM 起点清单](motivation_method/INITIALIZATIONS.md)；缺测不填占位数。

正文的 **LLM 合并**部分用两张完整表展示 Llama-3.2-3B 的六组和 Gemma-2-2B 的四组起点对照，包含 GSM8K、IFEval 与已完成的 Llama 三域结果；附录补充参考点和校准种子重复。

**版本与配置先看 [协议对齐说明](motivation_method/PROTOCOL_ALIGNMENT.md)**：区分目标插值、FeatCal 移植、串联和多种子，列明 110 条已找到的运行及五种子待执行规范。T5 插值消融按共同 seed 0、1、2 单列，默认方法主表保留原版 CM；LLM 校准种子更正为 42。历史工作台/LLM 与正式 CLIP/T5 的 CG 初值不同，完整对齐需要修改实现并重跑，不能用旧成绩冒充已完成新规范。

- [回填说明、修正和剩余缺口](motivation_method/RESULTS_UPDATE.md)
- [可独立重建表格的数据快照](motivation_method/data/verified_results.json)
- [数据检查结果与缺测清单](motivation_method/data/result_validation.json)
- [逐运行配置清单](motivation_method/data/protocol_runs.csv) 与 [待执行的对齐规范](motivation_method/data/alignment_plan.json)
- [RegMean 与 CM 的方程和求解入门](motivation_method/LINEAR_SYSTEMS_GUIDE.md)：从逐层拟合讲到直接求解、共轭梯度与外层重测，附 CPU 示例。
- [外积与梯度形状的数值例子](motivation_method/OUTER_PRODUCT_EXAMPLE.md)：展示向量外积、完整参数外积、对角近似，以及它们与 CM 的 G 的区别。

重建表格使用 `python3 motivation_method/update_results.py`，编译使用 `bash motivation_method/build.sh`。下面涉及随机占位或旧方法的说明属于历史全文入口，不适用于已回填的 CM 聚焦稿。

## 中文引言、动机与方法精简稿

本分支的独立稿件从当前师生分歧定义 A/G，解释继续迭代及接受后的重测。主图使用本方法的归一化 KL-G 实验，展示起点适配、刷新/冻结对照和相邻轮度量变化；普通 Fisher 的实验对照已移出稿件。方法继续沿用提供的 Coexist-Merge 公式和 AXG 正规方程，附录保留归一化的理论依据。

- [编译后的 PDF](motivation_method.pdf)
- [LaTeX 主入口](motivation_method.tex)；Overleaf 选择此文件及 **XeLaTeX**。
- [章节、图表和复现说明](motivation_method/README.md)
- [论点 → issue → 原报告/源码/数据](motivation_method/SOURCE_MAP.md)

在仓库根目录运行 `bash motivation_method/build.sh`。图表 PDF 已随稿件提供，编译正文不需要 Python。
动机图使用已归档的 ViT-B/32 实测结果；跨设定主表来自 2026-09-16 核验的数据快照，不加载旧稿的占位表格或预期趋势图。
按照此次写作要求，独立稿的整篇 PDF 随源码提交；原稿及模板文件保持原样。下文为原稿的编译与内容说明。

## 编译入口

仓库根目录的 `iclr2027_conference.tex` 是主文档，加载
`INK_before_publish/main.tex` 中的当前中文论文。Overleaf 中请选择该主文档，编译器使用 **XeLaTeX**。
两种入口共用正文、图表和真实文献库，不需要维护两份文章。

在仓库根目录运行：

```bash
latexmk -xelatex -bibtex -interaction=nonstopmode -halt-on-error \
  -outdir=/private/tmp/ink-iclr2027-build iclr2027_conference.tex
```

也可进入 `INK_before_publish/` 后运行：

```bash
latexmk -xelatex -bibtex -interaction=nonstopmode -halt-on-error \
  -outdir=/private/tmp/ink-iclr2027-standalone-build main.tex
```

## 内容与模板

- 使用本仓库原版 `iclr2027_conference.sty` 和 `.bst`，保持匿名审稿、ICLR 2027 页眉及审稿行号。
- `INK_before_publish/` 中的 2027 样式副本与根目录版本一致，支持该目录独立编译。
- 章节、算法及表格仍在既有 `INK_before_publish/iclr2023/` 路径下；这是历史目录名，不代表使用旧模板。
  旧 2023 样式仅保留为历史资产，两个当前入口均不加载它们。
- 正文文献库为 `INK_before_publish/references.bib`；根目录模板附带的示例 `.bib` 不参与论文编译。
- 中文使用 ctex/Fandol。插图 PDF/SVG 是论文资源；整篇编译 PDF 和辅助文件只写临时目录，不提交。

## 当前是研究草稿，不是可直接投稿的最终稿

真实归档结果、随机占位表格和预期趋势示意仍按原稿保留。所有标注“待运行”或
“非实验结果”的内容不能被当作新实验数据。参数扫描、步长诊断及核心消融尚需实际运行。

原 2027 模板说明给出初稿正文 9 页的限制；当前编译共 15 页，正文结论位于第 10 页，已超过此限制。
本次仅迁移模板，不通过缩小字体、改页边距或删除研究内容来凑页数。
投稿前须以届时正式要求核对页数、补齐实验、审阅引用与结论，并由作者完成 AI 使用声明。
本仓库中的 AI 声明仅描述已知辅助工作，没有代替作者宣称已完成人工审核。
