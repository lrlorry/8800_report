# 论文补充证据：移出PDF的辅助图表

本文件对应以 `86bf0f0` 为基线的精准精简：12张辅助表与1张估算图不再编入中英文PDF。
完整原表、图注和数值仍在仓库；这些是既有记录，没有运行新实验。论文不增加同PDF附录。
核心公式与证明、T4/T5、FULL及抽样风险、直接复用、规模结果和两项负案例保持在论文中。
第4章的内存生命周期表继续留在正文。下文显示英文原表内容；中英文精确TeX原件及SHA-256见
[归档清单](../evidence/editorial/86bf0f0/manifest.json)。标签为移出前的历史标签，当前PDF编号已更新。

## 证据登记字段

历史标签：`tab:3-ledger`。正文保留身份与哈希边界，完整字段在此复查。

[英文原件](../evidence/editorial/86bf0f0/en/tab-3-ledger.tex) · [中文原件](../evidence/editorial/86bf0f0/zh/tab-3-ledger.tex)

Claim-to-evidence record and available provenance. Appendix A maps implementation names, executable names and result-to-figure paths.

| Field group | Recorded identity / condition | Interpretation |
| --- | --- | --- |
| Claim and intervention | RQ, mechanism, control, metric, result location and figure/table | Scope identifies what the comparison tests |
| Execution | Run-head or report version, harness, compiler flags, GPU/driver/toolkit | Current analysis checkout is separate from run source; complete executable hashes are missing |
| Index and queries | Shape, metric, training request, cache path, split/seed, $k$, probes, $\alpha$, batch | Cache names and dimensions are recorded; complete historical data/state fingerprints are missing |
| Measurement | Timing scope, warm-up, round/call counts, reference semantics and diagnostics | Family-specific protocols remain attached to their records |
| Analysis | Raw relative path and SHA-256, parser, generated output, validity status | Supports offline regeneration of reported quantities |

## 证据类别与推断范围

历史标签：`tab:3-evidence`。正文改为短段落，仍区分证明、有限参考、配对测量、系统测量和模型。

[英文原件](../evidence/editorial/86bf0f0/en/tab-3-evidence.tex) · [中文原件](../evidence/editorial/86bf0f0/zh/tab-3-evidence.tex)

Evidence classes and the conclusions they support.

| Class | Supported inference and scope |
| --- | --- |
| Formal proof | Selection or coverage property under explicit score, ordering, nestedness and memory assumptions |
| Reference correctness | Agreement on tested cases and comparison keys; ties and ID-set versus bitwise equality remain distinct |
| Paired benchmark | Throughput effect within a fixed state/workload; microarchitectural attribution needs additional measurements |
| End-to-end measurement | Observed operating region on the measured device, batch and tuning grids |
| Model estimate | Byte decomposition or calibration payback under stated accounting and reuse assumptions |
| Unverified claim | A proposed explanation or pending measurement; supplies a research direction rather than an empirical result |

## 历史残差迭代诊断

历史标签：`tab:4-lloyd`。保留2,000轮预算的理由；历史数据不混入最终前沿。

[英文原件](../evidence/editorial/86bf0f0/en/tab-4-lloyd.tex) · [中文原件](../evidence/editorial/86bf0f0/zh/tab-4-lloyd.tex)

Historical residual-iteration diagnostic (100K sample). Recall@10 improves markedly from 25 to 2,000 updates; subsequent gains are small and nonmonotonic. These are not the final Chapter 7 benchmark points.

| Dataset | Cap 25 | Cap 2,000 | Cap 5,000 | Cap 40,000 |
| --- | --- | --- | --- | --- |
| Vogue | 0.9770 | 0.9846 | 0.9843 | 0.9845 |
| BGE | 0.9514 | 0.9585 | 0.9592 | 0.9586 |
| Stella | 0.9852 | 0.9915 | 0.9921 | 0.9916 |

## 表示pilot的逐数据集误差

历史标签：`tab:4-pilot`。正文保留误差范围、总体和跳过缺失ID的限制。

[英文原件](../evidence/editorial/86bf0f0/en/tab-4-pilot.tex) · [中文原件](../evidence/editorial/86bf0f0/zh/tab-4-pilot.tex)

