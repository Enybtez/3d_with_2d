import json

import pytest

from toonforge.ollama import OllamaVision
from toonforge.skills import load_skill


def test_skill_is_loaded_and_sent_to_local_model(tmp_path):
    image = tmp_path / "input.png"
    image.write_bytes(b"image")
    calls = []

    def post(url, payload):
        calls.append((url, payload))
        return {"message": {"content": json.dumps({"subject": "红色茶杯", "palette": ["红", "白"]})}}

    result = OllamaVision("http://127.0.0.1:11434", "qwen3-vl:8b-instruct", post).analyze(
        image, load_skill("image-analysis")
    )
    assert result["subject"] == "红色茶杯"
    assert calls[0][0] == "http://127.0.0.1:11434/api/chat"
    assert "单个主体" in calls[0][1]["messages"][0]["content"]
    assert calls[0][1]["messages"][0]["images"]


def test_bad_model_json_is_rejected(tmp_path):
    image = tmp_path / "input.png"
    image.write_bytes(b"image")
    vision = OllamaVision("http://localhost:11434", "qwen3-vl:8b-instruct", lambda *_: {"message": {"content": "oops"}})
    with pytest.raises(ValueError):
        vision.analyze(image, "rule")


def test_review_requires_score_and_summary(tmp_path):
    image = tmp_path / "input.png"
    image.write_bytes(b"image")
    vision = OllamaVision(
        "http://localhost:11434",
        "qwen3-vl:8b-instruct",
        lambda *_: {"message": {"content": '{"score": 4, "summary": "轮廓相近"}'}},
    )
    assert vision.review(image, image, "rule")["score"] == 4
