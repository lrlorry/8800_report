#!/usr/bin/env python3
"""Recompute the 28 October evidence without modifying JHQ_GPU or using a GPU.

Original E1 and budget campaigns remain separate from the supplementary runs.
Outputs: a hashed ledger, bilingual numeric tables, and supplementary figures.
"""
import csv
import hashlib
import json
import math
import re
import statistics as st
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT.parent / "JHQ_GPU"
SRC = CODE / "experiments/thesis_evidence"
OUT = ROOT / "data/supplement"
FIG = ROOT / "figures/supplement"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)
DS = ["vogue-768", "arxiv-768", "openai3-1536", "openai3-3072", "bge-m3", "stella"]
NAMES = dict(zip(DS, ["Vogue", "arXiv", "OpenAI-1536", "OpenAI-3072", "BGE", "Stella"]))
ledger = []


def read(path):
    p = Path(path)
    data = p.read_bytes()
    ledger.append(dict(repository="JHQ_GPU", path=str(p.relative_to(CODE)),
                       sha256=hashlib.sha256(data).hexdigest()))
    return data.decode()


def table(name, headers, rows, spec=None):
    for zh, header in zip((False, True), headers):
        dest = ROOT / ("zh/tables/supplement" if zh else "tables/supplement")
        dest.mkdir(parents=True, exist_ok=True)
        text = [r"\begin{tabular}{@{}" + (spec or "l" + "r" * (len(header)-1)) + "@{}}",
                r"\toprule", " & ".join(header) + r" \\", r"\midrule"]
        text += [" & ".join(map(str, row)) + r" \\" for row in rows]
        text += [r"\bottomrule", r"\end{tabular}"]
        (dest / (name + ".tex")).write_text("\n".join(text) + "\n")


def frontier(points):
    result, best = [], -1
    for recall, qps in sorted(points, key=lambda p: (-p[0], -p[1])):
        if qps > best:
            result.append((recall, qps))
            best = qps
    return sorted(result)


def interp(points, target):
    near = [q for r, q in points if abs(r-target) <= 5e-4]
    if near:
        return max(near)
    for (r0, q0), (r1, q1) in zip(points, points[1:]):
        if r0 <= target <= r1 and r1 > r0:
            return math.exp(math.log(q0)+(target-r0)/(r1-r0)*math.log(q1/q0))
    raise ValueError((points, target))


# A1: rebuild from timestamped stdout and 20-ms device samples.
builds, build_summary = {}, {}
for ds in DS:
    runs = {}
    for mode in ["disk", "warm1", "warm2", "warm3", "phases"]:
        tag = f"{ds}_{mode}"
        start = float(read(SRC / f"RAW_A1/{tag}.t0"))
        text = read(SRC / f"RAW_A1/{tag}.txt")
        train = float(re.search(r"(?m)^\S+ train ([\d.]+) ms", text)[1])
        m = re.search(r"(?m)^(\S+) add ([\d.]+) ms", text)
        end, add = map(float, m.groups())
        matches = re.findall(r"(?m)^\S+\s+0\s+([\d.]+)\s+[\d.]+ ms\s+[\d.]+ ms\s+(\d+)", text)
        assert len(matches) == 1
        samples = []
        for line in read(SRC / f"RAW_A1/{tag}.smi").splitlines():
            stamp, mib = line.split(", ")
            ts = datetime.strptime(stamp, "%Y/%m/%d %H:%M:%S.%f").replace(
                tzinfo=timezone(timedelta(hours=8))).timestamp()
            if ts <= end + .02:
                samples.append((ts, int(mib)))
        runs[mode] = dict(train_ms=train, add_ms=add, to_searchable_s=end-start,
                          recall=float(matches[0][0]), build_peak_mib=max(v for _, v in samples))
    builds[ds] = runs
    w = [runs[f"warm{i}"] for i in (1, 2, 3)]
    totals = [(r["train_ms"]+r["add_ms"])/1000 for r in w]
    rec = [r["recall"] for r in runs.values()]
    build_summary[ds] = dict(train_add_s=totals, train_add_median_s=st.median(totals),
                             warm_start_s=[r["to_searchable_s"] for r in w],
                             first_read_start_s=runs["disk"]["to_searchable_s"],
                             peak_gib=max(r["build_peak_mib"] for r in w)/1024,
                             recall_range=[min(rec), max(rec)])
