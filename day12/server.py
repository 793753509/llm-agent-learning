"""真实 MCP stdio 服务；演示身份固定 alice，数据全部虚构。"""

from mcp.server.fastmcp import FastMCP

from day05.rag_baseline import KNOWLEDGE_DIR, load_documents, retrieve, split_documents
from day12.tickets import get_ticket as lookup_ticket

mcp = FastMCP("qinghe-study-room")
DEMO_USER = "alice"  # 真实服务应从已验证的凭证取得身份。


@mcp.tool()
def get_ticket(ticket_id: str) -> dict:
    """查看当前演示用户的工单，例如 T001。"""
    return lookup_ticket(ticket_id, DEMO_USER)


@mcp.tool()
def search_notes(query: str) -> list[dict]:
    """在青禾自习室的公开教学资料中查找最多两段原文。"""
    if not 1 <= len(query.strip()) <= 200:
        raise ValueError("query 要有 1～200 个字符")
    chunks = split_documents(load_documents(KNOWLEDGE_DIR))
    return [
        {"id": r.chunk.id, "text": r.chunk.text} for r in retrieve(query, chunks, 2)
    ]


@mcp.resource("study://rules")
def rules() -> str:
    return "演示服务：工单属于用户；查不到或无权限时统一返回错误。"


if __name__ == "__main__":
    # stdout 留给 MCP 协议。不要在这里 print 调试信息。
    mcp.run(transport="stdio")
