// Strict CPU reference for the primary top-c and the final top-k (thesis Chapter 5; experiments/
// thesis_evidence, T4, 2026-10-28), on jhq_v73_topcref.
//
// The index is built exactly as demo_jhq_batch_pipeline builds it (trained-state cache, so the paper's
// state loads). For each alpha (JHQ_TR_ALPHAS), forced primary path G (JHQ_TR_GROUPS; 0 = the one-block
// scan, >= 1 grouped) and shared bound (JHQ_TR_SHARED), it searches JHQ_TR_NQ queries in one batch,
// then once more with JHQ_DUMP_TOPCK set: v73 writes every query's complete candidate scores (the
// dump kernel performs the scan's arithmetic in the scan's order) beside what the selector and the
// final selection returned. Per query, on the CPU:
//   score     every returned (position, primary distance) equals that position's dumped score, bit
//             for bit -- the dump is the scorer the selector saw
//   strict    sort all candidates by (distance, position); the first min(c, total) are the reference
//             top-c. G >= 1 promises exactly this, in order. G = 0 promises the distance preorder only:
//             everything strictly below the cutoff distance, then any members of the cutoff tie
//   pad       a query with fewer than c candidates returns sentinels in the remaining slots
//   final     the k returned ids are the exact top-k of the c refined scores under (score, id)
// One TR line per configuration; JHQ_TR_KEEP=1 keeps the dumps (the cross-binary table comparison).
//
// Usage: demo_jhq_batch_pipeline's, with <nprobe> fixed per process.

#ifndef JHQ_INDEX_HEADER
#define JHQ_INDEX_HEADER "jhq_v73_topcref/jhq_gpu_index.cuh"
#endif
#include JHQ_INDEX_HEADER
#include "common/fvecs_io.cuh"
#include "common/fvecs_mmap_io.cuh"

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <string>
#include <unordered_map>
#include <vector>

static std::vector<double> parse_list(const char* s, const char* dflt) {
    std::vector<double> v; std::string t = s ? s : dflt; size_t p = 0;
    while (p < t.size()) { size_t c = t.find(',', p); if (c == std::string::npos) c = t.size();
        if (c > p) v.push_back(atof(t.substr(p, c - p).c_str())); p = c + 1; }
    return v;
}

struct Tally {
    long long q = 0, cand = 0, score_mm = 0, set_eq = 0, order_eq = 0, preorder = 0, tie_only = 0,
              nontie = 0, pad_ok = 0, underfull = 0, cutoff_ties = 0, final_ok = 0, final_checked = 0;
};

