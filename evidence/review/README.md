# Follow-up review inputs

This directory mirrors the **consumed input subset** for the T4/T5 audit
and the full-review checks of T1 and A2. `JHQ_GPU/` preserves each original
relative path; `manifest.json` records byte hashes and the source checkout
used to collect the files. That checkout is not asserted to be the build
commit of every measured executable.

From the report root:

```sh
python3 evidence/review/check.py
python3 evidence/review/check.py --run-audits
```

The second command also reconstructs the tables and numerical ledgers with
Python's standard library. It uses this local source root and runs no GPU
or network operation. The same commands are available explicitly:

```sh
python3 scripts/audit_t4_t5.py --source evidence/review/JHQ_GPU --no-plot
python3 scripts/audit_full_review.py --source evidence/review/JHQ_GPU
```

T4 supplies retained strict-selection JSONL/stdout, table-form comparison
summaries, the CPU checker and relevant v71/v73 source. The temporary
`.topc` candidate arrays were deleted by the campaign; this package cannot
repeat comparisons of those deleted arrays. Padding checks count valid
survivors, and the final-selection reference sorts retained computed scores.

T5 supplies the consumed JSON measurements, timing harnesses and launcher.
The report corrects the original summary's omission of higher-recall
qualifying endpoints; the original inputs remain unchanged.

T1 supplies the JSON anchors, launcher and original analysis/summary.
Its baselines are contemporaneous with its JHQ repetitions; they are
separate from campaign D's archived-baseline comparison. This is not a
complete replacement E1 sweep or a full FP32-retraining experiment.

A2 supplies the captured kernel PTX, toolkit-generated SASS and extraction
metadata. The original executable bytes and driver-JIT SASS are absent.
The recorded binary hash identifies an archival claim, not an executable
that can be re-extracted from this package.

Source authorship remains with the original project and its cited work.
This is not the complete CUDA project, a standalone GPU build kit, vector
datasets, trained-state caches, or an independent GPU rerun. Other thesis
campaigns retain their own input ledgers and access boundaries.

The older 209-file LUT package is separately checked by
`python3 evidence/ch5/v71/check.py`. Its publication commit is
[`lrlorry/8800_report@1786e6e`](https://github.com/lrlorry/8800_report/commit/1786e6ec227ce54b657a605d9bfa11dbf3c89923),
not a commit in the code repository `lrlorry/JHQ_GPU`.
