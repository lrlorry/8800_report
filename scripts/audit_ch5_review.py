#!/usr/bin/env python3
"""Recount archived execution paths; reads local records, never runs CUDA."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import re


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path('../JHQ_GPU'))
    args = parser.parse_args()
    root = args.source.resolve()
    inputs, rows, records = [], [], []

    def consume(path):
        inputs.append({'path': str(path.relative_to(root)),
                       'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        return path.read_text()

    for path in sorted((root / 'experiments/comp8800_poster_e1/RAW_RESULTS').glob('jhq_*.json')):
        data = json.loads(consume(path))
        if 'sched_cv' not in data:
            raise ValueError(f'Missing CV in {path}')
        dataset = re.fullmatch(r'jhq_(.+)_np\d+_\d+\.json', path.name).group(1)
        records.append({'path': str(path.relative_to(root)), 'dataset': dataset,
                        'cv': data['sched_cv']})
        for run in data['runs']:
            arm = next(v for v in run['variants'] if v['G'] == -1)
            rows.append({'dataset': dataset, 'nprobe': data['nprobe'],
                         'alpha': run['alpha'], 'batch': run['batch'],
                         'nused': run['nused'], 'scheduled_groups': run['sched_G'],
                         'tie_only': arm['topck_tie_only'],
                         'nontie': arm['topck_nontie'],
                         'final_bit_identical': arm['final_bit_identical']})
    budget = consume(root / 'experiments/adc_v69/RAW/budget_v69.log')
    budget_rows = []
    for block in budget.split('### ')[1:]:
        match = re.search(r'G\(b=(\d+)\) = (\d+), G\(b=(\d+)\) = (\d+)', block)
        if match:
            b_eval, g_eval, b_cal, g_cal = map(int, match.groups())
            budget_rows.append({'configuration': block.splitlines()[0],
                                'evaluation_batch': b_eval, 'evaluation_groups': g_eval,
                                'calibration_batch': b_cal, 'calibration_groups': g_cal})
    for rel in ('cpu/pq_codebook.cpp', 'jhq_v69_probesel/search.cu',
                'jhq_v71_lutgroups/search.cu', 'jhq_v71_lutgroups/search.cuh',
                'examples/demo_jhq_budget_arms_v69.cu',
                'experiments/adc_v69/run_lutgroups_v71.sh', 'CMakeLists.txt'):
        consume(root / rel)
    vogue = [r for r in rows if r['dataset'] == 'vogue-768']
    np128 = [r for r in vogue if r['nprobe'] == 128]
    lut_cells = collections.defaultdict(list)
    lut_configs = set()
    lut_records = 0
    for path in sorted((root / 'experiments/adc_v69/RAW_LUT').glob('v71_*.json')):
        if '_check' in path.name:
            continue
        data = json.loads(consume(path))
        dataset = path.name.split('_', 2)[2].rsplit('_np', 1)[0]
        arm = next(v for v in data['runs'][0]['variants'] if v['G'] == -1)
        lut_cells[dataset, data['nprobe']].append(arm['recall'])
        lut_configs.add((data['M'], data['k'], data['runs'][0]['ck']))
        lut_records += 1
    result = {
        'scope': 'Offline audit of archived records; no new GPU execution or binary inspection.',
        'inputs': inputs,
        'e1': {'cv_records': len(records),
               'cv_at_least_0_3': [r for r in records if r['cv'] >= 0.3],
               'run_alpha_cells': len(rows),
               'path_counts': {d: dict(collections.Counter(r['scheduled_groups'] for r in rows if r['dataset'] == d))
                               for d in sorted({r['dataset'] for r in rows})},
               'vogue_tie_only_range': [min(r['tie_only'] for r in vogue), max(r['tie_only'] for r in vogue)],
               'vogue_np128_tie_only_range': [min(r['tie_only'] for r in np128), max(r['tie_only'] for r in np128)],
               'all_nontie_zero': all(r['nontie'] == 0 for r in rows),
               'all_final_bit_identical': all(r['final_bit_identical'] == r['nused'] for r in rows),
               'rows': rows},
        'budget': {'rows': budget_rows,
                   'evaluation_paths': dict(collections.Counter(r['evaluation_groups'] for r in budget_rows)),
                   'calibration_paths': dict(collections.Counter(r['calibration_groups'] for r in budget_rows)),
                   'different_paths': sum(r['evaluation_groups'] != r['calibration_groups'] for r in budget_rows)},
        'lut_sweep': {'records': lut_records, 'cells': len(lut_cells),
                      'M_k_c_configurations': sorted(lut_configs),
                      'max_recall_spread': max(max(v)-min(v) for v in lut_cells.values()),
                      'per_candidate_score_or_tie_audit': 'Not supplied by these recall records.'},
        'table_footprints': {'candidate_capacity': 2048,
                             'configuration': 'alpha=100, k=10, threads=512 or 1024, cap multiplier=1',
                             'device_limit_basis': 'Published CC12.0 architectural limit 99 KiB; not a fresh device query.',
                             'cases': [{'M': m, 'groups': g, 'table_bytes': 4*m*g*2**(8//g),
                                        'query_centric_bytes': 8*2048+8+4*m*g*2**(8//g),
                                        'grouped_bytes': 8*2048+24+4*m*g*2**(8//g)}
                                       for m in (96, 128, 192, 384) for g in (1, 2, 4, 8)]}}
    out = Path(__file__).resolve().parents[1] / 'data/ch5/review-audit.json'
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({k: v for k, v in result['e1'].items() if k not in ('rows', 'cv_at_least_0_3')}, indent=2))
    print('Budget:', {k: v for k, v in result['budget'].items() if k != 'rows'})
    print('Saved', out)


if __name__ == '__main__':
    main()
