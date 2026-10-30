# Thesis2 中文阅读对照版

以2026-10-30当前英文 `thesis2.pdf` 为依据，逐章翻译摘要及第1–9章；保留现稿的公式、实验数值、图表、标签、引用和证据边界。旧 `thesis-zh.pdf` 不作替换。

- 输出文件按用户指定拼写：仓库根目录 `thsis2-zh.pdf`。
- 图内标签及参考文献保留英文；正文、图注、表格文字与符号说明为中文。
- 不编译英文现稿已移除的A/B附录。
- 中文自然重新分页，不强求与英文逐页对应；公式、图表和章节编号保持对应。
- 独立中文源码位于本目录，英文 `variants/thesis2/` 及其PDF不修改。

从仓库根目录构建：

```sh
latexmk -xelatex -outdir=build/thesis2-zh -jobname=thsis2-zh variants/thesis2-zh/main.tex
python3 variants/thesis2-zh/verify.py
cp build/thesis2-zh/thsis2-zh.pdf thsis2-zh.pdf
```

`translation-ledger.json` 记录英文基准哈希、译稿覆盖、表格文字替换和原文件保护；`checks.json` 记录编译、数学／数值／编号一致性及版面检查。

后续个人贡献更新：用户确认导师提出方向并定期讨论，其余研究工作由本人承担；第1.5节已按此同步补入个人角色段落，保留现有实质性AI辅助披露。此后续改动单独记入 `author-update-2026-10-30.json`，不覆盖最初的翻译基准。
