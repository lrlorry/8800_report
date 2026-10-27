# COMP8800 / JHQ-GPU Thesis

九章正文和摘要均有中英文总稿。本轮已把Claude于2026-10-28完成的
`JHQ_GPU/experiments/thesis_evidence` 补证核对后纳入第3--9章、引言与摘要。
新增TF32/FP32敏感性、重复空缓存构建与采样峰值、表示审计、完整预算决策及直接复用计时。
补证基线已发布为 `1786e6e`。后续已补全Conclusion后的附录B/C，整理前置页，
移除示例附录及草稿文字，并默认启用正式编译。核对过程没有启动GPU实验。

- [本轮补证整合与边界](assessment/supplement-integration.txt)
- [补证离线复算](scripts/audit_supplement.py) · [数值和输入哈希](data/supplement/audit.json)
- [最新完成／待补清单](assessment/ch7-pending-experiments.txt)：C2严格CPU top-c与C3 Vogue诊断仍未完成。
- [上一轮章节迭代记录](assessment/synthesis-iteration.txt)

个人分工、声明签署与最终工具披露仍需作者确认，见
[作者确认项](assessment/author-confirmation.txt)。研究来源页及附录B/C已写入正式内容；个人课程签署由作者按实际任务办理。

第 3 章已按 `6.pdf` 的六节骨架完成中英文正文；统一研究对照、数据／GT／划分、
计时与显存口径、基线前沿和证据等级。见
[第 3 章证据说明](assessment/ch3-evidence.txt)；离线核对入口为
`python3 scripts/audit_ch3.py`，机器清单为 `data/ch3/audit.json`。

总稿按本目录 `6.pdf` 的九章骨架组织；排版不是 ANU 官方指定样式。
蓝图文字、旧 ADC 数字和未经核验的结果不自动成为当前实验结论。

## 当前审核入口

第一至九章正文及摘要均已写入总稿。最新的综述、引言、讨论、结论和摘要
离线核对入口为 `python3 scripts/audit_synthesis.py`；负结果复算为
`python3 scripts/audit_ch8.py --no-plot`。

- [论文总稿 thesis.pdf](thesis.pdf)
- [中文阅读对照稿 thesis-zh.pdf](thesis-zh.pdf)：包含第一至九章和摘要的中文版本。
- [第 1 章：引言](chapters/01-introduction.tex) · [第 2 章：背景与相关工作](chapters/02-background.tex)
- [第 8 章：讨论与未来研究](chapters/08-discussion.tex) · [负结果审计](data/ch8/audit.json)
- [第 9 章：结论](chapters/09-conclusion.tex) · [摘要](frontmatter/abstract.tex)
- [新五部分综合审计](data/synthesis/audit.json) · [相关工作原始来源](data/synthesis/primary-sources.json)
- [第 4 章：系统架构与 GPU 索引构建](chapters/04-architecture.tex) · [源码与证据核对](assessment/ch4-evidence.txt)
- [第 5.1 节：查询路径与排序对象](chapters/05-1-query-path.tex)
- [第 5.1 节核对与命题排版说明](assessment/ch5-section-1-evidence.txt)
- [第 5.2 节：LUT](chapters/05-2-lut.tex)、[5.3：packed access](chapters/05-3-packed-access.tex)、[5.6：精排](chapters/05-6-refinement.tex)、[5.7：probe selection](chapters/05-7-probe.tex)
- [第 5.2、5.3、5.6、5.7 节核对记录](assessment/ch5-sections-2-3-6-7-evidence.txt)
- [第 5.4 节：全局主码 top-c](chapters/05-4-global-selection.tex)与[第 5.5 节：共享界和调度](chapters/05-5-bound-scheduling.tex)
- [第 5.4、5.5 节源码核对记录](assessment/ch5-sections-4-5-evidence.txt)
- [第 6 章：工作负载级精排预算校准](chapters/06-refinement.tex) · [证据核对](assessment/ch6-evidence.txt) · [审稿意见逐项回复](assessment/ch6-review-response.txt) · [离线复算](scripts/audit_ch6.py)
- [第 6 章当前完成核对（含海报、预算作用图和成本算例）](assessment/ch6-completion.txt)
- [第 6 章二审：全池证明范围、有限池模型与去重](assessment/ch6-round2-response.txt)
- [第七章正文](chapters/07-evaluation.tex)
- [数据核对说明（含中文结论）](data/ch7/README.txt)
- [数值核对结果](data/ch7/audit.json)与[原始证据文件哈希](data/ch7/sources.csv)
- [Claude 审稿意见逐项复核与处理](assessment/ch7-review-response.txt)
- [第 7 章二审复核与处理](assessment/ch7-round2-response.txt) · [二审离线复算](scripts/audit_ch7_round2.py)
- [GPT 旧版审稿意见复核](assessment/ch7-gpt-review-response.txt)
- [补证完成状态与剩余实验](assessment/ch7-pending-experiments.txt)