assert max(v["recall_range"][1]-v["recall_range"][0] for v in build_summary.values()) < .00120001
rows = []
for ds, s in build_summary.items():
    lo, hi = min(s['train_add_s']), max(s['train_add_s'])
    rows.append([NAMES[ds], f"{lo:.3f}--{hi:.3f}",
                 f"{min(s['warm_start_s']):.1f}--{max(s['warm_start_s']):.1f}",
                 f"{s['first_read_start_s']:.1f}", f"{s['peak_gib']:.2f}",
                 f"{s['recall_range'][0]:.4f}--{s['recall_range'][1]:.4f}"])
table("build", [["Dataset", "Train+add (s)", "Start (s)", "First read (s)", "Peak (GiB)", "Recall range"],
                ["数据集", "训练+add (s)", "启动 (s)", "首次读取 (s)", "峰值 (GiB)", "召回范围"]], rows)

# C1: stored-matrix geometry, all-row structural checks, sampled recoding.
representation = {ds: json.loads(read(SRC / f"RAW_C1/ra_{ds}.json"))
                  for ds in [DS[0], DS[1], DS[3], DS[5]]}
rows = []
for ds, v in representation.items():
    assert v["placement_ok"] and v["bad_offsets"] == v["dup_or_range"] == 0
    if "compare" in v:
        assert v["compare"]["primary_differs"] == v["compare"]["residual_differs"] == 0
    rows.append([NAMES[ds], f"{v['sample_rows']:,}", f"{v['orth_max']:.2e}",
                 f"{v['primary_mismatch']:,}", f"{v['residual_mismatch']:,}",
                 f"{v['residual_mismatch_max_margin']:.2e}"])
table("representation", [["Dataset", "Rows", "Orth. error", "Primary flips", "Residual flips", "Max margin"],
                          ["数据集", "重编码行数", "正交误差", "主码差异", "残差差异", "最大边界距离"]], rows)

