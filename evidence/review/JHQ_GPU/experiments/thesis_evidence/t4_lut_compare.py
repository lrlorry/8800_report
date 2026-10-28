"""T4 table comparison (thesis evidence, 2026-10-28): the same queries' complete primary scores under the
full 256-entry table (JHQ_LUT_GROUPS=1) and the 16+16 / 4-way / 8-way factorisations, from the dumps
demo_jhq_v73_g<G>_topcref kept (one binary per table form; probes are identical across them, so the
candidate lists align position for position). Reference: g=2, the evaluated configuration.

    python3 t4_lut_compare.py <RAW_T4 dir>   -> prints a table and writes lut_compare.json
"""
import json, sys
from pathlib import Path
import numpy as np

R = Path(sys.argv[1])


def read(path):
    b = np.fromfile(path, dtype=np.int32)
    assert b[0] == 0x43504F54, path
    Bq, ck, k = int(b[1]), int(b[2]), int(b[3])
    o = 9; qs = []
    for _ in range(Bq):
        tot = int(b[o]); o += 1
        ad = b[o:o + tot].view(np.float32); o += tot
        ap = b[o:o + tot]; o += tot
        td = b[o:o + ck].view(np.float32); o += ck
        tp = b[o:o + ck]; o += ck
        cd = b[o:o + ck].view(np.float32); o += ck
        ci = b[o:o + ck]; o += ck
        fd = b[o:o + k].view(np.float32); o += k
        fi = b[o:o + k]; o += k
        qs.append(dict(ad=ad, ap=ap, td=td, tp=tp, fd=fd, fi=fi))
    return ck, qs


out = {}
lines = ["| dataset | path | table | cand./query | scores differing | max abs diff | max rel diff | "
         "top-c set differs | top-c order differs | final ids differ | final dist max diff |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for ds in sorted({p.name.split("_lut")[0] for p in R.glob("*_lutg2_np*.topc")}):
    for path in ("G0_sh1", "G2_sh1"):
        refp = next(R.glob(f"{ds}_lutg2_np*_{path}.topc"), None)
        if refp is None:
            continue
        ck, ref = read(refp)
        for g in (1, 4, 8):
            cp = next(R.glob(f"{ds}_lutg{g}_np*_{path}.topc"), None)
            if cp is None:
                continue
            _, cmp_ = read(cp)
            n = diff = setd = ordd = fid = 0; mabs = mrel = fdd = 0.0
            for a, b in zip(ref, cmp_):
                assert np.array_equal(a["ap"], b["ap"]), "candidate lists do not align"
                n += len(a["ad"])
                x, y = a["ad"].astype(np.float64), b["ad"].astype(np.float64)
                dmask = a["ad"].view(np.int32) != b["ad"].view(np.int32)
                diff += int(dmask.sum())
                if dmask.any():
                    mabs = max(mabs, float(np.abs(x - y).max()))
                    mrel = max(mrel, float((np.abs(x - y) / np.maximum(np.abs(x), 1e-30)).max()))
                va, vb = a["tp"][a["tp"] >= 0], b["tp"][b["tp"] >= 0]
                setd += int(set(va.tolist()) != set(vb.tolist()))
                ordd += int(not np.array_equal(va, vb))
                fid += int(not np.array_equal(a["fi"], b["fi"]))
                fdd = max(fdd, float(np.abs(a["fd"].astype(np.float64) - b["fd"].astype(np.float64)).max()))
            q = len(ref)
            out[f"{ds}/{path}/g{g}"] = dict(queries=q, candidates=n, scores_differing=diff, max_abs=mabs, max_rel=mrel,
                                            topc_set_differs=setd, topc_order_differs=ordd, final_ids_differ=fid,
                                            final_dist_max_diff=fdd)
            lines.append(f"| {ds} | {path} | g={g} vs 2 | {n / q:.0f} | {diff} ({diff / max(1, n):.2e}) | {mabs:.2e} | "
                         f"{mrel:.2e} | {setd}/{q} | {ordd}/{q} | {fid}/{q} | {fdd:.2e} |")
(R / "lut_compare.json").write_text(json.dumps(out, indent=1))
print("\n".join(lines))
