#!/usr/bin/env python3
"""Offline checks for the f010beb full review, applied to the newer thesis.

Recompute construction capacities and the already-completed T1 anchors;
inspect retained A2 instructions. No GPU or network operation is performed.
"""
import argparse
import hashlib
import json
import math
import re
import statistics as st
from collections import defaultdict
from pathlib import Path

from audit_t4_t5 import interpolated, measured

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser()
    default = ROOT.parent / 'JHQ_GPU'
    if not default.exists():
        default = ROOT / 'evidence/review/JHQ_GPU'
    ap.add_argument('--source', type=Path, default=default)
    args = ap.parse_args()
    code = args.source.resolve()
    src = code / 'experiments/thesis_evidence'
    inputs = {}

    def read(p):
        p = Path(p)
        b = p.read_bytes()
        repository, rel = ('JHQ_GPU', str(p.relative_to(code))) if p.is_relative_to(code) else (ROOT.name, str(p.relative_to(ROOT)))
        inputs[repository,rel] = dict(repository=repository,path=rel,sha256=hashlib.sha256(b).hexdigest())
        return b.decode()

    source = read(code/'jhq_v69_probesel/jhq_gpu_index.cu')
    header = read(code/'jhq_v69_probesel/jhq_gpu_index.cuh')
    assert re.search(r'add_batch\s*=\s*65536', header)
    assert 'stage_budget / (sizeof(float) * d_)' in source
    assert 'nlist_ * abatch * sizeof(float)' in source
    assert 'nlist_ >= 8192 ? 32768 : 8192' in source
    scratch = []
    for d,nlist in [(768,4096),(1024,32768),(1536,8192),(3072,8192)]:
        ain=max(1,min(65536,(128*2**20)//(4*d)))
        aa=32768 if nlist>=8192 else 8192
        scratch.append(dict(d=d,nlist=nlist,add_rows=65536,input_rows=ain,
                            assignment_rows=aa,buffers=3,stage_mib=128,
                            device_float_bytes=8*3*ain*d,
                            assignment_bytes=4*3*nlist*aa,
                            incorrect_substitution_bytes=4*3*nlist*ain))
    assert [r['input_rows'] for r in scratch]==[43690,32768,21845,10922]
    assert [r['assignment_bytes']/2**30 for r in scratch]==[.375,12,3,3]

    search=read(code/'jhq_v69_probesel/search.cu')
    assert 'cudaMalloc(&ws.d_qkey, (size_t)batch_cap * sizeof(unsigned long long))' in search
    assert '&qkey[bqi]' in search
    ptx=read(src/'RAW_A2/group_kernels.ptx')
    sass=read(src/'RAW_A2/group_kernels.sass')
    for name in ['toolchain.txt','contents.txt','ptx_bound_ops.txt','sass_bound_ops.txt']:
        read(src/'RAW_A2'/name)
    assert len(re.findall(r'ld\.volatile\.global\.u64[^\n]*\[%rd22\]',ptx))==2
    assert len(re.findall(r'atom\.global\.min\.u64[^\n]*\[%rd22\]',ptx))==2
    assert 'shl.b64 %rd96, %rd7, 3;' in ptx and 'add.s64 %rd22, %rd4, %rd96;' in ptx
    assert 'LDG.E.64.STRONG.SYS' in sass and 'REDG.E.MIN.64.STRONG.GPU' in sass

    launcher=read(src/'t1_tf32_session.sh')
    assert 'export RQ_POOL=2048 CUVS_POOL=1' in launcher
    read(src/'analyze_t1.py');read(src/'T1_SUMMARY.md');read(src/'RAW_T1/PROGRESS.log')
    anchors=[]
    for ds in ['openai3-1536','openai3-3072']:
        methods={};repeated={}
        for version in ['v69','v72']:
            parts=defaultdict(list)
            files=sorted((src/'RAW_T1').glob(f'jhq_{version}_{ds}_np*_r*.json'))
            assert len(files)==6
            for p in files:
                d=json.loads(read(p));assert d['rounds']==5 and d['nq']==1000
                for run in d['runs']:
                    assert run['batch']==1000
                    v=next(x for x in run['variants'] if x['G']==-1)
                    assert len(v['qps'])==5
                    parts[d['nprobe'],run['alpha']].append((v['recall'],st.median(v['qps'])))
            assert len(parts)==12 and all(len(v)==2 and v[0][0]==v[1][0] for v in parts.values())
            repeated[version]={k:dict(recall=v[0][0],qps=st.geometric_mean(x[1] for x in v)) for k,v in parts.items()}
            methods[version]=list(repeated[version].values())
        assert set(repeated['v69'])==set(repeated['v72'])
        for method,filename in [('rabitq',f'rabitq_{ds}.jsonl'),('cagra',f'cuvs_{ds}_cagra.jsonl')]:
            points=[]
            for line in read(src/'RAW_T1'/filename).splitlines():
                r=json.loads(line)
                if r.get('type')!='point':continue
                assert r['invalid_ids']==r['dup_rows']==0
                assert r.get('pool',False) if method=='cagra' else r['pool_mib']==2048
                points.append(dict(recall=r['recall'],qps=r['A']['qps_median']))
            assert points
            methods[method]=points
        qi={m:interpolated(v,.97) for m,v in methods.items()}
        qm={m:measured(v,.97) for m,v in methods.items()}
        assert all(qi.values()) and all(qm.values())
        anchors.append(dict(dataset=ds,paired_configurations=12,
                            paired_qps_ratio=st.geometric_mean(repeated['v72'][k]['qps']/repeated['v69'][k]['qps'] for k in repeated['v69']),
                            interpolated_qps=qi,measured_qps=qm,
                            fp32_tf32_at97=qi['v72']/qi['v69'],
                            fp32_rabitq_interp=qi['v72']/qi['rabitq'],fp32_rabitq_measured=qm['v72']/qm['rabitq'],
                            fp32_cagra_interp=qi['v72']/qi['cagra'],fp32_cagra_measured=qm['v72']/qm['cagra'],
                            rabitq_bracket=[max(p['recall'] for p in methods['rabitq'] if p['recall']<.97),min(p['recall'] for p in methods['rabitq'] if p['recall']>=.97)]))

    out=ROOT/'data/full-review';out.mkdir(parents=True,exist_ok=True)
    for prefix,headers in [('tables',[r'$d$',r'$n_{\rm list}$',r'$a_{\rm in}$',r'$a_{\rm assign}$','Dots GiB']),
                           ('zh/tables',[r'$d$',r'$n_{\rm list}$',r'$a_{\rm in}$',r'$a_{\rm assign}$','分配乘积 GiB'])]:
        dest=ROOT/prefix/'full-review';dest.mkdir(parents=True,exist_ok=True)
        lines=[r'\begin{tabular}{@{}rrrrr@{}}',r'\toprule',' & '.join(headers)+r' \\',r'\midrule']
        lines+=[' & '.join([f"{r['d']:,}",f"{r['nlist']:,}",f"{r['input_rows']:,}",f"{r['assignment_rows']:,}",f"{r['assignment_bytes']/2**30:.3f}"])+r' \\' for r in scratch]
        lines += [r'\bottomrule',r'\end{tabular}'];(dest/'scratch.tex').write_text('\n'.join(lines)+'\n')
        heads=['Dataset','FP32/TF32 at 0.97','FP32 / RaBitQ','FP32 / CAGRA'] if prefix=='tables' else ['数据集','0.97 处 FP32/TF32','FP32 / RaBitQ','FP32 / CAGRA']
        lines=[r'\begin{tabular}{@{}lrrr@{}}',r'\toprule',' & '.join(heads)+r' \\',r'\midrule']
        for r in anchors:
            name='OpenAI-1536' if r['dataset'].endswith('1536') else 'OpenAI-3072'
            lines.append(' & '.join([name,f"{r['fp32_tf32_at97']:.3f}",f"{r['fp32_rabitq_interp']:.3f} / {r['fp32_rabitq_measured']:.3f}",f"{r['fp32_cagra_interp']:.3f} / {r['fp32_cagra_measured']:.3f}"])+r' \\')
        lines += [r'\bottomrule',r'\end{tabular}'];(dest/'precision-anchors.tex').write_text('\n'.join(lines)+'\n')

    for rel in ['scripts/audit_full_review.py','scripts/audit_t4_t5.py',
                'assessment/full-review-response.txt','assessment/full-review-source.json',
                'data/t4-t5/audit.json', 'frontmatter/abstract.tex','zh/abstract.tex',
                'chapters/09-conclusion.tex','zh/chapters/09-conclusion.tex',
                'chapters/04-4-lifecycle.tex','chapters/04-5-construction.tex',
                'zh/chapters/04-4-lifecycle.tex','zh/chapters/04-5-construction.tex',
                'chapters/07-supp-precision.tex','zh/chapters/07-supp-precision.tex',
                'chapters/08-2-negative.tex','zh/chapters/08-2-negative.tex',
                'figures/ch4/architecture.tex','frontmatter/notation.tex',
                'appendices/b-supplementary.tex','zh/appendices/b-supplementary.tex']:
        read(ROOT/rel)
    strict=json.loads((ROOT/'data/t4-t5/audit.json').read_text())['t4']['path_counts']
    assert strict['complete_key']['order_equal']==55296
    assert strict['distance_only']['tie_only']==56
    result=dict(review_baseline='f010beb84d211438eaa61fe4b9f311bff1974dfc',
                checked_against='80abac9 plus the changes in this review response',
                scope='Offline source/record audit, no GPU run. T1 is separate from the earlier D campaign.',
                scratch=scratch,precision_anchors=anchors,
                ptx=dict(binary_sha256='5371616ed99ab2b2dd323688eb3cf7a23dafb9f3f6a3904cf44475f65cf63ceb',
                         scalar_volatile_loads=2,atomic_min_operations=2,key_stride_bytes=8,
                         scope='Recorded PTX and toolkit SASS only; no binary re-extraction or driver-JIT capture.'),
                findings=dict(F01='Corrected separate capacities',F02='Corrected D scope; T1 anchors separately audited',
                              F03='Corrected navigation title',F04='Already addressed by T4 in 80abac9',
                              F05='Qualified PTX contract retained and archived instructions inspected',
                              personal_contributions='Deferred by explicit author request; no invented attribution'),
                inputs=list(inputs.values()))
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(scratch=scratch,precision_anchors=anchors,inputs=len(inputs)),indent=2))


if __name__=='__main__':
    main()
