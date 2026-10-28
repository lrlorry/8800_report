#!/usr/bin/env python3
"""Audit retained T4/T5 records and generate bilingual tables; never runs CUDA.

T4 candidate dumps were deleted by the campaign. This rechecks retained
JSONL tallies against stdout and audits scorer correspondence in source;
it cannot independently repeat the deleted per-candidate comparisons.
T5 uses numeric JSON records, rather than rounded console QPS.
"""
import argparse
import csv
import hashlib
import json
import math
import re
import statistics as st
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT.parent / 'JHQ_GPU'
if not CODE.exists():
    CODE = ROOT / 'evidence/review/JHQ_GPU'
SRC = CODE / 'experiments/thesis_evidence'
OUT = ROOT / 'data/t4-t5'
DATASETS = ['vogue-768', 'arxiv-768', 'openai3-1536', 'openai3-3072']
NAMES = dict(zip(DATASETS, ['Vogue', 'arXiv', 'OpenAI-1536', 'OpenAI-3072']))
BASELINES = ['CAGRA fp32', 'CAGRA int8', 'IVF-RaBitQ']
ledger = {}


def read(path):
    p = Path(path)
    b = p.read_bytes()
    base = CODE if p.is_relative_to(CODE) else ROOT
    rel = str(p.relative_to(base))
    ledger[base.name, rel] = dict(repository=base.name, path=rel,
                                sha256=hashlib.sha256(b).hexdigest())
    return b.decode()


def erase_block(s, marker):
    start = s.index(marker)
    end = s.index('{', start) + 1
    depth = 1
    while depth:
        depth += (s[end] == '{') - (s[end] == '}')
        end += 1
    return s[:start] + s[end:]


def source_check():
    checked = []
    for p in sorted((CODE / 'jhq_v71_lutgroups').glob('*')):
        if p.suffix not in ['.cu', '.cuh']:
            continue
        a = read(p).replace('jhq_v71_lutgroups', 'JHQ_VERSION')
        b = read(CODE / 'jhq_v73_topcref' / p.name).replace('jhq_v73_topcref', 'JHQ_VERSION')
        if p.name == 'search.cu':
            for marker in ['__global__ void dump_primary_distances_kernel',
                           'if (const char* dp = std::getenv("JHQ_DUMP_TOPCK"))']:
                a, b = erase_block(a, marker), erase_block(b, marker)
        norm = lambda s: re.sub(r'\s+', '', re.sub(r'/\*[\s\S]*?\*/|//[^\n]*', '', s))
        assert norm(a) == norm(b), p.name
        checked.append(p.name)
    return checked


def table(name, headers, rows, spec):
    for lang, header in zip(['tables', 'zh/tables'], headers):
        dest = ROOT / lang / 't4-t5'
        dest.mkdir(parents=True, exist_ok=True)
        lines = [r'\begin{tabular}{@{}' + spec + '@{}}', r'\toprule',
                 ' & '.join(header) + r' \\', r'\midrule']
        lines += [' & '.join(map(str, row)) + r' \\' for row in rows]
        lines += [r'\bottomrule', r'\end{tabular}']
        (dest / (name + '.tex')).write_text('\n'.join(lines) + '\n')


def pareto(points):
    best, result = -1, []
    for p in sorted(points, key=lambda p: (-p['recall'], -p['qps'])):
        if p['qps'] > best:
            result.append(p)
            best = p['qps']
    return sorted(result, key=lambda p: p['recall'])


def measured(points, target):
    return max((p['qps'] for p in points if p['recall'] >= target), default=None)


def interpolated(points, target, qualifying_endpoint=False):
    f = pareto(points)
    near = [p['qps'] for p in f if abs(p['recall'] - target) <= 5e-4]
    if near:
        return max(near)
    for a, b in zip(f, f[1:]):
        if a['recall'] <= target <= b['recall'] and a['recall'] < b['recall']:
            w = (target-a['recall'])/(b['recall']-a['recall'])
            return math.exp((1-w)*math.log(a['qps'])+w*math.log(b['qps']))
    # A more accurate measured configuration still satisfies a lower target.
    # This is a measured endpoint, not an extrapolated segment.
    if qualifying_endpoint and f and target < f[0]['recall']:
        return measured(f, target)
    return None


