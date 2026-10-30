"""Content checks for the separately recorded figure/layout round.

Formatting may move blocks, but may not change their lexical content.
The two expressly authorised scientific-figure/caption additions are
excluded narrowly; mathematical blocks, proofs and table cells are not.
"""
import collections
import re


def group(text, pos):
    assert text[pos] == '{'
    depth, end = 1, pos + 1
    while depth:
        if text[end] == '{' and text[end - 1] != '\\':
            depth += 1
        if text[end] == '}' and text[end - 1] != '\\':
            depth -= 1
        end += 1
    return text[pos + 1:end - 1], end


def strip_caption(text):
    start = text.index('\\caption[')
    end = text.index(']', start) + 1
    _, end = group(text, end)
    return text[:start] + text[end:]


def lexical_content(text):
    text = re.sub(r'(?<!\\)%[^\n]*', '', text)
    text = re.sub(r'\\looseness\s*=\s*-?\d+', ' ', text)
    text = re.sub(r'\\captionof\{(?:figure|table)\}', r'\\caption', text)
    text = re.sub(r'\\begin\{(?:figure|table)\}(?:\[[^]]*\])?', ' ', text)
    text = re.sub(r'\\end\{(?:figure|table|minipage|samepage)\}', ' ', text)
    text = re.sub(r'\\begin\{samepage\}', ' ', text)
    text = re.sub(r'\\begin\{minipage\}(?:\[[^]]*\])?\{\\linewidth\}', ' ', text)
    for env, nargs in [('tabularx', 2), ('tabular', 1)]:
        token, cursor = '\\begin{' + env + '}', 0
        while (start := text.find(token, cursor)) >= 0:
            end = start + len(token)
            for _ in range(nargs):
                while text[end].isspace():
                    end += 1
                _, end = group(text, end)
            text = text[:start] + ' ' + text[end:]
            cursor = start + 1
    for pat in [r'\\setlength\{[^}]*\}\{[^}]*\}',
                r'\\enlargethispage\{[^}]*\}',
                r'\\captionsetup(?:\[[^]]*\])?\{[^}]*\}',
                r'\\(?:input|includegraphics)(?:\[[^]]*\])?\{[^}]*\}',
                r'\\(?:par|noindent|medskip|smallskip|centering|newpage)\b']:
        text = re.sub(pat, ' ', text)
    return collections.Counter(re.findall(
        r"\\[A-Za-z@]+|[A-Za-z]+(?:[-'][A-Za-z]+)*|\d+(?:\.\d+)?|[^\sA-Za-z\d]", text))


def validate(root, round_record):
    checked = []
    for change in round_record['changes']:
        rel, old, new = change['path'], change['before'], change['after']
        if old is None or ('/chapters/' not in rel and '/frontmatter/' not in rel):
            continue
        # Never exclude the original mathematics or numerical table cells.
        for env in ['equation', 'align', 'equation*', 'align*',
                    'lemma', 'proposition', 'corollary', 'proof']:
            pat = r'\\begin\{' + re.escape(env) + r'\}[\s\S]*?\\end\{' + re.escape(env) + r'\}'
            assert collections.Counter(re.findall(pat, old)) == collections.Counter(re.findall(pat, new)), (rel, env)
        for pat in [r'\\\[[\s\S]*?\\\]', r'\\toprule([\s\S]*?)\\bottomrule']:
            assert collections.Counter(re.findall(pat, old)) == collections.Counter(re.findall(pat, new)), (rel, pat)
        a, b = old, new
        if rel.endswith('/04-3-layout.tex'):
            a, b = strip_caption(a), strip_caption(b)
        if rel.endswith('/05-2-lut.tex'):
            pat = (r'\\par\\medskip\\noindent\\begin\{minipage\}\{\\linewidth\}'
                   r'\s*\\captionsetup\{hypcap=false\}\s*\\centering\s*'
                   r'\\input\{variants/thesis2/figures/cartesian-lut\}'
                   r'[\s\S]*?\\end\{minipage\}\\par\\medskip')
            b, count = re.subn(pat, '', b)
            assert count == 1, 'Exactly one new LUT figure block'
            assert b.count(r' (\cref{fig:5-cartesian-lut})') == 1
            b = b.replace(r' (\cref{fig:5-cartesian-lut})', '')
        assert lexical_content(a) == lexical_content(b), (rel, 'Non-layout prose change')
        for cmd in ['label', 'cite', 'cref', 'Cref']:
            pat = r'\\' + cmd + r'(?:\[[^]]*\])?\{[^}]+\}'
            assert collections.Counter(re.findall(pat, a)) == collections.Counter(re.findall(pat, b)), (rel, cmd)
        checked.append(rel)
    diagrams = [('figures/ch1/challenges.tex', 'challenges-layout.tex'),
                ('figures/ch6/calibration-flow.tex', 'calibration-flow-layout.tex'),
                ('figures/ch6/budget-scope.tex', 'budget-scope-layout.tex')]
    for shared, local in diagrams:
        labels = lambda p: re.findall(r'\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\};', p.read_text())
        assert labels(root / shared) == labels(root / 'variants/thesis2/figures' / local), local
    return dict(layout_prose_preserved=True, mathematical_blocks_and_proofs_identical=True,
                table_cells_identical=True, existing_labels_and_citations_preserved=True,
                spacing_only_diagram_labels_identical=True, body_files_checked=checked)
