v71 LUT sweep: review evidence
-----------------------------
Original project: https://github.com/lrlorry/JHQ_GPU
Recorded run head: d5e1526 (full hash in manifest.json and source extracted
from that commit). Source authorship remains with the original project.

source/ contains selected original source, the benchmark harness, CMake
definitions and run script. raw/ contains the archived measurement files:
96 timed JSON records covering 24 dataset/probe cells and four LUT choices,
four gate-check JSON records, corresponding text output, and build/progress
logs. Original .log filenames receive an extra .txt suffix to avoid the
report repository's build-log ignore rule. File contents are unchanged.
manifest.json maps every file to its original path and SHA-256.
Run python3 evidence/ch5/v71/check.py from the report root to verify all
209 archived file hashes and independently recount the 22/24 result.
This uses Python's standard library and does not execute CUDA.

The source was extracted from Git history, not reconstructed from prose.
The three archived v71 implementation files match the files reviewed in
data/ch5/execution-review.json. The run-header commit is source provenance;
the measured executables and trained-state caches have no archived hashes.

The Chapter 7 figure with label fig:7-lut uses these timed records;
scripts/build_ch7.py contains the analysis and figure construction.
All Chapter 7 inputs, including other campaigns, remain listed separately
in data/ch7/sources.csv. Do not invoke build_ch7.py on this partial bundle
as if it contained those other campaigns.

This bundle supports source review and offline checking of the archived
LUT measurements. It is not the complete JHQ_GPU source tree, a standalone
CUDA build kit, the vector datasets, the trained states, PTX/SASS, or an
independent GPU rerun. It supplies no per-candidate full-table/split-table
score-error or tie comparison. Publication requires pushing the new files;
local preparation alone does not make them available on GitHub.
