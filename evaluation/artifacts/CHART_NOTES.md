# Report chart contract and packaging notes

The report's four native charts answer categorical comparison questions. All use bars because no chart claims a time trend, independent-row distribution or causal response curve. They retain exact values and denominators in the reviewed snapshot and source dialogs.

| Chart | Question | Data grain | Interpretation and limit |
|---|---|---|---|
| Examiner disagreement | Which response profiles have larger C1/C2 differences? | Four profiles, nine rows each, QA4 JSON only | Mean absolute difference in 0–10 points, not human error |
| Recorded score range | Which cases vary across runs? | Twelve anonymous QA4 JSON cases, three repetitions each | Recorded maximum minus minimum; identical answers unverified |
| Threshold referrals | How many QA4 JSON rows would request arbitration? | Four strict thresholds over the same 36 rows | Counts only; unavailable counterfactual grades are not inferred |
| RAG score shift | How do recorded A/B grades differ? | Four separate exact-material comparisons, twelve pairs each | Signed RAG-minus-no-RAG grade shift; zero controlled historical pairs |

Single-series charts use a declared blue sequential palette with direct category labels, no redundant color grouping. Magnitude bars include zero; the signed RAG comparison keeps a visible zero baseline. The app applies native light/dark appearance. Source snapshots preserve neighboring counts, scale, cases, signed differences and controls for auditability. SQL aggregation queries are actually executed by `evaluation/presentation.py` against in-memory tables materialized from the reviewed results; source paths identify those inputs. Pair matching remains implemented in `evaluation/experiments.py`.

The portable report is packaged by the Data Analytics `deliver_portable_artifact.mjs` workflow. Final verification status and any browser limitation are recorded in `evaluation/VALIDATION.md`. The output embeds the reader, chart data and semantic no-script chart-data tables, with no external scripts or server dependency.
