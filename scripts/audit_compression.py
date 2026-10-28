#!/usr/bin/env python3
"""Verify this editorial round's PDF, assets and optional derived copies; no GPU."""
import argparse
import collections
import hashlib
import json
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from audit_synthesis import prose_count

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    return subprocess.check_output(args, cwd=ROOT, text=True)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-copies', action='store_true')
    args = parser.parse_args()
    inputs = []

    def read(rel):
        b = (ROOT / rel).read_bytes()
        inputs.append(dict(repository=ROOT.name, path=rel, sha256=digest(b)))
        return b

    manifest = json.loads(read('assessment/compression-edits.json'))
    preserved = json.loads(read('data/deduplication/audit.json'))
    assert preserved['chapters_and_abstract']['after'] == manifest['chapters_and_abstract']['after']
    assert preserved['protected_blocks']['proof'] == 12
    for entry in manifest['source_edits']:
        assert digest(read(entry['path'])) == entry['after_sha256']
    words = sum(prose_count(p.read_text()) for p in (ROOT / 'chapters').glob('*.tex'))
    words += prose_count(read('frontmatter/abstract.tex').decode())
    assert words == manifest['chapters_and_abstract']['after']

    assets = run('git', 'ls-tree', '-r', '--name-only', manifest['baseline'], '--',
                 'figures', 'tables', 'zh/tables').splitlines()
    for rel in assets:
        before = subprocess.check_output(['git', 'show', manifest['baseline'] + ':' + rel], cwd=ROOT)
        assert read(rel) == before, ('changed scientific asset', rel)

    pdfs = {}
    for name, pdf in [('main', 'thesis.pdf'), ('main-zh', 'thesis-zh.pdf')]:
        b = read(pdf)
        assert b == (ROOT / 'build' / (name + '.pdf')).read_bytes()
        log = (ROOT / 'build' / (name + '.log')).read_text()
        issues = [s for s in log.splitlines()
                  if re.search(r'Warning|Overfull|Underfull|Missing character|^!', s)]
        assert not issues, (name, issues)
        info = run('pdfinfo', pdf)
        pages = int(re.search(r'^Pages:\s*(\d+)', info, re.M)[1])
        fonts = run('pdffonts', pdf).splitlines()[2:]
        for line in fonts:
            m = re.search(r'\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$', line)
            assert m and m[1] == 'yes' and 'Type 3' not in line, line
        with tempfile.TemporaryDirectory(prefix='comp8800-bbox-') as directory:
            path = Path(directory) / 'bbox.html'
            subprocess.run(['pdftotext', '-bbox-layout', str(ROOT / pdf), str(path)], check=True)
            text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', path.read_text())
            tree = ET.fromstring(text)
            outside = []
            for i, page in enumerate(tree.findall('.//{*}page'), 1):
                w, h = float(page.attrib['width']), float(page.attrib['height'])
                for word in page.findall('.//{*}word'):
                    a = word.attrib
                    if min(float(a['xMin']), float(a['yMin'])) < -0.1 or float(a['xMax']) > w + .1 or float(a['yMax']) > h + .1:
                        outside.append((i, word.text))
            assert not outside, (pdf, outside)
        figures = (ROOT / 'build' / (name + '.lof')).read_text().count('contentsline {figure}')
        tables = (ROOT / 'build' / (name + '.lot')).read_text().count('contentsline {table}')
        assert (figures, tables) == (26, 31)
        pdfs[pdf] = dict(pages=pages, sha256=digest(b), bytes=len(b),
                         figures=figures, tables=tables, fonts=len(fonts),
                         all_fonts_embedded=True, type3_fonts=0, words_outside_page=0)

    toc = (ROOT / 'build/main.toc').read_text()
    chapter = lambda n: int(re.search(r'\\contentsline \{chapter\}\{\\numberline \{' + str(n) + r'\}[^\n]*?\}\{(\d+)\}\{chapter\.', toc)[1])
    bib = int(re.search(r'\\contentsline \{chapter\}\{\\nonumberline Bibliography\}\{(\d+)\}', toc)[1])
    source_pages = run('pdftotext', 'thesis.pdf', '-').split('\f')[:-1]
    destinations = run('pdfinfo', '-dests', 'thesis.pdf')
    front = int(re.search(r'^\s*(\d+)\s+.*"chapter\.1"\s*$', destinations, re.M)[1]) - 1
    end = front + bib - 1
    split = front + chapter(6)
    copies = []
    if args.check_copies:
        for filename, first, last in [('thesis-no-refs.pdf', 1, end),
                                      ('thesis-check-1.pdf', 1, split - 1),
                                      ('thesis-check-2.pdf', split, end)]:
            pages = run('pdftotext', filename, '-').split('\f')[:-1]
            assert len(pages) == last - first + 1, filename
            for offset, text in enumerate(pages):
                chars = lambda s: collections.Counter(re.sub(r'\s+', '', s))
                assert chars(text) == chars(source_pages[first - 1 + offset]), (filename, offset)
            copies.append(dict(path=filename, pages=len(pages),
                               source_physical_pages=[first, last],
                               sha256=digest((ROOT / filename).read_bytes()),
                               all_nonwhitespace_characters_preserved=True))

    records = json.loads(read('data/submission/ai-use-record.json'))['records']
    assert len(records) == 10 and records[-1]['id'] == 'P10'
    for record in records:
        assert digest(record['prompt'].encode()) == record['prompt_sha256']
        for steering in record.get('steering_messages', []):
            assert digest(steering['prompt'].encode()) == steering['prompt_sha256']
        if 'retained_patch' in record:
            assert digest(read(record['retained_patch'])) == record['retained_patch_sha256']
    assert records[-1]['retained_patch_sha256'] == manifest['round_patch_sha256']
    for rel in ['assessment/compression-review-source.json', 'assessment/compression-review-response.txt',
                'evidence/editorial/03775b7/manifest.json', manifest['patch'],
                'docs/supplementary-evidence.md', 'docs/ai-use-record.md',
                'assessment/adc-revision-response.txt','assessment/adc-revision-source.json',
                'assessment/layout-reflow-2026-10-29.txt',
                'scripts/audit_compression.py']:
        read(rel)
    result = dict(date='2026-10-29', timezone='Australia/Sydney',
                  scope='Editorial compression and offline/PDF checks; no GPU or AI-detector rerun',
                  baseline=manifest['baseline'], source_files=len(manifest['source_edits']),
                  words=dict(before=manifest['chapters_and_abstract']['before'], after=words,
                             removed=manifest['chapters_and_abstract']['before'] - words,
                             scope=manifest['word_count_scope']),
                  english_body_pages=bib - chapter(1), english_front_pages=front, pdfs=pdfs,
                  unchanged_scientific_assets=len(assets), retained_proof_blocks=12,
                  detector_score=None, derived_copies=copies,
                  visual_scope='Contact-sheet overview plus readable changed-page inspections; not full sentence proofreading or student-personal verification',
                  inputs=inputs)
    output = ROOT / 'data/compression/audit.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ['words', 'english_body_pages', 'pdfs', 'unchanged_scientific_assets']}, indent=2))


if __name__ == '__main__':
    main()
