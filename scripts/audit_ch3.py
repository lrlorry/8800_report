#!/usr/bin/env python3
"""Audit common thesis protocols using archived measurements; no GPU execution."""
import collections
import hashlib
import importlib.util
import json
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / 'JHQ_GPU'
E1 = SOURCE / 'experiments/comp8800_poster_e1'
DATASETS = ['vogue-768', 'arxiv-768', 'openai3-1536', 'openai3-3072', 'bge-m3', 'stella']
NAMES = ['Vogue', 'arXiv', 'OpenAI-1536', 'OpenAI-3072', 'BGE-M3', 'Stella']


def main():
    inputs = {}

    def record(path, repository=None, relative=None):
        path = Path(path)
        if repository is None:
            repository = ROOT.name if path.is_relative_to(ROOT) else SOURCE.name
            relative = str(path.relative_to(ROOT if repository == ROOT.name else SOURCE))
        item = dict(repository=repository, path=relative,
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        inputs[repository, relative] = item
        return path.read_text() if path.suffix != '.pdf' else None

    budget = record(SOURCE / 'experiments/adc_v69/RAW/budget_v69.log')
    cells = collections.defaultdict(list)
    for chunk in re.split(r'^### ', budget, flags=re.M)[1:]:
        h = re.match(r'(\S+) M=(\d+) nlist=(\d+) np=(\d+)', chunk)
        if not h:
            continue
        shape = re.search(r'base=(\d+)×(\d+)\s+query=(\d+)×(\d+)\s+gt=(\d+)×(\d+)', chunk)
        training = re.search(r'Training on (\d+) vectors', chunk)
        split = re.search(r'split: (\d+) calibration queries, (\d+) held-out', chunk)
        assert shape and training and split
        n, d, nq, dq, ng, width = map(int, shape.groups())
        assert d == dq and nq == ng and width >= 10
        cal, held = map(int, split.groups())
        assert cal + held == nq
        cells[h[1]].append(dict(N=n, d=d, nq=nq, gt_width=width,
                               M=int(h[2]), nlist=int(h[3]), nprobe=int(h[4]),
                               n_train_requested=int(training[1]), calibration_n=cal, held_out_n=held))
    assert list(cells) == DATASETS and all(len(v) == 2 for v in cells.values())
    datasets = []
    for name, display in zip(DATASETS, NAMES):
        a, b = cells[name]
        assert set([a['nprobe'], b['nprobe']]) == {128, 512}
        assert {k: v for k, v in a.items() if k != 'nprobe'} == {k: v for k, v in b.items() if k != 'nprobe'}
        assert a['n_train_requested'] == 39*a['nlist'] and a['M'] == a['d']//8
        datasets.append(dict(dataset=name, display=display, E1=name in DATASETS[:4],
                             **{k: v for k, v in a.items() if k != 'nprobe'}))
    assert [d['N'] for d in datasets] == [932328, 2253000, 999000, 999000, 10091524, 17776615]
    assert [d['nq'] for d in datasets] == [1000, 1000, 1000, 1000, 1000, 999]

    # Same raw parser used to reconstruct the thesis frontiers; import does not run benchmarks.
    spec = importlib.util.spec_from_file_location('ch3_e1_parser', E1/'analyze.py')
    parser = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(parser)
    points, failures, indexes = parser.load(str(E1/'RAW_RESULTS'))
    assert len(points) == 1590 and not failures
    assert {p['dataset'] for p in points} == set(DATASETS[:4])
    assert all(not p['invalid_ids'] and not p['dup_rows'] for p in points)
    point_counts = collections.Counter((p['dataset'], p['family']) for p in points)
    traces = 0
    metas = []
    for p in sorted((E1/'RAW_RESULTS').glob('*')):
        if p.suffix not in ('.json', '.jsonl') and not p.name.startswith('env_'):
            continue
        text = record(p)
        if p.suffix != '.jsonl':
            continue
        for line in text.splitlines():
            r = json.loads(line)
            if r.get('type') == 'meta':
                metas.append(dict(dataset=r.get('dataset'), method=r.get('method'),
                                  n=r.get('n'), d=r.get('d'), nq=r.get('nq'), gt_width=r.get('gt_width')))
                if r.get('dataset') in DATASETS[:4] and 'gt_width' in r:
                    d = datasets[DATASETS.index(r['dataset'])]
                    assert (r['n'],r['d'],r['nq'],r['gt_width'],r['k']) == (d['N'],d['d'],d['nq'],d['gt_width'],10)
            if r.get('type') != 'point' or 'A' not in r:
                continue
            assert r['rounds'] == 5 and len(r['A']['call_ms']) == 5
            q_rounds = [r['calls_per_round']*1000/(sum(ts)/1000) for ts in r['A']['call_ms']]
            # Call traces and throughputs are rounded independently on export.
            assert max(abs(q/x-1) for q,x in zip(q_rounds,r['A']['qps_rounds'])) < 2e-4
            assert abs(statistics.median(r['A']['qps_rounds'])-r['A']['qps_median']) < .11
            traces += 1
    assert metas and traces
    jhq_points = [p for p in points if p['family'] == 'JHQ-GPU v69']
    assert all(json.loads(p['params'])['batch'] == 1000 for p in jhq_points)
    assert all(p['rounds'] == 5 and p['calls_per_round'] == 24 for p in jhq_points)

    source_files = [
        'experiments/comp8800_poster_e1/run_e1.sh',
        'experiments/comp8800_poster_e1/analyze.py',
        'experiments/comp8800_poster_e1/bench_cuvs.py',
        'experiments/comp8800_poster_e1/bench_rabitq_sweep.cu',
        'experiments/comp8800_poster_e1/FAIRNESS_AUDIT.md',
        'experiments/adc_v69/run_budget_v69.sh', 'experiments/adc_v69/run_lutgroups_v71.sh',
        'examples/demo_jhq_budget_arms_v69.cu', 'examples/demo_jhq_batch_pipeline.cu',
        'common/recall.cuh', 'scripts/preprocess.py', 'scripts/download_jhq_datasets.py',
        'paper_adc2026/ADC/Experiment_ADC.tex', 'paper_adc2026/ADC/reference.bib',
    ]
    for path in source_files:
        record(SOURCE/path)
    prep = (SOURCE/'scripts/download_jhq_datasets.py').read_text()
    assert 'SEED = 42' in prep and 'finite_mask = np.all(np.isfinite(vecs), axis=1)' in prep
    assert 'where=norms > 1e-12' in prep and 'split="corpus"' in prep
    assert 'config="it"' in prep
    bh = (SOURCE/'examples/demo_jhq_budget_arms_v69.cu').read_text()
    assert 'std::srand(12345)' in bh and 'run_rule(all, &cm, &pr);' in bh
    env = (E1/'RAW_RESULTS/env_20261014T130637Z.txt').read_text()
    assert '575.00 W' in env and 'V13.0.88' in env and '595.71.05' in env

    out_table = ROOT/'tables/ch3/datasets.tex'
    out_table.parent.mkdir(parents=True,exist_ok=True)
    rows = ''.join(' & '.join([d['display']]+[f"{d[k]:,}" for k in ['N','d','nq','nlist','n_train_requested']])+r' \\'+ '\n' for d in datasets)
    for path, title in [(out_table, 'Dataset'), (ROOT/'zh/tables/ch3-datasets.tex','数据集')]:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text('% Generated by scripts/audit_ch3.py from the budget shape logs.\n'+
            r'\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrrrrr@{}}'+'\n'+
            '\\toprule\n'+title+r' & $N$ & $d$ & $n_q$ & $n_{\rm list}$ & $n_t$ \\'+'\n'+
            '\\midrule\n'+rows+'\\bottomrule\n\\end{tabular*}\n')

    families = [
        ('E1','RQ4','end-to-end measurement','data/ch7/audit.json','e1','fig:7-frontiers'),
        ('LUT','RQ2','paired benchmark','data/ch7/audit.json','lut','fig:7-lut'),
        ('PACK','RQ2','paired benchmark','data/ch7/audit.json','packing','sec:7-3'),
        ('REFINE','RQ2','paired benchmark','data/ch7/audit.json','refinement_gain_range','sec:7-3'),
        ('SCAN','RQ2','reference correctness','data/ch7/audit.json','correctness','sec:7-4'),
        ('BOUND','RQ2','reference correctness and paired benchmark','data/ch7/audit.json','bound_gain_range','sec:7-4'),
        ('PIPE','RQ2','paired benchmark','data/ch7/audit.json','pipeline','sec:7-6'),
        ('PROBE','RQ2','reference correctness','data/ch7/audit.json','correctness','sec:5-7'),
        ('BUDGET','RQ3','held-out assessment and model estimate','data/ch6/audit.json','cells','sec:7-5'),
        ('BUILD','RQ1','end-to-end measurement','data/ch4/audit.json','cold_train_add_records','sec:7-7'),
        ('MEMORY','RQ1','resident measurement and component model','data/ch4/audit.json','resident_samples','fig:7-memory'),
    ]
    registry = []
    for claim, rq, kind, file, field, target in families:
        d = json.loads((ROOT/file).read_text())
        assert field in d
        registry.append(dict(claim_id=claim, RQ=rq, evidence_class=kind,
                             detailed_audit=file, detailed_field=field, thesis_target=target,
                             provenance='family-specific source and raw input ledger; see Appendix A',
                             raw_identity_join='inputs[] in the detailed audit, or data/ch7/sources.csv',
                             analysis_script='scripts/audit_ch6.py' if claim=='BUDGET' else
                                             'scripts/audit_ch4_review.py' if claim in ['BUILD','MEMORY'] else
                                             'scripts/build_ch7.py',
                             execution_identity_table='tab:a-components',
                             timing_and_metric_contract='sec:3-2 / sec:3-3; family-specific protocol in Appendix A',
                             executable_sha256=None, complete_index_fingerprint=None,
                             complete_vector_file_fingerprint=None))
    poster = Path.home()/'Documents/26 s1/COMP8800/my poster/poster.pdf'
    record(poster,'user_local_poster',str(poster.relative_to(Path.home())))
    for name in ['6.pdf','assessment/thesis-marking-guide.txt','assessment/ch3-evidence.txt',
                 'assessment/ch7-pending-experiments.txt','appendices/a-reproducibility.tex',
                 'chapters/07-evaluation.tex','zh/chapters/07-evaluation.tex', 'main-zh.tex',
                 'references.bib','scripts/audit_ch3.py','tables/ch3/datasets.tex','zh/tables/ch3-datasets.tex',
                 'data/ch7/audit.json','data/ch4/audit.json','data/ch6/audit.json',
                 'data/ch7/round2-audit.json','data/ch3/sources.json']:
        record(ROOT/name)
    for pattern in ['chapters/03-*.tex','zh/chapters/03-*.tex',
                    'figures/ch3/*.tex','zh/figures/ch3/*.tex']:
        for p in sorted(ROOT.glob(pattern)):
            record(p)
    def prose_words(s):
        s=re.sub(r'(?<!\\)%[^\n]*','',s)
        s=re.sub(r'(\\(?:caption(?:of\{(?:figure|table)\})?|chapter))\[[^\]]*\]',r'\1',s)
        s=re.sub(r'\\begin\{(equation\*?|align\*?|tabularx|tabular)\}[\s\S]*?\\end\{\1\}',' ',s)
        s=re.sub(r'\$[^$]*\$',' ',s)
        s=re.sub(r'\\(?:label|input|cite|[Cc]ref|ref|path|operatorname)\*?(?:\[[^]]*\])?\{[^}]*\}',' ',s)
        s=re.sub(r'\\(?:begin|end)\{[^}]*\}(?:\{[^}]*\})?',' ',s)
        s=s.replace(r'\\', ' ')
        s=re.sub(r'\\[A-Za-z@]+\*?',' ',s)
        return len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*",s))
    words={str(p.relative_to(ROOT)):prose_words(p.read_text()) for p in sorted(ROOT.glob('chapters/03-*.tex'))}
    result=dict(scope='Offline source and archived measurement audit; no new GPU experiment.',
                datasets=datasets, E1=dict(valid_points=len(points),failures=len(failures),
                    reconstructed_call_trace_points=traces, batch=1000, rounds=5,
                    point_counts=[dict(dataset=d,family=f,points=n) for (d,f),n in sorted(point_counts.items())]),
                comparison_registry=registry,
                timing_source='actual CUDA toolkit from nvcc; driver-reported compatibility is not toolkit identity',
                preparation_scope='inspected preparation source and archived dimensions; not byte-level data lineage',
                missing=['complete historical binary, index and exported-vector hashes',
                         'complete retrained frontiers and baseline-training distribution (fixed-point repeats now available)',
                         'arbitrary-subset per-query invariance beyond traced aggregate checks',
                         'new-traffic calibrated-stream timing beyond four replayed fixed pools',
                         'matched cross-system small-batch experiments'],
                prose_word_estimate=dict(total=sum(words.values()),per_file=words,
                    method='prose/captions, excluding math/table bodies/labels/macros; not official course count'),
                inputs=list(inputs.values()))
    out=ROOT/'data/ch3/audit.json'
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(datasets=len(datasets),E1_points=len(points),
                         call_trace_points=traces,claims=len(registry),
                         prose_words=sum(words.values()),hashed_inputs=len(inputs)),indent=2))


if __name__ == '__main__':
    main()
