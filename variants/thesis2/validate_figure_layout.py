"""Content checks for the separately recorded figure/layout round.

Formatting may move blocks, but may not change their lexical content.
The two expressly authorised scientific-figure/caption additions are
excluded narrowly; mathematical blocks, proofs and table cells are not.
The later architecture replacement has its own recorded source/caption checks.
"""
import collections
import hashlib
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


def validate(root, round_record, architecture_record=None, technical_record=None):
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
        labels = lambda s: re.findall(r'\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\};', s)
        local_name = 'variants/thesis2/figures/' + local
        prior = next((x['before'] for x in (technical_record or {}).get('changes', [])
                      if x['path'] == local_name), (root / local_name).read_text())
        assert labels((root / shared).read_text()) == labels(prior), local
    architecture_checks = {}
    if architecture_record:
        shared = root / 'figures/ch4/architecture.tex'
        assert hashlib.sha256(shared.read_bytes()).hexdigest() == architecture_record['shared_figure_sha256'], 'Shared architecture changed'
        local = 'variants/thesis2/figures/architecture-layout.tex'
        assert set(architecture_record['added_files']) == {local}, 'Architecture source scope'
        assert (root / local).read_text() == architecture_record['added_files'][local], 'Architecture source not recorded'
        for lang, title in [('thesis2', architecture_record['english_caption']),
                            ('thesis2-zh', architecture_record['chinese_caption'])]:
            source = (root / 'variants' / lang / 'chapters/04-1-boundaries.tex').read_text()
            assert source.count(r'\input{variants/thesis2/figures/architecture-layout}') == 1, lang
            assert re.search(r'\\caption(?:\[[^]]*\])?\{([^{}]*)\}', source)[1] == title, ('Short architecture caption', lang)
        architecture_checks = dict(architecture_replacement_recorded=True,
                                   shared_architecture_unchanged=True,
                                   short_architecture_captions_verified=True)
    return dict(layout_prose_preserved=True, mathematical_blocks_and_proofs_identical=True,
                table_cells_identical=True, existing_labels_and_citations_preserved=True,
                spacing_only_diagram_labels_identical=True, body_files_checked=checked,
                **architecture_checks)


def validate_technical_figures(root, record, later_changes=None):
    """Check the later, explicitly authorised diagram/content changes separately."""
    for name, digest in record['shared_source_sha256'].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest, ('Shared diagram changed', name)
    for name, digest in record['unchanged_source_sha256'].items():
        prior = (later_changes or {}).get(name, {}).get('before')
        content = prior.encode() if prior is not None else (root / name).read_bytes()
        assert hashlib.sha256(content).hexdigest() == digest, ('Figure-review scope spill', name)
    for change in record['changes']:
        name, before, after = change['path'], change['before'], change['after']
        observed = (later_changes or {}).get(name, {}).get('before', (root / name).read_text())
        assert observed == after, ('Figure-review source not recorded', name)
        if before is None or '/chapters/' not in name:
            continue
        for env in ['equation', 'equation*', 'align', 'align*', 'lemma', 'proposition', 'corollary', 'proof']:
            pat = r'\\begin\{' + re.escape(env) + r'\}[\s\S]*?\\end\{' + re.escape(env) + r'\}'
            assert re.findall(pat, before) == re.findall(pat, after), (name, env)
        for pat in [r'\\\[[\s\S]*?\\\]', r'\\toprule[\s\S]*?\\bottomrule', r'\\cite(?:\[[^]]*\])?\{[^}]*\}']:
            assert re.findall(pat, before) == re.findall(pat, after), (name, 'Mathematics/data/citations')
        for command, title in re.findall(r'(\\caption(?:of\{(?:figure|table)\})?\[[^]]*\]\{([^{}]*)\})', after):
            if command in before:
                continue
            if '/thesis2/' in name and not name.endswith('/04-5-construction.tex'):
                assert len(title.split()) <= 8, ('Caption should be short', name, title)
    original = (root / 'figures/ch6/nesting-example.tex').read_text()
    revised = (root / 'variants/thesis2/figures/nesting-example.tex').read_text()
    rows = lambda s: re.search(r'\\midrule([\s\S]*?)\\bottomrule', s)[1]
    assert rows(original) == rows(revised), 'Constructed nesting table rows changed'
    return dict(shared_sources_unchanged=True, formal_mathematics_and_proofs_preserved=True,
                measured_tables_preserved=True, constructed_table_rows_preserved=True,
                removed_figures=record['removed_figure_labels'], figure_converted_to_table=True,
                captions_shortened=True, scope_checked=True)
