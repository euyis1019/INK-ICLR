# INK-Merge manuscript (ICLR 2027 template)

## 新增：中文 motivation → method 精简稿

本分支的独立稿件从当前师生分歧定义 A/G，解释继续迭代及接受后的重测。主图使用本方法的归一化 KL-G 实验，展示起点适配、刷新/冻结对照和相邻轮度量变化；普通 Fisher 的实验对照已移出稿件。方法继续沿用提供的 Coexist-Merge 公式和 AXG 正规方程，附录保留归一化的理论依据。

- [编译后的 PDF](motivation_method.pdf)
- [LaTeX 主入口](motivation_method.tex)；Overleaf 选择此文件及 **XeLaTeX**。
- [章节、图表和复现说明](motivation_method/README.md)
- [论点 → issue → 原报告/源码/数据](motivation_method/SOURCE_MAP.md)

在仓库根目录运行 `bash motivation_method/build.sh`。图表 PDF 已随稿件提供，编译正文不需要 Python。
动机图使用已归档的 ViT-B/32 实测结果；跨设定主表摘录本次提供的方法与结果说明，不加载旧稿的占位表格或预期趋势图。
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
