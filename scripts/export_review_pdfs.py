#!/usr/bin/env python3
"""Export the body and the same chapter scopes as the supplied two reports."""
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    toc = (ROOT / 'build/main.toc').read_text()
    destinations = subprocess.check_output(['pdfinfo', '-dests', 'thesis.pdf'], cwd=ROOT, text=True)
    front = int(re.search(r'^\s*(\d+)\s+.*"chapter\.1"\s*$', destinations, re.M)[1]) - 1
    chapter6 = int(re.search(r'\\contentsline \{chapter\}\{\\numberline \{6\}[^\n]*?\}\{(\d+)\}\{chapter\.', toc)[1])
    bibliography = int(re.search(r'\\contentsline \{chapter\}\{\\nonumberline Bibliography\}\{(\d+)\}', toc)[1])
    info = subprocess.check_output(['pdfinfo', 'thesis.pdf'], cwd=ROOT, text=True)
    total = int(re.search(r'^Pages:\s*(\d+)', info, re.M)[1])
    split = front + chapter6
    exports = [('thesis-body', front + 1, front + bibliography - 1),
               ('thesis-part1', 1, split - 1),
               ('thesis-part2', split, total)]
    results = []
    for name, first, last in exports:
        tex = ('\\documentclass[a4paper]{article}\n\\usepackage{pdfpages}\n'
               '\\begin{document}\\pagestyle{empty}\n'
               '\\includepdf[pages=' + str(first) + '-' + str(last) +
               ',fitpaper=true,pagecommand={}]{thesis.pdf}\n\\end{document}\n')
        (ROOT / 'build' / (name + '.tex')).write_text(tex)
        result = subprocess.run(['pdflatex', '-interaction=nonstopmode', '-halt-on-error',
                                 '-output-directory=build', 'build/' + name + '.tex'],
                                cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        assert result.returncode == 0, result.stdout.decode(errors='replace')[-2000:]
        shutil.copyfile(ROOT / 'build' / (name + '.pdf'), ROOT / (name + '.pdf'))
        results.append(dict(path=name + '.pdf', physical_pages=[first, last], pages=last - first + 1))
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    main()
