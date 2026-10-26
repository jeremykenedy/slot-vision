#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
bash -n "$ROOT/build.sh"
python3 "$ROOT/scripts/check-privacy.py"
(cd "$ROOT" && python3 -m unittest tests.test_models)
bash "$ROOT/scripts/test-python-coverage.sh"
bash "$ROOT/scripts/test-coverage.sh"
