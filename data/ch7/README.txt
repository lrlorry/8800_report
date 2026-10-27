Chapter 7 evidence and review notes
=================================

Purpose
-------
This directory supports chapters/07-evaluation.tex. The chapter follows all
8 sections in 6.pdf. It contains 9 figures and 9 tables. Numeric tabular
outputs are generated under tables/ch7; the manifest is written in the
chapter itself. Four previously completed vector figures are used directly:
LUT grouping, held-out risk, payback and memory. Five new figures recompute
existing measurements: E1 frontiers, packing/refinement, batch execution,
construction and large-dataset frontiers. CAGRA int8 is included wherever
its measurements are available. No new GPU measurement was performed.

Commands (from 8800_report)
-------------------------
  python3 scripts/build_ch7.py --source ../JHQ_GPU
  make pdf

Python analysis requires matplotlib and numpy, in addition to the standard
library. LaTeX requires the packages already used by this thesis template.
thesis.pdf is the single integrated review draft, with Chapter 7 in place.
Other thesis chapters remain in their prior skeleton state.

Outputs
-------
audit.json   Raw-derived counts, ratios, coverage, budget and memory values.
matched.csv  Interpolated and actual measured threshold comparisons; empty
             numeric fields mean no coverage. No extrapolation is performed.
sources.csv  Input paths relative to JHQ_GPU and SHA-256 hashes.

The source_snapshot field is the checkout audited here, NOT the commit of
every experimental binary. Historical run headers retain their own commit
identifiers. For example, the v69 budget/LUT campaign header is d5e1526,
and the successful isolated Stella degree-64 int8 record is ad433a4.
The ledger includes the current relevant implementation files but does not
reconstruct every historical binary or capture the full build environment.

Source families
---------------
E1:       experiments/comp8800_poster_e1/RAW_RESULTS/
          Parser: experiments/comp8800_poster_e1/analyze.py
          Protocol: experiments/comp8800_poster_e1/FAIRNESS_AUDIT.md
LUT:      experiments/adc_v69/RAW_LUT/v71_g*.json
Packing:  paper_adc2026/data/layout6.log
Refine:   experiments/warp_refine/raw/ab/*.json and raw/summary.json
Scan:     experiments/pipeline_v62/raw/{check,perf}/
Bound:    experiments/pipeline_campaign/exp2/v63_raw/{check,perf}/
Schedule: experiments/pipeline_campaign/exp47/raw/bench/*.json
Probe:    experiments/practical_opt/v69_results/{id_*,t_*,v69_summary.json}
Budget:   experiments/adc_v69/RAW/budget_v69.log
          Harness: examples/demo_jhq_budget_arms_v69.cu
Scale:    experiments/adc_v69/RAW_BIG/ (top-level corrected records)
Memory:   v71_g2_*_np128.json (alpha=100)
Figures:  paper_adc2026/figures_v69/ and paper_adc2026/figs_v69/

关键核对结论（中文）
------------------
1. 跨系统结果：1590 个 E1 点、0 failure、50 个索引记录；重新计算并
   对照归档表核验了 110 个已有 matched-recall 比值。CAGRA int8 不能
   从正文对照中省略。JHQ 并非在所有 recall 区间都最快。

2. 两组 LUT：新版 v71 是 22/24 个 cell 中位吞吐最高，不能沿用 ADC
   旧版 23/24。两个例外差距约 0.23% 和 0.84%，不作显著性结论。
   同时明确区分 g_LUT、g_scan、refinement lanes。

3. 精确性：v62 有 64 个配置比较、v63 有 48 个配置比较。集成调度有
   250 个比较、234320 次逐查询比较，non-tie primary 差异和最终 ID
   集合差异均为零。不能把 set 相同一概写成距离、顺序逐位相同。

4. Probe：1792 个 synthetic case 无失败；12 个 workload/batch 的
   v69/v65 吞吐比从各 10 轮原始数组重新计算，并核对 summary。
   Vogue 的跨版本 IDENTITY_FAIL（0.9642 vs 0.9644）真实存在；记录
   显示 probe/primary 一致，不足以解释最终差异，正文保留异常，未
   擅自认定原因。可选 FP16 路径不并入 FP32 exact 的主结论。

5. 预算：新版 v69 在 10/12 cell 的 mean selected-arm QPS 上提高约
   1.028--1.691 倍。arXiv 是 recall 提高、吞吐降低，不能声称都有回本。
   QPS 是被选固定 arm 的已测 QPS 的算术平均，不是在线服务的新测量。
   表中平均 recall 从已四舍五入的 ceiling/mean_loss 重构，标作近似。
   2304 次同样本对照中 bisection 与 enumeration 一致，不等于泛化保证。

6. 分位数：预算 harness 实际输出 loss[floor(.95*(64-1))]，即排序后
   第 60 项，不是插值分位数。因此 4/64 个 tail losses 可与输出的
   p95_loss=0 共存。保留日志统计、明确口径，同时报告超标次数。
   不把这解释成“所有抽样都无损”。median_alpha 使用 64 项的上中位数。

7. 总体性能：调度各 batch 的 geometric-mean gain 从 raw arrays 重算，
   约 2.727/2.356/1.057/1.015。batch=1000 只有 11 行，其余 13 行；
   Stella 999 条查询不能进入 batch=1000 的完整批实验。held-out config
   与预算实验 held-out query 的定义不同。

8. 显存：Stella used total 20.44 GiB，raw FP32 67.81 GiB；used total
   含 context、workspace，不能当作 index-only 或 construction peak。
   调低 alpha 不释放已存 residual codes。CAGRA int8 的隔离重跑成功，
   初次有旧索引仍存活导致的失败不能当作最终不可运行证据。

9. 构建：JHQ 每个数据集只有一个真正 cold trained-state record，时间
   是 train+add；不含原始磁盘读取和后续调度校准。int8 图中计入数据集
   量化。RaBitQ build function 的 bar 不含其搜索必需的序列化往返。
   不把未尝试、计算超预算和实际 OOM 混为一谈。

What the checks do not establish
-------------------------------
These are offline consistency/reanalysis checks of archived evidence, not
independent reproduction on an RTX 5090. They do not resolve the cause of
Vogue's cross-binary anomaly, establish general recall guarantees, measure
construction peaks, add repeated cold builds, or test workload drift.
The chapter bounds its claims accordingly. Bibliography entries are reused
from the thesis and are outside this numeric audit; the course submission
rules and the remaining chapters also require their own final review.
