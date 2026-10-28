#!/bin/bash
# T1 (thesis evidence, 2026-10-28): the TF32 sensitivity at recall 0.97 on the two OpenAI sets with
# every method re-measured in one session. The thesis keeps v69 (TF32 rotation/centroid GEMMs at
# d >= 1536, as E1 measured it) as its main result; this supplies the FP32 (v72) sensitivity without
# the cross-day drift of comparing against E1's archived baselines.
#   JHQ          v69 and v72, E1's harness and index variables (arms6 state, batch 1000, groups 0,-1,
#                five rounds, identity check), nprobe 256/384/512 at the small alphas the frontier
#                uses near 0.97; each binary twice, ABBA around the baselines
#   IVF-RaBitQ   E1's bench_rabitq_sweep, only the indexes/modes/probes on E1's frontier near 0.97
#   CAGRA fp32   E1's bench_cuvs.py, graph degree 32, itopk 96-256, widths 1-8
#
#   bash experiments/thesis_evidence/t1_tf32_session.sh   (from the worktree; holds the GPU lock)
set -u
export PATH=/root/miniconda3/bin:/usr/local/cuda/bin:/usr/local/bin:$PATH OMP_NUM_THREADS=16
# E1's launchers (comp8800_poster_e1/launch/e1[abc]_launch.sh) export these: the baselines' search
# temporaries come from workspace pools. The first T1 run omitted them and is kept only as
# RAW_T1_nopool_invalid -- its baseline rates are not E1's protocol.
export RQ_POOL=2048 CUVS_POOL=1
REPO=$(cd "$(dirname "$0")/../.." && pwd); cd "$REPO" || exit 1
E=experiments/comp8800_poster_e1
OUT=$REPO/experiments/thesis_evidence/RAW_T1; mkdir -p "$OUT"
SP=/root/miniconda3/lib/python3.12/site-packages
export LD_LIBRARY_PATH="$(ls -d $SP/*/lib64 $SP/*/lib 2>/dev/null | tr '\n' ':')${LD_LIBRARY_PATH:-}"
L=$OUT/PROGRESS.log
say(){ echo "$(date -u +%FT%TZ) $*" | tee -a "$L"; }
say "=== T1 start head=$(git log --oneline -1) dirty=$(git status --porcelain --untracked-files=no | wc -l)"
for b in build/demo_jhq_v69_batch build/demo_jhq_v72_batch build_e1/bench_rabitq_sweep; do say "binary $(sha256sum $b)"; done
exec 8>/root/.gpu_lock; flock 8
say "got the GPU; loadavg $(cut -d' ' -f1-3 /proc/loadavg)"

D=/root/autodl-tmp
declare -A P MM BLK AL A
P[openai3-1536]="$D/openai3-1536/base.fvecs $D/openai3-1536/query.fvecs $D/openai3-1536/groundtruth.ivecs"
P[openai3-3072]="$D/openai3-3072/base.fvecs $D/openai3-3072/query.fvecs $D/openai3-3072/groundtruth.ivecs"
MM[openai3-1536]=192; BLK[openai3-1536]=512;  AL[openai3-1536]=8; A[openai3-1536]=4,8,16,32
MM[openai3-3072]=384; BLK[openai3-3072]=1024; AL[openai3-3072]=4; A[openai3-3072]=2,4,8,16

jhq(){  # bin ds np rep
  local b=$1 ds=$2 np=$3 r=$4 pre=$OUT/jhq_$1_$2_np$3_r$4
  env JHQ_INDEX_CACHE="$D/arms6_cache/$ds" JHQ_BLOCK=${BLK[$ds]} JHQ_TILE_M_RT=${MM[$ds]} \
      JHQ_N_TRAIN=319488 JHQ_GPU_CODEBOOK=1 JHQ_ENCODE_GROUPED_OFF=1 JHQ_Y_TRANSPOSED=1 \
      JHQ_RES_TRAIN_N=100000 JHQ_BP_LANES=16 JHQ_BP_ALPHAS=${A[$ds]} JHQ_BP_BATCHES=1000 \
      JHQ_BP_GROUPS=0,-1 JHQ_BP_ROUNDS=5 JHQ_BP_MIN_BATCHES=24 JHQ_BP_CHECK=1 \
      timeout 3600 build/demo_jhq_${b}_batch ${P[$ds]} ${MM[$ds]} 8 8 ${AL[$ds]} 10 8192 $np 8 1024 "$pre" 3 \
      > "$pre.txt" 2>&1
  say "jhq $b $ds np=$np r=$r rc=$? $(grep -c 'BP_OK' "$pre.txt") ok, $(grep -ci 'mismatch\|NON-TIE [1-9]\|error' "$pre.txt") flagged"
}
rabitq(){  # ds nlist bits modes nprobes
  local ds=$1 nl=$2 bits=$3
  RQ_IDX=$D/rq_t1_${ds}.idx RQ_MODES=$4 RQ_NPROBES=$5 timeout 3600 build_e1/bench_rabitq_sweep ${P[$ds]} $nl $bits \
      "$OUT/rabitq_${ds}.jsonl" > "$OUT/rabitq_${ds}_nl${nl}_b${bits}.log" 2>&1
  say "rabitq $ds nlist=$nl bits=$bits modes=$4 rc=$? $(grep -c '^  bits' "$OUT/rabitq_${ds}_nl${nl}_b${bits}.log") points, $(grep -c FAILED "$OUT/rabitq_${ds}_nl${nl}_b${bits}.log") failed"
}
cagra(){  # ds
  timeout 3600 python3 $E/bench_cuvs.py --dataset $1 --method cagra --graph-degrees 32 \
      --itopk 96,128,192,256 --search-width 1,2,4,8 --out "$OUT/cuvs_$1_cagra.jsonl" > "$OUT/cuvs_$1_cagra.log" 2>&1
  say "cagra $1 rc=$? $(grep -c '^  ' "$OUT/cuvs_$1_cagra.log") lines, $(grep -c FAILED "$OUT/cuvs_$1_cagra.log") failed"
}

for ds in openai3-1536 openai3-3072; do
  for np in 256 384 512; do jhq v69 $ds $np 1; jhq v72 $ds $np 1; done
  if [ $ds = openai3-1536 ]; then
    rabitq $ds 4096 9 0 192,256,384,512
    rabitq $ds 8192 9 0 256,384,512
    rabitq $ds 4096 8 0 256,384
  else
    rabitq $ds 4096 9 0,2 192,256,384,512
  fi
  cagra $ds
  for np in 256 384 512; do jhq v72 $ds $np 2; jhq v69 $ds $np 2; done
done
rm -f $D/rq_t1_*.idx
say "=== T1_DONE"
