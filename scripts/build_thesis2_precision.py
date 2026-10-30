#!/usr/bin/env python3
"""Redraw the precision figure from existing records; no tables or benchmarks change."""
from pathlib import Path
import csv,hashlib,json,statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1]
CODE=ROOT.parent/'JHQ_GPU'
OUT=ROOT/'variants/thesis2/figures/precision.pdf'
def frontier(points):
    result,best=[],-1
    for recall,qps in sorted(points,key=lambda p:(-p[0],-p[1])):
        if qps>best:result.append((recall,qps));best=qps
    return sorted(result)
def build():
    inputs={};curves={};base={}
    def read(p):
        data=p.read_bytes();inputs[str(p.relative_to(CODE))]=hashlib.sha256(data).hexdigest();return data.decode()
    for row in csv.DictReader(read(CODE/'experiments/comp8800_poster_e1/E1_points.csv').splitlines()):
        try:base.setdefault((row['dataset'],row['family']),[]).append((float(row['recall']),float(row['qps_A'])))
        except ValueError:pass
    datasets=['openai3-1536','openai3-3072']
    for ds in datasets:
        d={}
        for version in ['v69','v72']:
            points={}
            for p in sorted((CODE/'experiments/thesis_evidence/RAW_D').glob(f'jhq_{version}_{ds}_np*.json')):
                data=json.loads(read(p))
                for run in data['runs']:
                    assert run['batch']==1000 and data['rounds']==5
                    v=next(v for v in run['variants'] if v['G']==-1)
                    points[data['nprobe'],run['alpha']]=(v['recall'],statistics.median(v['qps']))
            d[version]=frontier(points.values())
        d['rabitq']=frontier(base[ds,'IVF-RaBitQ']);d['cagra']=frontier(base[ds,'CAGRA fp32']);curves[ds]=d
    plt.rcParams.update({'font.size':8.5,'font.family':'serif','font.serif':['STIXGeneral'],'mathtext.fontset':'stix','axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42,'figure.constrained_layout.use':True})
    fig,axes=plt.subplots(1,2,figsize=(6.14,2.65))
    for ax,ds in zip(axes,datasets):
        for key,label,color,style in [('v69','JHQ: TF32','#2166ac','-'),('v72','JHQ: FP32','#b2182b','-'),('rabitq','IVF-RaBitQ (archived)','#555555','--'),('cagra','CAGRA fp32 (archived)','#999999',':')]:
            points=curves[ds][key];ax.plot([p[0] for p in points],[p[1]/1000 for p in points],style,label=label,color=color,linewidth=1.2)
        ax.set(xlim=(.945,.985),xlabel='Recall@10',ylabel='Throughput (kQPS)',title=ds.replace('openai3','OpenAI'))
        ax.set_ylim(bottom=0,top=240 if ds==datasets[0] else 110);ax.set_xticks([.95,.96,.97,.98]);ax.grid(alpha=.2)
    axes[0].legend(fontsize=7.4,loc='upper right',handlelength=1.6,labelspacing=.3,borderpad=.3)
    fig.savefig(OUT);plt.close(fig)
    record={'inputs':inputs,'curves':curves,'note':'Same raw records, frontier rule, numerical series, axis ranges, colours and line styles as the shared original; reader-facing names, font and physical size changed.'}
    (ROOT/'build/final-review-2026-10-30/precision-series.json').write_text(json.dumps(record,indent=2)+'\n')
if __name__=='__main__':build()
