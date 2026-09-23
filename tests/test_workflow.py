import io

from PIL import Image

from toonforge.storage import JobStore
from toonforge.workflow import Workflow


def image_bytes():
    output = io.BytesIO()
    Image.new("RGB", (8, 8), "red").save(output, format="PNG")
    return output.getvalue()


def test_agents_run_in_order_and_persist_results(tmp_path):
    store = JobStore(tmp_path)
    job = store.create(image_bytes())
    calls = []

    class Vision:
        def analyze(self, image, skill):
            calls.append("analyze")
            return {"subject": "杯子", "palette": ["red"]}

        def review(self, source, preview, skill):
            calls.append("review")
            return {"score": 4, "summary": "相似"}

    class Tools:
        def run(self, name, args):
            calls.append(name)
            from pathlib import Path
            Path(args["output_path"]).write_bytes(b"artifact")

    result = Workflow(store, Vision(), Tools()).run(job["id"])
    assert calls == ["analyze", "generate_mesh", "render_toon", "review"]
    assert result["status"] == "completed"
    assert store.get(job["id"])["review"]["score"] == 4
    assert [entry["agent"] for entry in result["agent_trace"]] == [
        "image-analysis", "mesh-builder", "toon-stylist", "toon-review"
    ]


def test_tool_failure_is_persisted(tmp_path):
    store = JobStore(tmp_path)
    job = store.create(image_bytes())

    class Vision:
        def analyze(self, *_):
            return {"subject": "杯子", "palette": []}

    class Tools:
        def run(self, *_):
            raise RuntimeError("model offline")

    result = Workflow(store, Vision(), Tools()).run(job["id"])
    assert result["status"] == "failed"
    assert result["stage"] == "modeling"
    assert "model offline" in result["error"]