Archived pilot diagnostics. Correction error covers all indexed rows; returned-score error covers the GPU top-10 comparison for sampled queries. Relative score error is $\vert s_{\rm GPU}-s_{64}\vert /s_{64}$, where the reference includes the query-norm constant.

| Dataset | Indexed rows | Max correction absolute error | Max returned-score relative error |
| --- | --- | --- | --- |
| Vogue | 932,328 | $1.28\times10^{-7}$ | $2.66\times10^{-7}$ |
| arXiv | 2,253,000 | $1.35\times10^{-7}$ | $2.38\times10^{-7}$ |
| OpenAI-3072 | 999,000 | $2.77\times10^{-7}$ | $4.85\times10^{-5}$ |

## 库默认值与显式评测设置

历史标签：`tab:5-evaluation-settings`。正文保留16 lanes、策略−1、共享界及512伪查询；这些不是库默认值。

[英文原件](../evidence/editorial/86bf0f0/en/tab-5-evaluation-settings.tex) · [中文原件](../evidence/editorial/86bf0f0/zh/tab-5-evaluation-settings.tex)

Library defaults and measured pipeline settings. Environment variables or setters can override library defaults. The policy parameter $-1$ requests scheduling; it does not force a grouped kernel.

| Control | Unconfigured library | E1 / budget pipeline |
| --- | --- | --- |
| Refinement lanes | 0: scalar byte path | 16: cooperative word path |
| Scan policy | 0: query-centric | $-1$: scheduler chooses 0/2/4/8 |
| Shared bound | Enabled, inactive at $G_{\mathrm{scan}}=0$ | Enabled, used only when $G_{\mathrm{scan}}>1$ |
| Schedule statistic | Not calibrated automatically | 512 database pseudoqueries |

## 预算解释与复用条件

历史标签：`tab:6-scope`。正文保留有效输出、GT质量、尾部风险、共同排序／枚举、稳定性与复用成本条件。

[英文原件](../evidence/editorial/86bf0f0/en/tab-6-scope.tex) · [中文原件](../evidence/editorial/86bf0f0/zh/tab-6-scope.tex)

Conditions to check before interpreting or reusing a calibrated budget. Measured net cost and representation checks have stated finite coverage; future drift handling remains separate work.

| Failure mode | Evidence or condition needed |
| --- | --- |
| Reference misses true neighbours | Held-out GT quality alongside agreement |
| Sample misses difficult queries | Crossing frequency and tail loss over the stated pool |
| Non-nested ties or changed paths | Common ordering, or matched finite-grid enumeration |
| Noisy arm timing or short job | Repeated timing and direct total cost including calibration |
| Changed index, route or query mix | Fresh validation before reusing the chosen multiplier |
| Underfull or invalid outputs | Valid-ID counts and uniqueness before applying set agreement |

## 完整实验族清单

历史标签：`tab:7-manifest`。正文保留分组说明；下表数量不是独立索引构建次数。

[英文原件](../evidence/editorial/86bf0f0/en/tab-7-manifest.tex) · [中文原件](../evidence/editorial/86bf0f0/zh/tab-7-manifest.tex)

Evidence families. Counts denote measured configurations or checks, not independent index builds. All use the RTX 5090; timing protocols differ.

| Family | Purpose and implementation | Coverage |
| --- | --- | --- |
| E1 | v69 versus cuVS graph, PQ, RaBitQ and brute force | 1,590 points; 4 datasets |
| LUT | v71 table grouping, $G_{\mathrm{LUT}}\in\{1,2,4,8\}$ | 24 cells; 96 arms |
| Packing | Historical byte/word access factorial | 48 paired cells |
| Refinement | v61 scalar/load/lane ablation | 13 configurations |
| Scan/bound | v62 global selection; v63 shared bound | 64 / 48 correctness checks |
| Scheduling | Integrated v65 execution policy | 50 workload--batch cells |
| Probe | v69 exact computed-score probe selection | 1,792 synthetic cases |
| Budget | v69 sampled, full-pool and oracle budgets | 12 cells; 64 draws per $S$ |
| Scale | v69 search, cold builds and resident memory | BGE and Stella extensions |
| Supplement | Repeated builds; PTX; pairing; budget traces; precision | 30 builds; 12 budget cells; 76 precision pairs |
| T4/T5 | Strict selection reference; small-batch frontiers | 270 checks; 1,808 timing points |

