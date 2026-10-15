# Multi-Agent LLM Reliability & Evaluation Lab

## Technical summary

The grader exhibits high overall examiner agreement while concentrating disagreement in weak synthetic responses. The JSON QA4 cohort contains 36 grading rows for 12 cases; mean absolute examiner difference is **0.343750 points**, and weak responses average **1.013889 points**. The largest final-score range across three repetitions is **0.625 points**. The separate notebook QA4 cohort has 12 rows for four Q2 cases and a maximum recorded range of **1.37 points**. These cohorts implement different protocols and are not pooled.

The accessible study material contains **no validated human reference grades**. Therefore this case establishes descriptive consistency, instrumentation gaps and reproducible experimental infrastructure. It does not establish grading accuracy, arbitration benefit, or improved grading quality from RAG. All grades use a 0–10 scale. Historical response profiles were authored/generated synthetic examples, not a sample of real learners.

The delivery reuses the capstone's actual grading graph, experiment store and historical exports. It adds frozen deidentified data, strict human-label provenance checks, three offline experiments, a Streamlit results interface, a blind annotation packet and integration tests with mocked external providers. It performs no paid inference or production deployment.

## Experiment 1: disagreement is concentrated in weak responses

The JSON QA4 denominator is three questions × four profiles × three repetitions. The following values are recomputed from C1/C2 scores, not taken from a narrative summary:

| Synthetic profile | Rows | Mean absolute C1/C2 difference (points) |
|---|---:|---:|
| Weak (`poor`) | 9 | 1.013889 |
| Excellent | 9 | 0.180556 |
| Off topic | 9 | 0.111111 |
| Intermediate (`average`) | 9 | 0.069444 |

Across all 36 rows, 16/36 examiner pairs match exactly, 28/36 differ by at most 0.5 points and 33/36 by at most 1.0 point. Pearson correlation is 0.990958 and Lin's concordance coefficient is 0.990569. These high aggregate values partly reflect the broad score range across response profiles. Within weak responses, concordance is only 0.289651. Neither aggregate correlation nor concordance measures correctness against a human standard.

The JSON QA4 exports did not persist exact answer text. Its 0.625-point maximum range is consequently a descriptive within-ID variation; identical inputs across repetitions cannot be verified from these exports. We do not substitute answers from a different A/B experiment. The notebook QA4 retains exact material but has inconsistencies among stored final grades, examiner fields and consensus metadata. Its 1.37-point range describes the recorded final-score field under that separate protocol; it does not validate the same scoring semantics as the JSON implementation.

## Experiment 2: arbitration changes grades, but quality benefit is unmeasured

For the JSON QA4 cohort, strict threshold routing (`|C1 − C2| > threshold`) gives:

| Threshold (points) | Simulated referrals | Denominator |
|---|---:|---:|
| 0.5 | 8 | 36 |
| 1.0 | 3 | 36 |
| 1.5 | 1 | 36 |
| 2.0 | 0 | 36 |

These are counterfactual call counts. The missing arbiter outputs for newly eligible cases are not generated, inferred or filled with the examiner mean. Lowering a threshold therefore does not imply a complete alternative-policy result.

The wider diagnostic corpus contains 144 valid historical grading rows across heterogeneous protocols, including **10 observed arbiter grades** in the JSON A/B families. Relative to the same-row two-examiner mean, their mean absolute recorded final-score movement is **1.9 points**. This is selected, observational grade movement, with no human-relative quality conclusion. The reports also stratify arbitration by source family; the heterogeneous corpus is not a calibration sample for a single threshold.

The software replays the current mean-of-two-closest rule only when the required observed scores exist. Historical notebook consensus inconsistencies remain diagnostic flags. Counterfactual completeness and stored-versus-replayed mismatch counts are exposed. No actual inference latency, token prices or monetary cost are recorded in the relevant historical rows, so these fields remain null. Offline execution time is not presented as model latency.

## Experiment 3: exact A/B material matches do not establish RAG benefit

Pairing fingerprints the exact question statement, rubric, scale and answer. It does not rely on participant IDs or quality-profile labels alone. Each row below has 12 exact material pairs; these are four separate comparisons, not 48 independent learners.

| Historical comparison | Exact pairs | Mean final score RAG minus no RAG (points) | Fully controlled pairs |
|---|---:|---:|---:|
| JSON paired | 12 | -0.182292 | 0 |
| JSON final | 12 | -0.437500 | 0 |
| JSON v3 | 12 | -0.229167 | 0 |
| Notebook A/B | 12 | +0.240000 | 0 |

The three JSON comparisons have no persisted retrieval context despite their RAG-on labels. The notebook A/B export has **four persisted retrieved chunks per case**, stored at question scope; the same question contexts may be repeated across profiles. We retain short evidence excerpts, full-content SHA-256 fingerprints, source-document locator, page, chunk index and retrieval score. These demonstrate recorded retrieval evidence; they do not show that the grader used it faithfully or that humans judged it relevant.

No historical comparison satisfies all required model, temperature, prompt/runtime fingerprint and retrieval-configuration controls. Notebook model configuration is particularly incomplete. Treatment allocation was not established as randomized. A positive or negative grade shift therefore measures neither causal RAG impact nor error reduction. No human reference effect or retrieval recall is reported.

