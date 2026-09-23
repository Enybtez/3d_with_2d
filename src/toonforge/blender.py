import subprocess
from pathlib import Path

from .config import PROJECT_ROOT


class BlenderRenderer:
    def __init__(self, executable: str, run=None):
        self.executable = executable
        self.run = run or subprocess.run

    def render(self, model_path: Path, output_path: Path) -> None:
        script = PROJECT_ROOT / "scripts" / "blender_toon.py"
        command = [self.executable, "--background", "--python", str(script), "--", str(model_path), str(output_path)]
        result = self.run(command, capture_output=True, text=True, timeout=600)
        if result.returncode:
            raise RuntimeError(f"Blender 渲染失败：{result.stderr[-1000:]}")
        if not Path(output_path).is_file() or not Path(output_path).read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
            raise RuntimeError("Blender 未生成 PNG")
