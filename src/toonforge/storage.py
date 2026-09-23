import io
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, UnidentifiedImageError


MAX_IMAGE_BYTES = 10 * 1024 * 1024
ACTIVE = {"queued", "analyzing", "modeling", "rendering", "reviewing"}


class JobStore:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def create(self, image_bytes: bytes) -> dict:
        if not image_bytes or len(image_bytes) > MAX_IMAGE_BYTES:
            raise ValueError("图片必须非空且不超过 10 MB")
        try:
            with Image.open(io.BytesIO(image_bytes)) as image:
                image.verify()
                image_format = image.format
        except (UnidentifiedImageError, OSError, SyntaxError) as exc:
            raise ValueError("图片格式无效") from exc
        if image_format not in {"PNG", "JPEG"}:
            raise ValueError("只支持 PNG 或 JPEG")
        job_id = str(uuid.uuid4())
        directory = self.root / job_id
        directory.mkdir()
        filename = "input.png" if image_format == "PNG" else "input.jpg"
        (directory / filename).write_bytes(image_bytes)
        job = {
            "id": job_id,
            "status": "queued",
            "stage": "queued",
            "input": filename,
            "analysis": None,
            "review": None,
            "agent_trace": [],
            "error": None,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self._write(job)
        return job

    def directory(self, job_id: str) -> Path:
        try:
            if str(uuid.UUID(job_id)) != job_id:
                raise ValueError
        except (ValueError, AttributeError) as exc:
            raise ValueError("无效任务 ID") from exc
        return self.root / job_id

    def get(self, job_id: str) -> dict:
        path = self.directory(job_id) / "job.json"
        if not path.is_file():
            raise FileNotFoundError(job_id)
        return json.loads(path.read_text(encoding="utf-8"))

    def update(self, job_id: str, **fields) -> dict:
        job = self.get(job_id)
        job.update(fields)
        self._write(job)
        return job

    def recover_interrupted(self) -> None:
        for path in self.root.glob("*/job.json"):
            job = json.loads(path.read_text(encoding="utf-8"))
            if job["status"] in ACTIVE:
                self.update(job["id"], status="failed", error="进程中断，请重新提交")

    def _write(self, job: dict) -> None:
        path = self.directory(job["id"]) / "job.json"
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(job, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)
