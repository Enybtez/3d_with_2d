import io

import pytest
from PIL import Image

from toonforge.storage import JobStore


def png_bytes():
    output = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(output, format="PNG")
    return output.getvalue()


def test_create_and_read_after_restarting_store(tmp_path):
    store = JobStore(tmp_path)
    job = store.create(png_bytes())
    assert (tmp_path / job["id"] / "input.png").exists()
    assert JobStore(tmp_path).get(job["id"])["status"] == "queued"


def test_rejects_invalid_or_oversize_image(tmp_path):
    store = JobStore(tmp_path)
    with pytest.raises(ValueError):
        store.create(b"not an image")
    with pytest.raises(ValueError):
        store.create(png_bytes() + b"x" * (10 * 1024 * 1024))


def test_rejects_path_traversal_and_recovers_interrupted(tmp_path):
    store = JobStore(tmp_path)
    with pytest.raises(ValueError):
        store.get("../outside")
    job = store.create(png_bytes())
    store.update(job["id"], status="modeling")
    JobStore(tmp_path).recover_interrupted()
    assert store.get(job["id"])["status"] == "failed"