# B: use individual raw traces, not the author's summary.
budget, prediction_rows, tc = {}, [], {}
for np in (128, 512):
    for ds in DS:
        tr = [json.loads(l) for l in read(SRC / f"RAW_B/trace_{ds}_np{np}.jsonl").splitlines()]
        meta = next(t for t in tr if t["type"] == "meta")
        full = next(t for t in tr if t["type"] == "full")
        draws = [t for t in tr if t["type"] == "draw"]
        assert len(draws) == 192 and full["pick"] == full["enum_pick"]
        grid = meta["grid"]
        # Check the invariance actually accessible in these traces: whole-curve
        # subset sums. This does not assert per-query invariance on all subsets.
        mismatch = 0
        for t in draws:
            assert len(t["sample"]) == t["S"] == len(set(t["sample"]))
            assert all(q % 2 == 0 for q in t["sample"])
            assert t["pick"] == t["enum_pick"]
            assert all(a <= b for a, b in zip(t["D"], t["D"][1:]))
            expected = [0] + [sum(full["Xq"][str(a)][q//2] for q in t["sample"])
                              for a in grid[1:]]
            mismatch += expected != t["D"]
            # The curve reproduces the independently recorded decision/loss.
            accepted = [i for i, d in enumerate(t["D"]) if d <= 1]
            assert grid[max(accepted)] == t["pick"]
            assert abs(t["loss"]-(meta["ceiling"]-meta["recall"][grid.index(t["pick"])])) < 1.1e-6
        assert mismatch == 0
        assert all(sum(full["Xq"][str(a)]) == full["D"][j] for j, a in enumerate(grid) if j)
        assert all(all(a <= b for a, b in zip(xs, xs[1:])) for xs in
                   zip(*[full["Xq"][str(a)] for a in grid[1:]]))
        full_loss = meta["ceiling"]-meta["recall"][grid.index(full["pick"])]
        assert full_loss <= .001+1e-12
        result = dict(full_pick=full["pick"], full_D=full["D"], full_enum_agrees=True,
                      full_heldout_loss=full_loss,
                      draws=len(draws), nonmonotone=0, subset_sum_mismatches=mismatch,
                      max_loss={str(s): max(t["loss"] for t in draws if t["S"] == s)
                                for s in (32, 64, 128)}, predictions={})
        for s in (32, 64, 128):
            acc = [1.0]
            for a in grid[1:]:
                x = full["Xq"][str(a)]
                n0, n1 = x.count(0), x.count(1)
                acc.append((math.comb(n0, s)+n1*math.comb(n0, s-1))/math.comb(meta["nc"], s))
            assert all(a+1e-12 >= b for a, b in zip(acc, acc[1:]))
            pick_prob = [a-b for a, b in zip(acc, acc[1:]+[0.0])]
            # Acceptance uses no GT. The loss map used to predict GT crossings does.
            pred = sum(p for p, r in zip(pick_prob, meta["recall"])
                       if meta["ceiling"]-r > .001+1e-12)
            obs = sum(t["loss"] > .001 for t in draws if t["S"] == s)/64
            result["predictions"][str(s)] = dict(predicted=pred, observed=obs)
            prediction_rows.append(dict(dataset=ds, nprobe=np, S=s, predicted=pred, observed=obs))
        key = f"{ds}/{np}"
        budget[key] = result
        streams = [t for t in tr if t["type"] == "tc"]
        if streams:
            policies = {}
            for pol in ("fixed64", "fixed100", "rule", "full"):
                runs = [t for t in streams if t["policy"] == pol]
                assert len(runs) == 5 and all(len(t["batch_ms"]) == 500 for t in runs)
                cumulative = [[t["cal_ms"]+sum(t["batch_ms"][:b]) for b in range(1,501)] for t in runs]
                policies[pol] = dict(alpha=[t["alpha"] for t in runs],
                    cal_ms=st.mean(t["cal_ms"] for t in runs),
                    first_ms=st.mean(t["batch_ms"][0] for t in runs),
                    steady_ms=st.mean(st.mean(t["batch_ms"][1:]) for t in runs),
                    recall=st.mean(t["recall"] for t in runs),
                    cumulative_ms=[st.mean(r[b] for r in cumulative) for b in range(500)])
            for pol in ("rule", "full"):
                p = policies[pol]
                p["break_even"] = {}
                for fixed in ("fixed100", "fixed64"):
                    f = policies[fixed]
                    delta = f["steady_ms"]-p["steady_ms"]
                    p["break_even"][fixed] = dict(
                        steady_fit_batches=p["cal_ms"]/delta if delta > 0 else None,
                        first_positive_mean_total=next((i+1 for i, (a,b) in enumerate(
                            zip(p["cumulative_ms"],f["cumulative_ms"])) if a < b), None),
                        saving_at_500=1-p["cumulative_ms"][-1]/f["cumulative_ms"][-1])
            tc[key] = policies
rows = [[NAMES[k.split('/')[0]], k.split('/')[1], v['full_pick']]+[
        f"{v['max_loss'][str(s)]:.4f}" for s in (32,64,128)] for k,v in budget.items()]
table("budget_tails", [["Dataset", "Probes", r"FULL $\alpha$", r"Max $L_{32}$", r"Max $L_{64}$", r"Max $L_{128}$"],
                       ["数据集", "探测数", r"全池 $\alpha$", r"最大 $L_{32}$", r"最大 $L_{64}$", r"最大 $L_{128}$"]], rows)
rows = [[NAMES[k.split('/')[0]]+"/"+k.split('/')[1]]+[
        f"{p[pol]['cumulative_ms'][-1]:.0f}" for pol in ('fixed100','fixed64','rule','full')]
        for k,p in tc.items()]
table("stream", [["Dataset/probes", "Fixed 100", "Fixed 64", r"Rule $S=128$", "FULL"],
                  ["数据集/探测数", "固定 100", "固定 64", r"规则 $S=128$", "全池"]], rows)

# Separately timed scheduling startup and alternating small-alpha repetitions.
schedule, retiming, cell = {}, {}, None
for line in read(SRC/'RAW_B/budget_trace.log').splitlines():
    m = re.match(r'### (\S+) .* np=(\d+)', line)
    if m:
        cell = f'{m[1]}/{m[2]}'
    m = re.match(r'SCHED_CAL gather_ms=([\d.]+) first_ms=([\d.]+) rep_med_ms=([\d.]+)', line)
    if m:
        schedule[cell] = dict(zip(('gather_ms','first_ms','repeat_median_ms'),map(float,m.groups())))
    m = re.match(r'ALT r=\d+ alpha=(\d+) recall=[\d.]+ qps=(\d+)', line)
    if m:
        retiming.setdefault(cell,{}).setdefault(m[1],[]).append(int(m[2]))
assert len(schedule) == 12
assert all(len(v) == 10 for arms in retiming.values() for v in arms.values())
retiming = {cell:{a:dict(rounds=len(q),mean_qps=st.mean(q),min_qps=min(q),max_qps=max(q))
                  for a,q in arms.items()} for cell,arms in retiming.items()}

# D: equal-configuration ratios from JSON round medians; historical baselines
# stay visibly separate. Recall in text has one fewer digit than the JSON.
e1 = {}
for row in csv.DictReader(read(CODE / "experiments/comp8800_poster_e1/E1_points.csv").splitlines()):
    try:
        e1.setdefault((row['dataset'],row['family']),[]).append((float(row['recall']),float(row['qps_A'])))
    except ValueError:
        pass
precision, curves = {}, {}
for ds in DS[2:4]:
    points = {}
    for version in ('v69','v72'):
        pts = {}
        for path in sorted((SRC/'RAW_D').glob(f"jhq_{version}_{ds}_np*.json")):
            d = json.loads(read(path))
            for run in d['runs']:
                assert run['batch'] == 1000 and d['rounds'] == 5
                v = next(v for v in run['variants'] if v['G'] == -1)
                pts[(d['nprobe'],run['alpha'])] = (v['recall'], st.median(v['qps']))
        points[version] = pts
    assert points['v69'].keys() == points['v72'].keys()
    qr = [points['v72'][k][1]/v[1] for k,v in points['v69'].items()]
    dr = [points['v72'][k][0]-v[0] for k,v in points['v69'].items()]
    f = {v: frontier(list(p.values())) for v,p in points.items()}
    rb = frontier(e1[ds,'IVF-RaBitQ']); cg = frontier(e1[ds,'CAGRA fp32'])
    curves[ds] = dict(**f, rabitq=rb, cagra=cg)
    precision[ds] = dict(configurations=len(qr), geo_ratio=st.geometric_mean(qr),
        ratio_range=[min(qr),max(qr)], recall_gain=[min(dr),max(dr)],
        at_097={v:interp(f[v],.97) for v in f},
        fp32_over_rabitq=interp(f['v72'],.97)/interp(rb,.97),
        fp32_over_cagra=interp(f['v72'],.97)/interp(cg,.97))
rows = [[NAMES[ds],v['configurations'],f"{v['geo_ratio']:.3f}",
         f"{v['recall_gain'][0]:+.4f}--{v['recall_gain'][1]:+.4f}",
         f"{v['fp32_over_rabitq']:.3f}",f"{v['fp32_over_cagra']:.3f}"] for ds,v in precision.items()]
table("precision", [["Dataset", "Pairs", "QPS ratio", r"$\Delta$Recall", "vs RaBitQ", "vs CAGRA"],
                     ["数据集", "配对数", "QPS 比值", r"$\Delta$Recall", "对 RaBitQ", "对 CAGRA"]], rows)

# Hash source, run manifests and machine-code evidence as well as measurements.
for pattern in ('*.sh','*.py','REPORT_CN.md','RAW_A2/*','RAW_A3/*'):
    for path in sorted(SRC.glob(pattern)):
        if path.is_file():
            read(path)
for rel in ('examples/demo_jhq_v69_budget_trace.cu','examples/demo_jhq_v66_repr_audit.cu',
            'jhq_v69_probesel/jhq_gpu_index.cu','jhq_v72_fp32gemm/jhq_gpu_index.cu'):
    read(CODE/rel)
for p in SRC.glob('RAW_B/*.log'):
    read(p)
for folder in ('RAW_A1','RAW_C1','RAW_D'):
    for p in (SRC/folder).glob('*.log'):
        read(p)
toolchain = (SRC/'RAW_A2/toolchain.txt').read_text()
assert '5371616ed99ab2b2dd323688eb3cf7a23dafb9f3f6a3904cf44475f65cf63ceb' in toolchain
assert 'ld.volatile.global.u64' in (SRC/'RAW_A2/ptx_bound_ops.txt').read_text()
assert 'LDG.E.64.STRONG.SYS' in (SRC/'RAW_A2/sass_bound_ops.txt').read_text()
assert 'REDG.E.MIN.64.STRONG.GPU' in (SRC/'RAW_A2/sass_bound_ops.txt').read_text()

local_ledger = dict(repository=ROOT.name,path='scripts/audit_supplement.py',
                    sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
result = dict(date='2026-10-28', builds=build_summary, representation=representation,
              budget=budget, precision=precision, streams=tc,
              schedule_calibration=schedule, alternating_retiming=retiming,
              checks=dict(sampled_curves=2304, sampled_nonmonotone=0, full_enum_agree=12,
                          full_subset_curve_mismatches=0, compared_grid_counts=18432),
              limitations=['Sampled peaks may miss sub-20-ms allocations.',
                'A2 SASS is toolkit sm_120 reassembly of extracted PTX, not driver JIT capture.',
                'A3 checks all query vectors and 10299 strided base rows, not original entity IDs.',
                'D reuses a TF32-trained cache; it compares add/query precision, not full retraining.',
                'Finite-pool risk uses fixed held-out GT arm losses after label-free acceptance.',
                'Subset sums reproduce all traced curves; arbitrary per-query invariance is unproved.',
                'Steady-rate break-even fits differ from directly observed cumulative crossings.',
                'C2 CPU top-c and C3 Vogue cross-process diagnosis remain pending.'],
              inputs=sorted({v['path']:v for v in ledger}.values(),key=lambda v:v['path'])+[local_ledger])
(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
with (OUT/'risk-prediction.csv').open('w') as f:
    w=csv.DictWriter(f,fieldnames=prediction_rows[0].keys());w.writeheader();w.writerows(prediction_rows)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,
                     'pdf.fonttype':42,'figure.constrained_layout.use':True})
fig, axes=plt.subplots(1,2,figsize=(9,3.1))
for ax,ds in zip(axes,DS[2:4]):
    for key,label,color,style in [('v69','v69: TF32 GEMMs','#2166ac','-'),
        ('v72','v72: FP32 GEMMs','#b2182b','-'),('rabitq','E1 IVF-RaBitQ','#555555','--'),
        ('cagra','E1 CAGRA fp32','#999999',':')]:
        f=curves[ds][key];ax.plot([r for r,q in f],[q/1000 for r,q in f],style,label=label,color=color)
    ax.set(xlim=(.945,.985),xlabel='Recall@10',ylabel='Throughput (kQPS)',title=NAMES[ds])
    ax.set_ylim(bottom=0,top=240 if ds==DS[2] else 110);ax.grid(alpha=.2)
axes[0].legend(fontsize=7)
fig.savefig(FIG/'precision.pdf');plt.close(fig)
fig, axes=plt.subplots(1,2,figsize=(9,2.8))
for ax,np in zip(axes,(128,512)):
    v=budget[f'arxiv-768/{np}']['predictions'];xs=[32,64,128]
    ax.plot(xs,[v[str(s)]['predicted'] for s in xs],'-o',label='Finite-pool prediction')
    obs=[v[str(s)]['observed'] for s in xs]
    ax.errorbar(xs,obs,yerr=[math.sqrt(p*(1-p)/64) for p in obs],fmt='s--',label='64 draws (±1 s.e.)')
    ax.set(ylim=(0,1.05),xticks=xs,xlabel='Calibration sample size S',ylabel='Loss crossing frequency',title=f'arXiv, {np} probes')
    ax.grid(alpha=.2)
axes[0].legend(fontsize=7);fig.savefig(FIG/'finite-pool.pdf');plt.close(fig)
fig,axes=plt.subplots(2,2,figsize=(9,5.3))
for ax,(key,policies) in zip(axes.flat,tc.items()):
    for pol,label,style in [('fixed100','Fixed 100','--'),('fixed64','Fixed 64',':'),
                            ('rule','Rule S=128','-'),('full','FULL','-.')]:
        ax.plot(range(1,501),policies[pol]['cumulative_ms'],style,label=label)
    ds,np=key.split('/');ax.set(title=f'{NAMES[ds]}, {np} probes',xlabel='Reuse batches',ylabel='Total time (ms)');ax.grid(alpha=.2)
axes.flat[0].legend(fontsize=7);fig.savefig(FIG/'stream-cost.pdf');plt.close(fig)
print(f"Supplement: {len(result['inputs'])} hashed inputs; 2304 monotone curves, 12 FULL matches, 18432 subset sums agree.")
