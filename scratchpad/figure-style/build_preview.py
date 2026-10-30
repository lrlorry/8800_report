#!/usr/bin/env python3
"""Restyle four existing figures, without running the table/audit generators.

Only this scratch directory receives output. Numerical records, primary
archives, original figures, thesis sources and existing PDFs are read-only.
The canvas aspect ratios preserve the original on-page figure heights.
"""
import ast
import csv
import hashlib
import json
import math
import os
import re
import statistics
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CODE = ROOT.parent / 'JHQ_GPU'
WIDTH_IN = 156 / 25.4
WIDTH_PT = WIDTH_IN * 72
METHOD = {'JHQ': '#184e77', 'JHQ FP32': '#397da7',
          'CAGRA fp32': '#d77919', 'CAGRA int8': '#659429',
          'IVF-RaBitQ': '#b53434', 'IVF-PQ': '#7252a3'}
inputs, traces, outputs = {}, {}, {}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    key = str(path.relative_to(ROOT if path.is_relative_to(ROOT) else CODE))
    inputs[('report/' if path.is_relative_to(ROOT) else 'JHQ_GPU/') + key] = digest(path)
    return path.read_text()


def original_height(asset):
    info = subprocess.check_output(['pdfinfo', str(ROOT / 'figures' / asset)], text=True)
    width, height = map(float, re.search(r'Page size:\s*([\d.]+) x ([\d.]+)', info).groups())
    return height / width * WIDTH_IN


def save(figure, asset):
    dest = OUT / 'figures' / asset
    dest.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(dest, metadata={'CreationDate': None, 'ModDate': None})
    figure.savefig(dest.with_suffix('.png'), dpi=180)
    outputs[asset] = {'sha256': digest(dest), 'width_inches': WIDTH_IN,
                      'height_inches': figure.get_figheight(),
                      'original_sha256': digest(ROOT / 'figures' / asset)}
    plt.close(figure)


def precision_curves(supplement):
    # Reuse only the original pure frontier/interpolation functions. Never
    # execute audit_supplement's module body, which writes tables and audits.
    tree = ast.parse(read(ROOT / 'scripts/audit_supplement.py'))
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name in {'frontier', 'interp'}]
    assert len(functions) == 2
    namespace = {'math': math}
    exec(compile(ast.Module(body=functions, type_ignores=[]), '<original-pure-functions>', 'exec'), namespace)
    frontier, interp = namespace['frontier'], namespace['interp']
    recorded = {x['path']: x['sha256'] for x in supplement['inputs']
                if x['repository'] == 'JHQ_GPU'}

    def archived(path):
        assert digest(path) == recorded[str(path.relative_to(CODE))], path
        return read(path)

    e1 = {}
    for row in csv.DictReader(archived(CODE / 'experiments/comp8800_poster_e1/E1_points.csv').splitlines()):
        try:
            e1.setdefault((row['dataset'], row['family']), []).append((float(row['recall']), float(row['qps_A'])))
        except ValueError:
            pass
    result = {}
    for dataset in ['openai3-1536', 'openai3-3072']:
        points = {}
        for version in ['v69', 'v72']:
            rows = {}
            for path in sorted((CODE / 'experiments/thesis_evidence/RAW_D').glob(f'jhq_{version}_{dataset}_np*.json')):
                runset = json.loads(archived(path))
                for run in runset['runs']:
                    assert run['batch'] == 1000 and runset['rounds'] == 5
                    variant = next(v for v in run['variants'] if v['G'] == -1)
                    rows[(runset['nprobe'], run['alpha'])] = (variant['recall'], statistics.median(variant['qps']))
            assert rows
            points[version] = rows
        assert points['v69'].keys() == points['v72'].keys()
        curves = {version: frontier(list(rows.values())) for version, rows in points.items()}
        curves.update(rabitq=frontier(e1[dataset, 'IVF-RaBitQ']), cagra=frontier(e1[dataset, 'CAGRA fp32']))
        summary = supplement['precision'][dataset]
        ratios = [points['v72'][key][1] / row[1] for key, row in points['v69'].items()]
        assert len(ratios) == summary['configurations']
        assert math.isclose(statistics.geometric_mean(ratios), summary['geo_ratio'], rel_tol=1e-12)
        for version in ['v69', 'v72']:
            assert math.isclose(interp(curves[version], .97), summary['at_097'][version], rel_tol=1e-12)
        result[dataset] = curves
    return result


