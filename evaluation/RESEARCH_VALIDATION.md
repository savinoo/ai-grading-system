# Research validation

**Assessment: share with caveats.** The descriptive results and offline pipeline are reviewable. Claims of human-relative grading quality, causal RAG benefit and optimal arbitration policy remain unsupported and are explicitly withheld.

## Verified scope and calculations

The frozen source is `79495d00948908503ed4489861ea319a2c7e7972`. The source-to-normalized build was executed against that commit, and its complete manifest was identical to the committed manifest. Reanalysis verified 28 generated-file hashes and used exactly the 16 listed exports. An unlisted extra JSON, a changed file, duplicate manifest entries or a path outside the dataset directory fails validation.

An independent direct read of the three original QA4 JSON exports confirmed 36 rows, 12 cases, profile mean absolute examiner differences 1.013889/0.180556/0.111111/0.069444 for weak/excellent/off-topic/intermediate responses, threshold counts 8/3/1/0 and maximum recorded within-case range 0.625. The separate Q2 notebook export has 12 rows/four cases and range 1.37. No pooling or independent-row interval was used.

The A/B material match checks question text, rubric semantics, explicit scale and exact answer text. Four comparisons each contain twelve matched materials. Mean descriptive score shifts were checked against saved per-pair deltas: -0.182292, -0.437500, -0.229167 and +0.240000. All historical controlled-pair counts are zero. Ten actual arbiter-score rows exist, with 1.9-point mean absolute final-versus-examiner-mean movement. These figures measure recorded grades, not accuracy.

The blind packet contains 48 distinct materials, split into 40 development and eight held-out items by response-text hash. Identical answer text stays in one partition. This is a small convenience challenge set, not a representative learner sample. Zero legitimate human labels were found or manufactured.

## Material review issues addressed

- The original reanalysis runner could include an unmanifested extra export after checking listed hashes. It now rejects any mismatch between listed and actual exports and derives inputs from the manifest. Regression tests exercise the extra-file case.
- Missing or malformed rubric/scale material is not considered an exact match. Changed question/rubric/answer material and different source families do not enter one repeatability group.
- Incomplete historical configuration is explicitly marked; matching missing values does not establish controlled repeatability or a controlled RAG comparison.
- The human importer requires recorded independent blind ratings, per-criterion evidence, adjudication and exact material fingerprints. Synthetic and legacy bare-score labels cannot become research gold. This validates evidence structure, not human identity or authenticity.
- Stored notebook divergence/consensus inconsistencies are preserved and flagged. The analyzer recomputes examiner difference from the two stored examiner fields without asserting those fields are canonical final totals.
- Initial backend TIMEOUT exports remain in failure diagnostics. Empty results are not successful zero-score observations.

## Required caveats

Examiner agreement can conceal shared-model errors. Synthetic response profiles are not real learners or human grade references. QA4 JSON lacks exact answers; the notebook uses different scoring semantics. Recorded retrieval excerpts establish trace availability, not relevance, grounding or causal benefit. Question-scoped context duplicated across profiles is not independent retrieval evidence. Unobserved arbiter outcomes, human-relative errors, token costs and model-inference latency stay unavailable. The synthetic demonstrations test software only.

The full test and hosted-check outcomes are in `VALIDATION.md`. Security scan findings are reported separately from this methodological assessment; this document is not a security audit.