## Vogue前沿的执行路径敏感性

历史标签：`tab:7-e1-paths`。两行比值全部并入正文；调度路径与单block路径的比较不单独隔离共享界。

[英文原件](../evidence/editorial/86bf0f0/en/tab-7-e1-paths.tex) · [中文原件](../evidence/editorial/86bf0f0/zh/tab-7-e1-paths.tex)

Vogue E1 path sensitivity at batch 1,000. Both frontiers use the same run--budget grid and log-QPS interpolation rule against RaBitQ; each paired run has bit-identical final outputs.

[原数值表](../tables/ch7/e1_paths.tex)

| Recall | $G_{\mathrm{scan}}=4$ / RaBitQ | $G_{\mathrm{scan}}=0$ / RaBitQ |
| --- | --- | --- |
| 0.96 | 1.250 | 1.072 |
| 0.97 | 1.059 | 0.933 |

## 全部八档固定预算

历史标签：`tab:7-fixed-budget`。正文保留64／100／200的质量及吞吐缺口，64仍是重要的更强对照。

[英文原件](../evidence/editorial/86bf0f0/en/tab-7-fixed-budget.tex) · [中文原件](../evidence/editorial/86bf0f0/zh/tab-7-fixed-budget.tex)

Fixed-budget controls over twelve held-out cells. Qualifying means within $10^{-3}$ of the best tested recall at printed precision. Worst recall loss uses all cells; QPS deficit uses only cells where that arm qualifies. A dash means no qualifying cells.

[原数值表](../tables/ch7/fixed_budgets.tex)

| $\alpha$ | Qualifying cells | Worst recall loss | Max qualifying QPS deficit |
| --- | --- | --- | --- |
| 2 | 0/12 | 0.3100 | -- |
| 4 | 2/12 | 0.1774 | 2.3% |
| 8 | 4/12 | 0.0930 | 2.1% |
| 16 | 6/12 | 0.0408 | 4.4% |
| 32 | 7/12 | 0.0170 | 9.1% |
| 64 | 10/12 | 0.0050 | 26.6% |
| 100 | 10/12 | 0.0016 | 40.9% |
| 200 | 12/12 | 0.0000 | 57.1% |

## 模型估算的回本图

历史标签：`fig:7-budget-payback`。PDF保留回本公式、十二配置估算表和范围，优先展示四配置直接复用实测图。

[英文原件](../evidence/editorial/86bf0f0/en/fig-7-budget-payback.tex) · [中文原件](../evidence/editorial/86bf0f0/zh/fig-7-budget-payback.tex)

Estimated calibration payback relative to fixed budgets 100 and 64. Filled circles denote 128 probes and open triangles 512 probes. Top-row points have no throughput payback. Estimates invert mean selected-arm QPS and use 500 queries, or 499 for Stella.

[查看原估算图](../figures/ch7/budget_payback.pdf)。
该图由固定臂QPS推算，不是直接复用计时；500查询／批，Stella为499。

## 六数据集重复空缓存构建

历史标签：`tab:7-build-repeat`。正文保留主要范围、五次构建的召回波动、启动边界及采样峰值。

[英文原件](../evidence/editorial/86bf0f0/en/tab-7-build-repeat.tex) · [中文原件](../evidence/editorial/86bf0f0/zh/tab-7-build-repeat.tex)

Supplementary empty-cache construction. Train+add and Start give ranges over three normal warm-input runs; First read is this session's first-read startup observation. Start ends at add completion, before schedule calibration/search. Peak is the maximum 20 ms device sample over the normal runs, including context. Recall spans five independent builds at fixed 128-probe operating points, including the phase diagnostic.

[原数值表](../tables/supplement/build.tex)

