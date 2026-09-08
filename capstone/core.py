"""有限规则路由 + LangGraph + 检索/MCP/工具；默认离线资料预览。"""

import asyncio
import json
import re
from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from day05.rag_baseline import Chunk, build_prompt, generate_answer, retrieve
from day07.fusion import deduplicate_text, rrf_fuse, select_context
from day07.reranker import rerank
from day12.client import fetch
from day13.memory import MemoryStore
from day15.tracing import Trace
from day16.gateway import dispatch

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "capstone" / "data"


class State(TypedDict):
    question: str
    route: str
    args: dict
    response: dict


def route_request(state: State) -> dict:
    question = state["question"]
    ticket = re.fullmatch(r"查工单\s+(T[0-9]{3})", question)
    calculation = re.fullmatch(r"计算\s+(-?\d+)\s*\*\s*(-?\d+)", question)
    if ticket:
        return {"route": "get_ticket", "args": {"ticket_id": ticket.group(1)}}
    if calculation:
        return {
            "route": "multiply",
            "args": {"a": int(calculation.group(1)), "b": int(calculation.group(2))},
        }
    if "创建工单" in question:
        return {"route": "approval_required", "args": {}}
    return {"route": "retrieve", "args": {}}


class Engine:
    def __init__(
        self,
        data_dir: Path = DATA_DIR,
        *,
        hybrid: bool = False,
        ask_model: bool = False,
    ):
        self.data_dir = data_dir
        self.hybrid = hybrid
        self.ask_model = ask_model
        self.user = "alice"  # 固定演示用户，由应用设置，不从问题中取身份。
        self.memory = MemoryStore(data_dir / "memory.sqlite")
        records = json.loads((ROOT / "day07/knowledge.json").read_text())
        # 课程作品只服务北店；两个检索分支接触相同范围。
        self.chunks = [
            Chunk(id=r["id"], source=r["source"], index=r["index"], text=r["text"])
            for r in records
            if r["branch"] == "north"
        ]
        self.client = None
        self.model = None
        if hybrid:
            from qdrant_client import QdrantClient

            from day06.vector_store import embed_texts, load_embedder, write_collection

            self.model = load_embedder()
            vectors = embed_texts(self.model, [c.text for c in self.chunks])
            self.client = QdrantClient(":memory:")
            try:
                write_collection(self.client, "capstone_north", self.chunks, vectors)
            except Exception:
                self.client.close()
                raise
        builder = StateGraph(State)
        builder.add_node("route", route_request)
        builder.add_node("retrieve", self.search)
        builder.add_node("tool", self.tool)
        builder.add_node(
            "approval_required",
            lambda state: {
                "response": {
                    "mode": "approval_required",
                    "answer": "请用 CLI draft 准备草稿，审核后 approve。",
                    "sources": [],
                }
            },
        )
        builder.add_edge(START, "route")
        builder.add_conditional_edges(
            "route",
            lambda s: s["route"],
            {
                "retrieve": "retrieve",
                "get_ticket": "tool",
                "multiply": "tool",
                "approval_required": "approval_required",
            },
        )
        for node in ("retrieve", "tool", "approval_required"):
            builder.add_edge(node, END)
        self.graph = builder.compile()

    def search(self, state: State) -> dict:
        query = state["question"]
        lexical = retrieve(query, self.chunks, 3)
        vector = []
        if self.hybrid:
            from day06.vector_store import embed_query, search_vectors

            vector = search_vectors(
                self.client, "capstone_north", embed_query(self.model, query), 3
            )
        candidates = deduplicate_text(rerank(query, rrf_fuse(lexical, vector)))
        preferences = {r["key"]: r["value"] for r in self.memory.recall(self.user)}
        limit = 1 if preferences.get("style") == "简短" else 2
        results, skipped = select_context(query, candidates, limit, 1200)
        if not results:
            return {
                "response": {
                    "mode": "no_evidence",
                    "answer": "没有找到候选资料。",
                    "sources": [],
                    "skipped": skipped,
                }
            }
        if self.ask_model:
            answer = generate_answer(build_prompt(query, results))
            mode = "model_answer"
        else:
            answer = "候选资料（需核对是否回答问题）：\n" + "\n\n".join(
                f"{r.chunk.text} [来源: {r.chunk.id}]" for r in results
            )
            mode = "extractive_preview"
        return {
            "response": {
                "mode": mode,
                "answer": answer,
                "sources": [r.chunk.id for r in results],
                "skipped": skipped,
                "retrieval": "hybrid" if self.hybrid else "lexical",
            }
        }

    def tool(self, state: State) -> dict:
        result = dispatch(state["route"], state["args"], trusted_user=self.user)
        if state["route"] == "get_ticket" and "error" not in result:
            # 本地入口先检查权限，MCP Server 也在读取时检查。
            result = asyncio.run(fetch(state["args"]["ticket_id"]))["ticket"]
        return {
            "response": {
                "mode": "tool_result",
                "answer": json.dumps(result, ensure_ascii=False),
                "result": result,
                "sources": [],
            }
        }

    def answer(self, question: str) -> dict:
        question = question.strip()
        if not 1 <= len(question) <= 200:
            raise ValueError("问题要有 1～200 个字符")
        trace = Trace(self.data_dir / "logs")
        with trace.span("workflow"):
            state = self.graph.invoke(
                {"question": question, "route": "", "args": {}, "response": {}},
                config={"recursion_limit": 5},
            )
        return {
            **state["response"],
            "route": state["route"],
            "trace_id": trace.trace_id,
        }

    def close(self) -> None:
        if self.client is not None:
            self.client.close()


if __name__ == "__main__":
    engine = Engine()
    try:
        print(
            json.dumps(
                engine.answer("E101 预约失败怎么办？"), ensure_ascii=False, indent=2
            )
        )
    finally:
        engine.close()
