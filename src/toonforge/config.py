import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = Path(os.environ.get("TOONFORGE_DATA_ROOT", PROJECT_ROOT / "data" / "jobs")).resolve()
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3-vl:8b-instruct")
HUNYUAN_URL = os.environ.get("HUNYUAN_URL", "http://127.0.0.1:8081")
BLENDER_BIN = os.environ.get("BLENDER_BIN", "blender")
