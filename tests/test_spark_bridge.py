import base64
import io
import struct
import subprocess

from fastapi.testclient import TestClient
from PIL import Image

from toonforge.spark_bridge import create_app


GLB = b"glTF" + struct.pack("<II", 2, 12)


def payload():
    image = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(image, format="PNG")
    return {"image": base64.b64encode(image.getvalue()).decode(), "type": "glb", "texture": True}


def test_bridge_runs_local_shape_then_texture_and_returns_glb(tmp_path):
    (tmp_path / "compose.yaml").write_text("services: {}")
    calls = []

    def run(command, **kwargs):
        calls.append((command, kwargs))
        if command[4] == "shape":
            (tmp_path / "out" / command[-1].split("/")[-1]).write_bytes(GLB)
        else:
            (tmp_path / "out" / command[-1].split("/")[-1]).write_bytes(GLB)

    client = TestClient(create_app(tmp_path, runner=run))
    assert client.get("/health").json() == {"status": "ok"}
    response = client.post("/generate", json=payload())
    assert response.status_code == 200
    assert response.content == GLB
    assert [call[0][4] for call in calls] == ["shape", "full"]
    assert [call[0][5] for call in calls] == ["scripts/shape_infer.py", "scripts/texture_infer.py"]
    assert all(call[1]["cwd"] == tmp_path for call in calls)
    assert all(call[1]["check"] is True for call in calls)
    assert list((tmp_path / "assets").iterdir()) == []
    assert list((tmp_path / "out").iterdir()) == []


def test_bridge_rejects_bad_image_and_format_before_docker(tmp_path):
    (tmp_path / "compose.yaml").write_text("services: {}")
    calls = []
    client = TestClient(create_app(tmp_path, runner=lambda *args, **kwargs: calls.append(args)))
    assert client.post("/generate", json={**payload(), "image": "bad"}).status_code == 400
    assert client.post("/generate", json={**payload(), "type": "obj"}).status_code == 400
    assert calls == []


def test_bridge_reports_docker_failure(tmp_path):
    (tmp_path / "compose.yaml").write_text("services: {}")

    def fail(command, **kwargs):
        raise subprocess.CalledProcessError(1, command, stderr="CUDA failed")

    client = TestClient(create_app(tmp_path, runner=fail))
    response = client.post("/generate", json=payload())
    assert response.status_code == 502
    assert "CUDA failed" in response.json()["detail"]
