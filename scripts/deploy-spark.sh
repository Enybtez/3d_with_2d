#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if command -v python3.11 >/dev/null 2>&1; then
  python3.11 -m venv .venv
else
  python3.12 -m venv .venv
fi
source .venv/bin/activate
if [[ -f data/run.env ]]; then
  source data/run.env
fi
python -m pip install -e '.[test]'
python -m compileall -q src scripts examples
python -m pytest -q
command -v "${BLENDER_BIN:-blender}" >/dev/null
curl --fail --silent http://127.0.0.1:11434/api/tags >/dev/null
curl --fail --silent http://127.0.0.1:8081/health >/dev/null
exec python -m toonforge.cli serve
