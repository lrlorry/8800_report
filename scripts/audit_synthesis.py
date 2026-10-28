#!/usr/bin/env python3
"""Audit the requested synthesis chapters without executing GPU code."""
import collections
import hashlib
import json
import math
import re
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT.parent/'JHQ_GPU'


def prose_count(s):
    s=re.sub(r'(?<!\\)%[^\n]*','',s)
    s=re.sub(r'(\\(?:caption(?:of\{(?:figure|table)\})?|chapter))\[[^\]]*\]',r'\1',s)
    s=re.sub(r'\\begin\{(equation\*?|align\*?|tabularx|tabular|longtable)\}[\s\S]*?\\end\{\1\}',' ',s)
    s=re.sub(r'\$[^$]*\$',' ',s)
    s=re.sub(r'\\(?:label|input|cite|[Cc]ref|ref|path|operatorname)\*?(?:\[[^]]*\])?\{[^}]*\}',' ',s)
    s=re.sub(r'\\(?:begin|end)\{[^}]*\}(?:\{[^}]*\})?',' ',s)
    s=s.replace(r'\\', ' ')
    s=re.sub(r'\\[A-Za-z@]+\*?',' ',s)
    return len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*",s))


def main():
    inputs=[]
    def read(base,rel):
        p=base/rel;b=p.read_bytes()
        inputs.append(dict(repository=base.name,path=rel,sha256=hashlib.sha256(b).hexdigest()))
        return b.decode() if p.suffix!='.pdf' else None
    patterns=[r'\\label(?:\[[^]]*\])?\{([^}]+)\}',
              r'\\(?:[Cc]ref|[Ee]qref|ref)\{([^}]+)\}',r'\\(?:cite|citep|citet)\{([^}]+)\}']
    texts=[];words={};checked=[]
    for prefix in ['01','02','08','09']:
        total=0
        for p in sorted(ROOT.glob(f'chapters/{prefix}-*.tex')):
            rel=str(p.relative_to(ROOT));a=read(ROOT,rel);b=read(ROOT,'zh/'+rel)
            assert not any(x in a+b for x in ['\\draftnote','\\figureplaceholder','TO WRITE'])
            for pat in patterns:
                assert collections.Counter(re.findall(pat,a))==collections.Counter(re.findall(pat,b)),(rel,pat)
            ea=re.findall(r'\\begin\{equation\}([\s\S]*?)\\end\{equation\}',a)
            eb=re.findall(r'\\begin\{equation\}([\s\S]*?)\\end\{equation\}',b)
            assert [re.sub(r'\s+','',x) for x in ea]==[re.sub(r'\s+','',x) for x in eb],rel
            total+=prose_count(a);texts.append(a);checked.append(rel)
        words[prefix]=total
    abstract=read(ROOT,'frontmatter/abstract.tex');zhabs=read(ROOT,'zh/abstract.tex')
    assert '\\draftnote' not in abstract+zhabs
    words['abstract']=prose_count(abstract);assert 250<=words['abstract']<=350,words
    texts.append(abstract)
    bib=read(ROOT,'references.bib')
    keys=re.findall(r'@\w+\s*\{([^,]+),',bib);assert len(keys)==len(set(keys))
    cites={k.strip() for t in texts for c in re.findall(patterns[2],t) for k in c.split(',')}
    assert cites<=set(keys),cites-set(keys)
    all_tex='\n'.join(p.read_text() for folder in ['chapters','appendices','frontmatter'] for p in (ROOT/folder).glob('*.tex'))
    labels=set(re.findall(patterns[0],all_tex))
    refs={k.strip() for t in texts for c in re.findall(patterns[1],t) for k in c.split(',')}
    assert refs<=labels,refs-labels
    j=json.loads(read(ROOT,'data/ch7/audit.json'))
    c=json.loads(read(ROOT,'data/ch6/audit.json'))
    shapes=json.loads(read(ROOT,'data/ch3/audit.json'))['datasets']
    neg=json.loads(read(ROOT,'data/ch8/audit.json'))
    assert j['lut']['wins']['2']==22 and j['lut']['cells']==24
    stella=next(x for x in shapes if x['dataset']=='stella')
    assert f"{stella['N']/1e6:.2f}"=='17.78'
    assert f"{j['memory']['stella']['used_mib']/1024:.2f}"=='20.44'
    assert f"{sum(j['build']['stella'].values())/1000:.2f}"=='10.40'
    rates={x['batch']:x['gains']['-1'] for x in j['pipeline']['summary']}
    assert f"{rates[8]:.3f}"=='2.727' and f"{rates[1000]:.3f}"=='1.015'
    assert j['full_pool']['qualified']==12 and abs(j['full_pool']['max_loss']-.0006)<1e-8
    assert max(round(x['over']*x['reps']) for x in j['budget'])==40
    assert c['full_pool_coverage']['distance_only_configurations']==10
    # Four RaBitQ comparisons at recall .97: three positive differences and one near tie.
    matches=[x for x in j['matched'] if x['recall']==.97 and x['other']=='IVF-RaBitQ']
    assert len(matches)==4 and sum(x['ratio_interp']>1 for x in matches)==3
    assert abs(next(x['ratio_interp'] for x in matches if x['dataset']=='arxiv-768')-1)<.01
    supplement=json.loads(read(ROOT,'data/supplement/audit.json'))
    followup=json.loads(read(ROOT,'data/t4-t5/audit.json'))
    assert followup['t4']['path_counts']['complete_key']['order_equal']==55296
    assert followup['t4']['path_counts']['distance_only']['tie_only']==56
    small97=next(x for x in followup['t5']['ranges'] if x['batch']==8 and x['target']==.97)
    assert small97['interp_wins']==small97['measured_wins']==0
    flags=dict(capacity_vectors=stella['N'],resident_gib=j['memory']['stella']['used_mib']/1024,
               original_cold_train_add_s=sum(j['build']['stella'].values())/1000,
               repeated_train_add_s=supplement['builds']['stella']['train_add_s'],
               sampled_build_peak_gib=supplement['builds']['stella']['peak_gib'],
               supplementary_checks=supplement['checks'],
               fp32_sensitivity=supplement['precision'],
               lut_wins=22,lut_cells=24,batch8_gain=rates[8],batch1000_gain=rates[1000],
               full_quality_passes=12,full_max_loss=j['full_pool']['max_loss'],
               worst_S128_crossings=40,full_distance_only_cells=10,
               strict_grouped_instances=55296,smallbatch8_recall97=small97)
    sigma_quantile=statistics.NormalDist().inv_cdf(.75)
    sigma_mean=math.sqrt(2/math.pi)
    model=dict(quantile_level=sigma_quantile,conditional_mean_level=sigma_mean,
               quantile_mse=1+sigma_quantile**2-2*sigma_quantile*sigma_mean,
               optimal_zero_threshold_mse=1-sigma_mean**2,
               scope='analytic standard-normal model, not a dataset or GPU measurement')
    assert model['quantile_mse']>model['optimal_zero_threshold_mse']
    for rel in ['data/synthesis/primary-sources.json','assessment/synthesis-iteration.txt',
                'assessment/author-confirmation.txt','assessment/ch7-pending-experiments.txt',
                'appendices/c-author-tools.tex','main.tex','main-zh.tex',
                'config/layout.tex','config/preamble.tex','zh/preamble.tex',
                'config/metadata.tex','frontmatter/title.tex','zh/title.tex',
                'frontmatter/notation.tex','README.md','FORMAT_NOTES.txt',
                'scripts/audit_synthesis.py','figures/ch1/challenges.tex','figures/ch2/candidate-cascade.tex']:
        read(ROOT,rel)
    for rel in ['p1530-han.pdf','cpu/pq_codebook.cpp','paper_adc2026/ADC/mainADC.tex',
                'paper_adc2026/ADC/Preliminary_ADC.tex','paper_adc2026/ADC/MethodPart1_ADC.tex',
                'paper_adc2026/ADC/MethodPart2_ADC.tex','paper_adc2026/ADC/Experiment_ADC.tex']:
        read(SRC,rel)
    poster=Path.home()/'Documents/26 s1/COMP8800/my poster/poster.pdf'
    inputs.append(dict(repository='user_local_poster',path=str(poster.relative_to(Path.home())),
                       sha256=hashlib.sha256(poster.read_bytes()).hexdigest()))
    out=dict(scope='Requested Ch8/Ch2/Ch1/Ch9/Abstract: offline synthesis, source review and compilation; no GPU run.',
             checked_chapter_files=checked,prose_words=words,
             word_count_scope='prose and captions; math/table bodies excluded; not official course count',
             quoted_results=flags,gaussian_level_check=model,
             cited_keys=sorted(cites),bilingual_structure_and_equations=True,
             author_attestation='personal task allocation, signed declaration and final human adoption remain to be confirmed',
             negative_evidence_scope=neg['caveats'],inputs=inputs)
    p=ROOT/'data/synthesis/audit.json';p.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps(dict(chapter_files=len(checked),prose_words=words,citations=len(cites),
                         quoted_results=flags,inputs=len(inputs)),indent=2))


if __name__=='__main__':main()
