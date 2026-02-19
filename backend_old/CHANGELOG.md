# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (2026-02-10)
- Performance logging with `measure_time` context manager in DSPy agents
- Auto-detection and normalization for 0-1 → 0-10 grade scale
- Robust JSON parsing fallbacks in DSPy Examiner and Arbiter
- Detailed error logging for debugging LLM output issues
- `PERFORMANCE.md` with benchmarks, configuration guide, and troubleshooting
- `CHANGELOG.md` (this file)

### Changed (2026-02-10)
- **BREAKING**: Increased `API_CONCURRENCY` default from 2 to 10 (5x parallelism)
  - May hit rate limits on free-tier APIs (Gemini)
  - Use `export API_CONCURRENCY=5` to reduce if needed
- Updated corrector and arbiter prompts with explicit 0-10 scale instructions
- Improved schema validation in `AgentCorrection` to handle LLM output variations

### Fixed (2026-02-10)
- **Critical**: Grades appearing as 0-1 instead of 0-10 ([`fd4b42e`])
  - Added explicit scale instructions in prompts
  - Added auto-normalization when all scores ≤ 1.5
- **Critical**: `JSONDecodeError: Expecting value: line 1 column 1 (char 0)` in DSPy Arbiter ([`6d47c56`])
  - Added validation before JSON parsing (empty string, non-JSON text)
  - Arbiter fallback: average of two corrections
  - Examiner fallback: 0.0 with error message
- Asyncio Semaphore cross-event-loop error in Streamlit reruns
- LLM import-time creation causing Streamlit issues
- DSPy examiner validation loop with schema mismatches

### Performance (2026-02-10)
- **5x speedup**: 10 students × 3 questions from ~10min to ~2-3min
  - Increased parallelism (API_CONCURRENCY 2 → 10)
  - RAG cache already implemented (verified)
  - Batch processing with chunking
- **Reduced API calls**: RAG cache reduces 30 calls → 3 calls (one per question)

## [0.1.0] - 2026-02-08

### Added
- Initial release with DSPy-based grading agents
- Multi-agent correction system (2 correctors + arbiter)
- RAG context retrieval with Chroma vector DB
- LangSmith tracing integration
- Streamlit UI with batch processing
- Analytics dashboard with student tracking
- Mock data generation for testing

---

## Migration Guide

### Upgrading to 2026-02-10 Performance Update

**If you're using Gemini free-tier:**
```bash
# Add to your .env or export before running
export API_CONCURRENCY=5
export API_THROTTLE_SLEEP=0.5
export BATCH_CHUNK_SIZE=3
export BATCH_COOLDOWN_SLEEP=1.0
```

**If you're using OpenAI (paid tier):**
```bash
# Defaults should work fine
export API_CONCURRENCY=10  # or higher if you want more speed
export API_THROTTLE_SLEEP=0.2
```

**Grade normalization:**
- Old grades (0-1 scale) will be auto-converted to 0-10
- Check logs for `[NORMALIZAÇÃO]` warnings
- Update prompts if using custom corrector agents

**JSON parsing:**
- Errors now fallback gracefully instead of crashing
- Arbiter uses average of corrections on failure
- Check logs for `[Sistema] Fallback` messages

---

## Links

- [Performance Guide](PERFORMANCE.md)
- [Repository](https://github.com/savinoo/ai-grading-system)
- [Issues](https://github.com/savinoo/ai-grading-system/issues)

[Unreleased]: https://github.com/savinoo/ai-grading-system/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/savinoo/ai-grading-system/releases/tag/v0.1.0

[`fd4b42e`]: https://github.com/savinoo/ai-grading-system/commit/fd4b42e
[`6d47c56`]: https://github.com/savinoo/ai-grading-system/commit/6d47c56
[`1e3b2f0`]: https://github.com/savinoo/ai-grading-system/commit/1e3b2f0
