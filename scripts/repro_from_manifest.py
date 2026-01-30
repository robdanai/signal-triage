#!/usr/bin/env python3
"""
Replay a pipeline run from a run manifest (run_manifest.json).

Usage:
  python scripts/repro_from_manifest.py run_manifest.json
  python scripts/repro_from_manifest.py path/to/report.json   # finds run_manifest.json in same dir

Reads config_versions, document_sources, pipeline_mode, input_path from the manifest
and runs the same pipeline (single file or batch). Exits 0 on success.
"""

from __future__ import annotations

import json
import sys

from signal_triage.run_manifest import repro_from_manifest


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/repro_from_manifest.py run_manifest.json | report.json", file=sys.stderr)
        return 2
    try:
        report = repro_from_manifest(sys.argv[1])
        print(json.dumps(report, indent=2))
        return 0 if report.get("published", True) else 1
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
