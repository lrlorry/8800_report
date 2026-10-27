#!/usr/bin/env python3
"""Build the appendix's exact E1 configuration registry from archived records."""
import collections
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / 'JHQ_GPU/experiments/comp8800_poster_e1/E1_points.csv'
DATASETS = ['vogue-768', 'arxiv-768', 'openai3-1536', 'openai3-3072']
NAMES = ['Vogue', 'arXiv', 'OpenAI-1536', 'OpenAI-3072']
FAMILIES = ['JHQ-GPU v69', 'CAGRA fp32', 'CAGRA int8', 'IVF-RaBitQ', 'IVF-PQ', 'GPU brute force']
raw = SRC.read_bytes()
rows = list(csv.DictReader(raw.decode().splitlines()))
assert len(rows) == 1590
out = ROOT / 'data/appendix'
out.mkdir(parents=True, exist_ok=True)
with (out / 'e1-configurations.csv').open('w', newline='') as f:
    fields = ['record', 'dataset', 'family', 'params', 'recall', 'qps_A', 'source']
    w = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
    w.writeheader()
    for i, row in enumerate(rows, 1):
        json.loads(row['params'])
        assert float(row['qps_A']) > 0 and 0 <= float(row['recall']) <= 1
        w.writerow(dict(record=i, **{key: row[key] for key in fields if key != 'record'}))
counts = collections.Counter((r['family'], r['dataset']) for r in rows)
for zh in (False, True):
    folder = ROOT / ('zh/tables/appendix' if zh else 'tables/appendix')
    folder.mkdir(parents=True, exist_ok=True)
    lines = [r'\begin{tabular}{@{}lrrrrr@{}}', r'\toprule',
             ('方法' if zh else 'Family') + ' & ' + ' & '.join(NAMES) +
             (' & 总计' if zh else ' & Total') + r' \\', r'\midrule']
    for fam in FAMILIES:
        nums = [counts[fam, ds] for ds in DATASETS]
        lines.append(fam + ' & ' + ' & '.join(map(str, nums+[sum(nums)])) + r' \\')
    nums = [sum(counts[fam, ds] for fam in FAMILIES) for ds in DATASETS]
    lines += [r'\midrule', ('总计' if zh else 'Total') + ' & ' +
              ' & '.join(map(str, nums+[sum(nums)])) + r' \\', r'\bottomrule', r'\end{tabular}']
    (folder / 'e1-counts.tex').write_text('\n'.join(lines)+'\n')
report = dict(points=len(rows), families={fam:sum(counts[fam, ds] for ds in DATASETS) for fam in FAMILIES},
              source=dict(repository='JHQ_GPU', path=str(SRC.relative_to(ROOT.parent/'JHQ_GPU')),
                          sha256=hashlib.sha256(raw).hexdigest()),
              source_registry='data/appendix/e1-configurations.csv',
              scope='Exact observed parameter tuples, not a Cartesian product or a GPU rerun')
(out / 'audit.json').write_text(json.dumps(report, indent=2)+'\n')
print(f'Appendix: {len(rows)} exact E1 records; bilingual coverage table generated.')
