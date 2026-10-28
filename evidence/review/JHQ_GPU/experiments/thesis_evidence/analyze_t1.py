"""Summarise T1 (TF32 sensitivity at 0.97, every method in one session). Writes T1_SUMMARY.md.

Frontiers use only this session's points. JHQ's two ABBA repetitions of each (nprobe, alpha) are
averaged (QPS geometric mean; recall is identical across repetitions). Interpolation follows Chapter 7:
linear in log QPS between adjacent frontier points, no extrapolation, a measured recall within 5e-4 of
the target counts as a match. E1's archived ratios are shown for comparison.
"""
import csv, json, math, re, statistics as st
from pathlib import Path

H = Path(__file__).parent
R = H / "RAW_T1"
E1 = H.parent / "comp8800_poster_e1" / "E1_points.csv"
TARGETS = (0.96, 0.965, 0.97, 0.975, 0.98)


def jhq_points(b, ds):
    acc = {}
    for f in sorted(R.glob(f"jhq_{b}_{ds}_np*_r*.txt")):
        np_ = int(re.search(r"_np(\d+)_r", f.name).group(1)); al = None
        for l in f.read_text().splitlines():
            m = re.search(r"=== alpha=(\d+)", l)
            if m:
                al = int(m.group(1)); continue
            m = re.match(r"\s+(-?\d+)\s+([0-9.]+)\s+[0-9.]+ ms\s+[0-9.]+ ms\s+(\d+)", l)
            if m and al is not None and m.group(1) == "-1":
                acc.setdefault((np_, al), []).append((float(m.group(2)), float(m.group(3))))
    return {k: (v[0][0], st.geometric_mean([q for _, q in v]), len(v)) for k, v in acc.items()}


def jsonl_points(path):
    pts = []
    if not path.exists():
        return pts
    for l in path.read_text().splitlines():
        r = json.loads(l)
        if r.get("type") == "point":
            pts.append((float(r["recall"]), float(r["A"]["qps_median"])))
    return pts


def frontier(p):
    p = sorted(p, key=lambda x: (-x[0], -x[1])); f, best = [], -1
    for rc, q in p:
        if q > best:
            f.append((rc, q)); best = q
    return sorted(f)


def interp(f, t, tol=5e-4):
    near = [q for r, q in f if abs(r - t) <= tol]
    if near:
        return max(near)
    for (r0, q0), (r1, q1) in zip(f, f[1:]):
        if r0 <= t <= r1 and r1 > r0:
            w = (t - r0) / (r1 - r0)
            return math.exp(math.log(q0) + w * (math.log(q1) - math.log(q0)))
    return None


e1 = {}
for r in csv.DictReader(open(E1)):
    try:
        e1.setdefault((r["dataset"], r["family"]), []).append((float(r["recall"]), float(r["qps_A"])))
    except ValueError:
        pass

L = ["# T1: TF32 sensitivity at recall 0.97, all methods in one session (2026-10-28)", "",
     "v69 = the thesis's measured configuration (TF32 rotation/centroid GEMMs at d >= 1536); v72 = FP32. "
     "IVF-RaBitQ and CAGRA fp32 re-measured in the same session at the configurations bracketing 0.97.", ""]
for ds in ("openai3-1536", "openai3-3072"):
    j69, j72 = jhq_points("v69", ds), jhq_points("v72", ds)
    keys = sorted(set(j69) & set(j72))
    pair = [j72[k][1] / j69[k][1] for k in keys]
    f = {"v69": frontier([(v[0], v[1]) for v in j69.values()]),
         "v72": frontier([(v[0], v[1]) for v in j72.values()]),
         "rabitq": frontier(jsonl_points(R / f"rabitq_{ds}.jsonl")),
         "cagra": frontier(jsonl_points(R / f"cuvs_{ds}_cagra.jsonl"))}
    fe1 = {k: frontier(e1[(ds, fam)]) for k, fam in (("v69", "JHQ-GPU v69"), ("rabitq", "IVF-RaBitQ"), ("cagra", "CAGRA fp32"))}
    L += [f"## {ds}", "",
          f"Paired JHQ configurations: {len(keys)}; v72/v69 QPS geometric mean {st.geometric_mean(pair):.3f} "
          f"(range {min(pair):.3f}-{max(pair):.3f}); recall v72-v69 {st.mean(j72[k][0] - j69[k][0] for k in keys):+.5f}.", "",
          "| target | v69 kQPS | v72 kQPS | RaBitQ kQPS | CAGRA kQPS | v69/RaBitQ | v72/RaBitQ | v69/CAGRA | v72/CAGRA | E1 v69/RaBitQ | E1 v69/CAGRA |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for t in TARGETS:
        q = {k: interp(v, t) for k, v in f.items()}
        qe = {k: interp(v, t) for k, v in fe1.items()}
        r = lambda a, b: f"{a / b:.3f}" if a and b else "—"
        k_ = lambda x: f"{x / 1000:.1f}" if x else "—"
        L.append(f"| {t} | {k_(q['v69'])} | {k_(q['v72'])} | {k_(q['rabitq'])} | {k_(q['cagra'])} | "
                 f"{r(q['v69'], q['rabitq'])} | {r(q['v72'], q['rabitq'])} | {r(q['v69'], q['cagra'])} | {r(q['v72'], q['cagra'])} | "
                 f"{r(qe['v69'], qe['rabitq'])} | {r(qe['v69'], qe['cagra'])} |")
    L += ["", "Session frontier points near 0.97:", ""]
    for k, v in f.items():
        L.append(f"- {k}: " + ", ".join(f"{rc:.4f}@{qq / 1000:.1f}k" for rc, qq in v if 0.95 <= rc <= 0.99))
    L.append("")
(H / "T1_SUMMARY.md").write_text("\n".join(L) + "\n")
print("\n".join(L))
