#!/usr/bin/env python3
"""Thesis evidence T5 (2026-10-28): experiments/comp8800_poster_e1/bench_cuvs.py at small batch sizes.

Everything but the timed protocol is E1's file unchanged (datasets, builds, sweeps, records). The
protocol is JHQ's harness's small-batch one: floor(nq / B) batches of B, one synchronous host-to-host
call per batch, a round = one pass, QPS = queries / summed call time, recall over the queries used;
plus a "null" call (staging, H2D, D2H, sync, no search) that shows this binding's per-call floor.
E1's file is untouched.

---- E1's docstring follows ----
COMP8800 poster, experiment E1: the cuVS baselines on the protocol JHQ v69's harness measures.

    python3 bench_cuvs.py --dataset arxiv-768 --method cagra --out RAW/cuvs_arxiv-768_cagra.jsonl

Methods: cagra (fp32 dataset), cagra-int8 (cuVS scalar quantiser), ivfpq, ivfpq-refine (IVF-PQ
candidates re-ranked exactly against the fp32 dataset held on the device), bruteforce.

Protocol A, host to host -- the poster's. One timed call answers the whole query set and runs:
    copy the original host fp32 queries into a pinned staging buffer (JHQ's search() makes the
    same memcpy) -> H2D -> [cagra-int8: scalar-quantise the queries on the device] -> search
    [ivfpq-refine: -> exact re-rank] -> D2H of the ids and the distances -> synchronise.
Protocol B, device resident -- auxiliary. The queries are already on the device (for cagra-int8
already quantised): search (and re-rank) only, then synchronise.

What changed against scripts/bench_all.py, every item in the baseline's favour or neutral:
  * each index is built once and every search parameter is swept on it (bench_all rebuilt the
    index for every search parameter, so a sweep cost one build per point);
  * one cuVS Resources handle on one stream and preallocated outputs serve every call, as JHQ
    reuses its workspace (bench_all let every call create a handle and allocate its outputs);
  * the queries go up from pinned memory, as JHQ's do (bench_all copied from pageable memory);
  * cagra-int8 now quantises the queries inside the timed call (bench_all quantised them once,
    outside it, so its "host to host" number left out a step the method cannot skip).

Each point: WARMUP untimed calls, then ROUNDS rounds of CALLS timed calls (JHQ's harness: one
untimed call, then 24 timed, per round), every call's time kept. Slow points (a call over
SLOW_MS) run fewer calls a round so the sweep stays bounded; the record says how many.

Output: one JSON object per line -- "meta", "index", "point" and "failure" records. Failures
are results and are never dropped.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import traceback

import numpy as np

DATASETS = {
    # name: (base, query, groundtruth, d, N)
    "vogue-768": ("/root/data/vogue-768_base.fvecs", "/root/data/vogue-768_query.fvecs",
                  "/root/data/vogue-768_groundtruth.ivecs", 768, 932328),
    "arxiv-768": ("/root/autodl-tmp/arxiv-abstracts-768/base.fvecs",
                  "/root/autodl-tmp/arxiv-abstracts-768/query.fvecs",
                  "/root/autodl-tmp/arxiv-abstracts-768/groundtruth.ivecs", 768, 2253000),
    "openai3-1536": ("/root/autodl-tmp/openai3-1536/base.fvecs",
                     "/root/autodl-tmp/openai3-1536/query.fvecs",
                     "/root/autodl-tmp/openai3-1536/groundtruth.ivecs", 1536, 999000),
    "openai3-3072": ("/root/autodl-tmp/openai3-3072/base.fvecs",
                     "/root/autodl-tmp/openai3-3072/query.fvecs",
                     "/root/autodl-tmp/openai3-3072/groundtruth.ivecs", 3072, 999000),
    "bge-m3": ("/root/autodl-tmp/bge-m3/base.fvecs", "/root/autodl-tmp/bge-m3/query.fvecs",
               "/root/autodl-tmp/bge-m3/groundtruth.ivecs", 1024, 10091524),
    "stella": ("/root/autodl-tmp/stella-trec24/base.fvecs", "/root/autodl-tmp/stella-trec24/query.fvecs",
               "/root/autodl-tmp/stella-trec24/groundtruth.ivecs", 1024, 17776615),
}
K = 10


def fvecs(path):
    """One float32 copy of an .fvecs file (memmap, then row blocks), as bench_all's _fvecs."""
    mm = np.memmap(path, dtype=np.int32, mode="r")
    d = int(mm[0])
    n = mm.size // (d + 1)
    out = np.empty((n, d), dtype=np.float32)
    step = 1 << 19
    for i in range(0, n, step):
        j = min(i + step, n)
        out[i:j] = np.asarray(mm[i * (d + 1):j * (d + 1)]).reshape(-1, d + 1)[:, 1:].view(np.float32)
    del mm
    return out


