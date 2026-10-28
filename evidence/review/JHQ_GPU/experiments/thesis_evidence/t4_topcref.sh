#!/bin/bash
# T4 (thesis evidence, 2026-10-28): the strict CPU reference for Chapter 5's selection claims and the
# table factorisation's per-candidate effect, on jhq_v73_topcref (v71 whose dump covers every query and
# reads the scan's word layout).
#   strict  demo_jhq_v73_g2_topcref (16+16, the evaluated table): nprobe 1/8/128 (nprobe 1 with
#           alpha 200 leaves queries with fewer candidates than c), alpha 4/100/200, forced paths
#           G = 0 (one block, distance preorder) and 1/2/4/8 (complete key), shared bound off/on;
#           256 queries per configuration, every query sorted on the CPU
#   lut     the same queries at nprobe 128, alpha 100, G 0 and 2 with the bound on, under each table
#           form g = 1 (256 entries), 2, 4, 8; dumps kept and compared candidate by candidate
# Vogue, arXiv and OpenAI-3072, the three workloads of Chapter 5's checks; the paper's trained state.
#
#   bash experiments/thesis_evidence/t4_topcref.sh   (from the worktree; waits for T5, holds the GPU lock)
set -u
export PATH=/root/miniconda3/bin:/usr/local/cuda/bin:$PATH OMP_NUM_THREADS=16
REPO=$(cd "$(dirname "$0")/../.." && pwd); cd "$REPO" || exit 1
OUT=$REPO/experiments/thesis_evidence/RAW_T4; mkdir -p "$OUT"
L=$OUT/PROGRESS.log
say(){ echo "$(date -u +%FT%TZ) $*" | tee -a "$L"; }
until grep -q T5_DONE experiments/thesis_evidence/RAW_T5/PROGRESS.log 2>/dev/null; do sleep 30; done
say "=== T4 start head=$(git log --oneline -1) dirty=$(git status --porcelain --untracked-files=no | wc -l)"
cmake -S . -B build > "$OUT/reconfigure.log" 2>&1
timeout 3600 cmake --build build -j 16 --target demo_jhq_v73_g1_topcref demo_jhq_v73_g2_topcref \
    demo_jhq_v73_g4_topcref demo_jhq_v73_g8_topcref > "$OUT/build.log" 2>&1
rc=$?; say "build_rc=$rc"
[ $rc -ne 0 ] && { grep -m 20 -i error "$OUT/build.log" | tee -a "$L"; say "=== T4_DONE build failed, nothing run ==="; exit 1; }
for g in 1 2 4 8; do say "binary $(sha256sum build/demo_jhq_v73_g${g}_topcref)"; done
exec 8>/root/.gpu_lock; flock 8
say "got the GPU"

D=/root/autodl-tmp; V=/root/data
declare -A P MM NL NT BLK
P[vogue-768]="$V/vogue-768_base.fvecs $V/vogue-768_query.fvecs $V/vogue-768_groundtruth.ivecs"
P[arxiv-768]="$D/arxiv-abstracts-768/base.fvecs $D/arxiv-abstracts-768/query.fvecs $D/arxiv-abstracts-768/groundtruth.ivecs"
P[openai3-3072]="$D/openai3-3072/base.fvecs $D/openai3-3072/query.fvecs $D/openai3-3072/groundtruth.ivecs"
MM[vogue-768]=96;  NL[vogue-768]=4096; NT[vogue-768]=159744; BLK[vogue-768]=512
MM[arxiv-768]=96;  NL[arxiv-768]=8192; NT[arxiv-768]=319488; BLK[arxiv-768]=512
MM[openai3-3072]=384; NL[openai3-3072]=8192; NT[openai3-3072]=319488; BLK[openai3-3072]=1024

run(){  # g ds np tag [env...]
  local g=$1 ds=$2 np=$3 tag=$4; shift 4
  env "$@" JHQ_INDEX_CACHE="$D/arms6_cache/$ds" JHQ_BLOCK=${BLK[$ds]} JHQ_TILE_M_RT=${MM[$ds]} \
      JHQ_N_TRAIN=${NT[$ds]} JHQ_GPU_CODEBOOK=1 JHQ_ENCODE_GROUPED_OFF=1 JHQ_Y_TRANSPOSED=1 \
      JHQ_RES_TRAIN_N=100000 JHQ_BP_LANES=16 JHQ_TR_NQ=256 \
      timeout 3600 build/demo_jhq_v73_g${g}_topcref ${P[$ds]} ${MM[$ds]} 8 8 100 10 ${NL[$ds]} $np 8 1024 \
      "$OUT/${ds}_${tag}" 3 > "$OUT/${ds}_${tag}_np${np}.txt" 2>&1
  say "$tag $ds np=$np g=$g rc=$? $(grep -c '^TR ' "$OUT/${ds}_${tag}_np${np}.txt") configs, nontie $(awk '/^TR /{for(i=1;i<=NF;i++) if($i~/^nontie=/){split($i,a,"=");s+=a[2]}} END{print s+0}' "$OUT/${ds}_${tag}_np${np}.txt"), score_mm $(awk '/^TR /{for(i=1;i<=NF;i++) if($i~/^score_mm=/){split($i,a,"=");s+=a[2]}} END{print s+0}' "$OUT/${ds}_${tag}_np${np}.txt")"
}
for ds in vogue-768 arxiv-768 openai3-3072; do
  for np in 1 8 128; do
    run 2 $ds $np strict JHQ_TR_ALPHAS=4,100,200 JHQ_TR_GROUPS=0,1,2,4,8 JHQ_TR_SHARED=0,1
  done
  for g in 1 2 4 8; do
    run $g $ds 128 lutg$g JHQ_TR_ALPHAS=100 JHQ_TR_GROUPS=0,2 JHQ_TR_SHARED=1 JHQ_TR_KEEP=1
  done
done
python3 experiments/thesis_evidence/t4_lut_compare.py "$OUT" > "$OUT/lut_compare.md" 2>&1
cat "$OUT/lut_compare.md" >> "$L"
rm -f "$OUT"/*.topc
say "=== T4_DONE"
