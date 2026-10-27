#!/usr/bin/env python3
"""Recompute Chapter 4 review evidence offline; never runs CUDA."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / 'JHQ_GPU'


def main():
    ledger = {}

    def read(path):
        data = (SRC / path).read_bytes()
        ledger[path] = hashlib.sha256(data).hexdigest()
        return data.decode()

    pilot = json.loads(read('experiments/residual_aware_bound/BOUND_VALIDATION.json'))
    summaries = []
    for name, row in sorted(pilot.items()):
        raw = json.loads(read(f'experiments/residual_aware_bound/raw/{name}_summary.json'))
        assert raw['audit'] == row['audit']
        assert all(raw[k] == v for k, v in row['shape'].items())
        assert row['validation_cpp']['violations_cond'] == 0
        assert row['validation_cpp']['violations_glob'] == 0
        assert row['validation_cpp']['candidates'] == row['validation_py']['candidates']
        assert all(row['audit'][k] == 0 for k in [
            'separability_mismatches', 'level_mismatches', 'residual_unsorted_pairs'])
        summaries.append(dict(workload=name, shape=row['shape'], audit=row['audit'],
                              bound_checks=row['validation_cpp']['candidates']))

    read('experiments/residual_aware_bound/RESIDUAL_BOUND_PILOT_REPORT.md')
    read('experiments/residual_aware_bound/run_pilot.sh')
    read('examples/demo_jhq_v66_bound_pilot.cu')
    correspondence = {}
    for filename in ['encode.cu', 'train_pq_gpu.cu', 'train_res_gpu.cu', 'jhq_gpu_index.cu']:
        a = read(f'jhq_v66_boundpilot/{filename}').replace('jhq_v66_boundpilot', 'JHQ_VERSION')
        b = read(f'jhq_v69_probesel/{filename}').replace('jhq_v69_probesel', 'JHQ_VERSION')
        if filename == 'jhq_gpu_index.cu':
            start = a.index('void JHQGpuIndex::export_host_state(')
            stop = a.index('void JHQGpuIndex::calibrate_schedule(', start)
            a = a[:start] + a[stop:]
        assert a == b, filename
        correspondence[filename] = 'identical after namespace normalization and removal of pilot export only'

    read('results/sensitivity/residual_training/REPORT.md')
    sweep = read('results/sensitivity/residual_training/sweep_table.txt')
    cells = {}
    for ln in sweep.splitlines()[1:]:
        fields = ln.split()
        if len(fields) != 7 or fields[0] not in ['o3072', 'vogue']:
            continue
        ds, br, n, probes, recall, qps, ms = fields
        cells.setdefault((ds, int(br), int(probes)), {})[n] = float(recall)
    assert len(cells) == 12
    deltas = [c['100000'] - c[str(max(map(int, c)))] for c in cells.values()]
    assert abs(max(abs(d) for d in deltas) - .0018) < 1e-10
    assert sum(d < 0 for d in deltas) == 11
    assert sum(d == 0 for d in deltas) == 1
    read('results/v34_lloyd_iterations/README.md')
    lloyd = {}
    for line in read('results/v34_lloyd_iterations/v34cap.log').splitlines():
        match = re.match(r'(vogue|bge|stella)\s+cap=(\d+)\s+recall=([\d.]+)\s+train=([\d.]+)', line)
        if match:
            ds, cap, recall, ms = match.groups()
            lloyd.setdefault(ds, {})[int(cap)] = dict(recall=float(recall), train_ms=float(ms))
    assert len(lloyd) == 3 and all(len(c) == 10 for c in lloyd.values())
    assert [lloyd[d][2000]['recall'] for d in ['vogue', 'bge', 'stella']] == [.9846, .9585, .9915]
    read('results/v34_lloyd_iterations/v34.log')
    read('results/frontier_v39/WHY_RECALL_MOVED.md')
    read('results/ivf_assign_bound/README.md')
    read('results/v46_sigma/README.md')
    read('results/v46_sigma/v46.log')
    read('results/v46_sigma/v46_cached.log')
    read('CMakeLists.txt')
    read('experiments/comp8800_poster_e1/bench_cuvs.py')
    large_int8 = []
    for name in ['cuvs_stella_cagra-int8.jsonl', 'cuvs_stella_cagra-int8_gd64.jsonl']:
        for ln in read('experiments/adc_v69/RAW_BIG/' + name).splitlines():
            x = json.loads(ln)
            if x.get('type') == 'index':
                large_int8.append({k: x[k] for k in ['graph_degree', 'index_mib', 'build_s', 'quantise_dataset_s']})
    phase_bytes = {}
    for ds, n in [('bge-m3', 10091524), ('stella', 17776615)]:
        m, br = 128, 1024
        phase_bytes[ds] = dict(N=n, row_payload_gib=n*(br+m+8)/2**30,
                              one_pass_ten_arrays_gib=n*(2*br+3*m+20)/2**30,
                              two_pass_repack_arrays_gib=n*(br+2*m+8)/2**30,
                              actual_process_peak='unmeasured; pipeline/model/allocator costs excluded')
    audit = dict(date='2026-10-28', scope='offline re-analysis of existing records, no new GPU experiment',
                 pilot=summaries, total_bound_candidate_checks=sum(x['bound_checks'] for x in summaries),
                 total_query_instances=sum(x['shape']['n_queries'] for x in summaries),
                 gpu_returned_score_comparison_slots=sum(x['shape']['n_queries']*10 for x in summaries),
                 gpu_returned_score_scope='top-10 per query only; missing IDs are skipped by the historical harness',
                 correspondence=correspondence,
                 residual_sampling=dict(cells=len(cells), max_abs_recall_delta=max(abs(d) for d in deltas),
                                        below_all=sum(d < 0 for d in deltas),
                                        equal_all=sum(d == 0 for d in deltas),
                                        scope='historical two-dataset, Br=4/8, 25 Lloyd iterations'),
                 lloyd_iteration_diagnostic=lloyd,
                 phase_arrays=phase_bytes, stella_cagra_int8=large_int8,
                 inputs=[dict(path=k, sha256=v) for k, v in sorted(ledger.items())])
    path = ROOT / 'data/ch4/review-audit.json'
    path.write_text(json.dumps(audit, indent=2) + '\n')
    manifest_path = ROOT / 'data/ch4/audit.json'
    manifest = json.loads(manifest_path.read_text())
    manifest['scope'] = ('Offline source/record audit, incorporating the archived representation pilot; '
                         'no new GPU run or implementation edit.')
    inputs = {(x['source'], x['path']): x for x in manifest['inputs']}
    for name, sha in ledger.items():
        inputs['JHQ_GPU', name] = dict(source='JHQ_GPU', path=name, sha256=sha)
    report_inputs = ['data/ch4/review-audit.json', 'scripts/audit_ch4_review.py',
                 'scripts/build_ch7.py', 'scripts/build_zh_tables.py',
                 'assessment/ch4-review-response.txt', 'assessment/ch7-pending-experiments.txt',
                 'chapters/07-evaluation.tex', 'zh/chapters/07-evaluation.tex',
                 'tables/ch7/e1_memory.tex', 'zh/tables/e1_memory.tex', 'references.bib']
    for pattern in ['chapters/04-*.tex', 'zh/chapters/04-*.tex', 'figures/ch4/*.tex']:
        report_inputs.extend(str(p.relative_to(ROOT)) for p in sorted(ROOT.glob(pattern)))
    for name in report_inputs:
        inputs['8800_report', name] = dict(source='8800_report', path=name, sha256='')
    for (source, name), item in inputs.items():
        if source in ['JHQ_GPU', '8800_report']:
            root = SRC if source == 'JHQ_GPU' else ROOT
            item['sha256'] = hashlib.sha256((root / name).read_bytes()).hexdigest()
    manifest['inputs'] = sorted(inputs.values(), key=lambda x: (x['source'], x['path']))
    for row in manifest['payload_by_dimension']:
        row['sq8_vector_bytes'] = row['dimension']
        row['cagra_int8_vector_graph32_bytes'] = row['dimension'] + 128
    manifest['representation_reference'] = dict(
        C0_FP64_geometry='stored-matrix FP64 orthogonality and sampled norms checked on four datasets; actual GPU rotation-error dump not measured',
        C1_codebook_and_all_row_correction='archived pilot completed on three databases; see review-audit.json',
        C1_original_input_reencoding='sampled raw-input FP64 recoding on four datasets; TF32 discrepancies quantified; see data/supplement/audit.json',
        C1_independent_full_permutation_audit='four all-row offsets/ID audits and three ID-joined build comparisons; centroid membership not exported')
    manifest['supplementary_evidence'] = 'data/supplement/audit.json'
    manifest['review_audit'] = 'data/ch4/review-audit.json'
    manifest['phase_arrays'] = phase_bytes
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k:audit[k] for k in ['total_bound_candidate_checks', 'total_query_instances',
                                         'gpu_returned_score_comparison_slots', 'residual_sampling',
                                         'phase_arrays', 'stella_cagra_int8']}, indent=2))
    print(f'Hashed {len(ledger)} inputs; normalized v66/v69 construction sources agree.')


if __name__ == '__main__':
    main()
