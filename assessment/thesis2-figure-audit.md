# Thesis2 figure audit — 30 October 2026

Baseline: `1ff5b01cbdcf4c0b6788914c9eb89d1db6a44ce9` (actual HEAD at audit), 66 PDF pages, 28 figures, 28 tables, six statement/proof pairs. Existing uncommitted layout repairs are included in this round; their before-images are retained separately. This audit was written before implementing the two mandatory mechanism-figure changes.

Scope: only thesis2 and new assessment/verification records. Shared `figures/`, original thesis, thesis1, source code and experimental data are read-only. Decisions below concern information conveyed, rather than the number of figures. Figure paths refer to the assets actually included by thesis2; an asset's presence in the repository alone does not establish use.

## Chapter-by-chapter decisions

| Section | Core claim | Existing visual / label | Missing information | Decision / priority | Evidence | Expected gain |
|---|---|---|---|---|---|---|
| 1.1–1.2 context/scope | Practical representation/execution/budget problem | Scope definitions; no separate figure | None requiring a visual | Keep, P2 | Ch1 definitions | Avoid decorative introductory diagrams |
| 1.3 challenges | Challenges lead to mechanisms and tests | `fig:1-challenges`, shared challenges diagram, locally tightened layout | Layout originally consumed too much height | Upgrade spacing only, P1 | Existing node text | Remove isolated contribution-table page |
| 1.4–1.5 RQs/contributions | Project additions have inherited foundations | `tab:1-contributions`, challenge map | Personal versus joint ownership is unconfirmed | Keep table/map; separate provenance checklist, P1-A | Declaration, AI-use record, Ch4–7 | No duplicate contribution map or invented personal claim |
| 2.1 metrics | Recall and latency are different objectives | Metric equations | None | Keep, P2 | Ch2.1 | Definition is more precise than an icon |
| 2.2–2.3 hierarchy/JHQ | Routing, primary retention and reconstruction restrict different sets | `fig:2-cascade` (`ch2/candidate-cascade`) | None | Keep, P2 | Candidate-set definitions | Existing cascade already explains the hierarchy |
| 2.4–2.7 background/gap | GPU/graph/table ideas predate this project | `tab:2-position` | None | Keep; tighten table layout, P2 | Cited literature | Avoid a second generic taxonomy |
| 3.1 design | RQs require different controls | `tab:3-design` | None | Keep, P1 | Comparison definitions | Existing matrix provides experiment identity |
| 3.2 data/splits | Data scale and query partition define scope | `tab:3-data` | None | Keep, P1 | Dataset/source audit | No redundant scale bar chart |
| 3.3 timing/memory | API timing and GPU phases differ | `fig:3-boundary` (`ch3/measurement-boundary`) | None | Keep, P1 | Timing-boundary source and Ch3.3 | Preserve host-to-host/device-only distinction |
| 3.4 baselines/frontiers | Finite grids and estimators determine comparisons | `tab:3-grids` | None | Keep, P1 | Grid and interpolation definitions | A plot would duplicate later frontiers |
| 3.5 evidence families | Components, sessions and timing contracts cannot be pooled | `tab:a-components`; protocol/contract text; Ch7 D/T1 captions | No missing relation requiring another dense diagram | Keep, P1-B; reject evidence-boundaries figure | Actual includes and Ch7 captions | Preserve distinct E1, ablation, D, T1, T4/T5, budget and build evidence without a text-heavy second matrix |
| 4.1 boundaries | Build creates the state that search reuses | `fig:4-architecture` | None | Keep, P1 | Architecture and lifecycle | Existing separation sufficient |
| 4.2 training | Transform, analytical primary and fitted residual have different roles | Equations and source audit | None requiring a new figure | Keep, P2 | Ch4.2 / analytical codebook | Avoid suggesting an unmeasured training trace |
| 4.3 physical layout | Four independent buffers share physical position | `fig:4-layout` (`ch4/physical-layout`) | Word-group stride, residual row stride, independent allocation, common position arrows | Upgrade local copy, **P0-A** | `eq:4-offsets`, `eq:4-primary-address`; v69 allocation/gather/repack code | Reader can calculate relative offsets and distinguish storage from Ch5 warp access |
| 4.4 resident/lifecycle | Stored bytes differ from workspace/peak | `tab:4-bytes` | None | Keep, P1 | Byte model | Do not repeat resident-memory plots |
| 4.5 construction | Single/two-pass buffers have disjoint lifetimes | `fig:2-add-paths`, `fig:2-memory-lifetimes`, `tab:4-phase-storage` | None | Keep, P1 | Assignment scratch and lifetime equations | Existing diagrams already prevent summing 12 GiB scratch with gather |
| 4.6 contracts | Representation checks have explicit coverage | `tab:4-representation-audit`, `tab:4-contracts` | None | Keep, P1 | C1/T2 evidence | Numerical coverage belongs in tables |
| 5.1 query stages | Each stage ranks a different object | `fig:5-query-path`, `tab:5-query-stages` | None; float drift affected placement | Keep, repair placement, P1 | Stage contracts | Keep diagram/table with their introduction |
| 5.2 Cartesian LUT | Coordinate separation permits 256 → 16+16 | `tab:5-lut-resources`, factorisation equations | No existing mechanism drawing of nibble extraction and table reads | **Add `fig:5-cartesian-lut`, P0-B** | `eq:5-lut-halves`, `eq:5-lut-factorisation`; v69 LUT loads; Ch7 T4 | Explain storage reduction without implying general learned-PQ factorisation or bit identity |
| 5.3 packed access | Lanes read words across adjacent candidate positions | `fig:5-packed-access` | None | Keep, P1 | Address equation and warp diagram | Distinct from storage layout in upgraded Ch4 figure |
| 5.4 grouped top-c | Local exact retention and merge preserve global target | `fig:5-global-selection`; lemmas/proofs | None | Keep, repair placement, P1 | Unchanged proofs | Avoid restating a proof as a second flowchart |
| 5.5 bounds/scheduling | Witness keys safely prune admission, not score evaluation | `fig:5-shared-bound`; scheduling equations | None | Keep, repair placement, P1 | Bound proof, A2, observed dispatch | Does not generalise grouped gains to G=0 E1 runs |
| 5.6 refinement | Lanes share residual score work before final selection | `fig:5-lane-refinement` | None | Keep, repair placement, P1 | Computed-score contract | Preserve distinction from raw-space kNN |
| 5.7 probe selection | Four prefix histograms obtain a centroid cutoff | Rank recurrence, key transform and deterministic tie-set equations | No absent step that requires a diagram | Keep, P1-C; reject radix figure | Four-pass equations; `tab:7-probe` | Equations already specify bins, residual rank and ties more precisely |
| 6.1 budget scope | Expansion changes survivor refinement and scan admission work | `fig:6-budget-scope` (confirmed compiled) | Only layout spacing | Keep, spacing only, P1 | Caption already states score/admission distinction | No new budget pipeline |
| 6.2 agreement | Sample/reference outputs define acceptance, not GT labels | `fig:6-calibration`; sampling equations | Only diagram spacing | Keep, spacing only, P1 | Agreement definition and statistics | No change to statistical assumptions |
| 6.3 nesting | Primary nesting plus fixed refinement order gives monotone agreement | `fig:6-nesting`; theorem/corollary | None | Keep, P1 | Six protected statement/proof pairs | Retain scope distinction for FULL G=0 |
| 6.4–6.6 controls/economics/scope | Fixed, sample, FULL and oracle answer different questions | `tab:6-controls`; cost/payback equations | None | Keep; keep short heading with body, P1 | Ch6/7 cost evidence | No duplicate results chart |
| 8.1–8.2 interpretation/negative evidence | Local arithmetic/candidate gains may lose overall | `fig:8-negative` (`ch8/negative-evidence.pdf`) | None; caption already specifies GPU scorer versus offline FP64 pilot | Keep, P1 | Mailman and rank pilot | No implied end-to-end speedup |
| 8.3–8.5 validity/directions/deployment | Limits constrain deployment recommendations | `tab:8-threats` | None | Keep, P1 | Precision, T4/T5 and scope evidence | Do not repeat all experiment panels |
| 9 conclusion | Summarise answers already evidenced | No additional figure | None | Keep, P2 | Ch4–8 | No redundant concluding map |

