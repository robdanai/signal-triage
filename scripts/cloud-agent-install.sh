#!/usr/bin/env bash
# Idempotent environment bootstrap for Signal Triage Cloud Agents.
#
# Installs the system packages the Python stack needs, creates a project
# virtualenv, and installs the pinned Python dependencies. Safe to re-run.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

VENV_DIR="$REPO_ROOT/.venv"

# --- System dependencies -------------------------------------------------
# python3-venv: required to create the virtualenv (ensurepip).
# tesseract-ocr: backend for pytesseract (scanned-PDF OCR ingestion).
SYSTEM_PACKAGES=(python3-venv tesseract-ocr)
MISSING=()
for pkg in "${SYSTEM_PACKAGES[@]}"; do
  if ! dpkg -s "$pkg" >/dev/null 2>&1; then
    MISSING+=("$pkg")
  fi
done
if [ "${#MISSING[@]}" -gt 0 ]; then
  echo "Installing system packages: ${MISSING[*]}"
  sudo apt-get update -qq
  sudo apt-get install -y --no-install-recommends "${MISSING[@]}"
else
  echo "System packages already present: ${SYSTEM_PACKAGES[*]}"
fi

# --- Python virtualenv ---------------------------------------------------
if [ ! -x "$VENV_DIR/bin/python" ]; then
  echo "Creating virtualenv at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip

# --- Python dependencies -------------------------------------------------
echo "Installing Python dependencies (editable package + requirements)"
"$VENV_DIR/bin/pip" install -e . \
  -r requirements.txt \
  -r requirements_parsers.txt

echo "Signal Triage environment ready. Activate with: source .venv/bin/activate"
