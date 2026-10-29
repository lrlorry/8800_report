thesis1: selected-highlight revision
===================================
Independent output: thesis1.pdf. Original thesis.pdf and sources are preserved.
Uses the supplied T71/T76 highlights, mapped from their source baseline to current text.
Abstract and bibliography are unchanged. Highlighted narrative is deleted, shortened or rewritten;
unhighlighted text between selected blocks is retained. Mixed adjacent sentences are protected.
No whole-chapter generic polishing or new explanatory filler.
reviewed-blocks.json gives each decision, exact before/after text, source/report mapping and counts.
round1-edits.json and round2-edits.json record actual successive editing passes.
checks.json records final verification. No GPU or AI-detector rerun is claimed.

Build from repository root:
latexmk -pdf -outdir=build/thesis1 -jobname=thesis1 variants/thesis1/main.tex
cp build/thesis1/thesis1.pdf thesis1.pdf