## Every Chapter 7 experiment group

| Section / group | Core question | Actual existing visual / label | Missing information / action | Decision / priority | Evidence source | Expected gain |
|---|---|---|---|---|---|---|
| 7.1 protocol | Fair boundaries and reproducibility? | Ch3 `fig:3-boundary`, design/grids; Ch7 cross-references | Ch3 already identifies pageable C++/pinned Python and API/compilation differences | Keep, P1 | Ch3.3–3.5 | No redundant protocol picture |
| 7.2.1 E1 scope | Who leads within tested coverage? | `ch7/frontiers.pdf`, `fig:7-frontiers` | Caption already has 0.97 line, log QPS and int8 inclusion; text states batch1,000/G=0 versus Vogue G=4 | Keep, P1 | E1 source audit / frontier inputs | Preserve coverage and dispatch scope |
| 7.2.2 matched recall | Does interpolation change the answer? | `tab:7-matched` | Both interpolated and qualifying-measured ratios shown | Keep, fix local placement, P1 | `tables/ch7/matched97` | No duplicate ratio chart |
| 7.2 precision D | Does FP32 change OpenAI margins? | `supplement/precision.pdf`, `fig:7-precision`, `tab:7-precision` | Caption states paired JHQ variants and archived baseline comparison; same TF32-trained cache | Keep, P1 | Campaign D | Do not turn cross-session baselines into paired comparisons |
| 7.2 precision T1 | Are same-session anchors consistent? | `tab:b-precision-anchors` | Explicit separate session/configuration coverage | Keep, P1 | T1 table / caption | Same-session evidence stays separately identified |
| 7.2 interpretation | Dimension/representation association? | E1 frontiers + matched table | Current prose limits alignment evidence and association | Keep, P2 | A3 / Ch7 text | No invented causal diagram |
| 7.2 T5 small batch | Does batch8/32 change the winner? | `t4-t5/smallbatch.pdf`, `fig:7-smallbatch`, `tab:7-smallbatch` | Batch8/0.97 CAGRA leads all four; strict/interpolated difference retained | Keep, P1 | T5 | Preserve adverse result |
| 7.3 LUT | Which grouping wins, and is FP32 identical? | `ch7/lutgroups.pdf`, `fig:7-lut` | Mechanism gap belongs in Ch5, not new benchmark | Keep curve; add Ch5 mechanism only, P0-B | v71 / T4 | Separate algebra from empirical rounding |
| 7.3 packing/lanes | Load path or cooperative scoring? | `ch7/packing_refinement.pdf`, `fig:7-packing-refinement`, `tab:7-refinement` | Caption separates paired API and kernel ratios; Amdahl uses wall time | Keep, P1 | Packing / lane controls and profile | Avoid multiplying independent gains |
| 7.4 strict top-c / T4 | Does selector match ordering of GPU scores? | `tab:7-strict-selection`; Ch5 mechanism/proofs | Already distinguishes G≥1 exact order, G=0 tie-only and deleted raw dumps | Keep, P1 | T4 CPU resort of GPU-produced scores | Does not certify raw-space ANN exactness |
| 7.4 shared bound | What work decreases without changing target? | Ch5 `fig:5-shared-bound`; scan/merge numbers | Existing 48 checks and stage measurements sufficient | Keep, P1 | Bound comparison | No repeated bar plot for two stage timings |
| 7.4 probe | Speed and exactness of computed centroid order? | `tab:7-probe`, Ch5.7 key/rank equations | Cross-process Vogue anomaly remains separate | Keep table, P1-C | Alternating v65/v69 and synthetic checks | No unsupported mechanism extension |
| 7.5 controls | Which information does each rule use? | `tab:6-controls` | Existing cross-reference sufficient | Keep, P1 | Fixed/sample/FULL/oracle definitions | No duplicate table |
| 7.5 FULL | Does quality-first selection meet held-out target? | `tab:7-budget-full` | 12/12, max0.0006, fixed-arm timing lookup explicit | Keep, P1 | FULL results | Preserve lookup/direct timing distinction |
| 7.5 sample risk | What does a low-cost sample miss? | `tab:7-budget-quality`, `ch7/budget_risk.pdf`, `fig:7-budget-risk` | 40/64 and 32/64 crossings plus percentile/max evidence remain | Keep, P1 | 64 draws per S | Avoid mean-only presentation |
| 7.5 cost estimate | Does saved search time repay calibration? | `tab:7-budget-cost` and payback model | Caption marks selected-arm rate and separate quality failure | Keep, P1 | Budget arm lookup/model | No implied direct reuse measurement |
| 7.5 finite pool | Does without-replacement prediction fit? | `supplement/finite-pool.pdf`, `fig:7-finite-pool` | Caption states exact finite-pool model scope | Keep, P1 | Per-query disagreement traces | Avoid population/i.i.d. reinterpretation |
| 7.5 direct reuse | Does real calibration plus reuse match model? | `tab:7-stream-cost`, `supplement/stream-cost.pdf`, `fig:7-stream-cost` | Four repeated-pool cells, separate recall and scope explicit | Keep, fix placement, P1 | Direct500-batch traces | Cost validation remains distinct from new-workload quality |
| 7.6 fixed G / profiles | When does parallelism lose to repeated work? | `ch7/batch_execution.pdf`, `fig:7-batch` | Caption says independent-bound profiling versus scheduler experiment | Keep, P1 | Paired batch profiles | No cross-campaign gain multiplication |
| 7.6 schedule/skew | Does a fixed rule generalise? | `tab:7-scheduling` | Held-out configurations versus held-out queries distinguished; CV range and low-probe regressions explicit | Keep, P1 | Scheduling campaign and E1 dispatch | Connect Vogue benefit without claiming all E1 uses grouped bounds |
| 7.7 cold build | Construction speed and sampled peak? | `tab:7-build-memory`, `ch7/construction.pdf`, `fig:7-build` | Warm input pages, cold state, unattempted versus failed distinguished | Keep, repair placement, P1 | A1 / supplementary normal builds | Do not equate resident with build peak |
| 7.7 resident | Where do device bytes go? | `ch7/memory.pdf`, `fig:7-memory`, `tab:7-e1-memory` | Model versus measured remainder, workspace and context delta are explicit | Keep, repair placement, P1 | Resident samples + Ch4 byte model | 20.44GiB resident stays separate from22.58GiB sampled peak |
| 7.7 scale | What fits and which recall regions are covered? | `ch7/large_frontiers.pdf`, `fig:7-large` | Caption/endpoints already mark grid coverage; Stella corpus queries explicit | Keep, repair placement, P1 | BGE/Stella + isolated int8 reruns | No fabricated OOM or equal-recall ratio |
| 7.8 resolution/repeats | Which small margins are sensitive? | Precision figures, repeated-build ranges, Ch8 threats table | No missing visual relation | Keep, P1 | Quality step size, build/repeat audit | Do not turn local slopes into retrained-frontier bounds |
| 7.8 stage attribution | Which loss is primary budget versus routing/representation? | `tab:5-query-stages`; reconstruction pilot numbers | Arithmetic caveat and seven-arm scope already present | Keep, P1 | FP64 reconstruction pilot | No unsupported pure-loss decomposition |

