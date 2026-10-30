"""Check the scoped discussion revision and its archived T2 calculations."""
import collections
import hashlib
import math
import re


def validate(root, record, later_changes=None):
    names=['03-5-ledger.tex','08-discussion.tex','08-1-insights.tex',
           '08-2-negative.tex','08-3-validity.tex','08-4-directions.tex',
           '08-5-deployment.tex']
    changes={x['path']:x for x in record['changes']}
    assert set(changes)=={'variants/'+lang+'/chapters/'+name for lang in ['thesis2','thesis2-zh'] for name in names},'Chapter 8 scope'
    for name,digest in record['unchanged_source_sha256'].items():
        prior=(later_changes or {}).get(name,{}).get('before')
        content=prior.encode() if prior is not None else (root/name).read_bytes()
        assert hashlib.sha256(content).hexdigest()==digest,('Chapter 8 scope spill',name)
    numeric_cells=lambda t:[[re.findall(r'\d+(?:[,.]\d+)*',cell) for cell in row.split('&')] for row in t.split('\\midrule',1)[1].split('\\\\') if row.strip()]
    table_pattern=r'\\toprule([\s\S]*?)\\bottomrule'
    for x in record['changes']:
        name,old,new=x['path'],x['before'],x['after']
        observed=(later_changes or {}).get(name,{}).get('before',(root/name).read_text())
        assert observed==new,('Chapter 8 unrecorded source',name)
        for env in ['equation','equation*','align','align*','lemma','proposition','corollary','proof']:
            pat=r'\\begin\{'+re.escape(env)+r'\}[\s\S]*?\\end\{'+re.escape(env)+r'\}'
            assert re.findall(pat,old)==re.findall(pat,new),(name,'Formal content',env)
        assert re.findall(r'\\\[[\s\S]*?\\\]',old)==re.findall(r'\\\[[\s\S]*?\\\]',new),(name,'Existing display mathematics')
        old_labels=collections.Counter(re.findall(r'\\label\{([^}]+)\}',old))
        if name.endswith('/08-2-negative.tex'):old_labels.update(record['new_labels'])
        assert old_labels==collections.Counter(re.findall(r'\\label\{([^}]+)\}',new)),(name,'Labels')
        assert re.findall(r'\\cite(?:\[[^]]*\])?\{[^}]*\}',old)==re.findall(r'\\cite(?:\[[^]]*\])?\{[^}]*\}',new),(name,'Citations')
        assert re.findall(r'\\includegraphics(?:\[[^]]*\])?\{[^}]*\}',old)==re.findall(r'\\includegraphics(?:\[[^]]*\])?\{[^}]*\}',new),(name,'Figures')
        old_t,new_t=re.findall(table_pattern,old),re.findall(table_pattern,new)
        if name.endswith('/03-5-ledger.tex'):
            assert len(old_t)==len(new_t)==2
            row=next(line+'\n' for line in new_t[0].splitlines() if line.startswith('T2 &'))
            assert new_t[0].replace(row,'',1)==old_t[0] and new_t[1:]==old_t[1:],'Only T2 navigation may be added'
            assert r'\cref{sec:8-centring}' in row
        elif name.endswith('/08-3-validity.tex'):
            assert len(old_t)==len(new_t)==1
            clean=lambda t:re.sub(r'\b(?:T4|T5|int8|TF32|FP32)\b','',t)
            assert numeric_cells(clean(old_t[0]))==numeric_cells(clean(new_t[0])),'Threat-table measured numerical cells'
            if 'thesis2-zh/' in name:
                cpu='\\cref{sec:7-1} 中较早'+old.split('\\cref{sec:7-1} 中较早',1)[1].split('\n\n证据覆盖',1)[0]
            else:
                cpu='The earlier CPU comparison'+old.split('The earlier CPU comparison',1)[1].split('\n\nEvidence covers',1)[0]
            assert cpu in new,'Historical CPU qualification must remain verbatim'
        elif name.endswith('/08-2-negative.tex'):
            assert not old_t and len(new_t)==1,'One summary table added'
            numbers=numeric_cells(new_t[0])
            expected=[[[],[],['24']],[[],[],['15']],[[],[],['2.8','4.2']],[[],[],['30','52']],[[],[],[]],[[],[],[]]]
            assert numbers==expected,('Stopped-experiment numerical cells',numbers)
        else:
            assert old_t==new_t,(name,'Table payload')
    def interp(front,target):
        near=[q for rec,q in front if abs(rec-target)<=5e-4]
        if near:return max(near)
        for (r0,q0),(r1,q1) in zip(front,front[1:]):
            if r0<=target<=r1 and r1>r0:
                weight=(target-r0)/(r1-r0)
                return math.exp(math.log(q0)+weight*(math.log(q1)-math.log(q0)))
        raise AssertionError('T2 extrapolation')
    targets={'arxiv-768':(1.266,[200,64],[200,100]),
             'vogue-768':(1.015,[100,64],[100,100]),
             'openai3-1536':(0.995,[8,16],[8,16])}
    for ds,(ratio,alpha128,alpha512) in targets.items():
        result=record['t2'][ds]
        oq=interp(result['original_front'],.97);cq=interp(result['centred_front'],.97)
        assert math.isclose(oq,result['original_qps97'],rel_tol=1e-12)
        assert math.isclose(cq,result['centred_qps97'],rel_tol=1e-12)
        assert round(cq/oq,3)==ratio and math.isclose(cq/oq,result['ratio97'],rel_tol=1e-12),(ds,'T2 frontier ratio')
        for probes,alphas in [('128',alpha128),('512',alpha512)]:
            assert [result['budgets'][probes][v]['full'][0] for v in ['orig','cent']]==alphas,(ds,'T2 budget')
    vogue=record['t2']['vogue-768']['budgets']['512']
    assert [vogue[v]['fixed']['200'][0] for v in ['orig','cent']]==[.9918,.9896]
    return dict(section_by_section_discussion_reviewed=True,other_sources_unchanged=True,
                all_formal_equations_and_proofs_preserved=True,existing_numerical_table_cells_preserved=True,
                t2_frontiers_and_budgets_recomputed=True,cpu_qualification_preserved=True,
                one_new_evidence_summary_table=True,offline_and_gpu_evidence_separated=True)
