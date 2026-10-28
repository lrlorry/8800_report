# Fixed artifact access map

Checked 29 October 2026. These are public, fixed-revision entry points for the manuscript and the input subsets retained with the report. They supplement Appendices A–B. The source/record manifests distinguish an archival source revision from the measured executable’s identity.

The report evidence links below use `8800_report@5003f08b18eb7e3a9ed3e7376c0f88b56fc68503`. This revision already contains the cited bundles and numeric inputs. Later editorial changes do not relabel the original measurements.

| Material | Fixed public entry | Scope |
|---|---|---|
| Associated JHQ-GPU manuscript | [Manuscript source](https://github.com/lrlorry/JHQ_GPU/blob/70da383056b50f4e9b8e9a8030bc9b92281ba537/paper_adc2026/ADC/mainADC.tex) | Author/title checked against local source; the file bytes match local `19135c9`. This is a project manuscript, with its own historical measurements; no publication status inferred. |
| v71 LUT source and records | [209-file package](https://github.com/lrlorry/8800_report/tree/5003f08b18eb7e3a9ed3e7376c0f88b56fc68503/evidence/ch5/v71) | Selected original source, harness, CMake/run inputs and the archived LUT records; hashes and 22/24 recount can be checked offline. |
| T4 strict-selection source | [v73 export source](https://github.com/lrlorry/8800_report/tree/5003f08b18eb7e3a9ed3e7376c0f88b56fc68503/evidence/review/JHQ_GPU/jhq_v73_topcref) | Recorded source with debug exports; not a complete standalone CUDA build kit. |
| T4 retained outputs | [RAW_T4](https://github.com/lrlorry/8800_report/tree/5003f08b18eb7e3a9ed3e7376c0f88b56fc68503/evidence/review/JHQ_GPU/experiments/thesis_evidence/RAW_T4) | JSONL/stdout, table-form summaries and CPU-check results. Temporary `.topc` arrays were deleted; these records cannot re-execute comparisons of those arrays. |
| T5 small-batch baselines | [RAW_T5](https://github.com/lrlorry/8800_report/tree/5003f08b18eb7e3a9ed3e7376c0f88b56fc68503/evidence/review/JHQ_GPU/experiments/thesis_evidence/RAW_T5) | Numeric timing/quality records; relevant launchers and harnesses are in the parent evidence directory. |
| T1 precision anchors | [RAW_T1](https://github.com/lrlorry/8800_report/tree/5003f08b18eb7e3a9ed3e7376c0f88b56fc68503/evidence/review/JHQ_GPU/experiments/thesis_evidence/RAW_T1) | Contemporaneous anchor measurements, separate from campaign D and E1; not FP32 retraining. |
| A2 machine-code evidence | [RAW_A2](https://github.com/lrlorry/8800_report/tree/5003f08b18eb7e3a9ed3e7376c0f88b56fc68503/evidence/review/JHQ_GPU/experiments/thesis_evidence/RAW_A2) | Captured PTX, toolkit SASS and extraction metadata; not the executable bytes or the driver’s loaded JIT SASS. |
| Protocol and relocated displays | [Detailed protocol](https://github.com/lrlorry/8800_report/blob/5003f08b18eb7e3a9ed3e7376c0f88b56fc68503/docs/experiment-protocol.md), [supplementary evidence](https://github.com/lrlorry/8800_report/blob/5003f08b18eb7e3a9ed3e7376c0f88b56fc68503/docs/supplementary-evidence.md) | Definitions, input paths, analysis mapping and complete tables/figure moved outside the PDF. |

From a report checkout, the following checks use the bundled input subsets and execute no GPU benchmark:

```sh
python3 evidence/ch5/v71/check.py
python3 evidence/review/check.py --run-audits
```

The latter reconstructs T4/T5 and T1/A2 ledgers using the included source root. It checks retained records rather than rerunning GPU kernels or the deleted T4 arrays.

The complete local `JHQ_GPU` source was at `19135c965a2cfccf469efb6b75029a268c7c3b5b` during this review. Public `JHQ_GPU/main` was `70da383056b50f4e9b8e9a8030bc9b92281ba537`, 20 commits behind. That public main must not be presented as containing all supplementary work. The fixed report bundles above make their stated subsets accessible now; a full source release still requires the author to choose and publish the intended revision or supply it to assessors.

Complete vectors, trained-state caches, all historical executable bytes and all raw campaigns are not included in those bundles. Their acquisition, permissions and corresponding build environments remain additional GPU-reproduction inputs. The report’s hash ledgers do not replace those files. Whether the course requires a separate code upload remains a task-specific submission question.