## Evidence and identity rules retained

One new figure and one scientific figure upgrade are authorised by this audit. Three existing local layout copies only change spacing/size; scientific plots and numerical tables remain unchanged. E1, T5, D, T1, component ablations, budget and builds retain their own states/boundaries. No experiments, benchmark values, transaction counts, absolute GPU addresses or personal ownership are inferred.

The physical layout will show relative byte offsets in separate allocations, with a toy eight-position index, not measured addresses. The LUT figure will show an exact real-arithmetic identity under the Cartesian premise, with FP32 rounding/tie differences referred to Ch7.3. Ch5's six proof pairs and scientific data are protected by verification.

## Claude review reconciliation

- Inventory: baseline66 pages/28 figures refers to the committed PDF. The working tree already routes Ch1 and Ch6 through the three local `*-layout` copies listed above; those routes are retained. Ch2's candidate cascade is included. A generated include inventory accompanies the final change record and reflects the final29 figures, rather than the prompt's stale paths.
- No appendices are compiled in thesis2. Existing `app:` labels retained in Ch3 are compatibility cross-references to body sections, not proof that appendices are included. Nothing is newly moved to an uncompiled appendix.
- E1 dispatch is categorical: **all non-Vogue E1 cells use G=0**; Vogue uses G=4. The Ch7 text already says105/27 cells. The weaker phrase “most” is not used to qualify these E1 observations here.
- “Same candidates” in the LUT drawing is clarified to **same routed candidates**. Computed FP32 top-c may change. The figure now shows four sign bits per nibble and16 patterns, and its caption reports the existing T4 maximum relative score difference4.64e-7 across forms and Vogue2–4/256 final-ID differences (arXiv/OpenAI-3072 zero). This is not a new experiment or a bit-identity claim.
- Campaign B's complete budget traces, C1's representation audit and A2/A3's machine-code/input audits are retained as distinct evidence families alongside D/T1/T4/T5 and A1. They are not silently folded into E1 or treated as additional throughput tests.
- The physical-layout upgrade has modest explanatory value beyond the previous common-position illustration: independent allocation boundaries, two word groups and calculable relative byte offsets. It remains an upgrade, not a second layout figure. Only one net new figure is added. The two mandatory prompt items are completed; lower-value evidence-boundary/radix maps are rejected.
- Declaration: `main.tex` inputs acknowledgements, which inputs `frontmatter/declaration.tex`; a short research/AI declaration **is compiled**. A separate formal declaration page's institutional requirement is not established by that include chain. Personal ownership still requires author confirmation; no standalone page or fabricated ownership is inserted.
- Current changes were backed up before modification. Existing uncommitted layout work is part of this same recorded round; no other writer's files are overwritten. Final build, proof/table checks, full-page rendering and derived-PDF regeneration are required before replacing the root PDF.

