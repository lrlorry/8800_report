#!/usr/bin/env python3
"""Check thesis consolidation against its pre-edit commit; no GPU or network.

Protected proofs, displayed mathematics, figures, tables and labels must
remain intact. This is a preservation check, not an automatic judgement
that two prose passages have the same meaning; see the editorial record.
"""
import argparse
import collections
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from audit_synthesis import prose_count

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = 'e610272e50db0d416d92b41d19b8dbfa40c00baa'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', default=DEFAULT_BASE)
    args = parser.parse_args()
    git = lambda *a: subprocess.check_output(['git', *a], cwd=ROOT)
    baseline = git('rev-parse', args.baseline + '^{commit}').decode().strip()
    entries = []

    def current(rel):
        b = (ROOT / rel).read_bytes()
        entries.append(dict(repository=ROOT.name, path=rel,
                            sha256=hashlib.sha256(b).hexdigest()))
        return b

    def old(rel):
        return git('show', baseline + ':' + rel)

    protected = collections.Counter()
    envs = ['equation', 'align', 'lemma', 'proposition', 'proof',
            'corollary', 'definition', 'figure', 'table', 'minipage']
    labels_pattern = r'\\label(?:\[[^]]*\])?\{([^}]+)\}'
    checked = []
    citations_before, citations_after = set(), set()
    for folder in ['chapters', 'zh/chapters']:
        for p in sorted((ROOT / folder).glob('*.tex')):
            rel = str(p.relative_to(ROOT))
            a, b = old(rel).decode(), current(rel).decode()
            for env in envs:
                pat = r'\\begin\{' + env + r'\*?\}[\s\S]*?\\end\{' + env + r'\*?\}'
                before, after = re.findall(pat, a), re.findall(pat, b)
                assert before == after, (rel, env)
                protected[env] += len(before)
            assert re.findall(labels_pattern, a) == re.findall(labels_pattern, b), rel
            for text, keys in [(a, citations_before), (b, citations_after)]:
                for group in re.findall(r'\\(?:cite|citep|citet)\{([^}]+)\}', text):
                    keys.update(k.strip() for k in group.split(','))
            checked.append(rel)
    assert citations_before == citations_after, ('changed cited-source set', citations_before ^ citations_after)

    assets = git('ls-tree', '-r', '--name-only', baseline, '--',
                 'figures', 'tables', 'zh/tables').decode().splitlines()
    for rel in assets:
        assert current(rel) == old(rel), ('changed scientific figure/table asset', rel)
    for rel in ['frontmatter/abstract.tex', 'zh/abstract.tex',
                'appendices/b-supplementary.tex', 'zh/appendices/b-supplementary.tex']:
        assert current(rel) == old(rel), ('changed retained material', rel)

    word_rows = []
    for chapter in range(1, 10):
        names = sorted(str(p.relative_to(ROOT)) for p in
                       (ROOT / 'chapters').glob(f'{chapter:02}-*.tex'))
        before = sum(prose_count(old(n).decode()) for n in names)
        after = sum(prose_count((ROOT / n).read_text()) for n in names)
        word_rows.append(dict(chapter=chapter, before=before, after=after,
                              removed=before-after))
    abstract = prose_count((ROOT / 'frontmatter/abstract.tex').read_text())

    for rel in ['scripts/audit_deduplication.py', 'scripts/audit_synthesis.py',
                'assessment/deduplication-rounds.md', 'assessment/template-sources.json',
                'FORMAT_NOTES.txt', 'main.tex', 'main-zh.tex',
                'config/layout.tex', 'config/preamble.tex', 'zh/preamble.tex']:
        current(rel)
    result = dict(
        baseline=baseline,
        scope='Three bilingual rounds of prose consolidation; preserved unique evidence and protected blocks; no GPU run.',
        editorial_review='assessment/deduplication-rounds.md; semantic retention is a human/source review, not inferred from word counts',
        checked_chapter_files=checked,
        protected_blocks=dict(protected),
        identical_figure_and_table_assets=len(assets),
        retained_citation_keys=sorted(citations_after),
        chapter_words=word_rows,
        chapters_and_abstract=dict(before=sum(r['before'] for r in word_rows)+abstract,
                                   after=sum(r['after'] for r in word_rows)+abstract),
        word_count_scope='Prose and captions; table bodies and displayed/inline mathematics excluded; not an official course count',
        inputs=entries,
    )
    out = ROOT / 'data/deduplication/audit.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in
                      ['protected_blocks', 'identical_figure_and_table_assets',
                       'chapters_and_abstract']}, indent=2))


if __name__ == '__main__':
    main()
