# AI 使用记录 / AI assistance record

Compiled 29 October 2026 (Australia/Sydney). This record supplements the thesis’s Research Provenance and Tool Disclosure. It separates recoverable original prompts from tool-use summaries and author confirmation.

**Coverage is partial.** The entries below preserve selected user task messages visible in the current Codex conversation. They are not a complete chat export or a transcript of generated outputs. Earlier interaction dates and model versions are unavailable; compilation date is not substituted for interaction date.

Product names follow the retained workflow. These records document extensive assistance with writing, code, experiment automation, review and analysis, including substantive drafting. They do not reduce that assistance to language polishing or certify the student’s independent research contribution.

## Codex: recoverable original prompt excerpts

The Chinese quotations retain the user’s wording; surrounding IDE context, attachments and other turns are not reproduced. The artifact mapping identifies the task’s current outputs, not verbatim preservation of every intermediate response.

### P01 — 研究框架

Tool: OpenAI Codex. Interaction date: not preserved in the available history. Model version: not preserved.

> 你作为导师 和 评分人 结合我的代码 还有adc论文 还有我的海报 还有实验结果 先给个满分框架

Current artifact mapping: [`chapters/01-introduction.tex`](../chapters/01-introduction.tex), [`chapters/03-methodology.tex`](../chapters/03-methodology.tex).

### P02 — 第七章撰写与证据核查

Tool: OpenAI Codex. Interaction date: not preserved in the available history. Model version: not preserved.

> 我们一点点来做吧 你按照骨架 先实现并核对ch7 作为顶尖大学教授。和 ANN算法研究员 数据库专家 结合我的实验结果 和已经完成的图

Current artifact mapping: [`chapters/07-evaluation.tex`](../chapters/07-evaluation.tex), [`data/ch7/audit.json`](../data/ch7/audit.json).

### P03 — 中文阅读对照

Tool: OpenAI Codex. Interaction date: not preserved in the available history. Model version: not preserved.

> 再对应生成个中文版本 我看看写了啥

Current artifact mapping: [`main-zh.tex`](../main-zh.tex), [`zh/chapters/07-evaluation.tex`](../zh/chapters/07-evaluation.tex).

### P04 — 综合章节与摘要

Tool: OpenAI Codex. Interaction date: not preserved in the available history. Model version: not preserved.

> 我去睡一觉 你去按照满分标准 分几轮迭代依次完成 ch8 ch2 ch1 ch9 Abstract 作为顶尖大学教授。和 ANN算法研究员 数据库专家 结合我的实验结果 和已经完成的图 海报 ADC 论文

Current artifact mapping: [`chapters/08-discussion.tex`](../chapters/08-discussion.tex), [`chapters/02-background.tex`](../chapters/02-background.tex), [`chapters/01-introduction.tex`](../chapters/01-introduction.tex), [`chapters/09-conclusion.tex`](../chapters/09-conclusion.tex), [`frontmatter/abstract.tex`](../frontmatter/abstract.tex).

### P05 — 限制精简范围

Tool: OpenAI Codex. Interaction date: not preserved in the available history. Model version: not preserved.

> 只压缩重复的目前哦

Current artifact mapping: [`assessment/deduplication-rounds.md`](../assessment/deduplication-rounds.md).

### P06 — 提交要求审计

Tool: OpenAI Codex. Interaction date: 2026-10-29. Model version: not preserved.

> 在审核一下 还有如果提交 还有哪些不符合要求或者需要修改的 建议你先罗列出所有要求 然后一一核对 不要等我交了 再说漏了

Current artifact mapping: [`assessment/submission-audit-2026-10-29.txt`](../assessment/submission-audit-2026-10-29.txt), [`data/submission/audit-2026-10-29.json`](../data/submission/audit-2026-10-29.json).

### P07 — 本轮审稿处理

Tool: OpenAI Codex. Interaction date: 2026-10-29. Model version: not preserved.

> 结合这个 能改的先改一下 不能改的列出来 我手动去改

Current artifact mapping: [`assessment/final-review-edits.json`](../assessment/final-review-edits.json), [`assessment/submission-manual-actions.txt`](../assessment/submission-manual-actions.txt).

### P08 — 检测标注与形式化审计后的精简

Tool: OpenAI Codex. Interaction date: 2026-10-29 (Australia/Sydney). Model version: not preserved.

> gpt 给了这个报告 主要去压被AI标注的部分，请你结合这个和之前的分析 按照我的思路去压AI率

Used for substantive bilingual prose compression, consolidation of repeated protocols, relocation of implementation detail and replacement of duplicate equations by cross-references. The applied [TeX patch](../evidence/editorial/03775b7/compression.patch) and its hash are retained in [compression-edits.json](../assessment/compression-edits.json). This is the resulting source patch, not a separately archived complete model response. Checks and the disposition of the supplied audit are recorded in [compression-review-response.txt](../assessment/compression-review-response.txt). No new detector score or student-personal verification is inferred.

## ChatGPT: retained review record

The user supplied ChatGPT frameworks and reviews covering chapter structure, evidence, experimental design and final submission requirements. Retained review identities and accepted/corrected findings are in the following records:

- [Earlier full-review response](../assessment/full-review-response.txt) and [source identity](../assessment/full-review-source.json).
- [Display-curation review](../assessment/targeted-curation-review.md) and [source identity](../assessment/targeted-curation-source.json).
- [Submission requirements audit](../assessment/submission-audit-2026-10-29.txt).
- [Current review identity and applied edits](../assessment/final-review-edits.json).
- [Formalisation/compression review identity](../assessment/compression-review-source.json) and [response](../assessment/compression-review-response.txt). The user supplied the resulting review PDF; its original ChatGPT prompt and full research interaction were not supplied.

The original ChatGPT prompts, full responses, interaction dates and model versions are not supplied by those derivative records. The author must add the original recoverable records or accurately explain their absence. These references are evidence of retained review use, not a replacement for its original prompts.

## Claude: retained implementation, experiment and review record

The project disclosure and retained reports attribute implementation, experiment automation and review assistance to Claude. Campaign A–D, T1 and T4/T5 records distinguish measured outputs, timing boundaries, code variants and limitations. Public excerpts and the source map are listed in [artifact-access.md](artifact-access.md).

These logs are experimental records, not Claude prompt transcripts. Complete original Claude prompts/outputs, interaction dates and model versions are not included here. The author must supplement them where available.

## Use, checking and responsibility

AI suggestions were used for substantive chapter drafting and revision, bilingual reading copies, LaTeX and diagrams, implementation/harness work, offline analysis and review. Retained scripts, logs and review responses document source comparisons, numerical recomputation, rejected interpretations and compilation. They establish the recorded workflow, not that every suggested statement was independently checked by the student.

The author must review the final text and specify personal design decisions, implementation/experimental work and verification, separating supervisor/collaborator support from AI assistance. Do not backfill missing historical prompts, dates or model versions. Any institutional request for more complete interaction material still needs to be met.

Machine-readable selected prompt text and hashes: [ai-use-record.json](../data/submission/ai-use-record.json). Items requiring author action: [submission-manual-actions.txt](../assessment/submission-manual-actions.txt).
