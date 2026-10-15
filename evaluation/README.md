# Reproduce the Reliability & Evaluation Lab

This layer evaluates the existing TCC grader offline. The bundled results are historical model grades on synthetic response profiles. **No validated human gold labels are present.** Agreement, score movement and retrieval traces do not establish grading accuracy.

## 1. Install a bounded environment

From repository root, Python 3.12:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.lock
python -m pip check
```

`requirements-evaluation.lock` is sufficient for analysis and the dashboard. `requirements-dev.lock` also provides real LangGraph, agent-schema and test dependencies. The `.txt` counterparts declare maintained direct pins; `.lock` files resolve transitives for Python 3.12 with platform markers. These locks were exercised locally and by the CI configuration; they do not imply every OS/provider was tested. The large original `requirements.txt` remains the separate capstone application environment.

The analysis commands themselves use the Python standard library and need no API key, database server or internet access. They do not send data to providers.

## 2. Recompute the frozen results

```bash
python -m evaluation.run --output evaluation/output/reproduced
```

The runner verifies manifest hashes and the exact frozen export set before analyzing. It keeps QA4 cohorts separate and writes:

```text
evaluation/output/reproduced/
  reproduction.json
  qa4_json/report.json
  qa4_json/corrections.csv
  qa4_json/stability.csv
  qa4_notebook/report.json
  qa4_notebook/corrections.csv
  qa4_notebook/stability.csv
  experiments.json
  arbitration_observed.csv
  rag_pairs.csv
```

Inputs are the 16 reviewed exports in `evaluation/data/exports/`, with lineage in `evaluation/data/manifest.json`. Main result files are `evaluation/data/reliability_report.json`, `qa4_notebook_report.json` and `experiments.json`. The dataset README documents inclusions, missingness and deidentification limits. Repeated cases are not independent learners.

| Cohort | Corrections | Cases | Maximum recorded final-score range |
|---|---:|---:|---:|
| QA4 JSON | 36 | 12 | 0.625 |
| QA4 notebook, Q2 only | 12 | 4 | 1.370 |

The JSON QA4 exports lack exact answers, so same-input repetition is unverified. Notebook QA4 uses a different implementation and contains inconsistent score/divergence/consensus fields. We preserve those fields and flag mismatches rather than silently repairing them. The two QA4 results are not pooled.

## 3. Inspect the dashboard

```bash
streamlit run evaluation/dashboard.py --server.address 127.0.0.1
```

The sidebar selects one QA4 cohort or imports a generated reliability `report.json`. The reliability and threshold panels use only that selected report. Arbitration and RAG detail panels explicitly use the separate bundled historical A/B artifacts. They show recorded arbiter movement, exact-material pairs, comparability blockers, retrieved excerpts/hashes/pages and diagnostic flags. Changing the QA4 selector does not change the A/B experiment population.

No human-reference metric is shown for the bundled history. Monetary cost and model-inference latency remain unavailable where not observed. Model profile names describe synthetic construction, not human grades.

## 4. Rebuild data from original TCC exports

The source is pinned to commit `79495d00948908503ed4489861ea319a2c7e7972`. A shallow clone may need that history fetched once:

```bash
git fetch --no-tags origin tcc
python -m evaluation.dataset build \
  --source-ref 79495d00948908503ed4489861ea319a2c7e7972 \
  --output evaluation/output/rebuilt-data
python -m evaluation.run --data evaluation/output/rebuilt-data \
  --output evaluation/output/rebuilt-analysis
```

The builder uses read-only Git commands, not the live VPS or production database. It records original source-file and normalized-output SHA-256 hashes. It processes an explicit allowlist of this public synthetic study. It is not a general anonymizer for private student records. Participant names/IDs, feedback and reasoning are excluded; publicly linkable pseudonyms and short document traces remain. Exact answers are included only where present, never reconstructed for missing QA4 records.

Two initial backend A/B exports recorded `TIMEOUT` and no result rows despite their export status saying completed. Their failures are preserved and they are not counted as successful grading observations.

## 5. Run all validation

```bash
python -m pytest tests/
ruff check src/ app/ evaluation/ tests/
ruff format --check tests/integration_*.py
python -m compileall -q src/ app/ evaluation/ tests/
bandit -r src/ app/ evaluation/ -c pyproject.toml -f json -o evaluation/output/bandit.json
```

The **security command is expected to fail while reported findings remain**. It is not disabled, filtered or marked optional to obtain a green pipeline. The CI uploads findings even on failure and gates image building on test and security success. Security remediation is a separate workstream.

For standard-library-only checks, without the dashboard/graph dependencies:

```bash
python -m unittest discover -s tests -p 'test_*.py' -v
```

The full pytest run additionally collects `integration_*.py`: actual compiled graph, real examiner/arbiter prompt chains, SQLite round-trip and Streamlit user interactions with deterministic external provider doubles. These are software integration tests, not live model-quality measurements. See `VALIDATION.md` and `docs/CI_AND_RELEASE_STATUS.md` for exact observed outcomes and remaining limits.

## 6. Human annotation: ready for legitimate ratings

The prepared blind packet is `evaluation/data/annotation/blind_packet.json`. Its 48 distinct materials contain questions, rubrics and exact answers with model grades/profile names withheld. The empty `ratings_template.json` records no ratings. Follow `ANNOTATION_PROTOCOL.md` for independent blind review, per-criterion scores, consent/provenance and adjudication.

A real completed annotation file must be imported against the packet before analysis:

```bash
python -m evaluation.annotation import \
  --packet evaluation/data/annotation/blind_packet.json \
  --annotations path/to/legitimate-private-ratings.json \
  --output evaluation/output/validated-human-gold.json
python -m evaluation.run --gold evaluation/output/validated-human-gold.json \
  --output evaluation/output/human-reference-analysis
```

Only schema-v2 human labels with required recorded evidence and exact material fingerprints enter reference metrics. Draft/legacy labels and mismatched answers/rubrics are rejected or ineligible. Schema validation cannot certify that a human actually supplied the ratings; retain authentic rating evidence privately. QA4 JSON cannot be labelled retrospectively from other experiments because its exact answers are absent.

Exercise annotation import safely with an explicitly synthetic example:

```bash
python -m evaluation.annotation demo --output evaluation/output/synthetic-annotation-demo
python -m evaluation.experiments evaluation/examples/synthetic_arbitration_rag/rag.json evaluation/examples/synthetic_arbitration_rag/no_rag.json \
  --output evaluation/output/synthetic-policy-demo
```

Synthetic annotations are never research gold. Synthetic policy output is evaluated separately; attempts to mix it with historical exports fail. These examples demonstrate pipeline behavior, not grading accuracy or human review.

## 7. Reports and evidence

- `TECHNICAL_REPORT.md`: English methods, findings and limits.
- `SUMMARY_PT.md`: Portuguese handoff and portfolio framing.
- `EXPERIMENTS.md`: policy replay and RAG eligibility definitions.
- `RESEARCH_VALIDATION.md`: independent calculation and methodology checks.
- `VALIDATION.md`: actual test/check outcomes and CI links.
- `artifacts/report.html`: self-contained portable report with source-backed charts.
- `artifacts/report.artifact.json`: reviewed chart data, actual SQLite aggregation queries and narrative.

The portable report manifest can be regenerated with `python -m evaluation.presentation`. Its HTML is a packaged reader export, not a second analysis pipeline. The dataset reports and dashboard are reproducible entirely from repository code; optional regeneration of the identical portable reader requires the Data Analytics report-packaging plugin. The checked HTML opens locally without that plugin or a server. No hosted publication is part of this case.
