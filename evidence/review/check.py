#!/usr/bin/env python3
"""Verify archived input hashes; optionally rerun the two offline audits."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run-audits', action='store_true')
    args = ap.parse_args()
    manifest = json.loads((HERE/'manifest.json').read_text())
    paths = set()
    for row in manifest['files']:
        rel = Path(row['archived_path'])
        assert not rel.is_absolute() and '..' not in rel.parts
        assert str(rel) not in paths
        paths.add(str(rel))
        actual = hashlib.sha256((HERE/rel).read_bytes()).hexdigest()
        assert actual == row['sha256'], str(rel)
    print(f"Verified {len(paths)} archived source/record hashes.", flush=True)
    if args.run_audits:
        for script, options in [('audit_t4_t5.py', ['--no-plot']),
                                ('audit_full_review.py', [])]:
            subprocess.run([sys.executable, str(ROOT/'scripts'/script),
                            '--source', str(HERE/'JHQ_GPU'), *options],
                           cwd=ROOT, check=True)
        print('Both offline audits completed using the bundled inputs.')


if __name__ == '__main__':
    main()
