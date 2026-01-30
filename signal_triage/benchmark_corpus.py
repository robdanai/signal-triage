"""
Locked benchmark corpus for reproducible quality and regression runs.

Load the canonical corpus from tests/fixtures/benchmark_corpus_manifest.json.
Scripts and tests should use this manifest to run against a fixed set of
documents; changing the corpus must bump corpus_version in the manifest.
"""

from __future__ import annotations

import json
import warnings
from pathlib import Path
from typing import Any

# Default manifest path relative to package root (repo root when running from repo)
BENCHMARK_CORPUS_MANIFEST_FILENAME = "benchmark_corpus_manifest.json"
SUPPORTED_CORPUS_MANIFEST_SCHEMA_VERSIONS = ("1.0",)


def _default_manifest_path() -> Path:
    """Path to benchmark_corpus_manifest.json under tests/fixtures."""
    # From signal_triage/ go up to repo root, then tests/fixtures/
    pkg = Path(__file__).resolve().parent
    return pkg.parent / "tests" / "fixtures" / BENCHMARK_CORPUS_MANIFEST_FILENAME


def load_benchmark_corpus_manifest(
    manifest_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Load the benchmark corpus manifest (corpus_version, files list, etc.).

    Args:
        manifest_path: Optional path to manifest; default is tests/fixtures/benchmark_corpus_manifest.json.

    Returns:
        Dict with corpus_version, description, schema_version, files (list of relative paths), notes.
        If manifest is missing or invalid, returns a minimal dict with corpus_version "0", files [].

    Raises:
        None; logs warnings on missing/invalid manifest or unsupported schema_version.
    """
    path = Path(manifest_path) if manifest_path else _default_manifest_path()
    if not path.exists() or not path.is_file():
        warnings.warn(
            f"Benchmark corpus manifest not found: {path}; using empty corpus.",
            UserWarning,
            stacklevel=2,
        )
        return {"corpus_version": "0", "files": [], "description": ""}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        warnings.warn(
            f"Benchmark corpus manifest invalid: {path} ({e}); using empty corpus.",
            UserWarning,
            stacklevel=2,
        )
        return {"corpus_version": "0", "files": [], "description": ""}
    schema_version = data.get("schema_version")
    if schema_version is not None and str(schema_version) not in SUPPORTED_CORPUS_MANIFEST_SCHEMA_VERSIONS:
        warnings.warn(
            f"benchmark_corpus_manifest.json schema_version={schema_version!r} is not in supported "
            f"{SUPPORTED_CORPUS_MANIFEST_SCHEMA_VERSIONS}; corpus may not be reproducible.",
            UserWarning,
            stacklevel=2,
        )
    files = data.get("files")
    if not isinstance(files, list):
        files = []
    return {
        "corpus_version": str(data.get("corpus_version", "0")),
        "description": str(data.get("description", "")),
        "schema_version": str(schema_version) if schema_version is not None else None,
        "files": [f for f in files if isinstance(f, str) and f.strip()],
        "notes": str(data.get("notes", "")),
    }


def resolve_benchmark_corpus_paths(
    manifest_path: str | Path | None = None,
    base_dir: str | Path | None = None,
) -> list[Path]:
    """
    Return absolute paths to all files in the locked benchmark corpus.

    Args:
        manifest_path: Optional path to manifest; default is tests/fixtures/benchmark_corpus_manifest.json.
        base_dir: Directory to resolve relative file paths; default is manifest's parent.

    Returns:
        List of absolute Paths to corpus files that exist. Missing files are skipped with a warning.
    """
    manifest = load_benchmark_corpus_manifest(manifest_path)
    path = Path(manifest_path) if manifest_path else _default_manifest_path()
    base = Path(base_dir) if base_dir else path.parent
    resolved: list[Path] = []
    for rel in manifest.get("files", []):
        full = base / rel
        if full.exists() and full.is_file():
            resolved.append(full.resolve())
        else:
            warnings.warn(
                f"Benchmark corpus file missing: {full} (from manifest {path})",
                UserWarning,
                stacklevel=2,
            )
    return resolved
