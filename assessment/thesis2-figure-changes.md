# Thesis 2 figure and layout changes — 30 October 2026

**Historical figure/layout snapshot.** The counts and page locations below describe the 63-page build before the personal-contribution paragraph. Commit `02a44677` subsequently contained 64 pages. Current candidate counts and review decisions are recorded in `assessment/thesis2-review-response-02a4467.txt` and `variants/thesis2/checks.json`; the old page locations are not a current-PDF index.

Baseline HEAD: `1ff5b01cbdcf4c0b6788914c9eb89d1db6a44ce9`.
The root PDF before this round had 66 pages; the figure/layout-stage PDF had **63 pages: 7 preliminary, 53 body, 3 bibliography**. The body font and global margins are unchanged. There are **29 figures,28 tables and six complete statement/proof pairs**.

## Scientific drawings

| Change | Previous information and added value | Final location | Source/evidence and limits |
|---|---|---|---|
| Upgrade `fig:4-layout` | Previous figure already showed offsets, an empty list, IDs, one word group, residual rows, corrections and highlighted p=3. The local replacement adds four separate allocation boundaries, two word-group rows, explicit relative byte offsets and a row expansion. Arrows link the common p=3 to entries in each allocation. | Figure 4.2, Ch4.3; **PDF page 20, printed page 13**. Local source: `variants/thesis2/figures/physical-layout.tex`; route: `04-3-layout.tex`. | `eq:4-offsets`, `eq:4-primary-address`; local JHQ_GPU v69 `jhq_gpu_index.cu`: gather at 613, repack at 661, independent allocations around 2812–2832, final word allocation/repack around 2897–2903. Each word holds four subspace bytes of one candidate. Residual rows are contiguous internally; survivor rows can be scattered. Toy N=8/M≥8, **schematic**, relative offsets only; no measured transactions, absolute addresses or alignment claim. Ch5's existing packed-access figure still explains warp reads. |
| Add `fig:5-cartesian-lut` | No previous LUT mechanism figure existed. The new figure explains more than nibble extraction: four sign bits give 16 patterns per nibble, selects the two 16-entry tables, and combines their values. It contrasts 256 entries/1 lookup with 32 entries/2 lookups+sum and 1/8 FP32 storage. | Figure 5.2, Ch5.2, directly after `eq:5-lut-factorisation`; **PDF page 27, printed page 20**. Local source: `variants/thesis2/figures/cartesian-lut.tex`. | `eq:5-sign-codebook`, `eq:5-lut-halves`, `eq:5-lut-factorisation`; analytical Cartesian builder in `cpu/pq_codebook.cpp` around 241; v69 `search.cu` high/low-nibble loads around 578–579 and other scan paths. **Schematic**; exact real-arithmetic identity requires coordinate separation, not arbitrary learned PQ. Codes and routed candidates are unchanged; rounded primary top-c and final IDs can change. Caption cites existing T4 evidence: max relative score difference 4.64e-7 across forms; Vogue 2–4/256 final-ID differences, arXiv/OpenAI-3072 zero. Lookup counts describe the expression, not measured instructions. |

Both are native vector TikZ; neither uses raster generation or resizes an overfull image to hide small fonts. The new detailed diagrams use footnote-sized text with normal mathematical glyphs. The retained raw scientific curves, benchmark tables and algorithm implementations are unchanged.

## Layout repair

- Ch 1 challenge-map rows and boxes are closer together in a local copy, with identical node labels. Its caption remains next to it. The contribution table uses better column widths; its old isolated page is eliminated. `fig:1-challenges`: PDF 9 / printed 2.
- Ch 2's final gap sentence now precedes its comparison table; all wording and table cells are retained. This removes the old two-line final page.
- Ch5/6 mechanism diagrams and tables are kept beside their introducing subsections. Long captions use the available width. Floats cannot silently migrate into later unrelated sections.
- Ch6's calibration and budget-scope diagrams have local spacing-only copies and unchanged node labels. `fig:6-budget-scope`: PDF 37 / printed 30; `fig:6-calibration`: PDF 38 / printed 31. The short 6.6 closing section is kept together on printed 34, using a local page-height allowance with visible space above the footer, instead of four lines alone on the next page.
- Ch7 strict-selection/probe and memory tables, construction/memory/large-scale figures, and direct-reuse plot stay with their evidence group. E1's main frontier remains a normal float but precedes its precision follow-up. Ch8's short validity section stays with its table.
- No global font reduction, deleted body material, new appendix, new experimental run or altered mathematical statement is used to obtain the page reduction.

