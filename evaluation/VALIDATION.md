# Validation and release record

Validation performed on 14 October 2026. This record separates software checks from research claims and from security approval.

## Local checks actually executed

| Check | Result |
|---|---|
| Full pinned-environment pytest suite | **63 passed**, two upstream LangChain deprecation warnings, no skipped tests |
| Standard-library-only unittest discovery | **56 passed**; graph/dashboard integrations are additionally collected by pytest |
| Real grading integration | Five scenarios using compiled LangGraph, real examiner/arbiter structured-prompt chains and SQLite export; external provider/retrieval transport doubles |
| Streamlit interaction tests | Two passed: QA4 cohort separation, exact displayed counts/ranges, threshold changes and real notebook context inspection |
| Fatal Ruff correctness checks across src/app/evaluation/tests | Passed; no path exclusion baseline |
| Formatting of both integration test modules | Passed |
| Whole-source syntax compilation | Passed |
| Installed dependency consistency | Passed (`pip check`); the local uv-created environment first needed its standard pip bootstrap |
| Rebuild from pinned original TCC commit | Passed; generated manifest identical to committed manifest |
| Offline checksum-verified reanalysis | Passed; 28 output hashes checked, 16 exact listed exports, QA4 cohorts separate |
| Synthetic annotation import | Passed with explicit synthetic origin; zero human references |
| Synthetic arbitration/RAG demonstration | Passed, four authored rows in a separate report |
| Diff whitespace and changed-file credential-pattern check | Passed; no credential-shaped values found |

The covered evaluation/grading/storage modules have 78% aggregate statement coverage in this run. This is **not whole-application coverage**. The graph is 89%, nodes 91%, both real agent modules 100%; dataset rebuilding and report generation were also executed as separate end-to-end commands rather than represented by a blanket coverage claim. Coverage does not establish grading quality or security.

## Security gate remains red

The repaired unsuppressed Bandit job executes all default checks over `src/`, `app/` and `evaluation/`. The local final run exits 1 with **26 findings: one high and 25 low**, zero skipped checks. The high scanner finding is B324 at `src/core/file_hash_handler.py:65`, use of MD5. Low findings include inherited hardcoded-password/exception heuristics and five warnings around the new read-only Git dataset helper. These are scanner findings requiring review, **not 26 audited exploitable vulnerabilities**.

No skip list, `nosec`, severity filter or `continue-on-error` conceals these results. The workflow uploads the complete findings artifact on failure. Docker build requires both functional tests and security to pass, so it remains blocked. Security remediation and production approval are outside this case.

## Visual deliverables

The actual local Streamlit dashboard was inspected in the in-app browser; its chart and cohort interactions also pass the AppTests. The portable technical report's canonical manifest passes the shared artifact validator, self-contained packaging and exact-payload/semantic-fallback structural checks. Four source-backed native charts are included.

**Portable HTML browser QA limitation:** no compatible Chromium headless-shell is installed. An attempt to use installed Chrome failed the packager's requested chart-extraction environment check. Final packaging therefore uses the supported `structural_only` path. Automated enhanced-reader desktop/narrow-mode verification, source-dialog interaction and extracted static chart SVGs are not claimed. The report retains the shared interactive reader and semantic no-script chart-data tables; its packaging receipt records this limitation.

## Hosted checks and review

The consolidated work starts from draft PR #18's head `efe7d2e3ab250e91321592e7e31e55c7ea4c42d7`, on isolated branch `feat/reliability-lab-complete`. Current hosted results and raw artifacts are accessible in [branch GitHub Actions](https://github.com/savinoo/ai-grading-system/actions?query=branch%3Afeat%2Freliability-lab-complete) and the consolidated PR's checks. The final PR description records the observed hosted outcome and exact run link. PR #18 remains unchanged; no merge to `main` or production deployment was authorized or performed.

Expected hosted state after fixing setup: functional/offline checks pass; Security Scan fails on visible findings; Docker Build is skipped because of that security gate. A successful offline job alone must not be described as an entirely green CI.

## Not performed / unavailable

- Live LLM inference, token pricing and actual model-inference latency measurement.
- Real embedding-provider/vector-database retrieval or PostgreSQL backend integration.
- Docker image/runtime validation: Docker is unavailable locally, and the security gate blocks the hosted build. The inherited image's psycopg2/libpq prerequisites remain an unverified risk documented in `docs/CI_AND_RELEASE_STATUS.md`.
- Human rating/adjudication, human-relative accuracy, arbitration error reduction or causal RAG improvement.
- Production authentication/security audit, remediation or public deployment.

The three experiments are implemented as evidence-aware analyses and future measurement pipelines. Missing research evidence is an explicit study limitation, not a software test pass or a synthetic substitute.