## A1–T5 report-to-body coverage check

Checked against the local `JHQ_GPU/experiments/thesis_evidence/REPORT_CN.md`, especially its final chapter-action list. This is a source/coverage review, not a rerun of experiments. Existing final-review corrections take precedence over overstrong shorthand in that report.

| Campaign | Body coverage | Disposition |
|---|---|---|
| A1 cold builds/peaks | 4.5 assignment scratch/lifetimes;7.7 repeated builds/startup/peak/resident;7.8 five-build ranges | Present: Vogue298–303ms, Stella10.54–10.65s, BGE26.08GiB, Stella22.58GiB;12GiB scratch precedes gather rather than being added to it |
| A2 machine code | 5.5 publication paragraph;3.5 evidence contracts | Present: aligned strong64-bit PTX premise and toolkit corroboration, **not** captured driver-JIT SASS |
| A3 OpenAI alignment | 7.2 interpretation | Present:1,000 query/10,299 base-row sample, cosine/GT overlap. No entity IDs were checked, so wording supports alignment rather than claiming a proven entity-ID match |
| B complete budget traces | 6.2/6.3/6.5 cross-references;7.5 FULL, risk, trace and direct reuse groups | Present:2,304 sampled +12 FULL enumeration matches;18,432 aggregate counts; maximum losses; exact finite-pool model; separately timed four-cell reuse. Fixed-arm lookup remains distinct |
| C1 representation | 4.6 original-input recoding, permutation/offset, correction and joined-build evidence | Present: all-row structural checks versus sampled recoding, boundary/TF32 differences, later centroid-membership limitation |
| D precision switch | 4.2/5.7 TF32 fact;7.2 separate precision table/plot | Present as sensitivity, same TF32-trained cache; archived baseline ratios stay cross-session. Does not substitute D's margins for same-session T1 |
| T1 same-session anchors | 7.2 `sec:b-precision-anchors` and its table | Present with grid sensitivity and interpolation/strict measured distinction. No independent FP32 retraining inferred |
| T2 centred/median coding | 2.3 mean-bias modelling scope;8.2 rank/median-level follow-up | Present as separate-state mechanism/negative evidence, outside E1. Report's causal shorthand about arXiv is not upgraded to a controlled general explanation |
| T3 hashes | 3.5 record availability; linked artifact-access record | Historical binary/model availability limits retained. A hash ledger is not a replacement for missing vectors/model files; do not claim every historic artifact is public |
| T4 strict CPU reference/LUT | 5.2/5.4 scope;7.3 FP32 table comparison;7.4 strict-selection table | Present:55,296 grouped exact-order,13,824 distance-only/56 tie-only;69,120 total. CPU sorts GPU scores. New mechanism caption adds existing numerical evidence without new claims |
| T5 small batch | 7.2 small-batch plot/table;8.3 validity;8.5 recommendation | Present:batch8 at0.97 CAGRA fp32 leads all four;batch32 estimator sensitivity retained. Earlier report's broad low-recall win ratios are superseded by checked final tables, not copied back |

No additional result paragraphs or charts are needed for coverage. Personal contribution and any course-specific requirement for a separate formal declaration page remain author/task-specific confirmations; the already compiled research/AI paragraph is not removed.