| Dataset | Train+add (s) | Start (s) | First read (s) | Peak (GiB) | Recall range |
| --- | --- | --- | --- | --- | --- |
| Vogue | 0.558--0.566 | 2.0--2.1 | 4.9 | 4.11 | 0.9636--0.9644 |
| arXiv | 0.984--0.987 | 3.1--3.2 | 9.1 | 7.83 | 0.9757--0.9769 |
| OpenAI-1536 | 0.986--0.996 | 4.1--4.3 | 10.0 | 7.66 | 0.9313--0.9317 |
| OpenAI-3072 | 1.809--1.830 | 7.1--7.2 | 17.0 | 11.39 | 0.9266--0.9268 |
| BGE | 7.172--7.341 | 13.6--15.9 | 51.4 | 26.08 | 0.9174--0.9178 |
| Stella | 10.543--10.653 | 18.2--18.6 | 129.9 | 22.58 | 0.9887--0.9890 |

## 原第七章RQ答案表

历史标签：`tab:7-rq-answers`。正式答案集中到第九章；这里留存旧汇总以供追溯。

[英文原件](../evidence/editorial/86bf0f0/en/tab-7-rq-answers.tex) · [中文原件](../evidence/editorial/86bf0f0/zh/tab-7-rq-answers.tex)

Answers to the four research questions, supported by this chapter.

| RQ | Evidence | Answer | Boundary |
| --- | --- | --- | --- |
| RQ1 | Cold build; resident components; large searches | 17.78M vectors on one GPU; 20.44 GiB; repeated train+add 10.54--10.65 s | Sampled peak 22.58 GiB; no multi-GPU scaling |
| RQ2 | Strict CPU reference; paired execution checks | 55,296 complete-key instances match in order; scheduling $2.727\times$ at batch 8 | Finite T4 grid; FP32 table forms can change final IDs; full-batch gains smaller |
| RQ3 | Disjoint queries; fixed 64/100; full pool; oracle; enumeration | Full pool meets 12/12 quality targets; maximum loss 0.0006 | Retrospective working point; $S=128$ has up to 40/64 loss crossings; net cost directly measured on four cells |
| RQ4 | E1 and T5 frontiers; both recall estimators; memory | E1: three leads at 0.97; T5: CAGRA leads at batch 8 and 0.97; allocation below fp32 CAGRA, comparable to int8 | OpenAI E1 uses TF32; smaller FP32 leads; finite unequal grids and interface costs; batch-32 near ties depend on estimator |

## 十二配置完整尾部矩阵

历史标签：`tab:7-budget-tails`。正文保留最大损失、关键反例、FULL结果以及抽样风险图。

[英文原件](../evidence/editorial/86bf0f0/en/tab-7-budget-tails.tex) · [中文原件](../evidence/editorial/86bf0f0/zh/tab-7-budget-tails.tex)

Maximum held-out recall loss over the 64 draws at each sample size, relative to the best tested arm. All twelve FULL selections match enumeration. Maxima complement the earlier means, p95 and crossing rates.

[原数值表](../tables/supplement/budget_tails.tex)

| Dataset | Probes | FULL $\alpha$ | Max $L_{32}$ | Max $L_{64}$ | Max $L_{128}$ |
| --- | --- | --- | --- | --- | --- |
| Vogue | 128 | 100 | 0.0104 | 0.0104 | 0.0022 |
| arXiv | 128 | 200 | 0.0134 | 0.0024 | 0.0024 |
| OpenAI-1536 | 128 | 8 | 0.0018 | 0.0018 | 0.0018 |
| OpenAI-3072 | 128 | 4 | 0.0046 | 0.0046 | 0.0000 |
| BGE | 128 | 64 | 0.0100 | 0.0038 | 0.0038 |
| Stella | 128 | 16 | 0.0174 | 0.0030 | 0.0030 |
| Vogue | 512 | 100 | 0.0112 | 0.0030 | 0.0030 |
| arXiv | 512 | 200 | 0.0170 | 0.0050 | 0.0050 |
| OpenAI-1536 | 512 | 8 | 0.0272 | 0.0026 | 0.0026 |
| OpenAI-3072 | 512 | 4 | 0.0072 | 0.0072 | 0.0002 |
| BGE | 512 | 64 | 0.0294 | 0.0046 | 0.0046 |
| Stella | 512 | 16 | 0.0182 | 0.0030 | 0.0030 |

