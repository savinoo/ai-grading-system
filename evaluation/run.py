"""Reproduce the historical Lab from the committed deidentified exports, offline."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from evaluation.annotation import load_gold
from evaluation.experiments import evaluate_experiments, write_outputs as write_experiments
from evaluation.reliability import evaluate_exports, write_outputs


def verify_dataset(directory):
    """Reject changed frozen files before evaluating them; never silently trust cache."""
    directory = Path(directory)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    output_paths = [entry["path"] for entry in manifest["outputs"]]
    if len(output_paths) != len(set(output_paths)):
        raise ValueError("Frozen dataset manifest contains duplicate output paths")
    listed_exports = {entry["path"] for entry in manifest["outputs"]
                      if Path(entry["path"]).parent.as_posix() == "exports" and entry["path"].endswith(".json")}
    actual_exports = {path.relative_to(directory).as_posix()
                      for path in (directory / "exports").rglob("*.json")}
    if actual_exports != listed_exports:
        raise ValueError("Frozen dataset exports must match the manifest exactly; unlisted or missing export")
    for entry in manifest["outputs"]:
        target = directory / entry["path"]
        if not target.resolve().is_relative_to(directory.resolve()):
            raise ValueError("Manifest paths must stay inside the dataset directory")
        actual = hashlib.sha256(target.read_bytes()).hexdigest()
        if actual != entry["sha256"]:
            raise ValueError(f"Frozen dataset checksum mismatch: {entry['path']}")
    return manifest


def reproduce(directory, output, gold_path=None):
    directory, output = Path(directory), Path(output)
    manifest = verify_dataset(directory)
    gold = load_gold(gold_path)
    paths = sorted(directory / entry["path"] for entry in manifest["outputs"]
                   if Path(entry["path"]).parent.as_posix() == "exports" and entry["path"].endswith(".json"))
    cohorts = {"qa4_json": [], "qa4_notebook": []}
    for path in paths:
        obj = json.loads(path.read_text(encoding="utf-8"))
        family = (obj.get("provenance") or {}).get("source_family")
        if family == "tcc_qa4_json":
            cohorts["qa4_json"].append(path)
        elif family == "notebook_qa4":
            cohorts["qa4_notebook"].append(path)
    for name, cohort in cohorts.items():
        if not cohort:
            raise ValueError(f"Missing required separate cohort: {name}")
        report = evaluate_exports(cohort, gold=gold)
        report.update(dataset_id=f"tcc-{name}-v1", source_commit=manifest["source_commit"],
                      response_origin="synthetic_profiles", dataset_kind="historical_observational")
        write_outputs(report, output / name)
    experiments = evaluate_experiments(paths, gold=gold)
    write_experiments(experiments, output)
    receipt = {"source_commit": manifest["source_commit"], "verified_files": len(manifest["outputs"]),
               "cohorts": {name: len(cohort) for name, cohort in cohorts.items()},
               "human_reference_labels_loaded": len(gold.by_material),
               "scope": "Offline reanalysis; no new model calls or production services"}
    output.mkdir(parents=True, exist_ok=True)
    (output / "reproduction.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", default="evaluation/data")
    parser.add_argument("--output", default="evaluation/output/reproduced")
    parser.add_argument("--gold", default=None, help="Optional provenance-validated human annotations")
    args = parser.parse_args()
    print(json.dumps(reproduce(args.data, args.output, args.gold), indent=2))


if __name__ == "__main__":
    main()
