# Human reference annotation protocol (v2)

## Current status and eligible material

There are **zero legitimate human reference annotations** in the inspected historical exports. No reviewers have been recruited or promised. Model agreement and historical synthetic response profiles are not ground truth. The committed gold template contains zero labels.

`data/annotation/blind_packet.json` freezes 48 distinct question/rubric/answer materials actually present in the selected A/B and notebook exports. These answers are the repository owner's synthetic experiment responses, not a classroom sample. Annotation material is identified by exact SHA256 over the question statement, rubric, scale and response. The source commit, file paths and checksums are in `data/manifest.json`; normalized exports preserve those attributions. Public source records remain linkable, so the release is a reviewed deidentified synthetic corpus, not a claim of irreversible anonymization.

The 36-row JSON QA4 corpus has **no answer text**. Do not fill its answers from another A/B run, a notebook constant, an examiner explanation or an inferred response. Those grades cannot be evaluated against a reference until the exact historical answers are recovered with verifiable provenance. The separate 12-row notebook QA4 corpus has exact Q2 answers and a different rubric. Keep the cohorts separate.

## Freeze the evaluation plan before grading

1. Retain the source manifest and material hashes. Record an annotation dataset version and protocol version. Consent, reviewer identity/qualification and recruitment records belong in a restricted location outside the public repository.
2. Use at least two qualified reviewers who independently understand the questions and the scoring rubric. Record qualifications and any conflicts privately. Assign pseudonymous reviewer IDs; the code cannot verify that an ID represents a qualified person.
3. Declare the primary metric (MAE), secondary metrics (RMSE and signed bias), and error tolerance before seeing labels. The analyzer's pass/fail diagnostic uses a clearly labelled reporting convention of 6/10, not an asserted institutional pass mark.
4. The packet assigns development and held-out material before annotation. Exact duplicate response text remains in the same split across rubric versions. Check near duplicates manually before treating a held-out result as independent; these few authored profiles cannot support classroom generalization. Do not tune prompts, arbitration or retrieval settings on the held-out set.
5. Predeclare a 1-point discrepancy tolerance for adjudication triage and criteria for resolving disagreements. Keep all original independent ratings even when a later adjudication changes the total.

## Independent blind review

Send reviewers only the blind material packet and a blank rating form. The packet contains question, rubric, response, scale, material hash and pseudonymous case IDs. It excludes examiner/final scores, profile quality labels and experiment/source-condition paths. Do not send normalized grading exports or the results dashboard until independent ratings are locked. The underlying public repository can be searched; reviewers must attest they did not consult model grades.

For every rating record:

- `reviewer_id`: a pseudonym linked to a private qualification/consent record;
- `material_sha256`: the exact frozen material shown;
- `blinded_to_model_scores: true` only after that reviewer confirms this;
- `criterion_scores`: every rubric criterion's exact name, score and maximum;
- `score`: the weighted total on the 0–10 scale;
- `rationale`: concise evidence from the response for the scores;
- `recorded_at`: a timestamp recorded when the review occurred.

Use the rubric's declared criterion scales. Compute total as `10 × sum(weight × criterion_score / criterion_max_score)`; the import rejects inconsistent totals or a changed rubric. A null, placeholder or AI-generated rating is not a human annotation.

## Adjudication and import

After both independent reviews are locked, record an adjudication for every reference label. Reviewers may resolve the case jointly or use a third qualified adjudicator. Record who resolved it, the final criterion scores, material hash, timestamp and evidence-based rationale. This step does not erase disagreement in the independent ratings. Do not automatically average disagreements into a gold score.

`data/annotation/ratings_template.json` contains the frozen cases with `review_status: unreviewed`, null references and empty ratings. Populate each completed case with the following schema fields:

```text
review_status = "adjudicated"
reference_score = actual adjudicated total
independent_ratings = at least two distinct recorded reviewer objects
adjudication = recorded reviewer_id, criterion_scores, material_sha256,
               rationale and recorded_at
```

Validate and import actual completed annotations:

```bash
python -m evaluation.annotation import \
  --packet evaluation/data/annotation/blind_packet.json \
  --annotations /private/completed_ratings.json \
  --output /private/validated_gold.json

python -m evaluation.reliability \
  evaluation/data/exports/notebook_qa4_r1.json \
  evaluation/data/exports/notebook_qa4_r2.json \
  evaluation/data/exports/notebook_qa4_r3.json \
  --gold /private/validated_gold.json \
  --output evaluation/output/notebook-human-reference
```

The validator rejects legacy schema-v1 declarations, synthetic labels, duplicate reviewers, non-blind ratings, changed material, missing adjudication, missing criterion evidence and inconsistent totals. Research metrics require the reference fingerprint to match the evaluated question/rubric/answer exactly. Different answer versions sharing participant/question IDs retain separate fingerprints. Draft/unreviewed cases never enter reference metrics.

These checks validate the *recorded evidence*, not human identity or honest conduct. The research owner must verify the underlying consent, qualifications and independent-review records. Keep that audit private and cite the released, authorized reference dataset if it is eventually published.

## Synthetic pipeline demonstration

```bash
python -m evaluation.annotation demo --output evaluation/output/synthetic-annotation-demo
```

This exercises rating validation, rubric totals and adjudication import using invented arithmetic data and invented rater records. Outputs are permanently labelled `label_origin: synthetic_demo`; the default gold loader rejects them and `reference_for` never exposes them as human references. The committed `data/synthetic_demo/` fixture demonstrates format and plumbing only. It supplies **zero** evidence about grading correctness.

## Interpretation and future experiments

Report human-to-human differences before adjudication and reference-label coverage, not only the machine's final error. MAE over repeated runs contains correlated observations; report unique cases and do not attach an IID confidence interval. Stratify diagnostic differences by question/profile when useful, with the small synthetic sample caveat.

Arbitration effectiveness requires observed eligible arbiter outputs and matched references; a threshold replay alone measures potential calls and score changes. RAG quality requires exact question/rubric/answer pairing, comparable configuration, retrieved-context evidence and references. Neither an enabled-RAG flag nor a score shift establishes improvement. Do not deploy policy changes from this historical demonstration.
