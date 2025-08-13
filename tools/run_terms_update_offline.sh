#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

offline_dir="data/terms_catalog/html"
mkdir -p "$offline_dir"

if ! python3 -c "import bs4, lxml" 2>/dev/null; then
  echo "Installing dependencies (beautifulsoup4, lxml)..."
  pip3 install --quiet beautifulsoup4 lxml
fi

python3 tools/build_terms_catalog.py --offline-dir "$offline_dir"
echo "Terms catalog updated from offline HTML: $offline_dir"

