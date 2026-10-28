# Detailed Experiment Protocol and Provenance

This is the expanded protocol previously printed as Appendix A at report commit
[cddd860](https://github.com/lrlorry/8800_report/commit/cddd8602374c3804649da2bb2ea448fd90801a9b).
The submitted PDF retains a shorter protocol and the source-identity table.
PDF label identifiers below locate the corresponding claims and figures; the
text preserves the recorded campaigns and their limitations. This restructuring
adds no GPU measurements. Baseline E1, the supplementary D experiment and the
later contemporaneous T1 anchors retain separate identities; T1 details and raw
inputs are in [the review evidence package](../evidence/review/README.md) and
[the full-review audit](../data/full-review/audit.json).

Paths in the component and figure tables are relative to the sibling
`JHQ_GPU` repository. Other `data/`, `scripts/` and `assessment/` paths refer
to this report repository unless a source repository is explicitly named.
Bibliography keys resolve in [references.bib](../references.bib).

## Source and Build Environment

Chapter 7 is an offline analysis of archived measurements in the sibling
`JHQ_GPU` repository. The analysis checkout is recorded in
`data/ch7/audit.json`; this is distinct from each experimental run's
source head. `tab:a-components` maps component names to implementations,
recorded provenance and executable names. A run-head commit identifies
source visible to a run, not a cryptographic identity of its binary.
The archives do not supply a complete collection of executable SHA-256
hashes or immutable trained-state hashes. Missing identities are left
explicit rather than reconstructed from the current checkout.


| Component | Recorded source evidence | Executable or harness | Run/state source |
|---|---|---|---|
| E1 final pipeline | Environment logs include `a31c22d`; extensions have separate metadata | `demo_jhq_v69_batch`; `bench_cuvs.py`; `bench_rabitq_sweep` | E1 `RAW_RESULTS/`; shared trained-state cache |
| Lane refinement (v61) | Raw header `b37efa4` | `demo_jhq_v61_ab` | `warp_refine/raw/run.log`; `arms6_cache` |
| Grouped scan (v62) | Report `862543a`; run script `e0d0518` | `demo_jhq_v62_batch` | `pipeline_v62/raw/`; recorded compiler flags |
| Shared bound (v63) | Implementation/build flags archived; no inferred run head | `demo_jhq_v63_batch` | `pipeline_campaign/exp2/v63_raw/` |
| Batch scheduling (v65) | Raw header `d425ab8` | `demo_jhq_v65_batch` | `exp47/raw/run.log`; `arms6_cache` |
| Radix probe (v69) | Comparative runs/source archived; binary SHA not recorded | `demo_jhq_v65_batch`; `demo_jhq_v69_batch` | `practical_opt/v69_run.sh`; `v69_results/dumps.sha256` |
| Budget/table sweep | Raw header `d5e1526` | `demo_jhq_v69_budget_arms`; `demo_jhq_v71_gN_batch`, N in {1,2,4,8} | `adc_v69/RAW/`; `RAW_LUT/`; `arms6_cache` |
| Large int8 rerun | Stella degree-64 metadata `ad433a4` | `bench_cuvs.py` | `adc_v69/RAW_BIG/`; isolated processes |
| Historical budget | Raw header `bf31b41` (v57 family) | `demo_jhq_budget_arms.cu` | `paper_adc2026/data/budget_arms.log` |



Chapter 4's source and construction-record audit is recorded separately
in `data/ch4/audit.json`. It distinguishes the inspected source,
modelled bytes, archived train/add intervals and resident samples.
In particular, object construction, host QR and constructor library
warm-up precede the reported train/add timers.

The principal environment is RTX 5090, driver 595.71.05 and CUDA 13.0;
E1 uses cuVS 26.08.01. Release JHQ targets compute_80 PTX, JIT-compiled
on the device. Native-library baselines and C++/Python interface
boundaries differ. E1 improves comparability by reusing resources,
preallocating outputs, using pinned input staging and timing int8 query
quantization. JHQ and baseline output buffers still have different host
memory types. These details limit interpretations of small margins.

The adaptive call budget uses a warm-up interval containing the first
call. In the Python baseline harness that interval also includes initial
result conversion and validation before the decision; it is not a pure
steady-state latency measurement. The 274 reduced-call points therefore
include a RaBitQ point above 507 kQPS. Actual calls and five round arrays
remain in the JSONL records. The default exact-selection setting was
also inspected at the budget run's historical source head, not merely
in the current checkout: `JHQ_EXACT_TOPCK=0` opts into the old
lossy primary-retention implementation. Final selection scans all
retained refined scores and breaks ties by database ID.

## E1 Measurement Details and Review Diagnostics

E1 normally times 24 calls per round. The baseline harness reduces this
count when a warm-up interval exceeds its per-call threshold; 274 points
use fewer calls, including some fast steady-state points. Reported QPS
is the median of five round throughputs, each based on total queries
divided by elapsed time, rather than the reciprocal of median individual
latency. Device-only baseline timing is auxiliary: JHQ has no equivalent
device-query API for the main comparison.

The parser's 369 false repeat-call identifier flags comprise 170 RaBitQ,
80 IVF-PQ, 68 CAGRA int8, 50 CAGRA fp32 and one brute-force point.
They can include tie-order changes, without implying different ID sets
or invalid outputs; no point is discarded solely for the flag. The raw
records retain first/last recall and set/order diagnostics. JHQ does not
populate the same flag. The earlier count of 401 is the union of these
369 flags and 367 B-versus-A mismatches, with 32 adding only the latter.
Cross-protocol disagreement is distinct from repeat-call nondeterminism.

The second-review audit is `scripts/audit_ch7_round2.py`; its input
identities and calculations are in `data/ch7/round2-audit.json`.
It reconstructs the paired Vogue one-block frontier, counts actual scan
paths and computes continuous local frontier slopes. A single cold/cache
recall comparison is a sensitivity scale, not an empirical retraining
distribution. The later vector-row check supports alignment of all query rows and a
10,299-row base sample (`sec:a-supplement`); original entity-ID
mappings remain absent.

A binary paired sign test counts the signs of paired differences
[bibliography key: nist_signtest]. Under hypothetical independent fair signs, the
one-sided tail for at least 22 positives out of 24 is
$1.7941\times10^{-5}$; the two-sided value is twice that.
Here 22/24 instead counts wins among four LUT arms. The explicit
two-arm comparison gives 23/24, and probe configurations also share
datasets and indexes. The chapter therefore reports the paired counts
and per-dataset means rather than adopting that nominal significance test.
Likewise compute_80 PTX is translated into native target code by the
driver [bibliography key: cuda_platform]; without a matched compilation ablation the
sign of any throughput effect remains unmeasured.

## Budget Harness Contract and Diagnostic Coverage

Chapter 6's policy and review audits are reproducible with
`scripts/audit_ch6.py`; `data/ch6/audit.json` distinguishes
source-derived scan paths, statistical illustrations and archived
measurements. The budget harness's fallback grid string starts at 100,
although its header comment lists 200. The campaign script explicitly
sets the eight-point grid beginning at 200, so its recorded reference
is unaffected. Full-pool calibration is one call per cell; selected-arm
rates reuse the previously timed fixed arms.

The harness partitions query indices by parity: 500 even-indexed queries
calibrate and 500 odd-indexed queries evaluate, or 499 for Stella.
There are 64 draws for each $S=32,64,128$. Partial seeded shuffling samples
without replacement using `rand() % remaining`; the analytic
finite-pool formula models uniform subsets. The initial warm-up traverses
the entire query file, including held-out queries, but its outputs and GT
do not enter the agreement decision. Scan-schedule calibration uses
separate database pseudoqueries.

Each fixed arm receives one warm-up and three host-to-host timed calls.
Calibration gathers the selected vectors before starting its timer, then
runs a reference and candidate searches with graph capture bypassed.
The host agreement comparison costs $O(Sk^2)$ per tested budget; sample
gathering is $O(Sd)$ and reference-ID storage is $O(Sk)$. The timer includes
search-call setup and host comparisons, while sample gathering and separate
scan calibration are excluded. The logged percentile uses zero-based
sorted index $\lfloor0.95(m-1)\rfloor$, with $m=64$.

The helper returns a grid index, leaving the index at the last tested
multiplier. A caller must invoke `set_alpha(A[index])` before
future searches; selected-arm benchmark results instead use lookup.
Enumeration repeats the reference plus all seven other budgets, so both
timers include a fresh reference. In the original campaign it is requested only for the subsampled
calls: the FULL call omits `enum_out`. Thus the 2,304 matched
sample decisions exclude the twelve FULL decisions. At $S=500$, two
Vogue cells use four groups and ten cells use the distance-only path.
Matched calibration/evaluation paths remove a transfer difference, but
do not by themselves supply a common cutoff order. The supplementary
harness adds and passes all twelve FULL enumeration checks
(`sec:a-supplement`).

Finite-pool prediction requires more than a single 500-query score dump.
For each intended $S$, the per-query disagreement counts must be invariant
to subset membership and position under that execution regime. A FULL
$G=0$ dump cannot establish counts for grouped subsamples. Under
these conditions and monotone acceptance, arXiv's recorded fixed-arm
quality map makes selecting an unacceptable arm equivalent to accepting
100: 200 is its only qualifying budget. This mapping uses held-out quality
labels; acceptance counts alone do not predict unknown GT loss.
The original archived log lacks per-query curves and per-draw choices;
the supplementary traces supply them and reproduce all sampled grid
counts from full-pool per-query subset sums. This finite check does not
establish per-query invariance on arbitrary subsets.

## Data and Trained States

The six database shapes and actual query counts are stated in `tab:3-data`.
The comparisons use the same exported vectors and squared-L2 ground
truth per dataset. The budget split uses even query indices for
calibration and odd indices for evaluation; Stella has 500/499 queries.
Search sweeps load the recorded `arms6_cache` trained states,
whereas cold-build records explicitly start without trained state.
The chapter's file ledger hashes analysis inputs, not the full underlying
vector files or every cache object; it does not certify unrecorded data
or binary identities.

For the table-grouping sweep, `evidence/ch5/v71/` supplies selected
source extracted from the recorded run head `d5e1526`, its harness,
build definitions, run parameters and original records. Its manifest
hashes 96 timed JSON records, four gate-check JSON records, their text
outputs and build/progress logs, together with the selected source.
`fig:7-lut` is derived from the timed records using
`scripts/build_ch7.py`. This review bundle closes the local
source-to-result inspection path and is included in the report repository;
it supplies neither measured binary
identity nor the datasets and trained states needed for GPU reproduction.

The Vogue probe comparison stores matching SHA-256 hashes for the
one-group, batch-8 probe/primary dumps, covering all 1,000 queries.
Its baseline identity run reports recall 0.9642; the same baseline binary's
two subsequent timing runs report 0.9644. The dump controls a specific
routing/screening boundary. It does not store a complete cross-process
residual-code, query-rotation or score trace and therefore does not identify
the numerical root cause downstream.

Two exclusions affect the scale evidence. Initial large-baseline builds
retained an earlier index through a closure; successful isolated reruns
supersede those attempts, including Stella CAGRA int8. Separately,
Stella's 999-query pool causes the full-batch harness to skip batch 1,000.
Top-level corrected large-search records use batch 999; superseded
skipped-search files supply no throughput points. Cold-build logs are
used for train/add time even where their search list is empty.

## Result-to-Figure Mapping

The table below maps the empirical figures to their measurement families.
The estimated-payback figure is now repository-only; its historical label
is retained here for provenance. Relocated tables and the figure are in
[supplementary-evidence.md](supplementary-evidence.md), outside the PDFs.
The Chapter 7 empirical plots and main numeric tables are generated by
`scripts/build_ch7.py`; the additional path table is generated by
`scripts/audit_ch7_round2.py`. `data/ch7/sources.csv` gives consumed
input paths relative to `JHQ_GPU` and their hashes. Historical
v57 and newer budget comparisons retain separate versions and timing
protocols. The memory decomposition combines measured totals with an
explicit component model; its unaccounted remainder remains visible.


| Current or historical figure label | Raw source relative to JHQ_GPU |
|---|---|
| `fig:7-frontiers` | `experiments/comp8800_poster_e1/RAW_RESULTS/`; `analyze.py` frontier/interpolation definitions |
| `fig:7-lut` | `experiments/adc_v69/RAW_LUT/v71_g*.json` |
| `fig:7-packing-refinement` | `paper_adc2026/data/layout6.log`; `experiments/warp_refine/raw/ab/`; `raw/summary.json` |
| `fig:7-budget-risk`, `fig:7-budget-payback` | `experiments/adc_v69/RAW/budget_v69.log`; actual 500/499 query counts |
| `fig:7-batch` | `experiments/pipeline_campaign/exp47/raw/bench/`; `experiments/pipeline_v62/raw/perf/stages_summary.json` |
| `fig:7-build` | `experiments/thesis_evidence/RAW_A1/` normal repeats; baseline index records including int8 quantisation |
| `fig:7-memory` | `adc_v69/RAW_LUT/v71_g2_*_np128.json`; modelled component sizes in the analysis script |
| `fig:7-large` | `experiments/adc_v69/RAW_BIG/` corrected top-level records |



To regenerate the report, run `make ch7-data` and then
`make pdf`. The optional Chinese reading copy uses
`make pdf-zh`; its table translator reuses numeric data from the
English tables. Regeneration is an offline consistency check, not a new
GPU measurement. The original vectors, trained states, matching GPU
software environment and executable build would be needed for an
independent benchmark rerun.

## Supplementary Evidence of 28 October

The supplementary records are under
`JHQ_GPU/experiments/thesis_evidence/`.
Running `scripts/audit_supplement.py` recomputes the figures and
bilingual tables, with a ledger at `data/supplement/audit.json`. Its input ledger hashes
raw records, analysis/run scripts, exported PTX and toolkit SASS, and the
relevant source. Original E1 and ADC campaigns retain their own records.
The supplementary campaign uses RTX 5090, driver 595.71.05 and CUDA 13.0;
cross-session baseline comparisons are explicitly labelled.

### Construction and representation.

A1 uses an empty trained-state cache per run: first read, three normal
warm-input repetitions, and a synchronised phase diagnostic, for each of
six datasets. Process-start timestamps end at the printed add completion;
schedule calibration and the first search follow. Device memory is sampled
every 20 ms, with a 20 ms allowance at the output boundary. It is device
used memory including context, not an allocation-exact process trace.
The phase run forces one pipeline buffer and synchronisation, so its
times and peak remain separate. Five-build recall is measured at each
dataset's fixed 128-probe point, not over five complete frontiers.
C1 structurally checks four complete databases and recodes 200K/100K/20K/100K
rows for Vogue/arXiv/OpenAI-3072/Stella. Norm checks apply FP64 to the
stored matrix, not to a dump of actual GPU rotation outputs.

### Machine-code identity.

The inspected v69 executable has SHA-256:
`5371616ed99ab2b2dd323688eb3cf7a23dafb9f3f6a3904cf44475f65cf63ceb`
A2 extracts its `sm_80` PTX and reassembles it with toolkit
13.0.88 `ptxas` for `sm_120`. The bound read is
`LDG.E.64.STRONG.SYS`; publication is
`REDG.E.MIN.64.STRONG.GPU`. This validates the extracted PTX
contract and corroborates it with toolkit machine code. The driver JIT's
actual loaded SASS is not archived.

### Row correspondence and precision.

A3 checks every query and a stride-97 base sample by truncating and
renormalising the wider OpenAI embedding; it is vector correspondence,
not an original entity-ID export. D alternates v69/v72 order by probe
setting, using the original E1 grid and five timing rounds per
configuration. Both variants reuse the TF32-trained cache. The FP32
switch affects add/query GEMMs; the experiment does not retrain FP32
models or remeasure E1 baselines. Source patches are archived as local
commits `d924b30`, `b445c96`, `51d5502`, with server
counterparts documented in the experiment report; patch correspondence
is distinct from executable identity.

### Budget trace and direct timing.

B preserves the original `srand(12345)` sampling sequence for
2,304 draw records and adds twelve FULL enumerations. Its JSONL records
contain sample IDs, complete disagreement curves, selected arms, losses,
full-pool per-query counts and direct execution traces. All 18,432
sampled grid counts equal sums of the full-pool counts over the recorded
sample IDs; this is an aggregate check on measured subsets.
The 36 finite-pool predictions need no GT for acceptance; the conversion
to GT-loss crossing probability uses the held-out fixed-arm quality map.
Direct reuse timing instead uses a separate `mt19937(20261028)`
sequence, five rounds with rotated policy order, and 500 repetitions of
the same held-out batch. It includes sample gathering, calibration,
explicit budget installation and first-batch graph setup. Earlier
construction, schedule calibration and warm-up are excluded. Fractional
break-even values fit measured calibration and steady batches; cumulative
totals provide the direct observation. First schedule calibration calls
take 6.00--27.77 ms, separate from 0.81--7.04 ms pseudoquery gathering;
five repeated calls give medians of 2.72--18.13 ms.

The later T4 campaign completes the finite-grid strict CPU selection
reference (`sec:a-t4-t5`). The controlled same-model Vogue
cross-process diagnosis (C3) remains unperformed; T4 checks within-run
selection rather than that cross-process anomaly. Remaining contracts
are tracked in `assessment/ch7-pending-experiments.txt`.

## Strict Selection and Small-Batch Follow-ups

T4 uses `examples/demo_jhq_topc_reference.cu` and
`jhq_v73_topcref/search.cu`. Normalised source comparison of all ten
CUDA source/header files with `jhq_v71_lutgroups/` finds no execution
change after removing the two debug-export blocks. The dump follows the
packed word layout and calls the same `jhq_lut_sum` in subspace
order. CPU sorting consumes these GPU-produced primary scores, and the
retained refined scores for final selection. The zero score-mismatch count
compares exported scores against returned valid primary entries; it is
not separate instrumentation of every rejected candidate. The padding
counter verifies the number of valid entries, rather than the bytes of
every unused sentinel. Cutoff ties occur in 352 grouped and 88 one-block
query instances. Cases include natural short candidate pools; deliberately
constructed empty/adversarial lists remain a separate test.

The table-form comparison fixes 128 probes, $\alpha=100$, 256 queries,
shared bounds enabled, $G\in\{0,2\}$ and
$g_{\mathrm{LUT}}\in\{1,2,4,8\}$. It aligns candidate positions before comparing
FP32 score bits. Full-table versus two-way maximum absolute error is
$4.77\times10^{-7}$; the maximum over all forms is $5.97\times10^{-7}$.
On Vogue, the grouped four-way table changes four final answers despite
unchanged primary survivor sets: primary-score rounding can propagate
into the refined score. Thus this evidence establishes small numerical
error and measures its ranking effects, rather than FP32 identity.
Temporary `.topc` dumps were deleted by the campaign. The report
rechecks retained `RAW_T4/` JSONL tallies against stdout, and consumes
`lut_compare.json`; it does not rerun those deleted comparisons.

T5's launcher is `t5_smallbatch.sh`. Baseline harnesses are
`bench_cuvs_smallbatch.py` for CAGRA and
`bench_rabitq_smallbatch.cu` for RaBitQ, all under
`experiments/thesis_evidence/`. JHQ/CAGRA reuse their E1 grids;
RaBitQ uses 4/9-bit codes, two modes and eight probe counts.
Search timing includes staging,
transfers, int8 query quantisation when applicable, and synchronisation.
JHQ captures its graph with an untimed call; baseline warm-up traverses
the used query pool. Five round throughputs are reduced by their median.
The report consumes numeric JSON, avoiding rounded stdout at strict recall
thresholds. Null timing is a separate diagnostic and is not subtracted.
It does not equalise Python/C++ binding overhead or establish a service
latency guarantee.

`scripts/audit_t4_t5.py` generates the matched-recall table and figure,
normalised point registry and hashed input ledger under
`data/t4-t5/`. Its interpolation estimate follows the archived
near-target/log-QPS rule, retaining a qualifying measured endpoint below
the minimum frontier recall. The original T5 summary omitted such
competitors: OpenAI-3072 at recall 0.90 changes from about 2.08 to 1.032
at batch 8, and from 1.26 to 0.866 at batch 32. Strict measured thresholds
are reported separately, revealing the effect of finite grid spacing.
These estimates leave the historical E1 campaign unchanged.

Selected consumed T4/T5, T1 and A2 inputs are mirrored under
`evidence/review/JHQ_GPU/`, with original relative paths and hashes.
The package checker and the two follow-up audit scripts support offline
record reconstruction without the sibling code checkout. It excludes
vectors, trained states, measured binaries and deleted candidate dumps.
The archived PTX accesses the shared bound at the global query-key base
plus an eight-byte query offset; the inspected source allocates that
64-bit array with `cudaMalloc`. Its whole-key argument uses the
specified alignment, scope and proxy contract, not C++ volatile alone.
