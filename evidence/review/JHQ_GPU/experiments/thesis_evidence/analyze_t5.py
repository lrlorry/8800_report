"""Summarise T5 (cross-system comparison at batch 8 and 32). Reads RAW_T5/, writes T5_SUMMARY.md.

Each method's non-dominated frontier per (dataset, batch) from this session's points; QPS at matched
recall interpolated as in Chapter 7 (linear in log QPS, no extrapolation, a measured recall within
5e-4 of the target counts). JHQ is reported on its scheduled path (G = -1, as deployed) and on the
one-block path (G = 0) to show what scheduling contributes at small batch. Baselines also carry the
median latency of their "null" call (staging, H2D, D2H, sync without search): the harness floor.
"""
import json, math, re, statistics as st
from pathlib import Path

H = Path(__file__).parent
R = H / "RAW_T5"
DS = ("vogue-768", "arxiv-768", "openai3-1536", "openai3-3072")
TARGETS = (0.90, 0.92, 0.94, 0.95, 0.96, 0.97, 0.98)
METHODS = ("cagra", "cagra-int8", "ivf-rabitq")
NAMES = {"cagra": "CAGRA fp32", "cagra-int8": "CAGRA int8", "ivf-rabitq": "IVF-RaBitQ"}


def jhq(ds):
    pts = {}   # (batch, G) -> [(recall, qps, lat_med)]
    for f in sorted(R.glob(f"jhq_{ds}_np*.txt")):
        b = None
        for l in f.read_text().splitlines():
            m = re.search(r"=== alpha=\S+ ck=\d+\s+b=(\d+):", l)
            if m:
                b = int(m.group(1)); continue
            m = re.match(r"\s+(-?\d+)\s+([0-9.]+)\s+([0-9.]+) ms\s+[0-9.]+ ms\s+(\d+)", l)
            if m and b is not None:
                pts.setdefault((b, int(m.group(1))), []).append((float(m.group(2)), float(m.group(4)), float(m.group(3))))
    return pts


def base(ds, m):
    pts, null = {}, {}
    files = [R / f"rabitq_{ds}.jsonl"] if m == "ivf-rabitq" else [R / f"cuvs_{ds}_{m}.jsonl"]
    for f in files:
        if not f.exists():
            continue
        for l in f.read_text().splitlines():
            r = json.loads(l)
            if r.get("type") != "point":
                continue
            b = int(r["batch"])
            pts.setdefault(b, []).append((float(r["recall"]), float(r["A"]["qps_median"]),
                                          st.median(r["A"]["lat_med_ms_rounds"])))
            null.setdefault(b, []).append(st.median(r["null"]["lat_med_ms_rounds"]))
    return pts, {b: st.median(v) for b, v in null.items()}


def frontier(p):
    p = sorted(p, key=lambda x: (-x[0], -x[1])); f, best = [], -1
    for t in p:
        if t[1] > best:
            f.append(t); best = t[1]
    return sorted(f)


def interp(f, t, tol=5e-4):
    near = [q for r, q, *_ in f if abs(r - t) <= tol]
    if near:
        return max(near)
    for a, b in zip(f, f[1:]):
        (r0, q0), (r1, q1) = a[:2], b[:2]
        if r0 <= t <= r1 and r1 > r0:
            w = (t - r0) / (r1 - r0)
            return math.exp(math.log(q0) + w * (math.log(q1) - math.log(q0)))
    return None


L = ["# T5: cross-system comparison at batch 8 and 32 (2026-10-28)", "",
     "One small-batch protocol for every method (JHQ's harness's): floor(nq/b) synchronous host-to-host calls "
     "of b queries, QPS = queries / summed call time, recall over the queries used; E1's environment "
     "(workspace pools). JHQ = v69, scheduled path unless marked G=0. Ratios > 1 favour JHQ.", ""]
summary = {}
for ds in DS:
    J = jhq(ds)
    B = {m: base(ds, m) for m in METHODS}
    for b in (8, 32):
        fj = frontier(J.get((b, -1), [])); fj0 = frontier(J.get((b, 0), []))
        fb = {m: frontier(B[m][0].get(b, [])) for m in METHODS}
        L += [f"## {ds}, batch {b}", "",
              "| target | JHQ kQPS | JHQ G=0 kQPS | " + " | ".join(f"{NAMES[m]} kQPS" for m in METHODS) + " | "
              + " | ".join(f"JHQ/{NAMES[m]}" for m in METHODS) + " |",
              "|---" * (3 + 2 * len(METHODS)) + "|"]
        for t in TARGETS:
            qj, qj0 = interp(fj, t), interp(fj0, t)
            qb = {m: interp(fb[m], t) for m in METHODS}
            k_ = lambda x: f"{x / 1000:.1f}" if x else "—"
            r_ = lambda a, c: f"{a / c:.2f}" if a and c else "—"
            L.append(f"| {t} | {k_(qj)} | {k_(qj0)} | " + " | ".join(k_(qb[m]) for m in METHODS) + " | "
                     + " | ".join(r_(qj, qb[m]) for m in METHODS) + " |")
            summary[f"{ds}/b{b}/{t}"] = {"jhq": qj, "jhq_g0": qj0, **{m: qb[m] for m in METHODS}}
        mx = {"JHQ": max((r for r, *_ in fj), default=0), **{NAMES[m]: max((r for r, *_ in fb[m]), default=0) for m in METHODS}}
        nl = {NAMES[m]: B[m][1].get(b) for m in METHODS}
        L += ["", "Max measured recall: " + ", ".join(f"{k} {v:.4f}" for k, v in mx.items()) + ".  "
              "Null-call median latency (harness floor): " + ", ".join(f"{k} {v:.3f} ms" for k, v in nl.items() if v) + ".", ""]
(H / "T5_SUMMARY.md").write_text("\n".join(L) + "\n")
(H / "t5_summary.json").write_text(json.dumps(summary, indent=1))
print("\n".join(L))
