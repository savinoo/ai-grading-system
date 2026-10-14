# Human-Reviewed Gold Standard — Annotation Protocol

## Purpose

Measure how well the multi-agent grader agrees with qualified human assessment, rather than mistaking agreement between two LLM examiners for accuracy.

## Required source material

For each unique case: exact question statement, anonymized student response, the rubric with criterion weights, and the expected grading range. Do not publish student names, institutional IDs, emails or raw private submissions. Obtain authorization before using real student responses.

## Two independent reviews and adjudication

1. Freeze a balanced sample covering correct, partially correct, weak, and off-topic answers, including cases with large AI disagreement. Reserve a final blind test set.
2. Ask two independent qualified human reviewers to grade each answer against the *same* rubric without seeing model grades.
3. Save each criterion score and a brief evidence-based explanation in the private annotation worksheet. Do not mark a record as gold yet.
4. For a disagreement over the pre-declared tolerance (suggestion: 1.0 point, to be agreed **before** review), ask reviewers to discuss or involve a third adjudicator. Record the decision and the reason.
5. Only adjudicated scores enter the machine-readable `gold_standard.json`:

```json
{"schema_version":1,"items":[
  {"question_uuid":"<question-uuid>","student_id":"<pseudonymous-id>",
   "reference_score":7.0,"review_status":"adjudicated"}
]}
```

The `7.0` above **illustrates the schema**. It is not an actual gold label. The committed `gold_standard_template.json` contains no labels.

## Quality gates

- Pre-register scoring tolerances and success metrics: MAE, RMSE, bias, pass/fail boundary agreement, and disagreement by difficulty and rubric criterion.
- For each adjudicated score, verify reviewers saw the same question, answer, and rubric.
- Measure human-to-human disagreement *before* adjudication to understand irreducible variation.
- Prevent experiment leakage: don't tune prompts or arbitration thresholds on the blind test set.
- Evaluate the arbiter by re-running selected cases with a documented budget and comparing to human references. Threshold-only call counts are **not** evidence of improvement.
- Run post-change evaluations on a frozen matched set, and compare cost and latency separately.
- Keep annotation decisions in a restricted location outside the public repository unless the owners explicitly authorize publication.

## What can be done today

Review the already-public synthetic QA4 responses and produce a *small pilot* labelled by qualified experts. Until then, dashboard gold-standard metrics deliberately remain blank.
