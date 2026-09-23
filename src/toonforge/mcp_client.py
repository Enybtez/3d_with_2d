import asyncio
import os
import sys
from datetime import timedelta
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from .config import PROJECT_ROOT


class ToolClient:
    def __init__(self, data_root: Path):
        self.data_root = Path(data_root).resolve()

    def _parameters(self) -> StdioServerParameters:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
        env["TOONFORGE_DATA_ROOT"] = str(self.data_root)
        return StdioServerParameters(command=sys.executable, args=["-m", "toonforge.mcp_server"], env=env)

    async def list_tools(self) -> list[str]:
        async with stdio_client(self._parameters()) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(seconds=30)) as session:
                await session.initialize()
                result = await session.list_tools()
                return [tool.name for tool in result.tools]

    async def call(self, name: str, args: dict) -> str:
        async with stdio_client(self._parameters()) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=timedelta(minutes=21)) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments=args)
        message = " ".join(getattr(item, "text", "") for item in result.content)
        if result.isError:
            raise RuntimeError(message or f"MCP 工具失败：{name}")
        return message

    def run(self, name: str, args: dict) -> str:
        return asyncio.run(self.call(name, args))
