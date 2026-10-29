thesis1: selected-highlight revision
===================================
Latest revision: 2026-10-29, using the two supplied 59%/60% highlight reports.
Independent output: thesis1.pdf. Original thesis.pdf and tracked sources remain unchanged.

Only mapped highlighted prose and highlighted glossary definitions were revised.
Adjacent unmarked sentences, all original theorem statements, numerical tables,
scientific assets, cover metadata and bibliography are preserved.
Real-arithmetic identities, counterexamples, retention arguments and the cost model
are expanded where useful; measured results remain empirical findings.
Proofs follow the conditions -> derivation -> conclusion style of the user's A1 report.
Font size and page margins are unchanged. Floats cannot precede their declaration.

Current output: 71 total pages; 56 body pages. Same-estimator prose counts:
chapters plus abstract 16,174 -> 14,119; appendices 1,172 -> 1,042.
This source-level estimate excludes table bodies and is not an official word count.
No new detector score is available; 59%/60% describe the supplied BEFORE reports.

The previous 70-page thesis1 and its parts are in revision-59/before-*.pdf.
revision-59/baseline.json pins the prior PDFs, source and report identities.
revision-59/edits.json records exact before/after blocks and protected-source checks.
checks.json records final compilation, page geometry, fonts and proof alignment.
Older reviewed-blocks.json / round*-edits.json document the previous editing round.

Build from the repository root:
latexmk -pdf -outdir=build/thesis1 -jobname=thesis1 variants/thesis1/main.tex
cp build/thesis1/thesis1.pdf thesis1.pdf
python3 variants/thesis1/export_parts.py
