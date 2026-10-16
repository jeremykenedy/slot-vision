#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VENV="$ROOT/build/python-coverage"
if [[ ! -x "$VENV/bin/python" ]]; then python3 -m venv "$VENV"; fi
"$VENV/bin/python" -m pip install --disable-pip-version-check -r "$ROOT/requirements-dev.txt"
cd "$ROOT"
"$VENV/bin/python" -m coverage run --branch --include='install.py' -m unittest tests.test_installer
"$VENV/bin/python" -m coverage report --fail-under=100
