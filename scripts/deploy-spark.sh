#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
python -m compileall -q src scripts examples
python -m pytest -q
command -v blender >/dev/null
curl --fail --silent http://127.0.0.1:11434/api/tags >/dev/null
curl --fail --silent http://127.0.0.1:8081/health >/dev/null
exec python -m toonforge.cli serve