def main():
    global CODE, SRC
    args = argparse.ArgumentParser()
    args.add_argument('--no-plot', action='store_true')
    args.add_argument('--source', type=Path, default=CODE)
    opt = args.parse_args()
    CODE = opt.source.resolve()
    SRC = CODE / 'experiments/thesis_evidence'
    OUT.mkdir(parents=True, exist_ok=True)
    correspondence = source_check()
    for name in ['REPORT_CN.md', 't4_topcref.sh', 't4_lut_compare.py',
                 't5_smallbatch.sh', 'analyze_t5.py', 'bench_cuvs_smallbatch.py',
                 'bench_rabitq_smallbatch.cu', 'T5_SUMMARY.md']:
        read(SRC / name)
    for name in ['CMakeLists.txt', 'examples/demo_jhq_topc_reference.cu',
                 'examples/demo_jhq_batch_pipeline.cu']:
        read(CODE / name)
    for name in ['RAW_T4/PROGRESS.log', 'RAW_T5/PROGRESS.log']:
        read(SRC / name)

    strict = []
    for p in sorted((SRC / 'RAW_T4').glob('*_strict.jsonl')):
        ds = p.name.removesuffix('_strict.jsonl')
        rows = [json.loads(x) for x in read(p).splitlines()]
        assert len(rows) == 90
        for np in [1, 8, 128]:
            stdout = read(SRC / 'RAW_T4' / f'{ds}_strict_np{np}.txt')
            logs = [dict(re.findall(r'(\w+)=([^\s]+)', s)) for s in stdout.splitlines() if s.startswith('TR ')]
            assert len(logs) == 30 and 'TR_OK' in stdout
            for r in [x for x in rows if x['nprobe'] == np]:
                z = next(x for x in logs if float(x['a']) == r['alpha'] and int(x['G']) == r['G'] and int(x['sh']) == r['shared'])
                for key, logkey in [('queries','q'), ('score_mismatch','score_mm'),
                                   ('set_equal','set_eq'), ('order_equal','order_eq'),
                                   ('preorder_ok','preorder'), ('tie_only','tie_only'),
                                   ('nontie','nontie'), ('pad_ok','pad_ok'),
                                   ('underfull','underfull'), ('cutoff_ties','cutoff_ties')]:
                    assert r[key] == int(z[logkey]), (p, key)
                assert [r['final_ok'], r['final_checked']] == list(map(int, z['final_ok'].split('/')))
                assert r['score_mismatch'] == r['nontie'] == 0
                assert r['pad_ok'] == r['preorder_ok'] == r['final_ok'] == r['final_checked'] == r['queries']
                strict.append(dict(dataset=ds, **r))
    assert len(strict) == 270
    counts = {}
    for group, pred in [('complete_key', lambda r: r['G'] >= 1), ('distance_only', lambda r: r['G'] == 0)]:
        part = [r for r in strict if pred(r)]
        counts[group] = {k: sum(r[k] for r in part) for k in ['queries','score_mismatch','set_equal','order_equal','preorder_ok','tie_only','nontie','pad_ok','underfull','cutoff_ties','final_ok','final_checked']}
    assert counts['complete_key']['queries'] == counts['complete_key']['order_equal'] == 55296
    assert counts['distance_only']['queries'] == 13824 and counts['distance_only']['tie_only'] == 56
    assert sum(r['underfull'] for r in strict) == 19120
    (OUT / 'strict-selection.json').write_text(json.dumps(strict, indent=2) + '\n')
    lut = json.loads(read(SRC / 'RAW_T4/lut_compare.json'))
    read(SRC / 'RAW_T4/lut_compare.md')
    assert len(lut) == 18
    for r in lut.values():
        assert r['queries'] == 256
    (OUT / 'lut-comparison.json').write_text(json.dumps(lut, indent=2) + '\n')
    full = [v for k,v in lut.items() if k.endswith('/g1')]
    other = list(lut.values())
    lut_summary = dict(full_split_fraction_range=[min(v['scores_differing']/v['candidates'] for v in full), max(v['scores_differing']/v['candidates'] for v in full)],
                       full_split_max_abs=max(v['max_abs'] for v in full), full_split_max_rel=max(v['max_rel'] for v in full),
                       all_fraction_range=[min(v['scores_differing']/v['candidates'] for v in other), max(v['scores_differing']/v['candidates'] for v in other)],
                       all_max_abs=max(v['max_abs'] for v in other), all_max_rel=max(v['max_rel'] for v in other))

    points = []
    nulls = {}
    for ds in DATASETS:
        for p in sorted((SRC / 'RAW_T5').glob(f'jhq_{ds}_np*.json')):
            d = json.loads(read(p))
            for run in d['runs']:
                assert run['nused'] == (1000//run['batch'])*run['batch']
                for v in run['variants']:
                    assert len(v['qps']) == 5 and v['G'] in [0,-1]
                    points.append(dict(dataset=ds, batch=run['batch'], method='JHQ scheduled' if v['G'] == -1 else 'JHQ one block',
                                       recall=v['recall'], qps=st.median(v['qps']),
                                       nused=run['nused'], nprobe=d['nprobe'], alpha=run['alpha'],
                                       scheduled_groups=run['sched_G'], source=p.name))
        for method, filename in [('CAGRA fp32', f'cuvs_{ds}_cagra.jsonl'),
                                 ('CAGRA int8', f'cuvs_{ds}_cagra-int8.jsonl'),
                                 ('IVF-RaBitQ', f'rabitq_{ds}.jsonl')]:
            for line in read(SRC / 'RAW_T5' / filename).splitlines():
                r = json.loads(line)
                if r.get('type') != 'point':
                    continue
                assert r['invalid_ids'] == r['dup_rows'] == 0
                assert r['nused'] == (1000//r['batch'])*r['batch']
                assert r['rounds'] == 5 and len(r['A']['qps_rounds']) == 5
                assert abs(st.median(r['A']['qps_rounds']) - r['A']['qps_median']) < .11
                points.append(dict(dataset=ds, batch=r['batch'], method=method, recall=r['recall'], qps=r['A']['qps_median'],
                                   nused=r['nused'], nprobe=r['search'].get('n_probes', ''), alpha='', scheduled_groups='', source=filename))
                nulls.setdefault((ds, r['batch'], method), []).append(st.median(r['null']['lat_med_ms_rounds']))
    matched = []
    for ds in DATASETS:
        for batch in [8,32]:
            by = {m:[p for p in points if p['dataset']==ds and p['batch']==batch and p['method']==m]
                  for m in ['JHQ scheduled','JHQ one block'] + BASELINES}
            assert len(by['CAGRA fp32']) == len(by['CAGRA int8']) == 64 and len(by['IVF-RaBitQ']) == 32
            for target in [.90,.92,.94,.95,.96,.97,.98]:
                i = {m:interpolated(v,target,True) for m,v in by.items()}
                legacy = {m:interpolated(v,target,False) for m,v in by.items()}
                measured_qps = {m:measured(v,target) for m,v in by.items()}
                bi = max(BASELINES,key=lambda m:i[m] or -1)
                bm = max(BASELINES,key=lambda m:measured_qps[m] or -1)
                old = max((legacy[m] for m in BASELINES if legacy[m] is not None), default=None)
                matched.append(dict(dataset=ds,batch=batch,target=target, interpolated_qps=i,measured_qps=measured_qps,
                                    best_interpolated_baseline=bi,best_measured_baseline=bm,
                                    ratio_interp=i['JHQ scheduled']/i[bi],
                                    ratio_measured=measured_qps['JHQ scheduled']/measured_qps[bm],
                                    ratio_old_missing_endpoint=legacy['JHQ scheduled']/old,
                                    scheduler_ratio_interp=i['JHQ scheduled']/i['JHQ one block']))
    with (OUT/'smallbatch-points.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(points[0]),lineterminator='\n');writer.writeheader();writer.writerows(points)
    (OUT/'smallbatch-matched.json').write_text(json.dumps(matched,indent=2)+'\n')
    table('strict-selection', [['Path','Queries','Set / order exact','Tie-only','Valid count','Final exact'],
                               ['路径','查询数','集合／顺序精确','纯并列差异','有效数量正确','末端精确']],
          [[r'$\gscan\geq1$', '55,296','55,296 / 55,296',0,'55,296','55,296'],
           [r'$\gscan=0$','13,824','13,768 / 8,758',56,'13,824','13,824']], 'lrrrrr')
    table('smallbatch', [['Dataset','$b$','$R=0.90$','$R=0.95$','$R=0.97$'],
                         ['数据集','$b$','$R=0.90$','$R=0.95$','$R=0.97$']],
          [[NAMES[ds],b]+[f"{r['ratio_interp']:.3f} / {r['ratio_measured']:.3f}" for t in [.90,.95,.97]
                           for r in matched if r['dataset']==ds and r['batch']==b and r['target']==t]
           for ds in DATASETS for b in [8,32]], 'lrrrr')
    ranges=[]
    for b in [8,32]:
        for t in [.90,.95,.97]:
            rr=[r for r in matched if r['batch']==b and r['target']==t]
            ranges.append(dict(batch=b,target=t,interp_range=[min(r['ratio_interp'] for r in rr),max(r['ratio_interp'] for r in rr)],
                               measured_range=[min(r['ratio_measured'] for r in rr),max(r['ratio_measured'] for r in rr)],
                               interp_wins=sum(r['ratio_interp']>1 for r in rr),measured_wins=sum(r['ratio_measured']>1 for r in rr)))
    if not opt.no_plot:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.rcParams.update({'font.size':9,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
        fig,axes=plt.subplots(1,2,figsize=(7,2.65),sharey=True)
        for ax,b in zip(axes,[8,32]):
            for ds in DATASETS:
                r=[r for r in matched if r['batch']==b and r['dataset']==ds]
                ax.plot([x['target'] for x in r],[x['ratio_interp'] for x in r],marker='o',ms=3,label=NAMES[ds])
            ax.axhline(1,color='black',lw=.7,ls='--');ax.set_title(f'Batch {b}');ax.set_xlabel('Recall@10 target')
            ax.grid(alpha=.2);ax.set_xticks([.90,.94,.98]);ax.set_ylim(.4,1.65)
        axes[0].set_ylabel('JHQ / fastest tested competitor')
        axes[1].legend(fontsize=7,loc='lower left',ncol=2)
        fig.tight_layout();dest=ROOT/'figures/t4-t5';dest.mkdir(parents=True,exist_ok=True)
        fig.savefig(dest/'smallbatch.pdf',metadata={'CreationDate':None,'ModDate':None});plt.close(fig)
    for name in ['chapters/04-6-contracts.tex', 'chapters/05-2-lut.tex',
                 'chapters/05-4-global-selection.tex', 'chapters/07-evaluation.tex',
                 'chapters/07-supp-selection.tex', 'chapters/07-supp-smallbatch.tex',
                 'chapters/08-3-validity.tex', 'chapters/08-5-deployment.tex',
                 'chapters/09-conclusion.tex', 'appendices/b-supplementary.tex']:
        read(ROOT / name)
        read(ROOT / 'zh' / name)
    for name in ['appendices/a-reproducibility.tex', 'frontmatter/abstract.tex',
                 'zh/abstract.tex', 'assessment/t4-t5-integration.txt']:
        read(ROOT / name)
    read(Path(__file__))
    audit=dict(scope='Offline audit of retained T4/T5 records; no GPU experiment; temporary candidate dumps no longer retained.',
               t4=dict(configurations=270,query_instances=69120,path_counts=counts,source_correspondence=correspondence,
                       lut=lut_summary,score_equality_scope='Bitwise comparison of exported versus selector-returned valid primary entries; source arithmetic matches all-candidate export.',
                       padding_scope='Correct valid-entry count, not a bytewise check of each unused sentinel.',
                       final_scope='CPU sort of retained computed refined scores under (score, ID); not original-space exact kNN.'),
               t5=dict(points=len(points),counts=[dict(dataset=d,batch=b,method=m,points=n) for (d,b,m),n in sorted(Counter((p['dataset'],p['batch'],p['method']) for p in points).items())],
                       ranges=ranges,null_median_ms=[dict(dataset=d,batch=b,method=m,latency=st.median(v)) for (d,b,m),v in sorted(nulls.items())],
                       estimation='Strict measured recall threshold; separately log-QPS interpolation with archived 5e-4 snapping and qualifying endpoint below minimum frontier recall.',
                       caveats=['Finite unequal grids; no IVF-PQ or brute-force baseline in T5.',
                                'CAGRA Python binding versus C++ JHQ/RaBitQ; measured null costs remain inside reported times.',
                                'Five within-build rounds; method-specific warm-up; no cross-device or concurrent-service measurements.']),
               inputs=list(ledger.values()))
    (OUT/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps(dict(t4=counts,lut=lut_summary,t5_points=len(points),ranges=ranges,inputs=len(ledger)),indent=2))


if __name__ == '__main__':
    main()