## Decisions against additional figures

The contribution map would duplicate `fig:1-challenges` and `tab:1-contributions` while failing to establish personal ownership. The proposed evidence-family matrix would repeat Ch 3 design/components and the explicit D/T1/budget captions. The radix drawing would repeat the existing four-pass rank/bin equations and probe table. **None is added.** The physical-layout upgrade has a limited but concrete information gain; the only net new figure is the Cartesian LUT drawing.

Every Ch7 experimental group was reviewed separately in `assessment/thesis2-figure-audit.md`, including precision D/T1, T5, T4, FULL/sample risk, finite-pool/direct reuse, scheduling, build/resident/scale and robustness. An A1–T5 coverage table reconciles the report's action list with the body and retains stronger final-review caveats where the report's shorthand overstates evidence.

## Build and verification

Executed from repository root:

```sh
latexmk -pdf -outdir=build/thesis2 -jobname=thesis2 variants/thesis2/main.tex
python 3 variants/thesis2/verify.py
python 3 variants/thesis2/export_parts.py
```

Build passes with **no warnings, overfull/underfull boxes, missing glyphs or undefined references**. All fonts are embedded and there are no Type3 fonts or extracted words outside the page. The verifier checks:

- Exact replay of the historical revision followed by this separately recorded round, including before-images for all changed TeX and contents of new local figure files.
- Unchanged historical `audit/edits.json`, the protected original/thesis1 files and 43 protected shared figure assets. The previously absent thesis1 split PDFs are not recreated.
- Unchanged original mathematical blocks, all six statement/proof pairs, table cell payloads, existing labels/citations and all spacing-only diagram node labels. Each statement/proof pair stays on one page with aligned heading/body margins.
- 29 figures and 28 tables, required numerical facts, embedded fonts, PDF/page structure, and no reintroduced appendices or internal repository paths printed in the thesis.

The root `thesis2.pdf` is copied from the verified build. Derived PDFs are regenerated by chapter scope: **part 1 pages 1–36; part 2 pages 37–63**. Export checks compare each page's non-whitespace character multiset to its full-PDF source page.

## Visual inspection

All pages of the 64-page intermediate layout were rendered and reviewed in contact sheets, followed by all 63 final pages. Fifty-four final body-page renders are pixel-identical to the already reviewed intermediate bodies after accounting for the removed short page; the nine changed body renders (contents/lists, two mechanism pages, nearby text flow and Ch6 ending) were reviewed again.

All changed diagram pages and their neighbours were rendered: **8–10,19–21,26–28,36–39**. Detailed 1500–1700-pixel page renders were inspected for pages 9,20,27,37,38 and 41. Revisions fixed cramped physical-layout labels, insufficient space between the word-stride annotation and packed-byte explanation, and LUT arrows crossing longer nibble labels. Final checks cover label/arrow clearance, relative offsets, font readability, captions, table width, heading placement and proof alignment. The final explicit reference to Figure5.2 reflowed pages26–27; both were rendered and inspected again, while the other61 final body renders were unchanged.

The final include inventory is `variants/thesis2/audit/figure-inventory-2026-10-30.json`: **9 shared TikZ, 7 local TikZ, 13 scientific PDFs**. The new replay ledger is `variants/thesis2/audit/figure-layout-2026-10-30.json`; the historical ledger is not rewritten. `variants/thesis2/checks.json` records final PDF hashes, page counts, proof positions and exports.

## Remaining author confirmation

`assessment/thesis2-contribution-provenance-check.md` separates inherited mechanisms, project additions and evidence for C1/C2/C3. Personal research ownership, joint/supervisor roles and personal verification still require **author confirmation**. No ownership is inferred from commit metadata. A research/AI declaration already compiles through acknowledgements; whether the task requires a separate formal declaration page remains unverified. These are separate from completion of the requested figure/layout repair.

This round is delivered locally; it has not been committed or pushed. No detector was rerun and no detector result is inferred.
