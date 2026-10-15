# Synthetic arbitration and RAG pipeline demonstration

Every question, answer, grade, context, provider/model name and fingerprint in
`rag.json` and `no_rag.json` is an explicitly authored **synthetic fixture**. No
model was called and no human assessed these grades. The zero fingerprints do
not describe real runtime code. The fixture tests evidence gates and arithmetic;
its numerical outputs are not research findings.

Run from the repository root:

```sh
python3 -m evaluation.experiments \
  evaluation/examples/synthetic_arbitration_rag/rag.json \
  evaluation/examples/synthetic_arbitration_rag/no_rag.json \
  --output evaluation/examples/synthetic_arbitration_rag/output
```

The output is marked `synthetic_demonstration`. The historical analysis rejects
mixing these files with the real historical exports. Both arms have exact paired
material and explicitly supplied synthetic configuration/context evidence. Their
grade shift only demonstrates the paired pipeline. Accuracy, human reference
error, cost and latency remain unavailable. The lower arbitration thresholds
expose an unavailable arbiter score rather than inventing it.

The separately documented annotation workflow provides a synthetic reference
example; these files intentionally contain **no reference labels**.
