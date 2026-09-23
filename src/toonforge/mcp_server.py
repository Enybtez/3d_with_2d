from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .blender import BlenderRenderer
from .config import BLENDER_BIN, DATA_ROOT, HUNYUAN_URL
from .hunyuan import HunyuanClient


server = FastMCP("toonforge-tools")


def guarded_path(path: str) -> Path:
    candidate = Path(path).resolve()
    if not candidate.is_relative_to(DATA_ROOT):
        raise ValueError("路径必须在任务数据目录内")
    return candidate


@server.tool()
def generate_mesh(image_path: str, output_path: str) -> str:
    """Use the local Hunyuan3D server to turn one image into a GLB mesh."""
    source = guarded_path(image_path)
    output = guarded_path(output_path)
    if not source.is_file() or output.suffix != ".glb":
        raise ValueError("输入图片不存在或输出不是 GLB")
    HunyuanClient(HUNYUAN_URL).generate(source, output)
    return str(output)


@server.tool()
def render_toon(model_path: str, output_path: str) -> str:
    """Render a GLB as a cel-shaded PNG with local Blender."""
    source = guarded_path(model_path)
    output = guarded_path(output_path)
    if not source.is_file() or source.suffix != ".glb" or output.suffix != ".png":
        raise ValueError("输入 GLB 不存在或输出不是 PNG")
    BlenderRenderer(BLENDER_BIN).render(source, output)
    return str(output)


if __name__ == "__main__":
    server.run(transport="stdio")
