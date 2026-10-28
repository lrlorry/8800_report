#!/usr/bin/env python3
"""Check thesis consolidation against its pre-edit commit; no GPU or network.

Proofs and unique displayed mathematics remain intact. Explicit duplicate
equation/display removals are checked against archived originals. Numeric assets remain unchanged;
one explicitly archived PDF font export is permitted. This is not an
automatic judgement of prose.
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

    # Validate this round separately; restore its pinned before-images for
    # the older exact-edit checks, whose historical scope stays unchanged.
    compression = json.loads(current('assessment/compression-edits.json'))
    assert compression['baseline'] == '03775b765ce0fbbc378f55a98cfa48669b9a223e'
    pre_compression = {}
    for edit in compression['source_edits']:
        rel = edit['path']
        assert (rel.startswith(('chapters/', 'zh/chapters/')) and rel.endswith('.tex')) or rel in [
            'frontmatter/abstract.tex', 'zh/abstract.tex', 'frontmatter/declaration.tex', 'zh/declaration.tex',
            'frontmatter/acknowledgements.tex', 'zh/acknowledgements.tex', 'main.tex', 'main-zh.tex',
            'config/layout.tex', 'config/preamble.tex', 'zh/preamble.tex']
        before = git('show', compression['baseline'] + ':' + rel)
        after = current(rel)
        assert hashlib.sha256(before).hexdigest() == edit['before_sha256']
        assert hashlib.sha256(after).hexdigest() == edit['after_sha256'], ('unrecorded compression edit', rel)
        pre_compression[rel] = before.decode()
    patch = current(compression['patch'])
    assert hashlib.sha256(patch).hexdigest() == compression['patch_sha256']
    subprocess.run(['git', 'apply', '--check', '--reverse', compression['patch']],
                   cwd=ROOT, check=True, capture_output=True)
    # The proof-layout round may add only transparent containers to chapters.
    wrappers = compression['formatting_only_wrappers']
    assert wrappers['baseline'] == 'cc696f2f98f29ebe794d930f08d2d5ab4add994e'
    assert wrappers['environment'] == 'resultblock' and len(wrappers['source_files']) == 6
    wrapper_count = 0
    for rel in wrappers['source_files']:
        actual = current(rel).decode()
        wrapper_count += actual.count('\\begin{resultblock}')
        stripped = actual.replace('\\begin{resultblock}\n', '').replace('\n\\end{resultblock}', '')
        assert stripped == git('show', wrappers['baseline'] + ':' + rel).decode(), rel
    assert wrapper_count == wrappers['statement_proof_pairs'] == 8
    new_curation = json.loads(current('evidence/editorial/03775b7/manifest.json'))
    assert new_curation['baseline'] == compression['baseline']
    assert len(new_curation['entries']) == 6
    new_blocks = collections.defaultdict(list)
    new_ref_map = {}
    for entry in new_curation['entries']:
        data = current(entry['archive'])
        assert hashlib.sha256(data).hexdigest() == entry['sha256']
        block = data.decode().removesuffix('\n')
        assert pre_compression[entry['source']].count(block) == 1
        new_blocks[entry['source']].append(block)
        new_ref_map[entry['label']] = entry['replacement_reference']
    assert set(new_ref_map) == {'tab:4-lifetimes', 'eq:7-agreement', 'eq:7-payback'}
    for lang in ['en', 'zh']:
        assert {e['label'] for e in new_curation['entries'] if e['language'] == lang} == set(new_ref_map)

    def remap_new_refs(s):
        def replace(m):
            return m[1] + ','.join(new_ref_map.get(k, k) for k in m[2].split(',')) + '}'
        return re.sub(r'(\\(?:[Cc]ref|[Ee]qref|ref)\{)([^}]+)\}', replace, s)

    additions = collections.defaultdict(list)
    for item in compression.get('approved_additions', []):
        assert item['source'] in ['chapters/08-1-insights.tex', 'zh/chapters/08-1-insights.tex']
        block = current(item['archive'])
        assert hashlib.sha256(block).hexdigest() == item['sha256']
        block = block.decode().removesuffix('\n')
        assert (ROOT / item['source']).read_text().count(block) == 1
        assert '\\label{eq:8-refinement-sensitivity}' in block
        additions[item['source']].append(block)
    assert sum(map(len, additions.values())) == 2

    # The unreferenced roadmap is editorial navigation, not scientific content.
    # Permit only its two exact, archived language versions to lose a label.
    section_removals = collections.defaultdict(list)
    for item in compression.get('approved_section_removals', []):
        assert item['source'] in ['chapters/01-introduction.tex', 'zh/chapters/01-introduction.tex']
        block = current(item['archive'])
        assert hashlib.sha256(block).hexdigest() == item['sha256']
        block = block.decode().removesuffix('\n')
        assert pre_compression[item['source']].count(block) == 1
        assert re.findall(r'\\label\{([^}]+)\}', block) == ['sec:1-6']
        assert not re.search(r'\\(?:cite|input|begin|includegraphics)\b', block)
        section_removals[item['source']].append(block)
    assert sum(map(len, section_removals.values())) == 2

    final_review = json.loads(current('assessment/final-review-edits.json'))
    assert final_review['baseline'] == '682ef939ee41e3a9b9c9ec984604c62008406744'
    # Explicitly recorded prose/source replacements; scientific blocks below
    # are still checked independently against the original baseline.
    expected_sources = {}
    for edit in final_review['source_edits']:
        rel = edit['path']
        expected = expected_sources.get(rel)
        if expected is None:
            expected = git('show', final_review['baseline'] + ':' + rel).decode()
        assert expected.count(edit['before']) == 1, ('invalid declared edit', rel)
        expected_sources[rel] = expected.replace(edit['before'], edit['after'])
    for rel, expected in expected_sources.items():
        candidate = pre_compression.get(rel, (ROOT / rel).read_text())
        assert candidate == expected, ('undeclared final-review edit', rel)

    manifest_path = 'evidence/editorial/86bf0f0/manifest.json'
    curation = json.loads(current(manifest_path))
    assert curation['baseline'] == '86bf0f0c2b048f2ec6ebb44634ffc7165b1a9f90'
    assert len(curation['entries']) == 26
    expected_labels = {
        'tab:3-ledger', 'tab:3-evidence', 'tab:4-lloyd', 'tab:4-pilot',
        'tab:5-evaluation-settings', 'tab:6-scope', 'tab:7-manifest',
        'tab:7-e1-paths', 'tab:7-fixed-budget', 'fig:7-budget-payback',
        'tab:7-build-repeat', 'tab:7-rq-answers', 'tab:7-budget-tails',
    }
    for language in ['en', 'zh']:
        selected = [e for e in curation['entries'] if e['language'] == language]
        assert len(selected) == 13 and {e['label'] for e in selected} == expected_labels
    by_source = collections.defaultdict(list)
    ref_map = {}
    for entry in curation['entries']:
        data = current(entry['archive'])
        assert hashlib.sha256(data).hexdigest() == entry['sha256']
        block = data.decode().removesuffix('\n')
        archived_source = git('show', curation['baseline'] + ':' + entry['source']).decode()
        assert archived_source.count(block) == 1, ('archive differs from curation baseline', entry)
        assert old(entry['source']).decode().count(block) == 1, ('archive differs from original baseline', entry)
        assert '\\label{' + entry['label'] + '}' in block
        assert '\\label{' + entry['label'] + '}' not in (ROOT / entry['source']).read_text()
        for item in entry['inputs']:
            assert hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256']
        by_source[entry['source']].append(block)
        ref_map[entry['label']] = entry['replacement_reference']

    def remap_refs(s):
        def replace(m):
            return m[1] + ','.join(ref_map.get(k, k) for k in m[2].split(',')) + '}'
        return re.sub(r'(\\(?:[Cc]ref|[Ee]qref|ref)\{)([^}]+)\}', replace, s)

    # The retained memory figure's caption now points to the immediately
    # preceding construction measurements instead of the relocated table.
    caption_edits = {
        'chapters/07-evaluation.tex': (
            'Separate construction samples are in\n\\cref{sec:7-7}; these resident markers are not peaks.',
            'The preceding construction measurements give sampled peaks; these\nresident markers are not peaks.'),
        'zh/chapters/07-evaluation.tex': (
            '另行构建采样见\\cref{sec:7-7}，这里的常驻标记不是峰值。',
            '前文构建测量另报采样峰值，这里的常驻标记不是峰值。'),
    }

    protected = collections.Counter()
    envs = ['equation', 'align', 'lemma', 'proposition', 'proof',
            'corollary', 'definition', 'figure', 'table', 'minipage']
    labels_pattern = r'\\label(?:\[[^]]*\])?\{([^}]+)\}'
    checked = []
    citations_before, citations_after = set(), set()
    for folder in ['chapters', 'zh/chapters']:
        for p in sorted((ROOT / folder).glob('*.tex')):
            rel = str(p.relative_to(ROOT))
            a, actual = old(rel).decode(), current(rel).decode()
            if rel not in pre_compression:
                assert actual == git('show', compression['baseline'] + ':' + rel).decode(), ('undeclared compression source', rel)
            b = pre_compression.get(rel, actual)
            for block in by_source[rel]:
                a = a.replace(block, '')
            a = remap_refs(a)
            if rel in caption_edits:
                before, after = caption_edits[rel]
                assert a.count(before) == 1 and b.count(after) == 1
                a = a.replace(before, after)
            for env in envs:
                pat = r'\\begin\{' + env + r'\*?\}[\s\S]*?\\end\{' + env + r'\*?\}'
                before, after = re.findall(pat, a), re.findall(pat, b)
                assert before == after, (rel, env)
            assert re.findall(labels_pattern, a) == re.findall(labels_pattern, b), rel
            # Further changes to protected blocks must match the archived
            # removals and reference substitutions, leaving proofs intact.
            restored = b
            for block in new_blocks[rel]:
                restored = restored.replace(block, '')
            restored = remap_new_refs(restored)
            for block in section_removals[rel]:
                restored = restored.replace(block, '')
            compared_actual = actual
            for block in additions[rel]:
                compared_actual = compared_actual.replace(block, '')
            for env in envs:
                pat = r'\\begin\{' + env + r'\*?\}[\s\S]*?\\end\{' + env + r'\*?\}'
                expected = re.findall(pat, restored)
                assert expected == re.findall(pat, compared_actual), ('changed retained scientific block', rel, env)
                protected[env] += len(re.findall(pat, actual))
            assert re.findall(labels_pattern, restored) == re.findall(labels_pattern, compared_actual), rel
            for text, keys in [(a, citations_before), (actual, citations_after)]:
                for group in re.findall(r'\\(?:cite|citep|citet)\{([^}]+)\}', text):
                    keys.update(k.strip() for k in group.split(','))
            checked.append(rel)
    relocated = set(compression.get('relocated_body_citations', []))
    assert relocated == {'adc_artifact'}
    assert citations_before - citations_after == relocated
    assert not citations_after - citations_before
    # The ADC source remains cited in the actual acknowledgement disclosure.
    for rel in ['frontmatter/declaration.tex', 'zh/declaration.tex']:
        front_cites = {k.strip() for group in re.findall(r'\\cite\{([^}]+)\}', current(rel).decode())
                       for k in group.split(',')}
        assert relocated <= front_cites
    for folder in ['chapters', 'zh/chapters', 'frontmatter', 'appendices']:
        for p in (ROOT / folder).glob('*.tex'):
            assert not re.search(r'\\(?:[Cc]ref|ref)\{[^}]*sec:1-6[^}]*\}', p.read_text())

    assets = git('ls-tree', '-r', '--name-only', baseline, '--',
                 'figures', 'tables', 'zh/tables').decode().splitlines()
    font_asset = final_review['cosmetic_asset']
    assert font_asset['path'] == 'figures/t4-t5/smallbatch.pdf'
    assert font_asset['numerical_audit_unchanged'] is True
    assert hashlib.sha256((ROOT / 'data/t4-t5/smallbatch-matched.json').read_bytes()).hexdigest() == font_asset['numeric_input_sha256']
    assert current(font_asset['before_archive']) == old(font_asset['path'])
    assert hashlib.sha256(old(font_asset['path'])).hexdigest() == font_asset['before_sha256']
    for rel in assets:
        data = current(rel)
        if rel == font_asset['path']:
            assert hashlib.sha256(data).hexdigest() == font_asset['after_sha256']
        else:
            assert data == old(rel), ('changed scientific figure/table asset', rel)
    for rel in ['frontmatter/abstract.tex', 'zh/abstract.tex',
                'appendices/b-supplementary.tex', 'zh/appendices/b-supplementary.tex']:
        data = current(rel)
        if rel in ['frontmatter/abstract.tex', 'zh/abstract.tex']:
            assert pre_compression[rel].encode() == old(rel)
            continue  # Current abstract is pinned by its declared before/after hashes above.
        suffix = ''
        if rel.endswith('b-supplementary.tex'):
            edits = [e for e in final_review['source_edits'] if e['path'] == rel]
            assert len(edits) == 1 and edits[0]['after'].startswith(edits[0]['before'])
            suffix = edits[0]['after'][len(edits[0]['before']):]
        assert data == old(rel) + suffix.encode(), ('changed retained material', rel)

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
                'assessment/targeted-curation-review.md', 'assessment/targeted-curation-source.json',
                'assessment/final-review-response.txt', 'assessment/submission-manual-actions.txt',
                'assessment/compression-review-response.txt', 'assessment/compression-review-source.json',
                'docs/ai-use-record.md', 'data/submission/ai-use-record.json', 'docs/artifact-access.md',
                'docs/supplementary-evidence.md',
                'FORMAT_NOTES.txt', 'main.tex', 'main-zh.tex',
                'config/layout.tex', 'config/preamble.tex', 'zh/preamble.tex']:
        current(rel)
    result = dict(
        baseline=baseline,
        scope='Prose consolidation, declared display/equation curation and review edits; no GPU run.',
        editorial_review='assessment/deduplication-rounds.md; assessment/targeted-curation-review.md; assessment/compression-review-response.txt; semantic retention requires source review',
        compression_round=dict(baseline=compression['baseline'],source_edits=len(compression['source_edits']),
                               archive_manifest='evidence/editorial/03775b7/manifest.json',
                               removed_tables_per_language=1,removed_duplicate_equations_per_language=2,
                               reference_remapping=new_ref_map),
        display_curation=dict(baseline=curation['baseline'],
                              archived_blocks=len(curation['entries']),
                              removed_tables_per_language=12,
                              removed_figures_per_language=1,
                              archive_manifest=manifest_path,
                              reference_remapping=ref_map,
                              retained_caption_edits=caption_edits),
        checked_chapter_files=checked,
        protected_blocks=dict(protected),
        identical_figure_and_table_assets=len(assets)-1,
        font_only_asset_update=font_asset,
        retained_citation_keys=sorted(citations_after | relocated),
        relocated_body_citations=sorted(relocated),
        removed_editorial_sections=len(compression['approved_section_removals']),
        chapter_words=word_rows,
        chapters_and_abstract=dict(before=sum(r['before'] for r in word_rows)+prose_count(old('frontmatter/abstract.tex').decode()),
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
