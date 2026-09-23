import io

from fastapi.testclient import TestClient
from PIL import Image

from toonforge.api import create_app
from toonforge.storage import JobStore


def test_submit_status_and_invalid_image(tmp_path):
    store = JobStore(tmp_path)

    class Queue:
        def submit(self, job_id):
            pass

    client = TestClient(create_app(store, Queue()))
    assert client.post("/api/jobs", files={"image": ("bad.png", b"bad", "image/png")}).status_code == 400
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), "red").save(buffer, format="PNG")
    response = client.post("/api/jobs", files={"image": ("cup.png", buffer.getvalue(), "image/png")})
    assert response.status_code == 202
    job_id = response.json()["id"]
    assert client.get(f"/api/jobs/{job_id}").json()["status"] == "queued"
    assert client.get(f"/api/jobs/{job_id}/model").status_code == 404
