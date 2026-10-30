# Thesis2 contribution/provenance check

30 October 2026; baseline HEAD `1ff5b01cbdcf4c0b6788914c9eb89d1db6a44ce9`.

This is an evidence checklist, not a declaration of the student's independent work. It makes no personal ownership inference from Git commits, first-person thesis wording, or an AI-produced draft.

**Author-confirmation update, 30 October 2026:** the user has now confirmed that the supervisor proposed the GPU direction and provided regular discussion, and that the other research work was the user's. Section1.5 now records this broad allocation in English and Chinese, retaining substantial AI assistance in development, experiment automation, analysis, review and writing. The table below preserves the earlier pre-confirmation audit; it should not be read as the current status of that broad role allocation. Exact before/after text and confirmation excerpts are in `variants/thesis2/audit/individual-contribution-2026-10-30.json`. The new paragraph makes no claim of sole manual coding, original invention of inherited mechanisms, or personal rerun of every experiment.

| Item | Inherited foundation | Recorded project additions | Corresponding checks | Evidence for personal ownership | Status |
|---|---|---|---|---|---|
| C1 construction | JHQ transform, hierarchy, analytical/fitted codebooks; IVF | GPU training/encoding integration, bounded one/two-pass add, list-ordered packed state | Ch4 contracts, representation audit, repeated builds, resident/peak measurements in7.7 | Project source/results demonstrate mechanisms and outputs; do not identify which author designed or implemented each part | **author confirmation required**: student's design, implementation and experiment decisions; joint/supervisor roles |
| C2 execution | Cartesian additivity, small-table lookup, bitonic/radix primitives, merge and CUDA execution | Integrated lookup/packed scan, grouped complete-key retention and bound, lane refinement, dispatch and probe selection | Ch5 statements/proofs; Ch7.3/7.4/T4 exact computed-score checks; Ch7.6 scheduling and T5 | Mechanism/version records identify project components; commit authorship alone is insufficient for independent research attribution | **author confirmation required**: personal design choices, alternatives rejected, code and correctness work versus assisted/joint work |
| C3 calibration | Candidate expansion/refine ratios, output agreement and ordered testing ideas | Workload-level rule, conditional selection analysis, FULL/sample/oracle controls, quality/cost evaluation | Ch6 proof/corollary, 2,304 sample and12 FULL enumeration checks, finite-pool traces, direct reuse | Logs verify outputs and checks; original personal research decisions are not established | **author confirmation required**: who proposed the rule, proof and experiment design, who verified/adopted conclusions |

## Disclosure checked

- `frontmatter/acknowledgements.tex` includes `frontmatter/declaration.tex`; this declaration is therefore present in thesis2 even though no copy exists under `variants/thesis2/frontmatter/`.
- Existing declaration says the thesis extends **joint** JHQ-GPU work with Mengxuan Zhang and identifies the inherited JHQ basis. It credits Codex substantive writing/analysis/code checks, ChatGPT frameworks/reviews and Claude implementation/experiments/review. It does not claim wholly independent implementation or mere language polishing.
- `docs/ai-use-record.md` explicitly describes partial record coverage, unavailable dates/model versions and missing complete historical prompts. It records substantive assistance. None of those gaps is filled by invention in this round.
- `tab:1-contributions` deliberately says **project contribution**. `fig:1-challenges` already maps challenges to mechanisms and evidence. An additional map would duplicate both while failing to resolve personal attribution; none is added.
- This round generates layout changes and two mechanism drawings using Codex, checked against existing equations and source. It does not establish that the student independently authored those drawings or verified every previous claim.

## Author actions

1. For each C1/C2/C3, identify personal work and decisions, joint work, supervisor input and AI assistance. Include checks personally performed and alternatives personally accepted/rejected.
2. Confirm the existing joint-work and assistance wording accurately describes the project; amend it based on actual history if needed.
3. Add recoverable original interaction records and accurately identify unavailable material if required by the applicable assessment instructions.

No fabricated confirmation text has been inserted into the thesis. These actions do not prevent the requested figure/layout work from being completed.
