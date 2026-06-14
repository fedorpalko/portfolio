#!/usr/bin/env bash
# WSLAB setup: create a virtual environment and install dependencies.
set -euo pipefail

cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"

echo "[wslab] Creating virtual environment in ./venv ..."
"$PYTHON" -m venv venv

echo "[wslab] Upgrading pip ..."
venv/bin/pip install --upgrade pip

echo "[wslab] Installing dependencies ..."
venv/bin/pip install -r requirements.txt

# Preferred indicator library; optional because it lacks Python 3.14 wheels.
# WSLAB falls back to built-in pandas indicators if this fails.
echo "[wslab] Installing pandas-ta (optional) ..."
venv/bin/pip install "pandas-ta>=0.3.14b0" \
    || echo "[wslab] pandas-ta unavailable on this Python — using pandas fallback."

echo
echo "[wslab] Setup complete. Launch with:"
echo "    venv/bin/python src/main.py"
