#!/bin/bash
# ADC figures on v69, part 3: the paper's table-grouping ablation (RQ3, fig_lutgroups) on v71 = v69 with
# the table granularity as a compile-time choice. The original sweep's settings (scripts/run_lutgroups6.sh,
# v59): alpha 100, batch 1000, nprobe 8/32/128/512, six datasets, table groups 1/2/4/8. Measured with E1's
# harness and protocol (scheduled list groups, 16 refinement lanes, 5 rounds) on the trained indexes E1 and
# the budget run use (arms6_cache), so the three describe one index.
#   bash experiments/adc_v69/run_lutgroups_v71.sh      (from a worktree at the commit under test)
set -u
export PATH=/root/miniconda3/bin:/usr/local/cuda/bin:$PATH OMP_NUM_THREADS=16
REPO=$(cd "$(dirname "$0")/../.." && pwd); cd "$REPO" || exit 1
OUT=${OUT:-$REPO/experiments/adc_v69/RAW_LUT}; mkdir -p "$OUT"
P=$OUT/PROGRESS.log
say(){ echo "$(date -u +%FT%TZ) $*" | tee -a "$P"; }
say "=== head=$(git log --oneline -1)"
timeout 3600 cmake --build build -j 16 --target demo_jhq_v71_g1_batch demo_jhq_v71_g2_batch \
    demo_jhq_v71_g4_batch demo_jhq_v71_g8_batch > "$OUT/build.log" 2>&1
rc=$?; say "build rc=$rc"
[ $rc -ne 0 ] && { grep -m 20 error "$OUT/build.log" | tee -a "$P"; say "=== LUT_V71_DONE build failed"; exit 1; }
[ -z "${E1_LOCK_HELD:-}" ] && { exec 8>/root/.gpu_lock; flock 8; }
D=/root/autodl-tmp; V=/root/data
declare -A PA MM NL NT BLK
PA[vogue-768]="$V/vogue-768_base.fvecs $V/vogue-768_query.fvecs $V/vogue-768_groundtruth.ivecs"
PA[arxiv-768]="$D/arxiv-abstracts-768/base.fvecs $D/arxiv-abstracts-768/query.fvecs $D/arxiv-abstracts-768/groundtruth.ivecs"
PA[openai3-1536]="$D/openai3-1536/base.fvecs $D/openai3-1536/query.fvecs $D/openai3-1536/groundtruth.ivecs"
PA[openai3-3072]="$D/openai3-3072/base.fvecs $D/openai3-3072/query.fvecs $D/openai3-3072/groundtruth.ivecs"
PA[bge-m3]="$D/bge-m3/base.fvecs $D/bge-m3/query.fvecs $D/bge-m3/groundtruth.ivecs"
PA[stella]="$D/stella-trec24/base.fvecs $D/stella-trec24/query.fvecs $D/stella-trec24/groundtruth.ivecs"
MM[vogue-768]=96;  NL[vogue-768]=4096;  NT[vogue-768]=159744;  BLK[vogue-768]=512
MM[arxiv-768]=96;  NL[arxiv-768]=8192;  NT[arxiv-768]=319488;  BLK[arxiv-768]=512
MM[openai3-1536]=192; NL[openai3-1536]=8192; NT[openai3-1536]=319488; BLK[openai3-1536]=512
MM[openai3-3072]=384; NL[openai3-3072]=8192; NT[openai3-3072]=319488; BLK[openai3-3072]=1024
MM[bge-m3]=128; NL[bge-m3]=32768; NT[bge-m3]=1277952; BLK[bge-m3]=512
MM[stella]=128; NL[stella]=32768; NT[stella]=1277952; BLK[stella]=512
one(){  # dataset nprobe tablegroups rounds
  local ds=$1 np=$2 g=$3 rounds=$4 pre=$OUT/v71_g$3_$1_np$2
  [ "$rounds" = 0 ] && pre=${pre}_check
  env JHQ_INDEX_CACHE="$D/arms6_cache/$ds" JHQ_BLOCK=${BLK[$ds]} JHQ_TILE_M_RT=${MM[$ds]} \
      JHQ_N_TRAIN=${NT[$ds]} JHQ_GPU_CODEBOOK=1 JHQ_ENCODE_GROUPED_OFF=1 JHQ_Y_TRANSPOSED=1 \
      JHQ_RES_TRAIN_N=100000 JHQ_BP_LANES=16 JHQ_BP_ALPHAS=100 JHQ_BP_BATCHES=1000 \
      JHQ_BP_GROUPS=0,-1 JHQ_BP_ROUNDS=$rounds JHQ_BP_MIN_BATCHES=24 JHQ_BP_CHECK=1 \
      timeout 3600 build/demo_jhq_v71_g${g}_batch ${PA[$ds]} ${MM[$ds]} 8 8 100 10 ${NL[$ds]} $np 8 1024 "$pre" 3 \
      > "$pre.txt" 2>&1
  local rc=$?
  say "v71 table groups $g $ds np=$np rc=$rc $(grep -c BP_OK "$pre.txt") ok, recall $(python3 -c "import json;j=json.load(open('$pre.json'));print(' '.join('%.4f'%v['recall'] for r in j['runs'] for v in r['variants'] if v['G']==-1))" 2>/dev/null)"
}
# gate: every table split computes the same primary distances up to the order of a few float additions,
# so recall must agree across them to the tie-break floor (v59: identical, or 0.0001 apart at G = 8)
for g in 1 2 4 8; do one vogue-768 128 $g 0; done
spread=$(python3 -c "
import json
r=[json.load(open('$OUT/v71_g%d_vogue-768_np128_check.json'%g))['runs'][0]['variants'][1]['recall'] for g in (1,2,4,8)]
print('%.4f'%(max(r)-min(r)), ' '.join('%.4f'%x for x in r))")
say "gate: recall spread across table groups on vogue np128 = $spread"
ok=$(python3 -c "print(1 if float('${spread%% *}') <= 0.0005 else 0)")
[ "$ok" != 1 ] && { say "=== LUT_V71_DONE gate failed: recall differs across table groups, nothing timed"; exit 1; }
for np in 8 32 128 512; do
  for g in 1 2 4 8; do
    for ds in vogue-768 arxiv-768 openai3-1536 openai3-3072 bge-m3 stella; do one $ds $np $g 5; done
  done
done
say "=== LUT_V71_DONE"
