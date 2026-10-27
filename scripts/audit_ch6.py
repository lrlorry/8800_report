#!/usr/bin/env python3
"""Offline audit of Chapter 6 policy, archived budget data and set theorem.

No GPU benchmark, index reconstruction or implementation edit is performed.
"""
import collections
import csv
import hashlib
import itertools
import json
import math
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / 'JHQ_GPU'


def main():
    inputs = []

    def read(root, name):
        data = (root / name).read_bytes()
        inputs.append(dict(repository=root.name, path=name,
                           sha256=hashlib.sha256(data).hexdigest()))
        return data.decode()

    log = read(SRC, 'experiments/adc_v69/RAW/budget_v69.log')
    script = read(SRC, 'experiments/adc_v69/run_budget_v69.sh')
    harness = read(SRC, 'examples/demo_jhq_budget_arms_v69.cu')
    search = read(SRC, 'jhq_v69_probesel/search.cu')
    read(SRC, 'jhq_v69_probesel/jhq_gpu_index.cuh')
    read(SRC, 'jhq_v69_probesel/jhq_gpu_index.cu')
    read(SRC, 'CMakeLists.txt')
    read(SRC, 'paper_adc2026/ADC/MethodPart2_ADC.tex')
    assert 'JHQ_AS_GRID=200,100,64,32,16,8,4,2' in script
    assert 'JHQ_AS_SLOTS=1' in script
    rule = harness[harness.index('auto run_rule ='):harness.index('// ---- the same criterion')]
    assert all(x not in rule for x in ['Arec', 'Aqps', 'gt.data()', 'ceil_rec'])
    assert 'return lo;' in rule and 'idx.set_alpha(A[lo])' not in rule
    full_call = harness[harness.index('// ---- the same criterion'):harness.index('// ---- the sampled rule')]
    assert 'run_rule(all, &cm, &pr);' in full_call
    assert 'enum_out' not in full_call
    assert harness.index('std::vector<float> sq') < harness.index('auto t0 = Clock::now();', harness.index('auto run_rule ='))
    assert 'return !(e && e[0]' in search[search.index('static bool exact_topck()'):][:400]

    run_head = re.search(r'head=([0-9a-f]+)', log).group(1)
    old = subprocess.run(['git', 'show', f'{run_head}:examples/demo_jhq_budget_arms_v69.cu'],
                         cwd=SRC, capture_output=True, check=True).stdout
    assert old.decode() == harness
    old_search = subprocess.run(['git', 'show', f'{run_head}:jhq_v69_probesel/search.cu'],
                                cwd=SRC, capture_output=True, check=True).stdout.decode()
    assert 'return !(e && e[0]' in old_search[old_search.index('static bool exact_topck()'):][:400]

    cells = []
    for block in log.split('### ')[1:]:
        m = re.match(r'(\S+) M=\d+ nlist=\d+ np=(\d+)', block)
        if not m:
            continue
        ds, probes = m.group(1), int(m.group(2))
        split = re.search(r'split: (\d+) calibration queries, (\d+) held-out', block)
        paths = re.search(r'G\(b=(\d+)\) = (\d+), G\(b=(\d+)\) = (\d+)', block)
        assert split and paths
        fixed = {int(float(a)): dict(recall=float(r), qps=int(q)) for a, r, q in
                 re.findall(r'ARM FIXED alpha=([\d.]+)\s+recall=([\d.]+) qps=(\d+)', block)}
        assert set(fixed) == {200, 100, 64, 32, 16, 8, 4, 2}
        draws = {}
        for s, reps, cal, loss, p95, frac, a, q in re.findall(
                r'ARM RULE S=(\d+)\s+reps=(\d+) cal_ms=([\d.]+) mean_loss=([\d.]+) '
                r'p95_loss=([\d.]+) frac_over_1e-3=([\d.]+) median_alpha=(\d+) mean_qps=(\d+)', block):
            draws[int(s)] = dict(reps=int(reps), cal_ms=float(cal), mean_loss=float(loss),
                                 p95_loss=float(p95), crossing_fraction=float(frac),
                                 crossings=round(float(frac)*int(reps)), median_alpha=int(a), mean_qps=int(q))
        enumeration = [dict(S=int(s), reps=int(reps), different=int(d), denominator=int(n),
                            enum_ms=float(e), bisect_ms=float(b)) for s, reps, d, n, e, b in re.findall(
                                r'ARM ENUM S=(\d+)\s+reps=(\d+) disagree=(\d+)/(\d+) '
                                r'enum_ms=([\d.]+) bisect_ms=([\d.]+)', block)]
        assert set(draws) == {32, 64, 128} and len(enumeration) == 3
        fm = re.search(r'ARM FULL alpha=([\d.]+) recall=([\d.]+) qps=(\d+) cal_ms=([\d.]+)', block)
        full = dict(alpha=int(float(fm[1])), recall=float(fm[2]), qps=int(fm[3]), cal_ms=float(fm[4]))
        cv = float(re.search(r'candidate-count CV ([\d.]+)', block)[1])
        threads = 1024 if ds == 'openai3-3072' else 512
        def groups(batch):
            fill = max([1]+[g for g in [2, 4, 8] if batch*g*threads <= 156672])
            chosen = max(fill, 4 if cv >= .3 else 1)
            return 0 if chosen == 1 else chosen
        predicted = {s: groups(s) for s in [32, 64, 128, 500]}
        assert predicted[128] == int(paths[4])
        assert groups(int(paths[1])) == int(paths[2])
        assert predicted[500] == int(paths[2])
        cells.append(dict(dataset=ds, nprobe=probes, calibration_n=int(split[1]), held_out_n=int(split[2]),
                          evaluation_groups=int(paths[2]), calibration_128_groups=int(paths[4]),
                          source_derived_groups=predicted, fixed=fixed, full=full,
                          draws=draws, enumeration=enumeration))
    assert len(cells) == 12
    total = sum(e['denominator'] for c in cells for e in c['enumeration'])
    mismatches = sum(e['different'] for c in cells for e in c['enumeration'])
    assert total == 2304 and mismatches == 0
    assert sum(c['evaluation_groups'] == 0 for c in cells) == 10
    assert sum(c['calibration_128_groups'] == 2 for c in cells) == 8
    assert sum(c['evaluation_groups'] != c['calibration_128_groups'] for c in cells) == 8

    ch7 = json.loads(read(ROOT, 'data/ch7/audit.json'))
    indexed = {(c['dataset'], c['nprobe']): c for c in ch7['budget']}
    for c in cells:
        r = c['draws'][128]
        old = indexed[c['dataset'], c['nprobe']]
        assert (r['median_alpha'], r['cal_ms'], r['mean_loss'], r['p95_loss'], r['mean_qps']) == (
            old['alpha'], old['cal_ms'], old['mean_loss'], old['p95_loss'], old['qps'])
        assert c['held_out_n'] == old['test_n']
        assert c['full'] == old['full']
    gains100 = [c['draws'][128]['mean_qps']/c['fixed'][100]['qps'] for c in cells]
    gains64 = [c['draws'][128]['mean_qps']/c['fixed'][64]['qps'] for c in cells]
    assert sum(g > 1 for g in gains100) == 10 and sum(g > 1 for g in gains64) == 9
    grouped_draws = sum(64 for c in cells for s in [32, 64, 128] if c['source_derived_groups'][s] > 0)
    assert grouped_draws == 2176
    full_grouped = sum(c['source_derived_groups'][500] > 0 for c in cells)
    assert full_grouped == 2
    archived_ties = {}
    for dataset in ['arxiv-768', 'vogue-768', 'openai3-3072']:
        j = json.loads(read(SRC, f'experiments/pipeline_v62/raw/check/{dataset}.json'))
        rows = [v for r in j['runs'] if r['nused'] == 1000
                for v in r['variants'] if v['G'] > 0]
        archived_ties[dataset] = max(v['topck_tie_only'] for v in rows)
        assert all(v['final_bit_identical'] == 1000 for v in rows)
    assert archived_ties == {'arxiv-768': 9, 'vogue-768': 7, 'openai3-3072': 0}
    full_results = []
    economics = {'S128': [], 'full': []}
    inversions = []
    for c in cells:
        old = indexed[c['dataset'], c['nprobe']]
        f = c['full']
        loss = old['oracle']['ceiling']-f['recall']
        full_results.append(dict(dataset=c['dataset'], nprobe=c['nprobe'], alpha=f['alpha'],
                                 loss=loss, oracle_fraction=f['qps']/old['oracle']['qps'],
                                 gain100=f['qps']/c['fixed'][100]['qps'],
                                 control100_qualifies=old['oracle']['ceiling']-c['fixed'][100]['recall'] <= .001+1e-9))
        for label, qps, cal in [('S128', c['draws'][128]['mean_qps'], c['draws'][128]['cal_ms']),
                                ('full', f['qps'], f['cal_ms'])]:
            for control in [100, 64]:
                base_q = c['fixed'][control]['qps']
                saving = c['held_out_n']*1000*(1/base_q-1/qps)
                batches = cal/saving if saving > 0 else None
                queries = batches*c['held_out_n'] if batches else None
                economics[label].append(dict(dataset=c['dataset'], nprobe=c['nprobe'], control=control,
                                             batches=batches, queries=queries,
                                             baseline_seconds=queries/base_q if queries else None))
        grid = sorted(c['fixed'])
        for a, b in zip(grid, grid[1:]):
            if c['fixed'][b]['qps'] > c['fixed'][a]['qps']:
                inversions.append(dict(dataset=c['dataset'], nprobe=c['nprobe'], smaller=a, larger=b,
                                       larger_over_smaller=c['fixed'][b]['qps']/c['fixed'][a]['qps']))
    assert max(x['loss'] for x in full_results) < .00061

    example_cell = next(c for c in cells if c['dataset'] == 'openai3-1536' and c['nprobe'] == 128)
    base, chosen = example_cell['fixed'][100], example_cell['full']
    n = example_cell['held_out_n']
    base_ms, chosen_ms = 1000*n/base['qps'], 1000*n/chosen['qps']
    reuse_star = chosen['cal_ms']/(base_ms-chosen_ms)
    assert chosen['alpha'] == 8 and base['recall'] == chosen['recall'] == .928
    assert math.ceil(reuse_star) == 9
    worked_reuse = dict(dataset='openai3-1536', nprobe=128, batch=n,
                        fixed_alpha=100, chosen_alpha=chosen['alpha'],
                        requested_survivors=[1000, 80], reduction_fraction=.92,
                        fixed_qps=base['qps'], chosen_qps=chosen['qps'],
                        recall=chosen['recall'], cal_ms=chosen['cal_ms'],
                        fixed_batch_ms=base_ms, chosen_batch_ms=chosen_ms,
                        break_even_batches=reuse_star, first_positive_batches=math.ceil(reuse_star),
                        status='Derived from archived arm rates; not directly timed calibrated-stream cost')

    poster = json.loads(read(ROOT, 'data/ch6/poster-link.json'))
    poster_path = Path.home()/poster['path_relative_to_home']
    poster_local_check = 'not available in this checkout environment'
    if poster_path.is_file():
        sha = hashlib.sha256(poster_path.read_bytes()).hexdigest()
        assert sha == poster['sha256']
        inputs.append(dict(repository='user_local_poster', path=poster['path_relative_to_home'], sha256=sha))
        desktop = Path.home()/poster['desktop_copy']
        if desktop.is_file():
            assert hashlib.sha256(desktop.read_bytes()).hexdigest() == sha
        poster_local_check = 'PDF hash verified; poster content inspected in the completion review'

    def upper_one(n):
        lo, hi = 0., 1.
        for _ in range(100):
            p = (lo+hi)/2
            cdf = (1-p)**n+n*p*(1-p)**(n-1)
            if cdf > .05:
                lo = p
            else:
                hi = p
        return hi

    resolution = {s: dict(query_event_upper95=upper_one(s), iid_slot_upper95=upper_one(10*s))
                  for s in [32, 64, 128, 500]}
    read(SRC, 'experiments/residual_aware_bound/analyze.py')
    read(SRC, 'examples/demo_jhq_v66_bound_pilot.cu')
    pilot_rows = list(csv.DictReader(read(SRC, 'experiments/residual_aware_bound/RECALL_COMPARISON.csv').splitlines()))
    pilot = {}
    for tag in sorted({r['tag'] for r in pilot_rows}):
        rows = [r for r in pilot_rows if r['tag'] == tag]
        pilot[tag] = dict(queries=len(rows),
                          recall_gpu=sum(float(r['recall_v65']) for r in rows)/len(rows),
                          recall_full_ivf=sum(float(r['recall_full_ivf']) for r in rows)/len(rows),
                          identical_sets=sum(float(r['overlap_v65_full']) == 1 for r in rows),
                          mean_reference_survivor_coverage=sum(float(r['full_top_k_in_v65_topck']) for r in rows)/len(rows))
    assert pilot['arxiv-768_np128_a200']['identical_sets'] == 128
    assert abs(pilot['arxiv-768_np128_a100']['recall_gpu']-.9734375) < 1e-12
    assert abs(pilot['arxiv-768_np128_a100']['recall_full_ivf']-.975) < 1e-12
    qa = {r['qid'] for r in pilot_rows if r['tag']=='arxiv-768_np128_a100'}
    qb = {r['qid'] for r in pilot_rows if r['tag']=='arxiv-768_np128_a200'}
    assert qa == qb and len(qa) == 128

    # Exhaustively check the proof's set identity on four objects, all total
    # refined orders, nested three-level pools, and every valid k. This checks
    # the mathematical examples, not GPU primary scores or survivor nesting.
    checks = 0
    universe = range(4)
    for order in itertools.permutations(universe):
        rank = {v: i for i, v in enumerate(order)}
        for levels in itertools.product(range(4), repeat=4):
            small = {v for v in universe if levels[v] == 3}
            medium = {v for v in universe if levels[v] >= 2}
            large = {v for v in universe if levels[v] >= 1}
            for k in range(1, len(small)+1):
                top = lambda pool: set(sorted(pool, key=rank.get)[:k])
                ref = top(large)
                assert top(small) & ref == small & ref
                assert len(top(small) & ref) <= len(top(medium) & ref)
                checks += 1
    top1 = lambda pool: {min(pool)}
    example = [{0}, {1, 2}, {0, 1, 2}]
    overlaps = [len(top1(c) & {0}) for c in example]
    assert overlaps == [1, 0, 1]
    mask = [True, False, True]  # descending budgets 3, 2, 1
    lo, hi = 0, 2
    while lo < hi:
        mid = (lo+hi+1)//2
        if mask[mid]:
            lo = mid
        else:
            hi = mid-1
    assert lo == 0 and max(i for i, ok in enumerate(mask) if ok) == 2

    # Reference answers can avoid every tied primary cutoff while an outsider
    # enters a smaller pool through a tie at the reference pool's boundary.
    primary = dict(r=0, a=1, b=1, c=1)
    refined_rank = dict(b=0, r=1, a=2, c=3)
    pools = [{'r'}, {'r', 'b'}, {'r', 'a', 'c'}]
    reference = {min(pools[-1], key=refined_rank.get)}
    for pool in pools:
        tau = max(primary[x] for x in pool)
        assert {x for x, p in primary.items() if p < tau}.issubset(pool)
        tie_block = {x for x, p in primary.items() if p == tau}
        assert len(tie_block) == 1 or reference.isdisjoint(tie_block)
    reference_avoids_ties = [len({min(pool, key=refined_rank.get)} & reference) for pool in pools]
    assert reference_avoids_ties == [1, 0, 1]

    # Independently count admissible subsets rather than sampling from a fitted
    # workload. Values >=2 are interchangeable for the epsilon=1 event.
    finite_pool_checks = 0
    choose = lambda n, k: math.comb(n, k) if 0 <= k <= n else 0
    for n in range(1, 7):
        for xs in itertools.product(range(3), repeat=n):
            n0, n1 = xs.count(0), xs.count(1)
            for size in range(n+1):
                expected = choose(n0, size)+n1*choose(n0, size-1)
                observed = sum(sum(xs[i] for i in ids) <= 1
                               for ids in itertools.combinations(range(n), size))
                assert observed == expected
                finite_pool_checks += 1

    # A reproducible prose/caption estimate, not the course's official count.
    # Mathematical environments, inline math and table bodies are excluded.
    def prose_words(s):
        s = re.sub(r'(?<!\\)%[^\n]*', '', s)
        s = re.sub(r'(\\(?:caption(?:of\{(?:figure|table)\})?|chapter))\[[^\]]*\]', r'\1', s)
        s = re.sub(r'\\begin\{(equation\*?|align\*?|tabularx|tabular)\}[\s\S]*?\\end\{\1\}', ' ', s)
        s = re.sub(r'\$[^$]*\$', ' ', s)
        s = re.sub(r'\\(?:label|input|cite|[Cc]ref|ref|path|operatorname)\*?(?:\[[^]]*\])?\{[^}]*\}', ' ', s)
        s = re.sub(r'\\(?:begin|end)\{[^}]*\}(?:\{[^}]*\})?', ' ', s)
        s=s.replace(r'\\', ' ')
        s = re.sub(r'\\[A-Za-z@]+\*?', ' ', s)
        return len(re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)*", s))
    words = {str(p.relative_to(ROOT)): prose_words(p.read_text())
             for p in sorted(ROOT.glob('chapters/06-*.tex'))}

    for name in ['6.pdf', 'assessment/thesis-marking-guide.txt', 'chapters/07-evaluation.tex',
                 'zh/chapters/07-evaluation.tex', 'assessment/ch7-pending-experiments.txt',
                 'assessment/ch6-evidence.txt', 'assessment/ch6-review-response.txt',
                 'assessment/ch6-completion.txt',
                 'assessment/ch6-round2-response.txt',
                 'data/ch6/review-sources.json', 'scripts/audit_ch6.py', 'main-zh.tex',
                 'config/preamble.tex', 'zh/preamble.tex',
                 'references.bib', 'appendices/a-reproducibility.tex',
                 'tables/ch7/budget_full.tex', 'zh/tables/budget_full.tex',
                 'tables/ch7/budget_cost.tex', 'zh/tables/budget_cost.tex',
                 'figures/ch7/budget_risk.pdf', 'figures/ch7/budget_payback.pdf']:
        if name.endswith('.pdf'):
            data = (ROOT/name).read_bytes()
            inputs.append(dict(repository=ROOT.name, path=name, sha256=hashlib.sha256(data).hexdigest()))
        else:
            read(ROOT, name)
    for pattern in ['chapters/06-*.tex', 'zh/chapters/06-*.tex', 'figures/ch6/*.tex']:
        for p in sorted(ROOT.glob(pattern)):
            read(ROOT, str(p.relative_to(ROOT)))
    supplement = json.loads(read(ROOT, 'data/supplement/audit.json'))
    assert supplement['checks']['full_enum_agree'] == 12
    result = dict(scope='Original campaign/source audit plus separately identified supplementary traces; no GPU run.',
                  supplementary_checks=supplement['checks'],
                  recorded_run_head=run_head, historical_harness_matches_current=True,
                  historical_harness_sha256=hashlib.sha256(harness.encode()).hexdigest(),
                  historical_search_sha256=hashlib.sha256(old_search.encode()).hexdigest(),
                  binary_identity='not archived; source correspondence is not executable identity',
                  grid=[200, 100, 64, 32, 16, 8, 4, 2], epsilon_slots=1,
                  application='helper returns grid index; caller must set selected alpha before future searches',
                  normalized_allowance={str(s):1/(10*s) for s in [32, 64, 128, 500]},
                  enumeration=dict(draws=total, mismatches=mismatches),
                  full_pool_coverage=dict(calls=len(cells), grouped_configurations=full_grouped,
                                          distance_only_configurations=len(cells)-full_grouped,
                                          original_campaign_enumeration_checks=0,
                                          enumeration_checks=12,
                                          scope='Supplementary FULL enumeration agrees in twelve cells; general common-cutoff ordering remains conditional for G=0'),
                  historical_tie_diagnostics=dict(max_marked_queries_per1000=archived_ties,
                                                   scope='v62 path comparisons; not FULL budget-decision differences'),
                  paths=dict(evaluation=dict(collections.Counter(c['evaluation_groups'] for c in cells)),
                             calibration_128=dict(collections.Counter(c['calibration_128_groups'] for c in cells)),
                             changed=8),
                  S128=dict(wins_vs100=10, wins_vs64=9,
                            gmean_vs64=math.exp(sum(map(math.log, gains64))/12),
                            calibration_ms_range=[min(c['draws'][128]['cal_ms'] for c in cells),
                                                  max(c['draws'][128]['cal_ms'] for c in cells)]),
                  review=dict(grouped_configuration_draws=grouped_draws,
                              group_counts={s: dict(collections.Counter(c['source_derived_groups'][s] for c in cells))
                                            for s in [32, 64, 128, 500]},
                              resolution=resolution, full_pool=full_results, economics=economics,
                              pilot=pilot, qps_inversions=inversions,
                              statistical_scope='query-iid and iid-slot binomial models are distinct; no fitted arXiv crossing prediction'),
                  worked_reuse=worked_reuse,
                  poster=dict(record=poster, local_check=poster_local_check),
                  synthetic_sets=dict(objects=4, total_order_and_nested_pool_checks=checks,
                                      non_nested_overlap=overlaps,
                                      reference_outside_cutoff_ties_counterexample=reference_avoids_ties,
                                      GPU_validation=False),
                  finite_pool=dict(admissible_subset_checks=finite_pool_checks, epsilon=1,
                                   observed_query_curves_available=True,
                                   scope='Synthetic identity checked; supplement predicts fixed-pool crossings using per-query counts and held-out arm quality, with all traced subset sums verified'),
                  prose_word_estimate=dict(per_file=words, total=sum(words.values()),
                                           method='prose/captions only; table bodies, math, labels, citations and macro names excluded; not an official count'),
                  limitations=['arbitrary-subset per-query invariance unproved despite all traced subset sums matching',
                               'direct calibrated reuse covers four repeated held-out pools, not new traffic',
                               'no drift detection experiment'],
                  cells=cells, inputs=inputs)
    out = ROOT / 'data/ch6/audit.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ['enumeration', 'paths', 'S128', 'synthetic_sets']}, indent=2))
    print(f'Hashed {len(inputs)} inputs; Chapter 7 numeric correspondence verified.')


if __name__ == '__main__':
    main()
