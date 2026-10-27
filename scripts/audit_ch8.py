#!/usr/bin/env python3
"""Reconstruct the two negative case studies from archives; never runs CUDA."""
import argparse
import hashlib
import json
import os
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent/'JHQ_GPU'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--no-plot',action='store_true');args=ap.parse_args()
    inputs=[]
    def read(base,rel):
        p=base/rel; b=p.read_bytes()
        inputs.append(dict(repository=base.name,path=rel,sha256=hashlib.sha256(b).hexdigest()))
        return json.loads(b) if p.suffix=='.json' else b.decode() if p.suffix!='.pdf' else None
    mail=[]; med=[]; offline=[]
    tags=['vogue-768_np128_a64','arxiv-768_np128_a100','openai3-3072_np128_a4']
    summary=read(SRC,'experiments/mailman_primary/results/summary.json')
    rank=read(SRC,'experiments/rank_optimal_quantization/eval_final_test.json')
    perq=read(SRC,'experiments/rank_optimal_quantization/perquery_final_test.json')
    for tag in tags:
        ds=tag.split('_')[0]
        r=read(SRC,f'experiments/mailman_primary/results/bench_{tag}.json')
        read(SRC,f'experiments/mailman_primary/results/bench_{tag}_profile.json')
        assert r['gpu']=='NVIDIA GeForce RTX 5090'
        for run in r['runs']:
            arms={a['impl']:a for a in run['impls']}
            best=min((a for a in run['impls'] if a['impl'].startswith(('H1','H2'))),key=lambda a:a['median_us'])
            ratio=arms['B0']['median_us']/best['median_us'];assert ratio<1
            old=summary[ds][str(run['batch'])]
            assert abs(ratio-old['s_best'])<1e-9 and best['impl']==old['best']
            model=1/(1-old['f']+old['f']/ratio)
            assert abs(model-old['S_model'])<1e-12
            mail.append(dict(dataset=ds,batch=run['batch'],best=best['impl'],
                             baseline_us=arms['B0']['median_us'],alternative_us=best['median_us'],
                             speed_ratio=ratio,optimistic_model=model,end_to_end_measured=False))
        assert perq[tag]['n']==400
        off=rank[tag]['methods']; row=dict(dataset=ds,n_test=400,target=rank[tag]['target']['test'],
                    original_T=off['JHQ']['test']['T_min'],median_T=off['median']['test']['T_min'])
        assert row['original_T']==perq[tag]['methods']['JHQ']['T_min_strict']
        assert row['median_T']==perq[tag]['methods']['median']['T_min_strict']
        offline.append(row)
        gpu=read(SRC,f'experiments/practical_opt/median_results/{ds}_np128.json')
        assert gpu['rounds']==3 and gpu['nprobe']==128
        target_alpha={'arxiv-768':100,'vogue-768':64,'openai3-3072':4}[ds]
        for batch in [8,1000]:
            runs=[dict(a,qps_median=statistics.median(a['qps'])) for a in gpu['runs'] if a['batch']==batch]
            target=next(a['recall'] for a in runs if a['rep']=='A' and a['alpha']==target_alpha)
            rates={rep:max((a['qps_median'] for a in runs if a['rep']==rep and a['recall']>=target),default=None) for rep in ['A','B']}
            med.append(dict(dataset=ds,batch=batch,target=target,control_qps=rates['A'],
                            alternative_qps=rates['B'],ratio=rates['B']/rates['A'] if rates['B'] else None,
                            alternative_max_recall=max(a['recall'] for a in runs if a['rep']=='B')))
    assert len(mail)==6
    assert next(x for x in offline if x['dataset']=='arxiv-768')['median_T']==375
    for rel in ['experiments/mailman_primary/FINAL_REPORT_CN.md','experiments/mailman_primary/mailman_bench.cu',
                'experiments/mailman_primary/analyze.py','experiments/rank_optimal_quantization/FINAL_REPORT_CN.md',
                'experiments/rank_optimal_quantization/THEORY.md',
                'experiments/practical_opt/median_gpu.sh','experiments/practical_opt/analyze_median.py',
                'experiments/seq_calibration/SEQUENTIAL_CALIBRATION_REPORT.md',
                'experiments/residual_aware_bound/RESIDUAL_BOUND_PILOT_REPORT.md']:
        read(SRC,rel)
    if not args.no_plot:
        os.environ.setdefault('MPLCONFIGDIR','/private/tmp/comp8800-mpl')
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42})
        fig,(a,b)=plt.subplots(1,2,figsize=(8.5,3.1),gridspec_kw={'width_ratios':[1.6,1]})
        labels=[f"{x['dataset'].replace('-768','').replace('openai3-3072','OpenAI')}\nb={x['batch']}" for x in mail]
        a.bar(range(6),[x['speed_ratio'] for x in mail],color=['#557b94','#18344a']*3)
        a.axhline(1,color='#9a4b35',ls='--',lw=1);a.set_ylim(0,1.12)
        a.set_xticks(range(6),labels,fontsize=8);a.set_ylabel('Scorer speed / packed-table baseline')
        a.set_title('(a) Isolated GPU measurement')
        for i,x in enumerate(mail):a.text(i,x['speed_ratio']+.03,f"{x['speed_ratio']:.3f}",ha='center',fontsize=8)
        b.bar(['Original','Median'],[875,375],color=['#557b94','#18344a'])
        b.set_ylim(0,1030);b.set_ylabel('Minimum tested survivors');b.set_title('(b) FP64 offline test: arXiv')
        for i,n in enumerate([875,375]):b.text(i,n+25,str(n),ha='center')
        for ax in [a,b]:ax.spines[['top','right']].set_visible(False);ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True)
        fig.tight_layout();out=ROOT/'figures/ch8';out.mkdir(parents=True,exist_ok=True)
        fig.savefig(out/'negative-evidence.pdf',bbox_inches='tight',metadata={'CreationDate':None,'ModDate':None})
        fig.savefig(out/'negative-evidence.png',dpi=180,bbox_inches='tight');plt.close(fig)
    for pattern in ['chapters/08-*.tex','zh/chapters/08-*.tex']:
        for p in sorted(ROOT.glob(pattern)):read(ROOT,str(p.relative_to(ROOT)))
    for rel in ['figures/ch8/negative-evidence.pdf','assessment/ch7-pending-experiments.txt',
                'scripts/audit_ch8.py','references.bib']:
        read(ROOT,rel)
    result=dict(scope='Archived GPU scorer, offline representation and separate GPU median follow-up; no new GPU run.',
                mailman=mail,rank_offline=offline,median_gpu_followup=med,
                caveats=['Mailman end-to-end replacement is modelled only',
                         'Rank-optimal main study is offline; median follow-up alone has GPU search timing',
                         'Median codes, levels and residuals change together; not a threshold-only ablation',
                         'Old sequential replay is not the v69 six-dataset protocol'],inputs=inputs)
    out=ROOT/'data/ch8/audit.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(mailman_range=[min(x['speed_ratio'] for x in mail),max(x['speed_ratio'] for x in mail)],
                         rank_offline=offline,median_gpu_followup=med,inputs=len(inputs)),indent=2))


if __name__=='__main__':main()
