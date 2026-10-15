# Frozen historical evaluation corpus

This reviewed release contains synthetic experimental responses authored/generated for the repository owner's TCC. Model grades are observations, not human labels. It excludes participant names, emails, original participant/exam/question IDs, feedback and reasoning chains. Pseudonyms can be linked to the public source; this is not irreversible anonymization. Do not use the builder as a general anonymizer for real student data.

Rebuild from the pinned source commit without model calls:

```bash
git fetch origin tcc
python -m evaluation.dataset build
```

The default commit is `79495d00948908503ed4489861ea319a2c7e7972`. `manifest.json` records source paths, source SHA256 checksums and generated-file checksums. The normalized `exports/` retain the common ExperimentStore structure, provenance, actual status and configuration unknowns. Initial A/B runs with no outcomes remain present as failed/timeout evidence.

Two QA4 cohorts are separate:

| Corpus | Rows | Cases | Questions | Largest final-score range | Answer identity |
| --- | ---: | ---: | --- | ---: | --- |
| JSON (`reliability_report.json`) | 36 | 12 | Q1, Q2, Q3 | 0.625 | Exact text absent; descriptive stability only |
| Notebook (`qa4_notebook_report.json`) | 12 | 4 | Q2 | 1.37 | Exact text present; different rubric/implementation |

The notebook's exported final/consensus/divergence fields contain inconsistencies. Reports preserve the final scores as observed, recompute examiner differences from C1/C2, and flag inconsistent source metadata. They do not silently repair results or pool the cohorts.

Retrieved-context evidence consists of 240-character excerpts, full original-content SHA256, original text length and source/page metadata when recorded. A document UUID in a source PDF basename is retained as a public retrieval locator. Notebook contexts were recorded at question level, explicitly marked as such when attached to answer records. The exact full textbook passages remain in the pinned historical source; the corpus does not reproduce them wholesale.

`annotation/blind_packet.json` contains 48 exact annotation materials without model grades, quality-profile labels or experiment-condition paths. The rating template is unreviewed. `synthetic_demo/` contains invented format-test annotations and is excluded from human-reference metrics. There are zero human gold labels in this release. See `../ANNOTATION_PROTOCOL.md` for the provenance, blindness, rubric and adjudication gates.
