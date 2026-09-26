"""Local HTTP adapter for the DGX Spark Hunyuan3D Docker Compose CLI."""

import argparse
import base64
import binascii
import io
import struct
import subprocess
import threading
from pathlib import Path
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel


class GenerateRequest(BaseModel):
    image: str
    type: str = "glb"
    texture: bool = True


def create_app(repo_root: Path, runner=subprocess.run) -> FastAPI:
    repo_root = Path(repo_root).resolve()
    if not (repo_root / "compose.yaml").is_file():
        raise FileNotFoundError(f"找不到 Spark Hunyuan3D compose.yaml: {repo_root}")
    assets = repo_root / "assets"
    outputs = repo_root / "out"
    assets.mkdir(exist_ok=True)
    outputs.mkdir(exist_ok=True)
    lock = threading.Lock()
    app = FastAPI(title="ToonForge Spark Hunyuan bridge")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/generate")
    def generate(request: GenerateRequest):
        if request.type != "glb" or not request.texture:
            raise HTTPException(400, "桥接服务只支持带纹理 GLB")
        try:
            raw = base64.b64decode(request.image, validate=True)
            with Image.open(io.BytesIO(raw)) as image:
                image.verify()
            with Image.open(io.BytesIO(raw)) as image:
                normalized = image.convert("RGBA" if "A" in image.getbands() else "RGB")
        except (binascii.Error, ValueError, UnidentifiedImageError, OSError):
            raise HTTPException(400, "输入不是有效的 base64 图片") from None

        name = f"toonforge-{uuid4().hex}"
        image_path = assets / f"{name}.png"
        shape_path = outputs / f"{name}-shape.glb"
        textured_path = outputs / f"{name}-textured.glb"
        with lock:
            try:
                normalized.save(image_path, format="PNG")
                runner(
                    ["docker", "compose", "run", "--rm", "shape", "scripts/shape_infer.py",
                     "--image", f"/workspace/assets/{image_path.name}",
                     "--out", f"/workspace/out/{shape_path.name}"],
                    cwd=repo_root, check=True, capture_output=True, text=True, timeout=1200,
                )
                runner(
                    ["docker", "compose", "run", "--rm", "full", "scripts/texture_infer.py",
                     "--mesh", f"/workspace/out/{shape_path.name}",
                     "--image", f"/workspace/assets/{image_path.name}",
                     "--out", f"/workspace/out/{textured_path.name}"],
                    cwd=repo_root, check=True, capture_output=True, text=True, timeout=1200,
                )
                data = textured_path.read_bytes()
                if len(data) < 12 or data[:4] != b"glTF" or struct.unpack_from("<II", data, 4) != (2, len(data)):
                    raise ValueError("纹理脚本未生成有效 GLB")
                return Response(data, media_type="model/gltf-binary")
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, ValueError) as exc:
                detail = getattr(exc, "stderr", None) or str(exc)
                raise HTTPException(502, f"Spark Hunyuan3D 生成失败: {detail}") from exc
            finally:
                for path in (image_path, shape_path, textured_path):
                    path.unlink(missing_ok=True)

    return app


def main():
    parser = argparse.ArgumentParser(description="Spark Hunyuan3D Compose 本地 HTTP 桥接")
    parser.add_argument("--repo", type=Path, required=True, help="hunyuan3d-spark-fast 仓库目录")
    parser.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()
    uvicorn.run(create_app(args.repo), host="127.0.0.1", port=args.port, workers=1)


if __name__ == "__main__":
    main()
