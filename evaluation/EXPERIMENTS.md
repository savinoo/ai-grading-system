# Experiments 2 and 3: evidence and interpretation

The offline experiment pipeline reads the deidentified, versioned exports under
`evaluation/data/exports`. It makes no model calls. Run from the repository root:

```sh
python3 -m evaluation.experiments evaluation/data/exports/*.json --output evaluation/data
python3 -m unittest tests.test_evaluation_experiments -v
```

Outputs are `experiments.json`, `arbitration_observed.csv` and `rag_pairs.csv`.
The optional `--gold` accepts only the material-verified human annotation format
described in `ANNOTATION_PROTOCOL.md`. No legitimate adjudicated human labels
were found in the supplied TCC exports, so the bundled historical report has
**no accuracy, MAE, RMSE, or quality-improvement result**. Profile names such as
excellent/poor describe authored/generated response scenarios, not human scores.
Null measurements stay null; no wall-clock experiment duration is substituted
for per-case latency, and no token price is invented.

## Experiment 2: Arbitration Effectiveness

The current grader invokes an arbiter when `abs(c1-c2) > threshold`. Without an
arbiter the final is the examiner mean. With an arbiter the repository selects
the closest pair among three scores and averages it. On an exact distance tie,
the higher pair is selected. The offline replay mirrors that rule.

The observed comparison uses the **same stored examiner scores** to calculate a
mean-only baseline and compares it with the actual stored final. This isolates
the arithmetic grade movement on the historically selected cases. It does not
show that arbitration improved correctness. The selection is based on examiner
disagreement and is not randomized. Repeated runs and several configurations
must not be pooled as independent learner observations.

| Historical source family | Rows | Observed arbiter scores | Mean absolute final-vs-mean grade shift on those rows | Simulated calls at thresholds 0.5 / 1 / 1.5 / 2 |
|---|---:|---:|---:|---|
| TCC paired A/B | 24 | 2 | 1.375000 | 2 / 2 / 2 / 2 |
| TCC parallel A/B | 24 | 3 | 1.666667 | 3 / 3 / 3 / 3 |
| TCC v3 A/B | 24 | 5 | 2.250000 | 7 / 6 / 6 / 5 |
| TCC QA4 JSON | 36 | 0 | unavailable | 8 / 3 / 1 / 0 |
| Notebook A/B | 24 | 0 | unavailable | 8 / 3 / 0 / 0 |
| Notebook QA4 | 12 | 0 | unavailable | 1 / 1 / 1 / 0 |
| Initial backend A/B | 0 | 0 | unavailable | no recorded outcomes |

The initial `experiment_A_7.json` and `experiment_B_8.json` record
`config.final_status=TIMEOUT` and zero results despite a top-level completed
export status. This conflict is preserved in `source_failures`; these files do
not provide successful experimental observations.

For inventory only, all 144 recorded rows contain 10 arbiter scores. Thresholds
0.5, 1, 1.5 and 2 would request 29, 18, 13 and 10 calls. Respectively 19, 8, 3
and 0 required arbiter outputs are missing. A policy's average grade change is
withheld unless every required score exists. No missing arbiter output is
extrapolated from other cases. The 144-row totals are **not a threshold
recommendation**. The report also exposes results per source family.

The replay reconstructs a policy from the current arithmetic rule; it does not
silently repair stored finals. Sixteen notebook rows differ from the current
mean/closest-pair final rule by more than 0.011 points. Their originals and
`stored_consensus_differs_from_current_rule` flags remain visible. A threshold
replay records each reconstructed score, stored score and mismatch count.

All human-reference error, measured arbiter latency and incremental dollar
cost remain unavailable in the historical exports. If future exports provide
explicit nonnegative `processing_metadata.arbiter_elapsed_ms` and
`arbiter_cost_usd`, they can be summarized only for the actual calls carrying
those observations. A policy total is withheld if any triggered call lacks its
cost. No inference from timestamps, call counts or list prices is used.