int main(int argc, char** argv) {
    if (argc < 14) {
        fprintf(stderr, "Usage: %s <base> <query> <gt> <M> <B> <Br> <alpha> <k> <nlist> <nprobe> "
                        "<ivf_iters> <batch_size> <out_prefix> [kmeans_iters=5]\n", argv[0]);
        return 1;
    }
    const char* base_path = argv[1]; const char* query_path = argv[2];
    int M = atoi(argv[4]), B = atoi(argv[5]), Br = atoi(argv[6]);
    float alpha = (float)atof(argv[7]);
    int k = atoi(argv[8]), nlist = atoi(argv[9]), nprobe = atoi(argv[10]);
    int ivf_iters = atoi(argv[11]), batch_size = atoi(argv[12]);
    const std::string prefix = argv[13];
    int kmeans_iters = (argc > 14) ? atoi(argv[14]) : 5;

    std::vector<float> query; int d_query;
    MmapFloatMatrix base = load_fvecs_mmap(base_path);
    const int nb = base.n, d = base.d;
    const int nq_all = read_fvecs(query_path, query, d_query);

    // ---- the index, exactly as demo_jhq_batch_pipeline (cache key matches)
    jhq_gpu::JHQGpuIndex::Params p;
    p.M = M; p.B = B; p.Br = Br; p.alpha = alpha; p.nlist = nlist; p.nprobe = nprobe;
    p.ivf_iters = ivf_iters; p.batch_size = batch_size; p.kmeans_iters = kmeans_iters;
    if (const char* ab = std::getenv("JHQ_ADD_BATCH")) { const int v = std::atoi(ab); if (v > 0) p.add_batch = v; }
    jhq_gpu::JHQGpuIndex idx(d, p);
    int n_train = std::min(nb, 100000);
    if (const char* e = std::getenv("JHQ_N_TRAIN")) {
        const long long want = (std::strcmp(e, "all") == 0) ? nb : std::atoll(e);
        n_train = (want <= 0 || want > nb) ? nb : (int)want;
    }
    std::vector<float> sample; const float* train_src = base.data;
    if (n_train < nb) {
        sample.resize((size_t)n_train * d);
        const long long stride = (long long)nb / n_train;
        for (int i = 0; i < n_train; ++i)
            std::memcpy(sample.data() + (size_t)i * d, base.data + (size_t)(i * stride) * d, (size_t)d * sizeof(float));
        train_src = sample.data();
    }
    std::vector<float> res_sample; const float* res_src = base.data; int n_res_train = nb;
    if (const char* rt = std::getenv("JHQ_RES_TRAIN_N")) {
        n_res_train = std::atoi(rt);
        if (n_res_train <= 0 || n_res_train > nb) n_res_train = nb;
        if (n_res_train != nb) {
            res_sample.resize((size_t)n_res_train * d);
            const long long rstride = (long long)nb / n_res_train;
            for (int i = 0; i < n_res_train; ++i)
                std::memcpy(res_sample.data() + (size_t)i * d, base.data + (size_t)(i * rstride) * d, (size_t)d * sizeof(float));
            res_src = res_sample.data();
        }
    }
    idx.train(train_src, n_train, res_src, n_res_train);
    idx.add(base.data, nb);
    jhq_gpu::set_refine_lanes(std::getenv("JHQ_BP_LANES") ? std::atoi(std::getenv("JHQ_BP_LANES")) : 16);

    const int nq = std::min(nq_all, std::getenv("JHQ_TR_NQ") ? std::atoi(std::getenv("JHQ_TR_NQ")) : 256);
    const bool keep = std::getenv("JHQ_TR_KEEP") && std::getenv("JHQ_TR_KEEP")[0] == '1';
    std::vector<float> od((size_t)nq * k); std::vector<int> oi((size_t)nq * k);
    FILE* js = std::fopen((prefix + ".jsonl").c_str(), "a");

    for (double a : parse_list(std::getenv("JHQ_TR_ALPHAS"), "4,100,200"))
    for (double gd : parse_list(std::getenv("JHQ_TR_GROUPS"), "0,1,2,4,8"))
    for (double sh : parse_list(std::getenv("JHQ_TR_SHARED"), "0,1")) {
        const int G = (int)gd;
        idx.set_alpha((float)a);
        jhq_gpu::set_primary_groups(G);
        jhq_gpu::set_shared_bound(sh != 0);
        idx.search(query.data(), nq, k, od.data(), oi.data());               // capture, warm
        char path[512];
        std::snprintf(path, sizeof path, "%s_np%d_a%g_G%d_sh%d.topc", prefix.c_str(), nprobe, a, G, (int)sh);
        setenv("JHQ_DUMP_TOPCK", path, 1);
        idx.search(query.data(), nq, k, od.data(), oi.data());
        unsetenv("JHQ_DUMP_TOPCK");

        FILE* f = std::fopen(path, "rb");
        if (!f) { fprintf(stderr, "no dump %s\n", path); return 2; }
        int hdr[9];
        if (std::fread(hdr, sizeof(int), 9, f) != 9 || hdr[0] != 0x43504F54) { fprintf(stderr, "bad dump\n"); return 2; }
        const int Bq = hdr[1], ck = hdr[2], kk = hdr[3], effG = hdr[6], shf = hdr[7], lutg = hdr[8];
        Tally t;
        for (int q = 0; q < Bq; ++q) {
            int tot = 0;
            if (std::fread(&tot, sizeof(int), 1, f) != 1) { fprintf(stderr, "short dump\n"); return 2; }
            std::vector<float> ad(tot), tdist(ck), cd(ck), fd(kk);
            std::vector<int> ap(tot), tpos(ck), cid(ck), fi(kk);
            auto rd = [&](void* p2, size_t sz, size_t n) { if (std::fread(p2, sz, n, f) != n) { fprintf(stderr, "short\n"); std::exit(2); } };
            rd(ad.data(), 4, tot); rd(ap.data(), 4, tot); rd(tdist.data(), 4, ck); rd(tpos.data(), 4, ck);
            rd(cd.data(), 4, ck); rd(cid.data(), 4, ck); rd(fd.data(), 4, kk); rd(fi.data(), 4, kk);
            ++t.q; t.cand += tot;
            std::unordered_map<int, float> score_of; score_of.reserve(tot * 2);
            for (int i = 0; i < tot; ++i) score_of[ap[i]] = ad[i];
            // returned entries: valid positions only
            std::vector<std::pair<float, int>> got;
            for (int i = 0; i < ck; ++i) {
                const int ps = tpos[i];
                if (ps < 0 || ps >= nb) continue;
                got.push_back({tdist[i], ps});
                auto it = score_of.find(ps);
                if (it == score_of.end() || std::memcmp(&it->second, &tdist[i], 4) != 0) ++t.score_mm;
            }
            const int vc = std::min(ck, tot);
            if (tot < ck) ++t.underfull;
            if ((int)got.size() == vc) ++t.pad_ok;
            // strict reference under (distance, position)
            std::vector<std::pair<float, int>> all(tot);
            for (int i = 0; i < tot; ++i) all[i] = {ad[i], ap[i]};
            std::sort(all.begin(), all.end());
            std::vector<std::pair<float, int>> ref(all.begin(), all.begin() + vc);
            std::vector<std::pair<float, int>> gs = got; std::sort(gs.begin(), gs.end());
            const bool set_eq = (gs == ref);
            const bool order_eq = (got == ref);
            t.set_eq += set_eq; t.order_eq += order_eq;
            bool pre = ((int)got.size() == vc);
            if (vc > 0) {
                const float cut = ref[vc - 1].first;
                long long below_ref = 0, below_got = 0, at_cut_all = 0, at_cut_ref = 0;
                for (auto& x : ref) { if (x.first < cut) ++below_ref; else if (x.first == cut) ++at_cut_ref; }
                for (auto& x : all) if (x.first == cut) ++at_cut_all;
                if (at_cut_all > at_cut_ref) ++t.cutoff_ties;
                std::vector<int> gp; for (auto& x : got) { if (x.first < cut) ++below_got; if (x.first > cut) pre = false; gp.push_back(x.second); }
                std::sort(gp.begin(), gp.end());
                if (std::adjacent_find(gp.begin(), gp.end()) != gp.end()) pre = false;
                if (below_got != below_ref) pre = false;
            }
            t.preorder += pre;
            if (!set_eq) { if (pre) ++t.tie_only; else ++t.nontie; }
            // final top-k: exact top-k of the c refined scores under (score, database id)
            std::vector<std::pair<float, int>> fin;
            for (int i = 0; i < ck; ++i) if (tpos[i] >= 0 && tpos[i] < nb) fin.push_back({cd[i], cid[i]});
            std::sort(fin.begin(), fin.end());
            if ((int)fin.size() >= kk) {
                ++t.final_checked;
                bool ok = true;
                for (int i = 0; i < kk; ++i)
                    if (fin[i].second != fi[i] || std::memcmp(&fin[i].first, &fd[i], 4) != 0) { ok = false; break; }
                t.final_ok += ok;
            }
        }
        std::fclose(f);
        if (!keep) std::remove(path);
        printf("TR np=%d a=%g G=%d sh=%d effG=%d lutg=%d q=%lld cand_mean=%.0f score_mm=%lld set_eq=%lld order_eq=%lld "
               "preorder=%lld tie_only=%lld nontie=%lld pad_ok=%lld underfull=%lld cutoff_ties=%lld final_ok=%lld/%lld\n",
               nprobe, a, G, (int)sh, effG, lutg, t.q, (double)t.cand / std::max(1LL, t.q), t.score_mm, t.set_eq,
               t.order_eq, t.preorder, t.tie_only, t.nontie, t.pad_ok, t.underfull, t.cutoff_ties, t.final_ok, t.final_checked);
        fflush(stdout);
        if (js) {
            std::fprintf(js, "{\"nprobe\":%d,\"alpha\":%g,\"G\":%d,\"shared\":%d,\"effG\":%d,\"shared_flag\":%d,\"lut_groups\":%d,"
                             "\"queries\":%lld,\"cand_mean\":%.1f,\"score_mismatch\":%lld,\"set_equal\":%lld,\"order_equal\":%lld,"
                             "\"preorder_ok\":%lld,\"tie_only\":%lld,\"nontie\":%lld,\"pad_ok\":%lld,\"underfull\":%lld,"
                             "\"cutoff_ties\":%lld,\"final_ok\":%lld,\"final_checked\":%lld,\"ck\":%d}\n",
                         nprobe, a, G, (int)sh, effG, shf, lutg, t.q, (double)t.cand / std::max(1LL, t.q), t.score_mm,
                         t.set_eq, t.order_eq, t.preorder, t.tie_only, t.nontie, t.pad_ok, t.underfull, t.cutoff_ties,
                         t.final_ok, t.final_checked, ck);
            std::fflush(js);
        }
    }
    if (js) std::fclose(js);
    printf("=== TR_OK ===\n");
    return 0;
}
