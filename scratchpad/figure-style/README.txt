四张图的样式预览（2026-10-30）

只调整图7.2 precision、图7.7 finite-pool、图7.8 stream-cost、图8.1 negative-evidence。
当前论文实际29图，其中16张TikZ、13张数据图；本轮不更改TikZ。

交付：仓库根目录 thesis2-figure-comparison.pdf（四页前后对照）、
      thesis2-figure-preview.pdf（65页整篇预览）。
正式 thesis2.pdf、中译版、原图、章节、表格、原始生成脚本和既有审计均不覆盖。
预览通过独立 graphicspath 读取这里的四张图。

风格：按156mm正文宽度出图；标题9pt、坐标标题8.7pt、刻度与图例8.1pt。
使用可正确嵌入的 Computer Modern Roman TrueType 衬线字体，与正文 Latin Modern 同源。
JHQ精度变体用蓝色系；CAGRA fp32橙色、IVF-RaBitQ红色，与主前沿图对应。
预测/观测与精排策略有各自的线型；保留其含义，不将灰色参考策略当作其他系统。

数据：只读现有audit与存档，重用原始纯frontier/interp函数；不运行整套审计生成脚本。
D对照仍是TF32训练缓存上的同会话JHQ变体及历史E1基线，不变成T1。
有限池仍为原概率、64次抽样和1个标准误；复用曲线保留每条500个点。
负结果仍区分GPU打分器速度和FP64离线候选数，875/375不是GPU加速比。

验证：原版两套verify.py通过；1058个既有文件的哈希一致。
预览65页，全部编号和分页一致；29图、28表、6组证明保留。
61页文本一致，另外4页的像素差异均限制在图内；未改变正文或图注。
四图画布比例保持原图成稿尺寸；文字均在画布内，字体嵌入且无Type3。
详见 manifest.json、plot-data.json 和 checks.json。

重建（从仓库根目录）：
MPLCONFIGDIR=build/matplotlib python3 scratchpad/figure-style/build_preview.py
latexmk -pdf -outdir=build/thesis2-figure-preview -jobname=thesis2-figure-preview scratchpad/figure-style/preview.tex
latexmk -pdf -outdir=build/thesis2-figure-comparison -jobname=thesis2-figure-comparison scratchpad/figure-style/comparison.tex
python3 scratchpad/figure-style/check_preview.py