For a future quality experiment, freeze the material, rubric, model, prompts,
retrieval and aggregation rule; collect two independent examiner grades and an
arbiter output for every case, including cases below the existing threshold.
Then compare policies on exactly the same held-out materials using separately
adjudicated human scores. Tune thresholds on a development partition only.
Report paired error changes, per-case latency, recorded usage/cost and uncertainty
clustered by distinct material; reserve the test partition for one final check.
No such prospective evaluation is claimed by this historical replay.

## Experiment 3: RAG Impact Analysis

Matching by row position, question ID or profile name is insufficient. The
pipeline pairs exact question statement, rubric content, score scale and answer
text using canonical SHA-256 material fingerprints. Nonsemantic database UUIDs
inside a rubric are excluded; criteria, descriptions, order, weights and maxima
are preserved. Duplicate identical material produces an ambiguous-match failure
instead of a Cartesian join or an arbitrary selected row. Different A/B revisions
are compared separately.

| Comparison | Exact paired materials | Mean final-score difference, RAG minus no RAG | Controlled pairs |
|---|---:|---:|---:|
| `experiment_A_pareado_3` vs `experiment_B_pareado_4` | 12 | -0.182292 | 0 |
| `experiment_A_final_6` vs `experiment_B_final_7` | 12 | -0.437500 | 0 |
| `experiment_A_v3_13` vs `experiment_B_v3_14` | 12 | -0.229167 | 0 |
| Notebook `cond_A` vs `cond_B` | 12 | +0.240000 | 0 |

These are **descriptive grade shifts**, not gains/losses in grading quality.
They must not be combined across revisions. The first three A exports contain
no saved retrieval contexts. All three lack full temperature/prompt/runtime/
workflow/retriever/embedding provenance. A human reference is also absent.

The notebook A export does preserve actual retrieved textbook chunks: 48
question-to-case context assignments for 12 cases, with 11 distinct chunk content
hashes. Retrieval was captured at question scope and assigned to each answer of
that question; those assignments are not 48 independent retrieval operations.
The notebook lacks recorded model/temperature/prompt/runtime fingerprints and
other relevant setup. Recorded context cannot close those configuration gaps.

`rag.retrieval_coverage` exposes each source's coverage, unique content hashes,
scope, source document, page, rank/chunk index, similarity score and short
evidence excerpts. The exact complete chunk SHA-256 is retained while only the
first 240 characters are redistributed. TCC QA4 has 4 contexts per case and
notebook QA4 has 4 contexts per case; these are separate QA4 datasets with
different question coverage. A saved context or a vector similarity score does
not prove that a passage was relevant, correct or used faithfully by a grader.
Manual relevance/grounding annotation remains pending.

A controlled-comparison eligibility gate requires exact material plus matching
provider, model, temperature, divergence threshold and examiner prompt/runtime/
workflow fingerprints; the RAG arm additionally needs retriever, embedding and
top-k metadata and saved context content. The no-RAG arm must have an explicit
disabled treatment and no recorded context. Unknowns are blockers, not equal
configurations. Even eligible historical observational pairs do not by
themselves establish causal quality effects. `causal_quality_effect` remains
null. Reference error deltas additionally require consistent verified human
labels for both copies of the exact material.

Failure records include missing retrieval evidence, absent answer/rubric material,
high examiner disagreement, missing human reference, inconsistent stored
consensus, ambiguous material and configuration mismatch/unknowns. Together
with the context evidence they form an auditable failure-review queue, not an
automatically assigned explanation for why an answer was graded incorrectly.

For a prospective RAG experiment, use a frozen corpus/index and versioned
retrieval settings; reuse identical answers/rubrics with randomly ordered RAG
and no-RAG calls, repeat matched trials, and record the exact retrieved chunks
and per-call model/usage/latency. Predefine error/retrieval-grounding categories.
Use legitimate adjudicated reference grades for quality claims and independently
review retrieved relevance and grounding. Do not label score changes as accuracy.

## Synthetic pipeline exercise

`examples/synthetic_arbitration_rag/` is a deliberately separate, clearly labeled
fixture that demonstrates fully supplied pairing/configuration/retrieval gates
and missing arbiter outcomes. Its zero hashes and arithmetic scores are authored
test inputs, not an empirical experiment. Its report says
`data_origin=synthetic_demonstration`. The pipeline rejects pooling these inputs
with historical exports. No synthetic grade is passed off as a human label.
