"""Validate the Chapter 7 editorial review without changing measured artifacts."""
import collections
import hashlib
import math
import re


BLOCKS = (r'\\par\\medskip\\noindent\\begin\{minipage\}[\s\S]*?\\end\{minipage\}\\par\\medskip|'
          r'\\begin\{figure\}[\s\S]*?\\end\{figure\}|'
          r'\\begin\{table\}[\s\S]*?\\end\{table\}')


def validate(root, record, later_changes=None):
    names=['03-5-ledger.tex','07-evaluation.tex','07-supp-precision.tex',
           '07-supp-selection.tex','07-supp-budget.tex','07-supp-smallbatch.tex',
           '08-3-validity.tex','09-conclusion.tex']
    changes={x['path']:x for x in record['changes']}
    assert set(changes)=={'variants/'+lang+'/chapters/'+name for lang in ['thesis2','thesis2-zh'] for name in names},'Chapter 7 scope'
    for group in ['unchanged_source_sha256','protected_data_sha256']:
        for name,digest in record[group].items():
            prior=(later_changes or {}).get(name,{}).get('before')
            content=prior.encode() if prior is not None else (root/name).read_bytes()
            assert hashlib.sha256(content).hexdigest()==digest,('Chapter 7 protected source/data',name)
    for x in record['changes']:
        name,old,new=x['path'],x['before'],x['after']
        observed=(later_changes or {}).get(name,{}).get('before',(root/name).read_text())
        assert observed==new,('Chapter 7 unrecorded source',name)
        for env in ['equation','equation*','align','align*','lemma','proposition','corollary','proof']:
            pat=r'\\begin\{'+re.escape(env)+r'\}[\s\S]*?\\end\{'+re.escape(env)+r'\}'
            assert re.findall(pat,old)==re.findall(pat,new),(name,'Formal content',env)
        assert re.findall(r'\\\[[\s\S]*?\\\]',old)==re.findall(r'\\\[[\s\S]*?\\\]',new),(name,'Display mathematics')
        assert re.findall(BLOCKS,old)==re.findall(BLOCKS,new),(name,'Figure/table blocks')
        for pat in [r'\\includegraphics(?:\[[^]]*\])?\{[^}]*\}',r'\\cite(?:\[[^]]*\])?\{[^}]*\}']:
            assert collections.Counter(re.findall(pat,old))==collections.Counter(re.findall(pat,new)),(name,'Figures/citations')
        labels=collections.Counter(re.findall(r'\\label\{([^}]+)\}',old))
        if name.endswith('/07-evaluation.tex'):labels.update([record['new_label']])
        assert labels==collections.Counter(re.findall(r'\\label\{([^}]+)\}',new)),(name,'Labels')
        if name in record['outside_chapter7_replacements']:
            expected=old
            for a,b in record['outside_chapter7_replacements'][name]:
                assert expected.count(a)==1,(name,'Outside-Chapter-7 correction before-image')
                expected=expected.replace(a,b,1)
            assert expected==new,(name,'Outside-Chapter-7 correction scope')
        if name in record['protocol_note_additions']:
            assert old.replace(r'\label{sec:a-budget-contract}',record['protocol_note_additions'][name]+r'\label{sec:a-budget-contract}',1)==new,(name,'Protocol-note-only change')
    for x in record['document_changes']:
        assert (root/x['path']).read_text()==x['after'],('Pending-evidence record',x['path'])
    data=record['recalculated']
    full=data['full_pool']
    assert full['settings']==full['qualifying']==12
    assert math.isclose(full['max_loss'],.0006,abs_tol=1e-12)
    assert round(full['gain100_geomean'],3)==1.111 and round(full['quality_matched_gain100_geomean'],3)==1.193
    expected={'openai3-1536/128':{'rule':[4,6],'full':[9,14]},
              'openai3-3072/128':{'rule':[4,9],'full':[11,27]}}
    for ds,policies in expected.items():
        for policy,crossings in policies.items():
            actual=[data['stream_crossings'][ds][policy][fixed]['first_positive_mean_total'] for fixed in ['fixed100','fixed64']]
            assert actual==crossings,(ds,policy,'Direct cumulative crossings')
    pilot=data['reconstruction_pilot']
    arxiv=pilot['arxiv-768_np128_a100']
    assert arxiv['queries']==128 and math.isclose(arxiv['gpu_recall'],.9734375,abs_tol=1e-12)
    assert math.isclose(arxiv['full_reconstructed_recall'],.9750,abs_tol=1e-12)
    assert math.isclose(arxiv['gap'],.0015625,abs_tol=1e-12)
    assert math.isclose(pilot['arxiv-768_np128_a200']['answer_set_overlap'],1,abs_tol=1e-12)
    assert data['cpu_plot_log']=='cpu6.log'
    assert data['cpu_thread_records']['cpu6.log']['arxiv-768']==[32]
    assert data['cpu_thread_records']['cpu_four.log']['arxiv-768']==[16,32]
    return dict(result_first_structure_reviewed=True,all_figure_and_table_blocks_preserved=True,
                all_formal_equations_and_proofs_preserved=True,all_measured_artifacts_preserved=True,
                historical_cpu_frontier_scope_checked=True,full_pool_and_recall_pilot_recalculated=True,
                sampled_and_full_pool_paybacks_separated=True,net_memory_boundary_corrected=True,
                other_sources_preserved=True)
