"""
Run manifest and repro: re-play a pipeline run from run_manifest.json.

Used by --out (write manifest next to report) and scripts/repro_from_manifest.py.
"""

from __future__ import annotations

import json
from pathlib import Path

from signal_triage.pipeline import run_pipeline, run_pipeline_batch


def find_manifest(path: Path) -> Path | None:
    """Resolve to run_manifest.json: if path is a report file, look for run_manifest.json alongside."""
    path = path.resolve()
    if path.name == "run_manifest.json" and path.is_file():
        return path
    if path.is_file():
        manifest = path.parent / "run_manifest.json"
        if manifest.is_file():
            return manifest
    return None


def load_manifest(manifest_path: Path) -> dict:
    """Load and return manifest JSON."""
    with open(manifest_path, encoding="utf-8") as f:
        return json.load(f)


def repro_from_manifest(manifest_path: str | Path) -> dict:
    """
    Re-run the pipeline from a run manifest. Returns the new report dict.
    """
    path = Path(manifest_path)
    resolved = find_manifest(path)
    if resolved is None:
        raise FileNotFoundError(
            f"No run_manifest.json found for {path}. "
            "Provide path to run_manifest.json or to a report file that was written with --out."
        )
    manifest = load_manifest(resolved)
    pipeline_mode = manifest.get("pipeline_mode", "single")
    input_path_str = manifest.get("input_path")
    if not input_path_str:
        doc_sources = manifest.get("document_sources") or []
        if not doc_sources:
            raise ValueError("Manifest has no input_path and no document_sources")
        input_path_str = doc_sources[0]
    input_path = Path(input_path_str)
    if not input_path.exists():
        raise FileNotFoundError(f"input_path from manifest does not exist: {input_path}")

    if pipeline_mode == "batch":
        return run_pipeline_batch(input_path, require_audit_gate=False)
    return run_pipeline(input_path, require_audit_gate=False)
