#!/usr/bin/env bash
# Sets up a virtual environment and installs Fincli's dependencies.
set -e

cd "$(dirname "$0")"

echo "Creating virtual environment in ./venv ..."
python3 -m venv venv

echo "Upgrading pip ..."
./venv/bin/pip install --quiet --upgrade pip

echo "Installing dependencies ..."
./venv/bin/pip install --quiet -r requirements.txt

echo ""
echo "Done. Launch Fincli with:"
echo "    ./venv/bin/python src/main.py"
