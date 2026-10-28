#!/bin/bash
# T5 (thesis evidence, 2026-10-28): the E1 cross-system comparison at batch 8 and 32. E1 compared the
# methods at batch 1,000 only; the scheduler's gains are at small batches, where graph search is
# often strongest. Every method uses one small-batch protocol -- JHQ's harness's: floor(nq / b)
# batches of b, one synchronous host-to-host call per batch, a round is one pass, QPS = queries /
# summed call time, recall over the queries used -- and E1's environment (launcher exports included).
#   JHQ          demo_jhq_v69_batch, E1's (nprobe, alpha) grid, groups 0 and scheduled
#   CAGRA fp32 / int8   bench_cuvs_smallbatch.py (E1's bench, small-batch protocol), E1's grid
#   IVF-RaBitQ   bench_rabitq_smallbatch (E1's bench, same protocol), bits 9 and 4, LUT16 and QUANT4
# The baseline benches also time a "null" call (staging, H2D, D2H, sync, no search): the per-call host
# floor of each harness, which matters at small b and differs between C++ and Python.
#
#   bash experiments/thesis_evidence/t5_smallbatch.sh   (from the worktree; holds the GPU lock)
set -u
export PATH=/root/miniconda3/bin:/usr/local/cuda/bin:/usr/local/bin:$PATH OMP_NUM_THREADS=16
export RQ_POOL=2048 CUVS_POOL=1            # as E1's launchers
REPO=$(cd "$(dirname "$0")/../.." && pwd); cd "$REPO" || exit 1
TE=experiments/thesis_evidence
OUT=$REPO/$TE/RAW_T5; mkdir -p "$OUT"
SP=/root/miniconda3/lib/python3.12/site-packages
export LD_LIBRARY_PATH="$(ls -d $SP/*/lib64 $SP/*/lib 2>/dev/null | tr '\n' ':')${LD_LIBRARY_PATH:-}"
L=$OUT/PROGRESS.log
say(){ echo "$(date -u +%FT%TZ) $*" | tee -a "$L"; }
say "=== T5 start head=$(git log --oneline -1) dirty=$(git status --porcelain --untracked-files=no | wc -l)"
BE=$REPO/build_e1
INC="-I$SP/libraft/include/rapids"; LD=""
for p in $SP/*/include; do [ -d "$p" ] && INC="$INC -I$p"; done
for p in $SP/*/lib64 $SP/*/lib; do [ -d "$p" ] && LD="$LD -L$p -Xlinker -rpath -Xlinker $p"; done
timeout 1800 nvcc -O3 -std=c++20 -ccbin g++-12 --expt-relaxed-constexpr --extended-lambda -arch=sm_120 \
    $INC $TE/bench_rabitq_smallbatch.cu -o "$BE/bench_rabitq_smallbatch" $LD -lcuvs -lrmm -lcudart -lcublas \
    > "$OUT/build_rabitq.log" 2>&1
rc=$?; say "build bench_rabitq_smallbatch rc=$rc"
[ $rc -ne 0 ] && { grep -m 20 error "$OUT/build_rabitq.log" | tee -a "$L"; say "=== T5_DONE build failed, nothing run ==="; exit 1; }
for b in build/demo_jhq_v69_batch $BE/bench_rabitq_smallbatch $TE/bench_cuvs_smallbatch.py; do say "binary $(sha256sum $b)"; done
exec 8>/root/.gpu_lock; flock 8
say "got the GPU; loadavg $(cut -d' ' -f1-3 /proc/loadavg)"

D=/root/autodl-tmp; V=/root/data
declare -A P NL MM NT BLK AL RQNL G
P[vogue-768]="$V/vogue-768_base.fvecs $V/vogue-768_query.fvecs $V/vogue-768_groundtruth.ivecs"
P[arxiv-768]="$D/arxiv-abstracts-768/base.fvecs $D/arxiv-abstracts-768/query.fvecs $D/arxiv-abstracts-768/groundtruth.ivecs"
P[openai3-1536]="$D/openai3-1536/base.fvecs $D/openai3-1536/query.fvecs $D/openai3-1536/groundtruth.ivecs"
P[openai3-3072]="$D/openai3-3072/base.fvecs $D/openai3-3072/query.fvecs $D/openai3-3072/groundtruth.ivecs"
MM[vogue-768]=96;     NL[vogue-768]=4096; NT[vogue-768]=159744; BLK[vogue-768]=512;  AL[vogue-768]=64;  RQNL[vogue-768]=4096
MM[arxiv-768]=96;     NL[arxiv-768]=8192; NT[arxiv-768]=319488; BLK[arxiv-768]=512;  AL[arxiv-768]=100; RQNL[arxiv-768]=8192
MM[openai3-1536]=192; NL[openai3-1536]=8192; NT[openai3-1536]=319488; BLK[openai3-1536]=512;  AL[openai3-1536]=8; RQNL[openai3-1536]=4096
MM[openai3-3072]=384; NL[openai3-3072]=8192; NT[openai3-3072]=319488; BLK[openai3-3072]=1024; AL[openai3-3072]=4; RQNL[openai3-3072]=4096
# E1's measured JHQ grid (comp8800_poster_e1/E1_points.csv)
for np in 16 32; do G[vogue-768:$np]=16,32,64; done
for np in 64 96 128 192 256 384 512; do G[vogue-768:$np]=32,64,128; done
for np in 16 32; do G[arxiv-768:$np]=25,50,100; done
for np in 64 96 128 192 256 384 512; do G[arxiv-768:$np]=50,100,200; done
G[arxiv-768:1024]=50,100
G[openai3-1536:32]=4,8,16,32; G[openai3-1536:64]=4,8,16,32,64; G[openai3-1536:128]=4,8,16,32,64
G[openai3-1536:256]=4,8,16,32,64,128,256,512; G[openai3-1536:512]=4,8,16,32,64,128,256,512
G[openai3-1536:1024]=8,16,32,64,128,256,512
G[openai3-3072:32]=2,4,8,16; G[openai3-3072:64]=2,4,8,16,32
for np in 128 256 512; do G[openai3-3072:$np]=2,4,8,16,32,64,128,256; done
G[openai3-3072:1024]=8,16,32,64,128,256
NPS(){ case $1 in vogue-768) echo 16 32 64 96 128 192 256 384 512;; arxiv-768) echo 16 32 64 96 128 192 256 384 512 1024;;
       openai3-1536|openai3-3072) echo 32 64 128 256 512 1024;; esac; }

jhq(){  # ds np
  local ds=$1 np=$2 pre=$OUT/jhq_$1_np$2
  env JHQ_INDEX_CACHE="$D/arms6_cache/$ds" JHQ_BLOCK=${BLK[$ds]} JHQ_TILE_M_RT=${MM[$ds]} \
      JHQ_N_TRAIN=${NT[$ds]} JHQ_GPU_CODEBOOK=1 JHQ_ENCODE_GROUPED_OFF=1 JHQ_Y_TRANSPOSED=1 \
      JHQ_RES_TRAIN_N=100000 JHQ_BP_LANES=16 JHQ_BP_ALPHAS=${G[$ds:$np]} JHQ_BP_BATCHES=8,32 \
      JHQ_BP_GROUPS=0,-1 JHQ_BP_ROUNDS=5 JHQ_BP_MIN_BATCHES=24 JHQ_BP_CHECK=1 \
      timeout 3600 build/demo_jhq_v69_batch ${P[$ds]} ${MM[$ds]} 8 8 ${AL[$ds]} 10 ${NL[$ds]} $np 8 1024 "$pre" 3 \
      > "$pre.txt" 2>&1
  say "jhq $ds np=$np rc=$? $(grep -c BP_OK "$pre.txt") ok, $(grep -ci 'mismatch\|NON-TIE [1-9]\|error' "$pre.txt") flagged"
}
cuvs(){  # method ds
  timeout 7200 python3 $TE/bench_cuvs_smallbatch.py --dataset $2 --method $1 --batches 8,32 \
      --out "$OUT/cuvs_$2_$1.jsonl" > "$OUT/cuvs_$2_$1.log" 2>&1
  say "cuvs $1 $2 rc=$? $(grep -c ' b=' "$OUT/cuvs_$2_$1.log") points, $(grep -c FAILED "$OUT/cuvs_$2_$1.log") failed"
}
rabitq(){  # ds bits
  RQ_IDX=$D/rq_t5_$1.idx RQ_MODES=0,2 RQ_NPROBES=16,32,64,128,192,256,384,512 RQ_BATCHES=8,32 \
      timeout 7200 "$BE/bench_rabitq_smallbatch" ${P[$1]} ${RQNL[$1]} $2 "$OUT/rabitq_$1.jsonl" \
      > "$OUT/rabitq_$1_b$2.log" 2>&1
  say "rabitq $1 bits=$2 rc=$? $(grep -c ' b=' "$OUT/rabitq_$1_b$2.log") points, $(grep -c FAILED "$OUT/rabitq_$1_b$2.log") failed"
}
for ds in vogue-768 arxiv-768 openai3-1536 openai3-3072; do
  for np in $(NPS $ds); do jhq $ds $np; done
  rabitq $ds 9; rabitq $ds 4
  cuvs cagra $ds
  cuvs cagra-int8 $ds
done
rm -f $D/rq_t5_*.idx
say "=== T5_DONE"
