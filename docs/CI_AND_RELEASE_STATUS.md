# CI and release status

The Reliability Lab is an offline research deliverable. No merge, production
release or deployment is part of this case.

## Repaired execution path

The inherited CI referred to absent `requirements-dev.txt` and `pyproject.toml`,
so neither tests nor the security scan actually ran. Both files now exist.
`requirements.txt` was converted from UTF-16 to UTF-8 without changing its pins.
The lab has a separate `requirements-evaluation.txt` so reproducing historical
analyses does not require the production API, a database, vector server or model
credentials. `requirements-dev.txt` adds the real LangGraph runtime and test
instruments; it intentionally does not install cloud provider SDKs. The matching `.lock`
files pin transitive packages using the universal resolver's platform markers for
Python 3.12; install the lock files for the documented reproduction environment.

The main CI now runs dependency consistency, Python compilation, fatal Ruff
correctness checks across **all** `src`, `app`, `evaluation` and `tests`, and pytest
with coverage. Its format gate covers the new integration tests. A
whole-codebase style rewrite is outside this research case; broad fatal checks
have no baseline or per-file ignores. The independent Reliability Evaluation
workflow also runs the standard-library tests without installing dependencies.

`tests/integration_grading_workflow.py` executes the real compiled LangGraph,
Pydantic schemas, parallel examiner paths, divergence routing, closest-pair
consensus and SQLite export. Only the external examiner, arbiter and retrieval
boundaries return deterministic synthetic fixtures. It verifies exact threshold
behavior, nonempty RAG evidence and metadata, supplied-context bypass and error
propagation. The prompt/structured-output test also runs the real ExaminerAgent and
ArbiterAgent chains, replacing only the chat model transport. These are software
integration tests, never estimates of model
quality, real provider latency/cost or human agreement.

## Security remains a release gate

Bandit runs all default checks against `src`, `app` and `evaluation`. There is no
`continue-on-error`, skipped rule, severity filter, baseline or `nosec` addition.
The scanner writes a JSON artifact uploaded even on failure. An empty Bandit
TOML section replaces the previously missing configuration, without suppressions.

The Docker build depends on **both** test and security jobs. Findings therefore
block that build. This repository has no deployment step in these workflows;
passing research tests is never authorization or evidence for production safety.
A failed Security Scan is expected to stay visible until a separate reviewed
security change resolves or documents each finding. A clean Bandit scan alone
would still not constitute a full security audit. Remediation of inherited
application/authentication security is explicitly outside this case.

## Local commands

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/python -m pip check
.venv/bin/ruff check src/ app/ evaluation/ tests/
.venv/bin/ruff format --check tests/integration_*.py
.venv/bin/python -m compileall -q src/ app/ evaluation/ tests/
.venv/bin/pytest tests/ -q
.venv/bin/bandit -r src/ app/ evaluation/ -c pyproject.toml -f json -o bandit-report.json
```

The final command must return nonzero if it finds issues. Do not interpret that
failure as a flaky research test or change it to a nonblocking invocation.
A Python 3.12.12 local run passed **50 tests**, including all five graph/provider
transport integration scenarios. Dependency consistency, whole-source fatal
Ruff checks and the integration format check passed. Two existing upstream
deprecation warnings remained visible. The coverage run reports 89% for graph.py,
91% for nodes.py and 100% for both agent implementations; it does not cover live
cloud transport, a PostgreSQL server or the dashboard UI.

The final unsuppressed local scan reported 26 findings (1 high, 25 low).
The high finding is B324 at `src/core/file_hash_handler.py:65` (MD5); the low
findings include B105/B110 heuristics and B404/B603/B607 on the dataset import
helper's read-only Git subprocess calls. They are unreviewed scanner findings, not an
audited vulnerability count. No finding was remediated or suppressed here.

Full production API/provider compatibility, PostgreSQL integration and a Docker
runtime test are separate validations unless explicitly reported as executed.

## Unverified inherited container prerequisite

No Docker executable is available in the local validation environment, and the
hosted Docker job is intentionally gated by the failing security scan. No image
build or container startup has been validated for this delivery.

`requirements.txt` pins `psycopg2==2.9.11`. The Docker builder explicitly installs
`build-essential` and `gcc`, but does not install `libpq-dev` or provide `pg_config`;
the runtime stage only explicitly installs `curl`. Psycopg source builds require
the PostgreSQL client headers and `pg_config`, and dynamically linked builds also
need the client library at runtime. See the [official Psycopg installation
prerequisites](https://www.psycopg.org/docs/install.html#build-prerequisites).
The absent explicit packages are an inferred build/runtime risk, not an observed
Docker failure. A separate container validation should inspect the selected base
image, supply matching build/runtime libraries if needed, and execute an import
and startup check. The Dockerfile remains unchanged in this research case.
