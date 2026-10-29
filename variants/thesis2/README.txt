thesis2: selected-highlight revision
===================================
Completed 2026-10-30 (Australia/Sydney).
Independent output: thesis2.pdf. Original thesis.pdf and thesis1.pdf are preserved.
Inputs are the two supplied reports showing 38% and 49% for thesis1 parts.
Those are BEFORE measurements; no new detector score is claimed.

The supplied pages match all 29,050 source word/coordinate anchors.
201 highlighted paragraphs/fragments were shortened, removed or formalised.
Unmarked mapped prose and all theorem statements remain unchanged, except for
explicitly recorded structural relocation and cross-reference repair.
Numerical body tables and scientific plot assets are preserved.
Two native TikZ diagrams replace construction/lifetime explanations.

The standalone A/B appendices are omitted from this PDF. Unique timing/calibration
contracts and a short component map are consolidated in Chapter 3. The exact
same-session T1 precision table is retained in Chapter 7. Duplicate result lists,
commit-by-commit provenance, capacity-table repetition and secondary checklists
are omitted. Copied appendix sources remain only for audit and are not compiled.

Layout keeps 11pt font and original 27/28mm margins. Construction diagrams,
precision results and small-batch results stay next to their explanations.
A legacy empty heading and a nearly empty methods page were removed.

Build from the repository root:
latexmk -pdf -outdir=build/thesis2 -jobname=thesis2 variants/thesis2/main.tex
cp build/thesis2/thesis2.pdf thesis2.pdf
python3 variants/thesis2/export_parts.py

checks.json records output dimensions, fonts, references and proof alignment.
audit/baseline.json pins protected sources/PDFs; audit/edits.json records exact
before/after prose, structural changes, retained evidence and word-count scope.
