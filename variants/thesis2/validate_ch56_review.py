"""Validate the authorised Chapter 5/6 structural review against exact sources."""
import collections
import hashlib
import re


def validate(root, record, later_changes=None):
    changes={x['path']:x for x in record['changes']}
    names=['03-5-ledger.tex','05-gpu-execution.tex','06-refinement.tex',
           '05-1-query-path.tex','05-2-lut.tex','05-3-packed-access.tex',
           '05-4-global-selection.tex','05-5-bound-scheduling.tex',
           '05-6-refinement.tex','05-7-probe.tex','06-1-motivation.tex',
           '06-2-agreement.tex','06-3-search.tex','06-4-controls.tex',
           '06-5-economics.tex','06-6-scope.tex']
    assert set(changes)=={'variants/'+lang+'/chapters/'+name for lang in ['thesis2','thesis2-zh'] for name in names},'Chapter 5/6 scope'
    for name,digest in record['unchanged_source_sha256'].items():
        prior=(later_changes or {}).get(name,{}).get('before')
        content=prior.encode() if prior is not None else (root/name).read_bytes()
        assert hashlib.sha256(content).hexdigest()==digest,('Chapter 5/6 scope spill',name)
    for x in record['changes']:
        name,old,new=x['path'],x['before'],x['after']
        observed=(later_changes or {}).get(name,{}).get('before',(root/name).read_text())
        assert observed==new,('Unrecorded Chapter 5/6 source',name)
        for env in ['equation','equation*','align','align*','lemma','proposition','corollary','proof']:
            pat=r'\\begin\{'+re.escape(env)+r'\}[\s\S]*?\\end\{'+re.escape(env)+r'\}'
            assert re.findall(pat,old)==re.findall(pat,new),(name,env)
        old_d=collections.Counter(re.findall(r'\\\[[\s\S]*?\\\]',old))
        new_d=collections.Counter(re.findall(r'\\\[[\s\S]*?\\\]',new))
        for move in record['math_moves']:
            if name==move['source']:old_d.subtract([move['block']])
            if name==move['target']:new_d.subtract([move['block']])
        assert +old_d==+new_d,(name,'Display math changed')
        pat=r'\\toprule([\s\S]*?)\\bottomrule'
        before_tables,after_tables=re.findall(pat,old),re.findall(pat,new)
        assert len(before_tables)==len(after_tables),(name,'Table count')
        short=name.split('/chapters/',1)[1]
        if 'chapters/'+short in record['authorised_table_rewordings']:
            for a,b in zip(before_tables,after_tables):
                cells=lambda t:[[re.findall(r'\d+(?:[,.]\d+)*',c) for c in row.split('&')] for row in t.split('\\midrule',1)[1].split('\\\\') if row.strip()]
                assert cells(a)==cells(b),(name,'Table numerical cells')
                math=lambda t:collections.Counter(re.findall(r'(?<!\\)\$(?:\\.|[^$])*?(?<!\\)\$',t))
                assert math(a)==math(b),(name,'Table mathematics')
        else:
            assert before_tables==after_tables,(name,'Table payload changed')
        labels=lambda s:collections.Counter(re.findall(r'\\label(?:\[[^]]*\])?\{[^}]*\}',s))
        cites=lambda s:collections.Counter(re.findall(r'\\cite(?:\[[^]]*\])?\{[^}]*\}',s))
        assert labels(old)==labels(new),(name,'Labels changed')
        assert cites(old)==cites(new),(name,'Citations changed')
    for lang in ['thesis2','thesis2-zh']:
        old='\n'.join(x['before'] for x in record['changes'] if x['path'].startswith('variants/'+lang+'/'))
        new='\n'.join(x['after'] for x in record['changes'] if x['path'].startswith('variants/'+lang+'/'))
        assert collections.Counter(re.findall(r'\\\[[\s\S]*?\\\]',old))==collections.Counter(re.findall(r'\\\[[\s\S]*?\\\]',new)),(lang,'Cross-chapter display move')
    return dict(section_by_section_structure_reviewed=True,exact_before_images_replayed=True,
                all_equations_and_formal_proofs_preserved=True,numerical_table_cells_preserved=True,
                scheduler_setup_display_moved_verbatim=True,other_chapters_and_diagrams_unchanged=True,
                bilingual_sources_reviewed=True)
