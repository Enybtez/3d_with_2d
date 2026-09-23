from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from .config import DATA_ROOT, OLLAMA_MODEL, OLLAMA_URL, PROJECT_ROOT
from .jobs import JobQueue
from .mcp_client import ToolClient
from .ollama import OllamaVision
from .storage import JobStore
from .workflow import Workflow


def create_app(store=None, queue=None) -> FastAPI:
    store = store or JobStore(DATA_ROOT)
    if queue is None:
        store.recover_interrupted()
        queue = JobQueue(Workflow(store, OllamaVision(OLLAMA_URL, OLLAMA_MODEL), ToolClient(store.root)))
    app = FastAPI(title="ToonForge MVP")

    @app.get("/", response_class=HTMLResponse)
    def index():
        return (PROJECT_ROOT / "src" / "toonforge" / "static" / "index.html").read_text(encoding="utf-8")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/api/jobs", status_code=202)
    async def submit(image: UploadFile = File(...)):
        content = await image.read(10 * 1024 * 1024 + 1)
        try:
            job = store.create(content)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        queue.submit(job["id"])
        return {"id": job["id"], "status": job["status"]}

    @app.get("/api/jobs/{job_id}")
    def get_job(job_id: str):
        try:
            job = store.get(job_id)
        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=404, detail="任务不存在") from exc
        if job["status"] == "completed":
            job["model_url"] = f"/api/jobs/{job_id}/model"
            job["preview_url"] = f"/api/jobs/{job_id}/preview"
        return job

    @app.get("/api/jobs/{job_id}/{artifact}")
    def get_artifact(job_id: str, artifact: str):
        filename = {"model": "model.glb", "preview": "preview.png"}.get(artifact)
        if filename is None:
            raise HTTPException(status_code=404, detail="产物不存在")
        try:
            store.get(job_id)
            path = store.directory(job_id) / filename
        except (ValueError, FileNotFoundError) as exc:
            raise HTTPException(status_code=404, detail="任务不存在") from exc
        if not path.is_file():
            raise HTTPException(status_code=404, detail="产物不存在")
        return FileResponse(path, filename=filename if artifact == "model" else None)

    return app


app = create_app()