A separate synthetic controlled fixture exercises matching, context evidence, threshold replay and missing-measurement handling. Its declared outputs are software test data, isolated from the historical reports. It demonstrates that the pipeline runs; it is not an empirical RAG experiment.

## Scope, lineage and metric definitions

The immutable historical source is Git commit `79495d00948908503ed4489861ea319a2c7e7972` on the repository's `tcc` history. The dataset manifest records exact original paths, raw-file SHA-256 values and hashes of normalized outputs. It covers the two QA4 cohorts, completed A/B families and failed/empty exports needed to expose exclusions.

Normalization uses an allowlist: synthetic answers, questions, rubrics, scores, configuration evidence and short retrieval traces. It removes participant names, participant/exam UUIDs, feedback and reasoning chains. Deterministic pseudonyms are publicly linkable to the public source; this is deidentification of this reviewed corpus, not a guarantee of irreversible anonymization or a general tool for private student data.

- **Examiner difference:** absolute C1 minus C2; its mean is descriptive inter-examiner disagreement, not MAE against a human.
- **Signed examiner difference:** mean C1 minus C2, indicating direction of disagreement.
- **Pearson correlation:** covariance divided by the two standard deviations; undefined for a constant series.
- **Lin concordance:** twice covariance divided by the sum of variances and squared mean difference. Identical constant series remain undefined rather than being assigned perfect correlation.
- **Repeat range:** maximum minus minimum recorded final score within case/configuration. Known changed answers are excluded; missing answers produce an explicit unverified-input warning.
- **Reference MAE/RMSE/bias:** mean absolute, root mean squared and signed final-minus-human error, only for provenance-validated human labels matching exact annotation material.
- **RAG score delta:** same-material RAG final score minus no-RAG final score, with eligibility blockers retained.

Row counts, exclusions, source statuses and missing evidence are machine-readable. Empty/failed exports do not become zero-score learners. Descriptive statistics use correction rows and preserve repeated-case dependence; no independent-row confidence intervals or significance tests are claimed.

## Experimental design and human-reference pipeline

There are 48 distinct exact annotation materials: 40 assigned to development and 8 to held-out review by a deterministic response-text hash. This small challenge set is not a representative random sample. Annotation packets contain the statement, rubric, answer and scale, with model scores and profile names removed. The protocol requests two independent blind ratings followed by documented human adjudication. It does not imply that reviewers have been recruited.

The importer validates label origin, independent reviewer IDs, blind-review attestations, rationales, timestamps, adjudication and material fingerprints. Provisional ratings and legacy files without provenance do not enter research metrics. A schema can check recorded evidence; it cannot prove that a person actually performed the review. Research owners must retain legitimate rating evidence and reviewer authorization. Synthetic annotation examples require explicit demonstration mode and are rejected as research gold.

A future prospective study should freeze prompts, rubric, model and retrieval setup; grade identical material across randomized or counterbalanced repeated RAG conditions; capture retrieved contexts, arbiter alternatives, tokens and stage-level latency; and compare all policies on the same held-out human-labelled cases. Policy tuning uses development cases only. Human-relative paired errors should be summarized at case level with uncertainty respecting repeated runs. This study remains pending, rather than being represented by synthetic results.

## Validation, limitations and release state

The reanalysis checks frozen-file hashes before reading results. Tests cover missing/changed answers, material mismatches, malformed scores, human-label provenance, strict routing boundaries, missing counterfactual arbiter outputs, incomplete RAG configuration and separation of synthetic data. Integrated tests exercise the real compiled graph, real agent prompt/structured-output path and SQLite export using deterministic external-provider doubles. This confirms software integration without claiming new live model quality.

Detailed commands, exact pass counts, hosted CI links and pending checks appear in the validation record. The repaired security job runs without suppression and reports inherited findings plus low-severity subprocess warnings on the new dataset import helper. Image building depends on test and security success. Production release is blocked; security remediation is a separate scope. Live provider calls, real embedding retrieval, PostgreSQL integration, validated human grading and causal benefit measurements have not been performed for this delivery.

The dashboard and portable report expose the same historical results and unavailable fields. No merge to `main` or production deployment was performed.

## Next decisions and open research questions

Use this case to demonstrate evaluation design, data lineage, controlled comparison eligibility, failure triage and honest interpretation. The evidence supports prioritizing weak-answer cases for human review and improving trace capture before making quality claims. It does not justify lowering the live arbitration threshold or claiming RAG improves grading.

The next empirical milestone is a legitimate, blind, adjudicated reference set on the prepared material. Open questions are whether examiner agreement masks shared-model errors, whether arbitration reduces held-out error enough to justify measured latency and cost, and which retrieved contexts help or distract under a genuinely controlled design.

Source attribution: the original AI Grading System capstone by Lucas Lorenzo Savino and Maycon Mendes Fernandes, Instituto Federal Fluminense, April 2026. Exact experiment source paths and hashes are preserved in the dataset manifest; no external human-labelled dataset is claimed.
