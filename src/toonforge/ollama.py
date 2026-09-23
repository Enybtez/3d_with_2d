import base64
import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def _post_json(url: str, payload: dict) -> dict:
    request = Request(url, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    with urlopen(request, timeout=180) as response:
        return json.load(response)


class OllamaVision:
    def __init__(self, base_url: str, model: str, post_json=None):
        parsed = urlparse(base_url)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
            raise ValueError("Ollama 必须使用本机 HTTP 地址")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.post_json = post_json or _post_json

    def _ask(self, paths: list[Path], skill: str) -> dict:
        images = [base64.b64encode(Path(path).read_bytes()).decode("ascii") for path in paths]
        payload = {
            "model": self.model,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0},
            "messages": [{"role": "user", "content": skill, "images": images}],
        }
        response = self.post_json(f"{self.base_url}/api/chat", payload)
        try:
            result = json.loads(response["message"]["content"])
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("视觉模型未返回有效 JSON") from exc
        if not isinstance(result, dict):
            raise ValueError("视觉模型 JSON 不是对象")
        return result

    def analyze(self, image_path: Path, skill: str) -> dict:
        result = self._ask([image_path], skill)
        if not isinstance(result.get("subject"), str) or not result["subject"].strip():
            raise ValueError("视觉模型缺少主体描述")
        if not isinstance(result.get("palette"), list):
            raise ValueError("视觉模型缺少颜色列表")
        return {"subject": result["subject"], "palette": result["palette"]}

    def review(self, source_path: Path, preview_path: Path, skill: str) -> dict:
        result = self._ask([source_path, preview_path], skill)
        score = result.get("score")
        if type(score) is not int or not 0 <= score <= 5 or not isinstance(result.get("summary"), str):
            raise ValueError("视觉模型质检结果无效")
        return {"score": score, "summary": result["summary"]}
