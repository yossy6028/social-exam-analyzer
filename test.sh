#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 run_all_tests.py "$@"

