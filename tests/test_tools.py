import asyncio
import json
import struct
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from PIL import Image

from toonforge.blender import BlenderRenderer
from toonforge.hunyuan import HunyuanClient
from toonforge.mcp_client import ToolClient


GLB = b"glTF" + struct.pack("<II", 2, 12)


def test_hunyuan_writes_real_glb_response(tmp_path):
    source = tmp_path / "input.png"
    source.write_bytes(b"image")
    output = tmp_path / "model.glb"
    calls = []

    def post(url, payload):
        calls.append((url, payload))
        return GLB

    HunyuanClient("http://127.0.0.1:8081", post).generate(source, output)
    assert output.read_bytes() == GLB
    assert calls[0][1]["texture"] is True
    assert calls[0][1]["type"] == "glb"


def test_hunyuan_rejects_non_glb(tmp_path):
    source = tmp_path / "input.png"
    source.write_bytes(b"image")
    with pytest.raises(ValueError):
        HunyuanClient("http://127.0.0.1:8081", lambda *_: b"error").generate(source, tmp_path / "model.glb")


def test_blender_receives_script_and_produces_png(tmp_path):
    source = tmp_path / "model.glb"
    source.write_bytes(GLB)
    output = tmp_path / "preview.png"
    commands = []

    def run(command, **kwargs):
        commands.append(command)
        Image.new("RGB", (4, 4), "blue").save(output)
        return type("Result", (), {"returncode": 0, "stderr": ""})()

    BlenderRenderer("blender", run).render(source, output)
    assert "--background" in commands[0]
    assert "--python" in commands[0]
    assert output.read_bytes().startswith(b"\x89PNG")


def test_mcp_tool_discovery_and_path_guard(tmp_path):
    async def check():
        client = ToolClient(tmp_path)
        names = await client.list_tools()
        assert {"generate_mesh", "render_toon"} <= set(names)
        with pytest.raises(RuntimeError):
            await client.call("generate_mesh", {"image_path": str(tmp_path.parent / "escape.png"), "output_path": str(tmp_path / "out.glb")})

    asyncio.run(check())


def test_mcp_calls_local_hunyuan_and_saves_glb(tmp_path, monkeypatch):
    received = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            received.append((self.path, payload["type"]))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(GLB)

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv("HUNYUAN_URL", f"http://127.0.0.1:{server.server_port}")
    source = tmp_path / "input.png"
    source.write_bytes(b"image")
    output = tmp_path / "model.glb"
    try:
        asyncio.run(ToolClient(tmp_path).call("generate_mesh", {"image_path": str(source), "output_path": str(output)}))
    finally:
        server.shutdown()
        server.server_close()
    assert received == [("/generate", "glb")]
    assert output.read_bytes() == GLB
