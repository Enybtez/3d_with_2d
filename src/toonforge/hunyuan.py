import base64
import json
import struct
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


def _post_binary(url: str, payload: dict) -> bytes:
    request = Request(url, json.dumps(payload).encode(), {"Content-Type": "application/json"})
    with urlopen(request, timeout=1200) as response:
        return response.read()


class HunyuanClient:
    def __init__(self, base_url: str, post_binary=None):
        parsed = urlparse(base_url)
        if parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost"}:
            raise ValueError("Hunyuan 必须使用本机 HTTP 地址")
        self.base_url = base_url.rstrip("/")
        self.post_binary = post_binary or _post_binary

    def generate(self, image_path: Path, output_path: Path) -> None:
        payload = {
            "image": base64.b64encode(Path(image_path).read_bytes()).decode("ascii"),
            "remove_background": True,
            "texture": True,
            "type": "glb",
        }
        data = self.post_binary(f"{self.base_url}/generate", payload)
        if len(data) < 12 or data[:4] != b"glTF" or struct.unpack_from("<I", data, 4)[0] != 2:
            raise ValueError("Hunyuan 未返回有效 GLB")
        Path(output_path).write_bytes(data)