def draw_precision(supplement):
    asset = 'supplement/precision.pdf'
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH_IN, original_height(asset)))
    fig.subplots_adjust(left=.105, right=.965, bottom=.245, top=.74, wspace=.35)
    traces[asset] = {}
    styles = [('v69', 'JHQ TF32 (v69)', METHOD['JHQ'], '-'),
              ('v72', 'JHQ FP32 (v72)', METHOD['JHQ FP32'], '-'),
              ('rabitq', 'E1 IVF-RaBitQ', METHOD['IVF-RaBitQ'], '--'),
              ('cagra', 'E1 CAGRA fp32', METHOD['CAGRA fp32'], ':')]
    for ax, (dataset, curves) in zip(axes, precision_curves(supplement).items()):
        for key, label, colour, style in styles:
            xy = curves[key]
            ax.plot([p[0] for p in xy], [p[1] / 1000 for p in xy], style, color=colour, label=label)
        traces[asset][dataset] = curves
        ax.set(xlim=(.945, .985), ylim=(0, 240 if dataset.endswith('1536') else 110),
               xlabel='Recall@10', ylabel='Throughput (kQPS)', title=dataset.replace('openai3', 'OpenAI'))
        ax.set_xticks([.945, .955, .965, .975, .985])
        ax.yaxis.set_major_locator(MaxNLocator(nbins=4))
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=4, loc='upper center', bbox_to_anchor=(.53, 1.015),
               handlelength=1.8, columnspacing=.85, handletextpad=.45, frameon=False)
    save(fig, asset)


def draw_finite_pool(supplement):
    asset = 'supplement/finite-pool.pdf'
    fig, axes = plt.subplots(1, 2, figsize=(WIDTH_IN, original_height(asset)), sharey=True)
    fig.subplots_adjust(left=.11, right=.985, bottom=.27, top=.74, wspace=.25)
    traces[asset] = {}
    for ax, probes in zip(axes, [128, 512]):
        values = supplement['budget'][f'arxiv-768/{probes}']['predictions']; xs = [32, 64, 128]
        predicted = [values[str(s)]['predicted'] for s in xs]
        observed = [values[str(s)]['observed'] for s in xs]
        sem = [math.sqrt(p * (1 - p) / 64) for p in observed]
        ax.plot(xs, predicted, '-o', color=METHOD['JHQ'], label='Finite-pool prediction', markersize=3.8)
        ax.errorbar(xs, observed, yerr=sem, fmt='s--', color='#626b73', capsize=2,
                    markersize=3.6, label=r'64 draws ($\pm$1 s.e.)')
        ax.set(ylim=(0, 1.05), xticks=xs, xlabel='Calibration sample size $S$', title=f'arXiv, {probes} probes')
        ax.set_yticks([0, .25, .5, .75, 1])
        traces[asset][str(probes)] = dict(x=xs, predicted=predicted, observed=observed, standard_error=sem)
    axes[0].set_ylabel('Loss crossing frequency')
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=2, loc='upper center', bbox_to_anchor=(.54, 1.02), frameon=False)
    save(fig, asset)


def draw_streams(supplement):
    asset = 'supplement/stream-cost.pdf'
    fig, axes = plt.subplots(2, 2, figsize=(WIDTH_IN, original_height(asset)))
    fig.subplots_adjust(left=.11, right=.985, bottom=.125, top=.84, hspace=.65, wspace=.32)
    styles = [('fixed100', 'Fixed 100', '#5a6169', '--'), ('fixed64', 'Fixed 64', '#969ca2', ':'),
              ('rule', r'Rule $S=128$', METHOD['JHQ'], '-'), ('full', 'FULL', METHOD['JHQ FP32'], '-.')]
    traces[asset] = {}
    for ax, (key, policies) in zip(axes.flat, supplement['streams'].items()):
        series = {}
        for policy, label, colour, style in styles:
            ys = policies[policy]['cumulative_ms']; assert len(ys) == 500
            ax.plot(range(1, 501), ys, style, label=label, color=colour)
            series[policy] = ys
        traces[asset][key] = series
        dataset, probes = key.split('/')
        name = dataset.replace('arxiv-768', 'arXiv').replace('openai3', 'OpenAI').replace('bge-m3', 'BGE')
        ax.set(title=f'{name}, {probes} probes', xlabel='Reuse batches', ylabel='Total time (ms)')
        ax.set_xticks([0, 250, 500]); ax.yaxis.set_major_locator(MaxNLocator(nbins=3))
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles, labels, ncol=4, loc='upper center', bbox_to_anchor=(.54, .995), frameon=False)
    save(fig, asset)


