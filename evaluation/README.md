# LLM Reliability Lab — Phase 2 (offline evaluation)

This experimental layer is attached to the existing AI grading system, not a new chatbot.
It evaluates **agreement, repeatability, traceability and deviations from adjudicated human references**, without calling an LLM.

## Usage

From repository root, with Python 3.12+:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
python -m evaluation.reliability \
  tcc/results/experiment_QA4_9.json \
  tcc/results/experiment_QA4_10.json \
  tcc/results/experiment_QA4_11.json \
  --output evaluation/output/qa4-historical
```

The historical exports live in the **tcc** branch, *not* main; copy those three files locally before executing the example. The repository does **not** publish a real human-adjudicated gold dataset. The `evaluation/output/` directory is ignored by Git to avoid accidentally committing sensitive case-level output.

Generated reports:
- `report.json`: metric summaries, quality warnings, threshold simulation and per-case diagnostic tags;
- `corrections.csv`: pseudonymous case IDs, model scores, disagreement, presence of retrieval/criterion evidence, and **observable** diagnostic flags;
- `stability.csv`: QA4 score ranges; whether identical answer text could be verified from the exported records.

The following values are **not** automatically calculated without adjudicated references: model accuracy, hallucination rate, faithfulness, improved grading due to arbitration, retrieval recall, human agreement, or cost.

## Human gold standard

Create a separate private JSON with **human-reviewed**, anonymized grade references:

```json
{
  "schema_version": 1,
  "items": [
    {
      "question_uuid": "uuid-of-question",
      "student_id": "opaque-id-for-answer",
      "reference_score": 7.0,
      "review_status": "adjudicated"
    }
  ]
}
```

The example above describes the schema; **7.0 is not a real label**. Draft labels are excluded from accuracy metrics. Two or more blind human reviewers should grade the same answers using a predeclared rubric and resolve disagreements before the label is marked `adjudicated`.

Run:

```bash
python -m evaluation.reliability path/to/export.json --gold path/to/private_gold.json --output evaluation/output/human-audit
```

For cases with matched adjudicated labels, the analyzer computes MAE, RMSE and bias. It **does not** infer root causes from score differences alone. Its tags are triage signals (e.g. missing retrieval evidence, large reference error), not explanations.

## Provenance recorded for new experiments

`app/experiment_provenance.py` snapshots the **effective** model/provider, temperature, embeddings provider/model, RAG top-k, arbitration threshold and SHA-256 fingerprints of prompt, examiner runtime, retriever and workflow files. No API keys or student responses enter the configuration snapshot.

The retrieval node records `retrieval_status`, `retrieval_query_strategy`, `retrieval_scope`, `retrieval_context_count` and `retrieval_elapsed_ms` in `processing_metadata`. The store exports this per-result field, with an additive schema migration for existing SQLite experiment databases. Context content continues to be stored in `experiment_rag_contexts` *only when supplied to the ExperimentStore*. The backend API's separate execution path may not populate the same store; a UI config labelled RAG-on is **not** proof that retrieval evidence was recorded.

These fields do **not** measure LLM inference time, token usage or price. Use LangSmith or a separately validated token/cost capture in a later experiment. Temperature zero is not a determinism guarantee.

## Historical experiment interpretation

For `tcc/results/experiment_QA4_{9,10,11}.json` (Gemini 2.5 Flash, 3 questions, 4 response profiles, 3 repetitions), a direct read found **36 correction results**, with `|C1-C2|` thresholds **strictly greater than**:

| Arbitrator threshold | Would trigger (offline) |
|---|---:|
| 0.5 | 8/36 |
| 1.0 | 3/36 |
| 1.5 | 1/36 |
| 2.0 | 0/36 |

These are **potential calls** under altered thresholds, not regraded outcomes. Largest range of final scores across the three exports: **0.625** points. The exported QA4 answer tables are empty, so identical student-answer text across repetitions **cannot be verified from these JSON files alone**.

A **different** QA4 run in `notebooks/results/qa4_todas_runs_20260328_163833.csv` covers just Q2 and four profiles repeated 3 times; it reports a max final-score variation of **1.37**. Do not pool it with the JSON QA4 runs or claim they are the same protocol.

Critical data-quality issues:
- Historical exports have empty `criterion_scores` in corrections due to the old `criteria_scores` persistence mismatch. Old records cannot be recovered merely by fixing the serializer.
- Some exports labelled `A (com RAG)` contain zero persisted retrieval contexts. Label alone does not establish effective RAG usage.
- Human gold labels are absent. Examiner agreement is not evidence that both are correct.
- QA4 labels refer to synthetic response profiles, not measured performance on real classrooms.

## Root-cause protocol

1. Review high-disagreement and high-error cases first, **without exposing student data in public reports**.
2. Verify the original question, exact answer, rubric, prompt SHA, model configuration and retrieval traces.
3. Have independent humans adjudicate the grade before attributing wrong grading to a model.
4. Classify causes only after evidence review: incorrect retrieval, missing reference, prompt ambiguity, shared model bias, grading-rule ambiguity, or instrumentation failure.
5. Compare one change at a time on a frozen blind evaluation set. Track accuracy **and** cost/latency separately.
6. Do not change production arbitration thresholds based on simulations alone: compare real arbiter outputs and MAE to human labels.

## Scope / security

No migration of authentication, cookies, authorization rules, or Streamlit sessions is included in this evaluation PR. Previously identified security concerns need a separate security patch before any public deployment.


## Visual dashboard (Streamlit)

A working local dashboard is included in `evaluation/dashboard.py`. It reads the **same `report.json` schema** produced by the CLI, so dashboard graphics cannot invent metrics.

```bash
# Streamlit and pandas are already listed in requirements.txt
streamlit run evaluation/dashboard.py
```

The app initially displays `evaluation/examples/qa4_historical_report.json`, a **de-identified historical QA4 snapshot** built from public `tcc` exports, for visual exploration. It shows 36 grading results, 12 cases, a 0.625 maximum score range, and threshold simulations (8 / 3 / 1 / 0 calls at >0.5 / >1.0 / >1.5 / >2.0). It is labelled as an example and does not contain real human gold labels.

To view an actual newly generated dataset, upload the CLI's `report.json` in the dashboard sidebar. No requests are made to an LLM and no backend deployment is necessary.

Human annotation protocol: see `evaluation/ANNOTATION_PROTOCOL.md`. The committed `evaluation/gold_standard_template.json` starts with **zero** labels on purpose.

**Historical limitations:** source code configuration checksums, exact student answer text, and criterion scores were not stored consistently in old exports. These cannot be reconstructed by presentation styling or by the persistence fix.