def ivecs(path):
    a = np.fromfile(path, dtype=np.int32)
    d = int(a[0])
    return np.ascontiguousarray(a.reshape(-1, d + 1)[:, 1:])


def recall_at_k(ids, gt, k=K):
    """|returned top-k ∩ true top-k| / k averaged over queries -- common/recall.cuh's definition."""
    hits = 0
    for i in range(ids.shape[0]):
        hits += len(set(ids[i, :k].tolist()) & set(gt[i, :k].tolist()))
    return hits / (ids.shape[0] * k)


def id_checks(ids, n):
    """Out-of-range ids (including cuVS's sentinels) and rows that repeat an id."""
    bad = int(((ids < 0) | (ids >= n)).sum())
    dup_rows = int(sum(1 for r in ids if len(set(r.tolist())) != len(r)))
    return bad, dup_rows


def row_diffs(a, b):
    """Rows of b holding a different id set from a, and rows equal as sets but in another order."""
    set_diff = order_diff = 0
    for x, y in zip(a, b):
        if np.array_equal(x, y):
            continue
        if np.array_equal(np.sort(x), np.sort(y)):
            order_diff += 1
        else:
            set_diff += 1
    return set_diff, order_diff


def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True, choices=sorted(DATASETS))
    ap.add_argument("--method", required=True,
                    choices=["cagra", "cagra-int8", "ivfpq", "ivfpq-refine", "bruteforce"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--graph-degrees", default="32,64")
    ap.add_argument("--itopk", default="32,64,96,128,192,256,384,512")
    ap.add_argument("--search-width", default="1,2,4,8")
    ap.add_argument("--nlist", type=int, default=4096)
    ap.add_argument("--trainset-fraction", type=float, default=0.0,
                    help="IVF-PQ kmeans_trainset_fraction; 0 keeps cuVS's default (0.5)")
    ap.add_argument("--pq-dims", default="192,384,768")
    ap.add_argument("--nprobe", default="16,32,64,96,128,192,256,384,512")
    ap.add_argument("--lut", default="f32,f16", help="IVF-PQ lut/internal dtype pairs: f32 or f16")
    ap.add_argument("--refine-ratios", default="2,4,8")
    ap.add_argument("--warmup", type=int, default=3)
    ap.add_argument("--rounds", type=int, default=5)
    ap.add_argument("--calls", type=int, default=24)
    ap.add_argument("--slow-ms", type=float, default=40.0)
    ap.add_argument("--no-b", action="store_true", help="unused here: small-batch protocol A only")
    ap.add_argument("--batches", default="8,32", help="batch sizes, each a full pass of floor(nq/B) batches")
    a = ap.parse_args()
    a.batches = [int(x) for x in a.batches.split(",") if x]

    import cupy as cp
    from cuvs.common import Resources
    from cuvs.neighbors import brute_force, cagra, ivf_pq
    from cuvs.neighbors import refine as cuvs_refine
    from cuvs.preprocessing.quantize import scalar

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    fh = open(a.out, "a")

    def emit(rec):
        rec["utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        fh.write(json.dumps(rec) + "\n")
        fh.flush()

    def mem_used_mib():
        free, total = cp.cuda.runtime.memGetInfo()
        return (total - free) / 2**20

    def mem_note():
        try:
            free, total = cp.cuda.runtime.memGetInfo()
            return f"device free {free / 2**30:.2f} of {total / 2**30:.2f} GiB"
        except Exception:
            return "device memory unreadable"

    base, query, gtp, d, N = DATASETS[a.dataset]
    repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    # A handle built on a cupy stream (Resources(stream=...)) segfaults cuVS 26.08's build and search,
    # blocking or not. The default handle works; its stream, read back through the C API
    # (cuvsStreamGet), is the per-thread default stream, so cupy's uploads and downloads go on
    # that same stream and a call synchronises once, at its end, as JHQ's does.
    stream = cp.cuda.Stream.ptds
    pool_mode = os.environ.get("CUVS_POOL", "") == "1"
    import rmm
    plain_mr = rmm.mr.CudaMemoryResource()
    rmm.mr.set_current_device_resource(plain_mr)
    res = Resources()
    cp.cuda.runtime.deviceSynchronize()
    ctx_mib = mem_used_mib()          # CUDA context and the libraries, before anything of ours

    xq = fvecs(query)
    gt = ivecs(gtp)
    if gt.shape[1] < K or gt.shape[0] < xq.shape[0]:
        raise SystemExit(f"ground truth {gt.shape} cannot score {xq.shape[0]} queries at k={K}")
    nq = xq.shape[0]
    # Methods that hold the whole fp32 dataset on the device cannot run on a set larger than the
    # card. Say so with the arithmetic instead of loading 41-73 GB into host memory (minutes, and
    # most of the 90 GiB cgroup) only to watch the allocation fail: the record says "not attempted".
    max_deg = max(int(x) for x in a.graph_degrees.split(",") if x)
    need = {"cagra": N * (4 * d + 4 * max_deg), "bruteforce": N * 4 * d,
            "ivfpq-refine": N * 4 * d}.get(a.method)
    free_b, total_b = cp.cuda.runtime.memGetInfo()
    if need is not None and need > total_b:
        emit({"type": "failure", "dataset": a.dataset, "method": a.method, "label": "not attempted",
              "index": {}, "search": None,
              "error": f"not attempted (computed): the index holds the fp32 dataset on the device, "
                       f"{need / 2**30:.1f} GiB, and the card has {total_b / 2**30:.1f} GiB",
              "mem": f"device total {total_b / 2**30:.2f} GiB"})
        print(f"NOT ATTEMPTED {a.method} {a.dataset}: needs {need / 2**30:.1f} GiB", file=sys.stderr)
        print("BENCH_CUVS_DONE", file=sys.stderr, flush=True)
        return
    t_load = time.perf_counter()
    xb = fvecs(base)
    t_load = time.perf_counter() - t_load
    if xb.shape != (N, d):
        raise SystemExit(f"base {xb.shape} != expected {(N, d)}")
    emit({"type": "meta", "dataset": a.dataset, "method": a.method, "n": N, "d": d, "nq": nq,
          "gt_width": int(gt.shape[1]), "k": K, "argv": sys.argv,
          "commit": sh(f"git -C {repo} rev-parse --short HEAD"),
          "dirty": bool(sh(f"git -C {repo} status --porcelain -- experiments/comp8800_poster_e1")),
          "gpu": sh("nvidia-smi --query-gpu=name,driver_version --format=csv,noheader"),
          "cuvs": __import__("cuvs").__version__, "cupy": cp.__version__, "numpy": np.__version__,
          "loadavg": sh("cat /proc/loadavg"), "ctx_mib": round(ctx_mib, 1),
          "base_load_s": round(t_load, 2), "protocol_A": "pinned staging + H2D + [quantise] + search "
          "[+ refine] + D2H ids and distances + sync", "protocol_B": "resident queries, search only + sync"})

    def pinned(shape, dtype):
        count = int(np.prod(shape))
        mem = cp.cuda.alloc_pinned_memory(count * np.dtype(dtype).itemsize)
        return np.frombuffer(mem, dtype, count).reshape(shape)

    # buffers shared by every method and point, allocated before any index is measured
    pin_q = pinned((nq, d), np.float32)
    q_dev = cp.empty((nq, d), cp.float32)          # protocol A's upload target
    q_res = cp.asarray(xq)                          # protocol B's resident queries
    q8_dev = cp.empty((nq, d), cp.int8)
    q8_res = cp.empty((nq, d), cp.int8)
    # CAGRA writes uint32 neighbours (its docstring says int64; 26.08 rejects int64), the others int64
    id_t = np.uint32 if a.method in ("cagra", "cagra-int8") else np.int64
    ids_dev = cp.empty((nq, K), id_t)
    dist_dev = cp.empty((nq, K), cp.float32)
    idsB_dev = cp.empty((nq, K), id_t)
    distB_dev = cp.empty((nq, K), cp.float32)
    pin_ids = pinned((nq, K), id_t)
    pin_dist = pinned((nq, K), np.float32)
    pin_ids2 = pinned((nq, K), id_t)          # the null call's targets
    pin_dist2 = pinned((nq, K), np.float32)
    cp.cuda.runtime.deviceSynchronize()

    def search_handle():
        """The handle searches use. CUVS_POOL=1: search-time allocations come from an RMM pool
        (cuVS's own benchmark harness runs behind one), switched on only after a build so index
        memory is still measured on plain cudaMalloc; a handle's workspace follows the device
        resource current when it is created, so a fresh handle is made."""
        nonlocal res
        if pool_mode:
            rmm.mr.set_current_device_resource(rmm.mr.PoolMemoryResource(plain_mr, initial_pool_size=1 << 30))
            res = Resources()
        return res

    def plain_handle():
        nonlocal res
        if pool_mode:
            rmm.mr.set_current_device_resource(plain_mr)
            res = Resources()

    def measure(label, index_rec, sparams, search_into, quantise=None):
        """Small-batch protocol A (thesis evidence T5), with JHQ's harness's definitions
        (examples/demo_jhq_batch_pipeline.cu): the queries are cut into floor(nq / B) consecutive
        batches of exactly B; one call answers one batch host to host -- pinned staging -> H2D ->
        [cagra-int8: quantise] -> search -> D2H ids and distances -> synchronise -- and is timed on its
        own; a round is one pass over all batches; QPS = queries used / summed call time; recall over
        the queries used. "null" is the same call without the search (and quantiser): the host and
        transfer floor this Python binding pays per call, reported beside the result."""
        for B in a.batches:
            nbt = nq // B
            nused = nbt * B

            def call_a(i):
                s, e = i * B, (i + 1) * B
                np.copyto(pin_q[s:e], xq[s:e])
                q_dev[s:e].set(pin_q[s:e], stream=stream)
                if quantise is not None:
                    quantise(q_dev[s:e], q8_dev[s:e])
                    search_into(q8_dev[s:e], ids_dev[s:e], dist_dev[s:e])
                else:
                    search_into(q_dev[s:e], ids_dev[s:e], dist_dev[s:e])
                ids_dev[s:e].get(stream=stream, out=pin_ids[s:e], blocking=False)
                dist_dev[s:e].get(stream=stream, out=pin_dist[s:e], blocking=False)
                stream.synchronize()

            def call_null(i):
                s, e = i * B, (i + 1) * B
                np.copyto(pin_q[s:e], xq[s:e])
                q_dev[s:e].set(pin_q[s:e], stream=stream)
                ids_dev[s:e].get(stream=stream, out=pin_ids2[s:e], blocking=False)
                dist_dev[s:e].get(stream=stream, out=pin_dist2[s:e], blocking=False)
                stream.synchronize()

            try:
                t = time.perf_counter()
                call_a(0)
                first_ms = (time.perf_counter() - t) * 1e3
                for i in range(nbt):            # warm-up pass, which is also the recall pass
                    call_a(i)
                ref = pin_ids[:nused].astype(np.int64)
                rec = recall_at_k(ref, gt)
                bad, dup = id_checks(ref, N)

                def rounds(fn):
                    out = []
                    for _ in range(a.rounds):
                        ts = []
                        for i in range(nbt):
                            t0 = time.perf_counter()
                            fn(i)
                            ts.append((time.perf_counter() - t0) * 1e3)
                        out.append(ts)
                    return out

                ta = rounds(call_a)
                last = pin_ids[:nused].astype(np.int64)
                deterministic = bool(np.array_equal(ref, last))
                tn = rounds(call_null)

                def summ(tt):
                    q = [nused / (sum(r) / 1e3) for r in tt]
                    lat_med = [float(np.median(r)) for r in tt]
                    lat_p95 = [float(np.percentile(r, 95)) for r in tt]
                    return {"qps_rounds": [round(x, 1) for x in q], "qps_median": round(float(np.median(q)), 1),
                            "qps_min": round(min(q), 1), "qps_max": round(max(q), 1),
                            "lat_med_ms_rounds": [round(x, 4) for x in lat_med],
                            "lat_p95_ms_rounds": [round(x, 4) for x in lat_p95]}

                point = {"type": "point", "dataset": a.dataset, "method": a.method, "label": label, "pool": pool_mode,
                         "index": index_rec, "search": sparams, "batch": B, "nused": nused, "recall": round(rec, 6),
                         "invalid_ids": bad, "dup_rows": dup, "deterministic": deterministic,
                         "first_call_ms": round(first_ms, 3), "rounds": a.rounds, "calls_per_round": nbt,
                         "mem_used_mib": round(mem_used_mib(), 1), "A": summ(ta), "null": summ(tn)}
                emit(point)
                print(f"  {label} b={B} {sparams} R={rec:.4f} A={point['A']['qps_median']:.0f} "
                      f"lat={point['A']['lat_med_ms_rounds'][0]:.3f}ms null_lat={point['null']['lat_med_ms_rounds'][0]:.3f}ms "
                      f"bad={bad} dup={dup} det={deterministic}", file=sys.stderr, flush=True)
            except Exception as ex:
                emit({"type": "failure", "dataset": a.dataset, "method": a.method, "label": label, "batch": B,
                      "index": index_rec, "search": sparams, "error": f"{type(ex).__name__}: {str(ex)[:400]}",
                      "trace": traceback.format_exc()[-1500:], "mem": mem_note()})
                print(f"  FAILED {label} b={B} {sparams}: {ex}", file=sys.stderr, flush=True)

    def built(kind, params, build_fn):
        """Build once, record time and the device memory the index holds."""
        plain_handle()
        cp.get_default_memory_pool().free_all_blocks()
        cp.cuda.runtime.deviceSynchronize()
        m0 = mem_used_mib()
        t0 = time.perf_counter()
        try:
            # Builds run on cuVS's default resources: handing them the search handle (a cupy
            # stream) segfaulted cagra.build on a host dataset. Only the timed search path uses
            # the reused handle.
            idx = build_fn()
            cp.cuda.runtime.deviceSynchronize()
        except Exception as ex:
            emit({"type": "failure", "dataset": a.dataset, "method": a.method, "label": kind,
                  "index": params, "search": None, "error": f"{type(ex).__name__}: {str(ex)[:400]}",
                  "trace": traceback.format_exc()[-1500:], "mem": mem_note()})
            print(f"  BUILD FAILED {kind} {params}: {ex}", file=sys.stderr, flush=True)
            return None, None
        build_s = time.perf_counter() - t0
        cp.get_default_memory_pool().free_all_blocks()
        m1 = mem_used_mib()
        rec = dict(params, kind=kind, build_s=round(build_s, 3), index_mib=round(m1 - m0, 1),
                   mem_used_after_build_mib=round(m1, 1), ctx_mib=round(ctx_mib, 1))
        emit(dict(rec, type="index", dataset=a.dataset, method=a.method))
        print(f"  built {kind} {params}: {build_s:.1f} s, {m1 - m0:.0f} MiB", file=sys.stderr, flush=True)
        search_handle()
        return idx, rec

    ints = lambda s: [int(x) for x in s.split(",") if x]
    dtypes = {"f32": np.float32, "f16": np.float16}

    if a.method in ("cagra", "cagra-int8"):
        quantise = None
        data = xb
        extra = {}
        if a.method == "cagra-int8":
            # the quantiser belongs to the dataset, not to a search parameter: trained once,
            # bench_all's choice of quantile kept
            t0 = time.perf_counter()
            qz = scalar.train(scalar.QuantizerParams(quantile=0.99), xb)
            data = scalar.transform(qz, xb)
            data = np.asarray(data) if not hasattr(data, "__cuda_array_interface__") else data
            extra = {"quantile": 0.99, "quantise_dataset_s": round(time.perf_counter() - t0, 3)}
            del xb                              # the int8 index never reads it; Stella's is 73 GB
            import gc
            gc.collect()
            scalar.transform(qz, q_res, output=q8_res, resources=res)
            res.sync()

            def quantise(src, dst):
                scalar.transform(qz, src, output=dst, resources=res)
        for gd in ints(a.graph_degrees):
            p = dict(graph_degree=gd, intermediate_graph_degree=128, build_algo="ivf_pq", **extra)
            idx, irec = built(a.method, p, lambda: cagra.build(
                cagra.IndexParams(graph_degree=gd, intermediate_graph_degree=128), data))
            if idx is None:
                continue
            for it in ints(a.itopk):
                for sw in ints(a.search_width):
                    sp = cagra.SearchParams(itopk_size=it, search_width=sw)

                    def search_into(qin, ids_out, dist_out, sp=sp, idx=idx):
                        cagra.search(sp, idx, qin, K, neighbors=ids_out, distances=dist_out, resources=res)
                    measure(f"{a.method}-gd{gd}", irec, {"itopk_size": it, "search_width": sw},
                            search_into, quantise)
            del idx
    elif a.method in ("ivfpq", "ivfpq-refine"):
        ratios = ints(a.refine_ratios) if a.method == "ivfpq-refine" else [1]
        raw = {}
        xb_dev = None
        if a.method == "ivfpq-refine":
            # the exact re-rank reads the fp32 dataset on the device: part of this method's
            # footprint, uploaded once and recorded beside every index it serves
            m0 = mem_used_mib()
            xb_dev = cp.asarray(xb)
            cp.cuda.runtime.deviceSynchronize()
            raw = {"raw_fp32_on_device_mib": round(mem_used_mib() - m0, 1)}
        cand = {r: (cp.empty((nq, K * r), cp.int64), cp.empty((nq, K * r), cp.float32)) for r in ratios}
        for pd in ints(a.pq_dims):
            p = dict(n_lists=a.nlist, pq_dim=pd, pq_bits=8, code_bytes_per_vec=pd, **raw)
            kp = {"kmeans_trainset_fraction": a.trainset_fraction} if a.trainset_fraction > 0 else {}
            if kp:
                p["kmeans_trainset_fraction"] = a.trainset_fraction
            idx, irec = built(a.method, p, lambda pd=pd: ivf_pq.build(
                ivf_pq.IndexParams(n_lists=a.nlist, pq_dim=pd, pq_bits=8, **kp), xb))
            if idx is None:
                continue
            for lut in a.lut.split(","):
                for np_ in ints(a.nprobe):
                    for r in ratios:
                        sp = ivf_pq.SearchParams(n_probes=np_, lut_dtype=dtypes[lut],
                                                 internal_distance_dtype=dtypes[lut])
                        if a.method == "ivfpq":
                            def search_into(qin, ids_out, dist_out, sp=sp, idx=idx):
                                ivf_pq.search(sp, idx, qin, K, neighbors=ids_out, distances=dist_out,
                                              resources=res)
                        else:
                            def search_into(qin, ids_out, dist_out, sp=sp, idx=idx, r=r):
                                cv, cd = cand[r]
                                ivf_pq.search(sp, idx, qin, K * r, neighbors=cv, distances=cd, resources=res)
                                cuvs_refine(xb_dev, qin, cv, K, indices=ids_out, distances=dist_out,
                                            resources=res)
                        measure(f"{a.method}-pq{pd}-{lut}", irec,
                                {"n_probes": np_, "lut": lut, "refine_ratio": r}, search_into)
            del idx
    elif a.method == "bruteforce":
        holder = {}

        def build_fn():
            holder["xb"] = cp.asarray(xb)              # the index reads it: keep it alive
            return brute_force.build(holder["xb"], metric="sqeuclidean")
        idx, irec = built("bruteforce", {"metric": "sqeuclidean", "dtype": "fp32"}, build_fn)
        if idx is not None:
            def search_into(qin, ids_out, dist_out):
                brute_force.search(idx, qin, K, neighbors=ids_out, distances=dist_out, resources=res)
            measure("bruteforce-fp32", irec, {}, search_into)
    print("BENCH_CUVS_DONE", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
