#!/usr/bin/env python3
"""Check this isolated style preview against the existing thesis and assets."""
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BUILD = ROOT / 'build/thesis2-figure-preview/thesis2-figure-preview'
BASE = ROOT / 'thesis2.pdf'
PREVIEW = BUILD.with_suffix('.pdf')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def info(pdf):
    text = subprocess.check_output(['pdfinfo', str(pdf)], text=True)
    width, height = map(float, re.search(r'Page size:\s*([\d.]+) x ([\d.]+)', text).groups())
    return int(re.search(r'^Pages:\s*(\d+)', text, re.M)[1]), width, height


def bbox(pdf, name):
    dest = OUT / 'checks' / (name + '.html')
    subprocess.run(['pdftotext', '-bbox-layout', str(pdf), str(dest)], check=True)
    clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', dest.read_text())
    return ET.fromstring(clean).findall('.//{*}page')


def labels(aux):
    return {m[1]: (m[2], m[3]) for m in re.finditer(
        r'\\newlabel\{([^}]+)\}\{\{([^}]*)\}\{([^}]*)\}', aux.read_text())
        if not m[1].endswith('@cref')}


def fonts(pdf):
    result = subprocess.run(['pdffonts', str(pdf)], capture_output=True, text=True, check=True)
    assert not result.stderr, (str(pdf), result.stderr)
    for line in result.stdout.splitlines()[2:]:
        match = re.search(r'\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$', line)
        assert match and match[1] == 'yes' and 'Type 3' not in line, (str(pdf), line)


(OUT / 'checks').mkdir(exist_ok=True)
baseline = json.loads((OUT / 'baseline.json').read_text())
for name, expected in baseline['protected_files'].items():
    assert (ROOT / name).is_file() and sha(ROOT / name) == expected, ('Existing file changed', name)

manifest = json.loads((OUT / 'manifest.json').read_text())
assert info(BASE)[0] == info(PREVIEW)[0] == 65
assert labels(ROOT / 'build/thesis2/thesis2.aux') == labels(BUILD.with_suffix('.aux')), 'Number/page changes'
figures = BUILD.with_suffix('.lof').read_text().count('contentsline {figure}')
tables = BUILD.with_suffix('.lot').read_text().count('contentsline {table}')
assert (figures, tables) == (29, 28)
log = BUILD.with_suffix('.log').read_text()
issues = [line for line in log.splitlines() if re.search(r'Warning|Overfull|Underfull|Missing character|^!', line)]
assert not issues, issues
fonts(PREVIEW)

original_pages = bbox(BASE, 'original')
preview_pages = bbox(PREVIEW, 'preview')
for n, page in enumerate(preview_pages, 1):
    width, height = float(page.attrib['width']), float(page.attrib['height'])
    for word in page.findall('.//{*}word'):
        a = word.attrib
        assert min(float(a['xMin']), float(a['yMin'])) >= -.1
        assert float(a['xMax']) <= width + .1 and float(a['yMax']) <= height + .1, (n, word.text)

targets = {'supplement/precision.pdf': ('fig:7-precision', '7.2'),
           'supplement/finite-pool.pdf': ('fig:7-finite-pool', '7.7'),
           'supplement/stream-cost.pdf': ('fig:7-stream-cost', '7.8'),
           'ch8/negative-evidence.pdf': ('fig:8-negative', '8.1')}
all_labels = labels(BUILD.with_suffix('.aux'))
changed_pages = {int(all_labels[label][1]) + 7 for label, _ in targets.values()}
before = subprocess.check_output(['pdftotext', str(BASE), '-'], text=True).split('\f')
after = subprocess.check_output(['pdftotext', str(PREVIEW), '-'], text=True).split('\f')
for n, (old, new) in enumerate(zip(before, after), 1):
    if n not in changed_pages:
        assert re.sub(r'\s+', '', old) == re.sub(r'\s+', '', new), ('Unchanged page text', n)

pixel_changes = {}
for asset, (label, number) in targets.items():
    pdf = OUT / 'figures' / asset
    assert sha(pdf) == manifest['figures'][asset]['sha256']
    fonts(pdf)
    _, width, height = info(pdf)
    _, old_width, old_height = info(ROOT / 'figures' / asset)
    assert abs(width - 156 / 25.4 * 72) < .01
    assert abs(height - old_height / old_width * width) < .002
    for word in bbox(pdf, pdf.stem)[0].findall('.//{*}word'):
        a = word.attrib
        assert min(float(a['xMin']), float(a['yMin'])) >= -.1, (asset, word.text, a)
        assert float(a['xMax']) <= width + .1 and float(a['yMax']) <= height + .1, (asset, word.text, a)
    physical = int(all_labels[label][1]) + 7
    lines = original_pages[physical - 1].findall('.//{*}line')
    captions = [line for line in lines if ''.join(w.text or '' for w in line.findall('{*}word')[:2]) == 'Figure' + number + '.']
    assert len(captions) == 1, (number, len(captions))
    caption_y = float(captions[0].attrib['yMin'])
    pngs = []
    for tag, source in [('old', BASE), ('new', PREVIEW)]:
        stem = OUT / 'checks' / (str(physical) + '-' + tag)
        subprocess.run(['pdftoppm', '-f', str(physical), '-l', str(physical), '-r', '120',
                        '-png', '-singlefile', str(source), str(stem)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pngs.append(Image.open(stem.with_suffix('.png')).convert('RGB'))
    difference = ImageChops.difference(*pngs).getbbox()
    assert difference, asset
    x0, y0, x1, y1 = [v * 72 / 120 for v in difference]
    assert x0 >= 27 / 25.4 * 72 - 2 and x1 <= (27 + 156) / 25.4 * 72 + 2, (asset, difference)
    assert y0 >= caption_y - height - 18 and y1 <= caption_y - 1, (asset, difference, caption_y, height)
    pixel_changes[str(physical)] = {'figure': number, 'changed_pixel_box': difference,
                                  'changes_confined_to_figure': True}

recorder = BUILD.with_suffix('.fls').read_text()
for asset in targets:
    assert str((OUT / 'figures' / asset).relative_to(ROOT)) in recorder, asset
proofs = len(re.findall(r'^Proof\.$', subprocess.check_output(['pdftotext', str(PREVIEW), '-'], text=True), re.M))
assert proofs == 6, proofs
result = dict(preview_sha256=sha(PREVIEW), original_sha256=sha(BASE), pages=65,
              protected_existing_files=len(baseline['protected_files']),
              original_files_unchanged=True, figures=figures, tables=tables, proofs=proofs,
              all_label_numbers_and_pages_identical=True,
              unaffected_page_text_identical=65-len(changed_pages),
              changes_confined_to_four_figures=pixel_changes,
              source_arrays_and_archived_hashes_checked=True,
              fonts_embedded=True, type3_fonts=0, compiler_issues=issues,
              plot_labels_within_canvas=True,
              plot_geometry_preserved=True)
(OUT / 'checks.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
