"""客户端自动启动/关闭本地 MCP 子进程，无需另开 Server 终端。"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

ROOT = Path(__file__).resolve().parents[1]


async def interact(ticket_id: str = "T001") -> dict:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "day11.server"],
        cwd=str(ROOT),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            result = await session.call_tool("get_ticket", {"ticket_id": ticket_id})
            resource = await session.read_resource("study://rules")
            if result.isError:
                raise RuntimeError("MCP 工具执行失败")
            texts = [c.text for c in result.content if c.type == "text"]
            return {
                "tools": [tool.name for tool in listed.tools],
                "ticket": json.loads(texts[0]),
                "resource": [c.text for c in resource.contents if hasattr(c, "text")],
            }


async def fetch(ticket_id: str = "T001") -> dict:
    return await asyncio.wait_for(interact(ticket_id), timeout=20)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ticket_id", nargs="?", default="T001")
    args = parser.parse_args()
    print(json.dumps(asyncio.run(fetch(args.ticket_id)), ensure_ascii=False, indent=2))
