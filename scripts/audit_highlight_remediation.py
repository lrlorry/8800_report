#!/usr/bin/env python3
"""Check the declared highlight-block edit round and its preserved science."""
import collections
import hashlib
import itertools
import json
import re
import subprocess
from pathlib import Path

from audit_synthesis import prose_count

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = 'assessment/highlight-remediation-edits.json'


def validate_highlight_round(read):
    """Return exact pre-round sources, after validating every current edit."""
    manifest = json.loads(read(MANIFEST))
    assert manifest['baseline'] == '9613db1d6727d0518b9e2ae75a9449d3a59b08db'
    assert manifest['new_detector_result'] is None
    entries = manifest['entries']
    assert len(entries) == 60
    allowed = set(manifest['approved_formalisation_ids'])
    assert allowed == {'H09', 'H18', 'H19', 'H20'}
    environments = ['equation', 'align', 'lemma', 'proposition', 'proof',
                    'corollary', 'definition', 'figure', 'table', 'tabular',
                    'tabularx', 'longtable', 'minipage']
    labels = r'\\label(?:\[[^]]*\])?\{([^}]+)\}'
    protected = collections.Counter()
    originals = {}
    for lang in ['en', 'zh']:
        assert {e['id'] for e in entries if e['language'] == lang} == {
            f'H{i:02}' for i in range(1, 31)}
    for file in manifest['files']:
        rel = file['path']
        baseline = subprocess.check_output(
            ['git', 'show', manifest['baseline'] + ':' + rel], cwd=ROOT)
        before = read(file['before_archive'])
        assert before == baseline
        assert hashlib.sha256(before).hexdigest() == file['before_sha256']
        source = before.decode()
        edits = [e for e in entries if e['path'] == rel]
        for edit in edits:
            assert source.count(edit['before']) == 1, (rel, edit['id'])
            source = source.replace(edit['before'], edit['after'])
        actual = read(rel)
        assert actual == source.encode(), ('undeclared edit', rel)
        assert hashlib.sha256(actual).hexdigest() == file['after_sha256']
        # Revert only the four named mathematical transformations. Everything
        # else, including the original theorem assumptions, remains exact.
        canonical = source
        for edit in reversed(edits):
            if edit['id'] in allowed:
                assert canonical.count(edit['after']) == 1
                canonical = canonical.replace(edit['after'], edit['before'])
        for env in environments:
            pat = r'\\begin\{' + env + r'\*?\}[\s\S]*?\\end\{' + env + r'\*?\}'
            expected = re.findall(pat, before.decode())
            assert expected == re.findall(pat, canonical), (rel, env)
            protected[env] += len(expected)
        assert re.findall(labels, before.decode()) == re.findall(labels, canonical), rel
        originals[rel] = before.decode()
    # The two new identities are checked on every triple of 2-element sets
    # in a six-element universe. This is a finite sanity check, not a proof.
    sets = [set(x) for x in itertools.combinations(range(6), 2)]
    checks = 0
    for output, reference, truth in itertools.product(sets, repeat=3):
        missing = 2 - len(output & reference)
        assert 2 * missing == len(output ^ reference)
        assert len(output & truth) >= len(reference & truth) - missing
        checks += 1
    words = sum(prose_count(p.read_text()) for p in (ROOT / 'chapters').glob('*.tex'))
    words += prose_count(read('frontmatter/abstract.tex').decode())
    assert words == manifest['counts']['chapters_abstract_before'] - (
        manifest['counts']['targeted_english_before'] - manifest['counts']['targeted_english_after'])
    result = dict(baseline=manifest['baseline'], blocks=60, source_files=len(originals),
                  protected_before_counts=dict(protected), finite_set_checks=checks,
                  chapters_abstract_before=manifest['counts']['chapters_abstract_before'],
                  chapters_abstract_after=words, new_detector_result=None,
                  scope='Exact edit and preservation checks; finite sanity checks supplement the written arguments; no GPU or detector rerun')
    return originals, result


def main():
    inputs = []

    def read(rel):
        data = (ROOT / rel).read_bytes()
        inputs.append(dict(repository=ROOT.name, path=rel,
                           sha256=hashlib.sha256(data).hexdigest()))
        return data

    _, result = validate_highlight_round(read)
    read('scripts/audit_highlight_remediation.py')
    result['inputs'] = inputs
    target = ROOT / 'data/highlight-remediation/audit.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'inputs'}, indent=2))


if __name__ == '__main__':
    main()
