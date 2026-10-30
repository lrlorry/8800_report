"""Validate the final editorial layer without weakening previous audit layers."""
import collections
import hashlib
import re

def validate(root, record):
    changes={x['path']:x for x in record['changes']}
    for path,digest in record['unchanged_source_sha256'].items():
        assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,('Final review scope',path)
    for group in ['protected_data_sha256','raw_inputs_sha256']:
        for path,digest in record[group].items():
            assert hashlib.sha256((root/path).read_bytes()).hexdigest()==digest,('Final review evidence changed',path)
    correction=record['authorised_numeric_correction']
    for path,x in changes.items():
        old,new=x['before'],x['after']
        assert (root/path).read_text()==new,('Final review after-image',path)
        for env in ['equation','equation*','align','align*','lemma','proposition','corollary','proof']:
            pat=r'\\begin\{'+re.escape(env)+r'\}[\s\S]*?\\end\{'+re.escape(env)+r'\}'
            assert re.findall(pat,old)==re.findall(pat,new),(path,'Formal mathematics',env)
        assert re.findall(r'\\\[[\s\S]*?\\\]',old)==re.findall(r'\\\[[\s\S]*?\\\]',new),(path,'Display mathematics')
        inline=lambda s:collections.Counter(re.findall(r'(?<!\\)\$(?:\\.|[^$])*?(?<!\\)\$',s))
        assert inline(old.replace(correction['before'],correction['after']))==inline(new),(path,'Inline mathematics')
        for cmd in ['label','cite','cref','Cref','input']:
            pat=r'\\'+cmd+r'(?:\[[^]]*\])?\{[^}]*\}'
            assert collections.Counter(re.findall(pat,old))==collections.Counter(re.findall(pat,new)),(path,cmd)
        graphics=lambda s:re.findall(r'\\includegraphics(?:\[[^]]*\])?\{([^}]+)\}',s)
        assert [record['new_precision_figure']['path'] if a=='supplement/precision.pdf' else a for a in graphics(old)]==graphics(new),(path,'Graphics scope')
        tables=lambda s:re.findall(r'\\toprule([\s\S]*?)\\bottomrule',s)
        a,b=tables(old),tables(new)
        if path.endswith('/03-5-ledger.tex'):
            assert len(a)==len(b)==2
            labels=['E1','D','T1','T4','T5','A1','A2','A3','B','C1','T2']
            assert [line.split('&')[1].strip() for line in b[0].splitlines() if '&' in line and not line.startswith(('Name','正文'))]==labels
            assert 'v57 &' in b[1]
            assert b[1].split('v61 &',1)[1]==a[1].split('v61 &',1)[1],'Only historical version row may be added'
        else:assert a==b,(path,'Measured table cells')
    # Visible experiment labels live only in the Chapter 3.5 mapping table.
    banned=re.compile(r'\b(?:E1|T[1-5]|A[1-3]|R1|v(?:57|61|62|63|65|71|73))\b|check D|campaign C1')
    for lang in ['thesis2','thesis2-zh']:
        for folder in ['chapters','frontmatter','figures']:
            for p in (root/'variants'/lang/folder).glob('*.tex'):
                text=p.read_text()
                if p.name=='03-5-ledger.tex':
                    text=re.sub(r'\\toprule[\s\S]*?\\bottomrule','',text)
                # Paths, references and comments are identifiers rather than visible prose.
                text=re.sub(r'(?<!\\)%[^\n]*|\\(?:label|input|includegraphics|href|hyperref)(?:\[[^]]*\])?\{[^}]*\}','',text)
                assert not banned.search(text),('Visible experiment label',p,banned.findall(text))
                if p.name not in ['03-5-ledger.tex','04-2-training.tex']:
                    assert not re.search(r'\bv(?:69|72)\b',text),('Repeated version name',p)
    figure=record['new_precision_figure']
    assert hashlib.sha256((root/figure['path']).read_bytes()).hexdigest()==figure['sha256']
    # Bilingual paired edits preserve the same mathematical and reference objects.
    for path in changes:
        if not path.startswith('variants/thesis2/'):continue
        other=path.replace('variants/thesis2/','variants/thesis2-zh/',1)
        assert other in changes,('Missing Chinese edit',path)
    numbers=record['numerical_audit']
    assert numbers['main_valid_points']==1590 and numbers['sampled_decisions_checked']==2304
    assert numbers['strict_configurations']==270 and numbers['strict_selection']['grouped']['order_equal']==55296
    assert numbers['strict_selection']['one_block']['tie_only']==56 and numbers['underfull']==19120
    return dict(raw_records_recalculated=True,formal_mathematics_preserved=True,measured_tables_preserved=True,
                descriptive_experiment_names=True,one_navigation_table=True,source_paths_and_labels_preserved=True,
                numerical_rounding_corrected=True,precision_plot_data_preserved=True)
