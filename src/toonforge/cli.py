import argparse
from pathlib import Path

import uvicorn

from .config import DATA_ROOT, OLLAMA_MODEL, OLLAMA_URL
from .mcp_client import ToolClient
from .ollama import OllamaVision
from .storage import JobStore
from .workflow import Workflow


def main() -> None:
    parser = argparse.ArgumentParser(description="本地插画转三渲二工作流")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser("run", help="处理一张 PNG/JPEG")
    run.add_argument("image", type=Path)
    serve = subparsers.add_parser("serve", help="启动本地网页")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    if args.command == "serve":
        uvicorn.run("toonforge.api:app", host=args.host, port=args.port)
        return
    store = JobStore(DATA_ROOT)
    job = store.create(args.image.read_bytes())
    result = Workflow(store, OllamaVision(OLLAMA_URL, OLLAMA_MODEL), ToolClient(store.root)).run(job["id"])
    print(store.directory(job["id"]))
    print(result["status"], result.get("error") or "")
    if result["status"] != "completed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
