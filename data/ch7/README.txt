Chapter 7 evidence and review notes
=================================

Current chapter
---------------
chapters/07-evaluation.tex follows all 8 sections in 6.pdf. It has 9 figures
and 11 tables, including E1 memory and RQ evidence summaries. Appendix A
adds component/run provenance, exclusions and figure-to-source mapping.
zh/chapters/07-evaluation.tex is the corresponding Chinese reading text;
Chinese numeric tables reuse the English data. All 9 current figures are
plotted by the thesis analysis script from archived measurements. Earlier
figure PDFs remain as archived source references. No new GPU experiment
was run and the JHQ_GPU implementation was not modified.

The detailed response to every Claude review item is:
  assessment/ch7-review-response.txt
The original supplied review is preserved in:
  assessment/ch7-claude-review.txt

Commands (from 8800_report)
-------------------------
  python3 scripts/build_ch7.py --source ../JHQ_GPU
  make pdf
  make pdf-zh

Python analysis requires matplotlib and numpy. English LaTeX uses
pdfLaTeX/BibTeX; Chinese uses XeLaTeX and TeX-distributed Fandol fonts.
The outputs are thesis.pdf and thesis-zh.pdf. Chapter 5 is also
written and translated; other unfinished chapter text remains a skeleton.

Outputs
-------
audit.json   Raw-derived counts, ratios, selection-contract checks, quality,
             build, memory and timing sensitivity results.
matched.csv  Interpolated and measured threshold comparisons; empty fields
             indicate missing coverage, not zero throughput.
sources.csv  Input paths relative to JHQ_GPU and SHA-256 hashes.

The source_snapshot is the audited checkout, not the commit of every
experimental binary. Run headers and the appendix distinguish recorded
run heads from report versions. The historical_selection_contracts field
hashes the relevant search.cu at d5e1526 and bf31b41 read with git show.
The ledger includes current implementation sources as well as measurement
inputs. Executable/cache/data identities absent from the archive remain
unrecorded; the analysis does not reconstruct historical binaries.

Source families
---------------
E1:       experiments/comp8800_poster_e1/RAW_RESULTS/
          Parser: experiments/comp8800_poster_e1/analyze.py
LUT:      experiments/adc_v69/RAW_LUT/v71_g*.json
Packing:  paper_adc2026/data/layout6.log
Refine:   experiments/warp_refine/raw/ab/*.json and raw/summary.json
Scan:     experiments/pipeline_v62/raw/{check,perf}/
Bound:    experiments/pipeline_campaign/exp2/v63_raw/{check,perf}/
Schedule: experiments/pipeline_campaign/exp47/raw/bench/*.json
Probe:    experiments/practical_opt/v69_results/{id_*,t_*,dumps.sha256}
Budget:   experiments/adc_v69/RAW/budget_v69.log
          Harness: examples/demo_jhq_budget_arms_v69.cu
History:  paper_adc2026/data/budget_arms.log (v57 family, bf31b41 header)
Scale:    experiments/adc_v69/RAW_BIG/ (corrected top-level records)
Memory:   v71_g2_*_np128.json; E1 process and baseline index records

Important verified distinctions
-------------------------------
* Exact primary top-c is DEFAULT. K_LOCAL=4's lossy primary path is opt-in
  via JHQ_EXACT_TOPCK=0. Final top-k scans all ck candidates and breaks ties
  by database ID. Neither is an approximate final selector. Nested survivor
  arguments still require fixed scores and consistent total tie ordering.
* E1 has 1,590 valid points. Repeat-call A flags count 369; B-versus-A
  inequality flags count 367; their union is 401. The latter is a different
  diagnostic, not repeated B-call nondeterminism. 274 baseline points use
  a reduced call budget chosen from a warm-up interval including first use.
* Two-group LUT leads in 22/24 new cells, not the old ADC count 23/24.
* Scan/bound checks cover 64/48 comparisons. Integrated scheduling covers
  250 variant comparisons and 234,320 query comparisons, with zero non-tie
  primary differences and zero different final ID sets. This is not universal
  final order/distance-bit equivalence across every experiment.
* Probe dump equality covers G=1, b=8, all 1,000 queries. Baseline Vogue recall
  is .9642 in its identity process and .9644 in two timing processes on the
  same full pool. The archived dump hashes are recorded; server dump binaries
  are not locally rehashed. Root cause after the recorded primary boundary
  remains unconfirmed. FP16 probe data stays outside the FP32 exact claim.
* Mean selected-arm QPS beats fixed 100 in 10/12 cells (1.028--1.691x in
  winning cells), but beats fixed 64 in 9/12 (geometric-mean ratio 1.054).
  The latter comparison includes quality differences, not a same-quality
  guarantee. ArXiv oracle-relative threshold violations coexist with better
  mean recall than the default fixed-100 arm.
* Calibration mean QPS averages previously timed fixed arms. Mean recall is
  reconstructed from rounded ceiling/loss values. Neither is a new online
  service measurement. Budget arm timing uses 3 calls, not E1's 5x24 protocol.
* Logged p95 is loss[floor(.95*(64-1))], the 60th sorted item; 4/64 tail
  losses can coexist with p95=0. Reported median_alpha is the upper middle
  item. Enumeration/bisection agree in 2,304 draws, not a general recall proof.
* Payback uses 500 queries or 499 for Stella. Versus fixed 100 favourable
  estimates span 2.4--55.4 batches; versus 64, 5.7--404.3 batches. Reciprocal
  mean QPS makes these optimistic and sample gathering is excluded.
* E1 memory uses JHQ process-minus-context including workspace versus CAGRA
  build-time index delta. The 0.29--0.39 ratio is not a matched-peak budget.
  Large resident total includes context/workspace; alpha does not free stored
  residual codes. Cold train+add excludes original input-file I/O and later
  schedule calibration, with one recorded cold build per dataset.
* Corrected isolated int8 builds fit Stella. Earlier retained-index failures
  and skipped b1000 runs do not establish infeasibility or throughput.

Limits
------
This is offline consistency checking, not independent GPU reproduction.
No new bootstrap, per-query recall funnel, repeated cold builds, construction
peak trace, drift measurement or multi-GPU scaling is claimed. Bibliography
metadata and official course submission requirements need their own review.
