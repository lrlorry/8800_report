#!/usr/bin/env python3
"""Check the published thesis PDFs after the canonical-name cleanup."""
from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]

def output(*args):
    return subprocess.check_output(args, text=True)

def main():
    manifest = json.loads((ROOT / 'assessment/canonical-pdf-names-2026-10-31.json').read_text())
    state = json.loads((ROOT / 'assessment/thesis2-current-state.json').read_text())
    for name, language in [('thesis.pdf', 'english'), ('thesis-zh.pdf', 'chinese')]:
        pdf = ROOT / name
        digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
        assert digest == manifest['retained'][name]['sha256'] == state[language]['sha256'], (name, 'published hash')
        pages = int(re.search(r'^Pages:\s*(\d+)', output('pdfinfo', str(pdf)), re.M)[1])
        assert pages == state[language]['pages'], (name, 'page count')
        text = output('pdftotext', str(pdf), '-')
        assert not re.search(r'\?\?|\[cite:|draft only|\[\[KEEP', text, re.I), (name, 'unresolved text')
        for fact in ['17.78', '20.44', '0.0006', '55,296', '69,120']:
            assert fact in text, (name, fact)
        if language == 'english':
            assert len(re.findall(r'(?m)^\s*Proof\.', text)) == 6, 'Proof count'
        for font in output('pdffonts', str(pdf)).splitlines()[2:]:
            status = re.search(r'\s+(yes|no)\s+(yes|no)\s+(yes|no)\s+\d+\s+\d+\s*$', font)
            assert status and status[1] == 'yes' and 'Type 3' not in font, (name, 'font embedding', font)
        print(f'{name}: {pages} pages; hash, text and fonts verified')
    outline = ROOT / manifest['outline']['file']
    assert hashlib.sha256(outline.read_bytes()).hexdigest() == manifest['outline']['sha256'], 'Outline hash'
    expected = {'thesis.pdf', 'thesis-zh.pdf', 'thesis-outline.pdf'}
    assert {p.name for p in ROOT.glob('*.pdf')} == expected, 'Unexpected root PDF version'
    print('Canonical filenames and old-version cleanup verified')

if __name__ == '__main__':
    main()
