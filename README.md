# COMP8800 / JHQ-GPU LaTeX 模板

这是一套为本项目准备的英文 thesis 模板，不是 ANU 官方指定样式，也不是已完成的论文。章节按本目录 `6.pdf` 的九章骨架生成；不自动把蓝图文字、旧 ADC 数字或未经核验的结果写成正文。

## 当前审核入口

第五章（5.1--5.7）和第七章已写入论文总稿；其他未完成正文仍为写作骨架。

- [论文总稿 thesis.pdf](thesis.pdf)
- [中文阅读对照稿 thesis-zh.pdf](thesis-zh.pdf)：包含第五章、第七章的完整翻译。
- [第 5.1 节：查询路径与排序对象](chapters/05-1-query-path.tex)
- [第 5.1 节核对与命题排版说明](assessment/ch5-section-1-evidence.txt)
- [第 5.2 节：LUT](chapters/05-2-lut.tex)、[5.3：packed access](chapters/05-3-packed-access.tex)、[5.6：精排](chapters/05-6-refinement.tex)、[5.7：probe selection](chapters/05-7-probe.tex)
- [第 5.2、5.3、5.6、5.7 节核对记录](assessment/ch5-sections-2-3-6-7-evidence.txt)
- [第 5.4 节：全局主码 top-c](chapters/05-4-global-selection.tex)与[第 5.5 节：共享界和调度](chapters/05-5-bound-scheduling.tex)
- [第 5.4、5.5 节源码核对记录](assessment/ch5-sections-4-5-evidence.txt)
- [第七章正文](chapters/07-evaluation.tex)
- [数据核对说明（含中文结论）](data/ch7/README.txt)
- [数值核对结果](data/ch7/audit.json)与[原始证据文件哈希](data/ch7/sources.csv)
- [Claude 审稿意见逐项复核与处理](assessment/ch7-review-response.txt)
- [GPT 旧版审稿意见复核](assessment/ch7-gpt-review-response.txt)
- [待补实验清单（GPU 可用后）](assessment/ch7-pending-experiments.txt)

审核重点：结论是否得到实验支持、跨系统比较是否公平、精确性声明是否限定到相应阶段，以及校准的质量风险和回本估计是否表述准确。原始实验输入来自本地同级 `JHQ_GPU` 工作区，路径见证据清单；本报告仓库提供分析脚本和衍生数据，但不包含全部原始输入。重新生成分析需要另外取得清单中的文件及相关历史源码，不能将哈希清单本身视为原始文件已公开或 GPU 实验已独立重现的证明。

当前审核应覆盖已完成的第五章、第七章与附录 A。第 5.5 节明确保留共享界 `volatile` 读取的并发保证限制；相关实现修订和 GPU 复验仍在待办清单中。第 5.6 节区分精排排序分数与原空间距离；第七章区分实测结果、离线收益估算及尚未执行的补充实验。

## 编译

在本目录运行：

```sh
latexmk -pdf main.tex
```

直接编译输出为 `build/main.pdf`。运行 `make pdf` 会将论文总稿更新到根目录的 `thesis.pdf`，第七章已放入总稿。模板采用 pdfLaTeX + BibTeX；不需要 shell escape、外部字体、Python 或额外绘图程序。

Overleaf：上传源文件，选择 `main.tex` 为主文档，编译器设为 **pdfLaTeX**。若修改编译输出目录，请同步检查输出路径。避免将 `build/` 中的历史中间文件上传为源文件。

中文阅读稿运行 `make pdf-zh`，输出为 `thesis-zh.pdf`。它使用 `main-zh.tex`、XeLaTeX 和 TeX 随附的 Fandol 中文字体，保持英文稿的章节与图表编号。中文正文位于 `zh/chapters/`；图内英文标签保留，第七章表格数字由 `scripts/build_zh_tables.py` 从英文表格复用。英文提交稿仍使用原来的 `make pdf`。

## 从哪里开始

1. `config/metadata.tex`：标题、姓名、导师、月份、可选学号和草稿开关。
2. `chapters/`：九章、53 个小节的写作骨架。修改或合并标题不会影响模板运行。
3. `figures/`：放论文图件；优先使用矢量 PDF。用相对路径引用，避免依赖本机绝对路径。
4. `references.bib`：六条从现有 ADC 源文件复用的参考文献记录，提交前核对元数据。
5. `appendices/d-template-examples.tex`：引用、交叉引用、表格、公式、证明、代码和 TikZ 图的可编译示例，仅在草稿模式显示。

模板中的英文 `TO WRITE` 是写作提示，不能作为论文内容提交。表格中的 `To complete` 也必须填写或删除。

## 排版默认值

- A4，单面单栏，12pt Latin Modern 字体。
- 30mm 页边距，1.3 倍行距。
- 前置部分罗马页码，正文阿拉伯页码，附录字母编号。
- 自动目录、图目录、表目录、PDF 书签和可点击交叉引用。
- 数字引用，`natbib` + `plainnat`；没有套用 ADC 的 LNCS 或 ACM 双栏样式。

修改 `config/preamble.tex` 可调整页边距、行距、标题和引用形式。上述均为模板选择，不能声称为本届课程硬性规定。

## 提交模式

正文写完后，在 `config/metadata.tex` 中改为：

```tex
\draftthesisfalse
```

该模式会去掉草稿页脚和示例附录；任何残留的 `\draftnote` 或 `\figureplaceholder` 会使编译失败，要求先完成内容。模板不验证研究真实性、引用完整性或课程合规性。

检查声明页、贡献归属、真实工具使用记录和全部占位表格；模板没有预写“所有结果已经检查”等未经确认的承诺。签名与正式声明措辞按 Canvas 的实际要求填写。

可用下列命令查找提示，再人工复核 PDF：

```sh
rg -n 'draftnote|figureplaceholder|To complete' chapters frontmatter appendices
```

`appendices/d-template-examples.tex` 本身是示例，提交模式自动排除。若不需要致谢、符号表或某个附录，在 `main.tex` 中移除相应 `\input`。

## 字数

```sh
make wordcount
```

该命令需要额外提供 `texcount`；没有它也可正常编译 PDF。它按章节估算字数。声明、参考文献、图注、公式和附录的计数规则，以本届 Canvas 为准；工具输出不是官方字数认证。不要为了匹配典型页数而压缩字号或减少必要图表。

## 已核对的要求与来源

详见 `FORMAT_NOTES.txt`。公开课程页将详细指导交给 Canvas；目前查看到的资料没有规定必须使用哪种 LaTeX 文档类、字体、页边距或行距。本模板可在拿到进一步要求后集中调整。
