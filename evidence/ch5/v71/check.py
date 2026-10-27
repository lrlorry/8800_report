#!/usr/bin/env python3
"""Verify this review bundle and recount LUT results using only Python's stdlib."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
from statistics import median


def main():
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / 'manifest.json').read_text())
    for item in manifest['files']:
        path = root / item['bundle_path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError(f'Hash mismatch: {path}')
    cells = defaultdict(dict)
    for path in sorted((root / 'raw').glob('v71_*.json')):
        match = re.fullmatch(r'v71_g([1248])_(.+)_np(\d+)\.json', path.name)
        if not match:  # gate-check records are separate from timed results
            continue
        data = json.loads(path.read_text())
        run = data['runs'][0]
        arm = next(v for v in run['variants'] if v['G'] == -1)
        if len(arm['qps']) != 5 or run['alpha'] != 100 or run['ck'] != 1000:
            raise ValueError(f'Unexpected timing protocol in {path}')
        cells[match[2], int(match[3])][int(match[1])] = {
            'qps': median(arm['qps']), 'recall': arm['recall']}
    if len(cells) != 24 or any(set(v) != {1, 2, 4, 8} for v in cells.values()):
        raise ValueError('Incomplete table sweep')
    wins = Counter(max(arms, key=lambda g: arms[g]['qps']) for arms in cells.values())
    ratios = [arms[2]['qps'] / arms[1]['qps'] for arms in cells.values()]
    spread = max(max(a['recall'] for a in arms.values()) -
                 min(a['recall'] for a in arms.values()) for arms in cells.values())
    print(json.dumps({'verified_files': len(manifest['files']),
                      'recorded_run_head': manifest['recorded_run_head'],
                      'timed_cells': len(cells), 'wins': dict(sorted(wins.items())),
                      'two_vs_one_ratio_range': [min(ratios), max(ratios)],
                      'max_recall_spread': spread,
                      'gpu_executed': False}, indent=2))


if __name__ == '__main__':
    main()
