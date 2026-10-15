"""Non-secret experiment provenance, safe for exports and portfolio artifacts.

All hashes are SHA-256 digests of code files, not hashes of student data or credentials.
Missing source files are reported explicitly, never replaced by fabricated hashes.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_VERSIONED_SOURCES = {
    "examiner_prompt_file": "src/domain/ai/prompts.py",
    "examiner_runtime_file": "src/services/agents/examiner_agent.py",
    "arbiter_runtime_file": "src/services/agents/arbiter_agent.py",
    "consensus_runtime_file": "src/domain/ai/utils/consensus_builder.py",
    "retriever_file": "src/services/rag/retrieval_service.py",
    "workflow_file": "src/domain/ai/workflow/nodes.py",
}


def source_fingerprints(root: Path | None = None) -> dict:
    """Fingerprint the grading sources without recording secrets or answer text."""
    project_root = root if root is not None else _REPO_ROOT
    fingerprints = {}
    for label, relative_path in _VERSIONED_SOURCES.items():
        source = project_root / relative_path
        fingerprints[label + "_sha256"] = (
            hashlib.sha256(source.read_bytes()).hexdigest() if source.is_file() else None
        )
    return fingerprints


def build_experiment_config(settings) -> dict:
    """Capture the *effective* non-secret runtime configuration for a new run.

    Callers may override e.g. rag_enabled or divergence_threshold per experiment.
    That experiment-specific value must win in the final config dictionary.
    """
    revision = os.environ.get("GITHUB_SHA") or os.environ.get("SOURCE_COMMIT_SHA")
    return {
        "provenance_schema_version": 1,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL_NAME,
        "llm_temperature": settings.LLM_TEMPERATURE,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "embedding_model": settings.EMBEDDING_MODEL,
        "rag_top_k": settings.RAG_TOP_K,
        "divergence_threshold": settings.DIVERGENCE_THRESHOLD,
        "code_revision": revision,
        "source_fingerprints": source_fingerprints(),
    }