审核重点：结论是否得到实验支持、跨系统比较是否公平、精确性声明是否限定到相应阶段，以及校准的质量风险和回本估计是否表述准确。原始实验输入来自本地同级 `JHQ_GPU` 工作区，路径见证据清单；本报告仓库提供分析脚本和衍生数据，但不包含全部原始输入。重新生成分析需要另外取得清单中的文件及相关历史源码，不能将哈希清单本身视为原始文件已公开或 GPU 实验已独立重现的证明。

当前审核应覆盖第一至九章、摘要及附录A/C。原E1历史测量保留v69身份，
OpenAI旋转／质心GEMM明确为TF32；v72是在同一TF32训练缓存下修改add/query算术的
FP32敏感性，基线未同会话重跑。A2支持已提取PTX的完整64位读取契约，toolkit SASS
不冒充驱动JIT实码；C1的矩阵几何与输入重编码证据区分TF32误差和量化边界。
原历史数据审计仍保留原campaign范围，新补证当前状态由`data/supplement/audit.json`记录。
完整证据边界和未完成项目见本轮整合说明及最新清单。

## 编译

在本目录运行：

```sh
latexmk -pdf main.tex
```

直接编译输出为 `build/main.pdf`。运行 `make pdf` 会将论文总稿更新到根目录的 `thesis.pdf`，第七章已放入总稿。模板采用 pdfLaTeX + BibTeX；不需要 shell escape、外部字体、Python 或额外绘图程序。

Overleaf：上传源文件，选择 `main.tex` 为主文档，编译器设为 **pdfLaTeX**。若修改编译输出目录，请同步检查输出路径。避免将 `build/` 中的历史中间文件上传为源文件。

中文阅读稿运行 `make pdf-zh`，输出为 `thesis-zh.pdf`。它使用 `main-zh.tex`、XeLaTeX 和 TeX 随附的 Fandol 中文字体，保持英文稿的章节与图表编号。中文正文位于 `zh/chapters/`；图内英文标签保留，第七章表格数字由 `scripts/build_zh_tables.py` 从英文表格复用。英文提交稿仍使用原来的 `make pdf`。

## 从哪里开始

1. `config/metadata.tex`：标题、姓名、导师、月份及可选学号，默认正式编译。
2. `chapters/`：九章正文及各节源文件。修改或合并标题不会影响模板运行。
3. `figures/`：放论文图件；优先使用矢量 PDF。用相对路径引用，避免依赖本机绝对路径。
4. `references.bib`：项目参考文献与官方技术文档，提交前核对元数据。
5. `appendices/`：来源与复现、完整参数／正确性补充、贡献及工具使用记录。
6. `data/appendix/e1-configurations.csv`：1,590个E1点的精确参数、质量、吞吐及来源。

模板示例附录已移除，前置页及附录不再包含写作填空提示。

## 排版默认值

- A4，单面单栏，12pt Latin Modern 字体。
- 30mm 页边距，1.3 倍行距。
- 前置部分罗马页码，正文阿拉伯页码，附录字母编号。
- 自动目录、图目录、表目录、PDF 书签和可点击交叉引用。
- 数字引用，`natbib` + `plainnat`；没有套用 ADC 的 LNCS 或 ACM 双栏样式。

修改 `config/preamble.tex` 可调整页边距、行距、标题和引用形式。上述均为模板选择，不能声称为本届课程硬性规定。

## 正式编译

`config/metadata.tex` 默认使用 `\draftthesisfalse`。封面和页脚不显示草稿标识，
示例附录已移除。未解决的写作／图件占位命令会使编译失败，避免提示被静默隐藏。
附录A说明原始记录、补证和运行身份，附录B给出参数覆盖／正确性证据及次要结果，
附录C说明研究角色、继承工作、AI协助及责任。

研究来源页没有伪造个人签名或独立完成承诺，实际课程声明手续由作者按任务办理。

## 字数

```sh
make wordcount
```

该命令需要额外提供 `texcount`；没有它也可正常编译 PDF。它按章节估算字数。声明、参考文献、图注、公式和附录的计数规则，以本届 Canvas 为准；工具输出不是官方字数认证。不要为了匹配典型页数而压缩字号或减少必要图表。

## 已核对的要求与来源

详见 `FORMAT_NOTES.txt`。公开课程页将详细指导交给 Canvas；目前查看到的资料没有规定必须使用哪种 LaTeX 文档类、字体、页边距或行距。本模板可在拿到进一步要求后集中调整。