def draw_negative(study):
    asset = 'ch8/negative-evidence.pdf'
    fig, (left, right) = plt.subplots(1, 2, figsize=(WIDTH_IN, original_height(asset)),
                                    gridspec_kw={'width_ratios': [1.6, 1]})
    fig.subplots_adjust(left=.11, right=.985, bottom=.29, top=.78, wspace=.46)
    rows = study['mailman']
    labels = [r['dataset'].replace('-768', '').replace('openai3-3072', 'OpenAI') + '\nb=' + str(r['batch']) for r in rows]
    ys = [r['speed_ratio'] for r in rows]
    left.bar(range(6), ys, color=['#84909a' if r['batch'] == 8 else '#53616d' for r in rows], width=.7)
    left.axhline(1, color=METHOD['JHQ'], linestyle='--', linewidth=1)
    left.set(ylim=(0, 1.12), xticks=range(6), xticklabels=labels,
             ylabel='Scorer speed /\npacked-table baseline', title='(a) Isolated GPU\nmeasurement')
    left.set_yticks([0, .25, .5, .75, 1]); left.tick_params(axis='x', labelsize=8.1, length=0)
    for i, y in enumerate(ys):
        left.text(i, y + .025, f'{y:.3f}', ha='center', va='bottom', fontsize=8.1)
    arxiv = next(r for r in study['rank_offline'] if r['dataset'] == 'arxiv-768')
    survivors = [arxiv['original_T'], arxiv['median_T']]
    assert survivors == [875, 375]
    right.bar(['Original', 'Median'], survivors, color=[METHOD['JHQ'], '#7252a3'], width=.58)
    right.set(ylim=(0, 1030), ylabel='Minimum tested survivors', title='(b) FP64 offline test:\narXiv')
    right.set_yticks([0, 250, 500, 750, 1000])
    for i, y in enumerate(survivors):
        right.text(i, y + 20, str(y), ha='center', va='bottom', fontsize=8.5)
    left.grid(axis='x', visible=False); right.grid(axis='x', visible=False)
    traces[asset] = {'scorer': {'labels': labels, 'ratios': ys}, 'offline': {'survivors': survivors}}
    save(fig, asset)


if __name__ == '__main__':
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'build/matplotlib'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.ticker import MaxNLocator
    # Matplotlib bundles a TrueType Computer Modern Roman. It matches the
    # thesis's CM-derived serif style without CFF/OpenType embedding warnings.
    plt.rcParams.update({'font.family': 'cmr10', 'font.size': 9,
                         'mathtext.fontset': 'cm', 'pdf.fonttype': 42, 'ps.fonttype': 42,
                         'axes.formatter.use_mathtext': True, 'axes.unicode_minus': False,
                         'axes.labelsize': 8.7, 'axes.titlesize': 9,
                         'xtick.labelsize': 8.1, 'ytick.labelsize': 8.1, 'legend.fontsize': 8.1,
                         'axes.spines.top': False, 'axes.spines.right': False, 'axes.linewidth': .55,
                         'axes.grid': True, 'grid.alpha': .14, 'grid.linewidth': .45,
                         'axes.axisbelow': True, 'lines.linewidth': 1.25,
                         'xtick.major.width': .5, 'ytick.major.width': .5,
                         'axes.labelpad': 3, 'axes.titlepad': 4,
                         'figure.facecolor': 'white', 'savefig.facecolor': 'white'})
    supplement = json.loads(read(ROOT / 'data/supplement/audit.json'))
    negative = json.loads(read(ROOT / 'data/ch8/audit.json'))
    draw_precision(supplement); draw_finite_pool(supplement)
    draw_streams(supplement); draw_negative(negative)
    payload = json.dumps(traces, sort_keys=True, separators=(',', ':'))
    (OUT / 'plot-data.json').write_text(json.dumps(traces, indent=2) + '\n')
    manifest = dict(scope='Four style-only previews; original chapter/figure/table/data files unchanged.',
                    width_mm=156, method_colours=METHOD, font_family='Computer Modern Roman (TrueType)',
                    label_size_pt=8.7, tick_and_legend_size_pt=8.1,
                    input_hashes=inputs, figures=outputs,
                    plot_data_sha256=hashlib.sha256(payload.encode()).hexdigest(),
                    semantics={'precision': 'D: paired JHQ on a TF32-trained cache; archived E1 baselines.',
                               'finite_pool': 'The same finite-pool probabilities and 64-draw standard errors.',
                               'streams': 'All original 500 cumulative values per policy and workload.',
                               'negative': 'Six GPU scorer ratios and a separate FP64 offline survivor comparison.'})
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('Wrote four style previews; preserved source values, aspect ratios and evidence scopes.')
