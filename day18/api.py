"""本机 FastAPI：资料摘录、会话计数、阶段 SSE。无鉴权，不面向公网。"""

import json
import threading
from collections.abc import Callable
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from day05.rag_baseline import KNOWLEDGE_DIR, load_documents, retrieve, split_documents


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    session_id: str = Field(min_length=1, max_length=40, pattern=r"^[a-zA-Z0-9_-]+$")
    question: str = Field(min_length=1, max_length=200)


def answer_question(question: str) -> dict:
    chunks = split_documents(load_documents(KNOWLEDGE_DIR))
    results = retrieve(question, chunks, 1)
    return {
        "mode": "extractive_preview",
        "answer": "\n".join(r.chunk.text for r in results) or "没有找到候选资料。",
        "sources": [r.chunk.id for r in results],
    }


def create_app(answer_fn: Callable[[str], dict] = answer_question) -> FastAPI:
    application = FastAPI(
        title="青禾学习 API", description="本机教学服务，当前为固定演示用户。"
    )
    sessions: dict[str, dict] = {}
    registry_lock = threading.Lock()

    def respond(request: ChatRequest, request_id: str) -> dict:
        with registry_lock:
            if request.session_id not in sessions:
                if len(sessions) >= 100:
                    raise HTTPException(429, "演示 session 已达 100 个，请重启练习服务")
                sessions[request.session_id] = {"lock": threading.Lock(), "turn": 0}
            session = sessions[request.session_id]
        # 同一 session 串行，其他 session 可以各自执行。
        with session["lock"]:
            result = answer_fn(request.question)
            session["turn"] += 1
            return {
                **result,
                "request_id": request_id,
                "session_id": request.session_id,
                "turn": session["turn"],
            }

    @application.get("/health")
    def health():
        return {"status": "ok", "demo_user": "alice"}

    @application.post("/chat")
    def chat(request: ChatRequest):
        request_id = uuid4().hex
        try:
            return respond(request, request_id)
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(
                500, {"error": "request_failed", "request_id": request_id}
            ) from None

    @application.post("/events")
    def events(request: ChatRequest):
        request_id = uuid4().hex

        def frame(event: str, data: dict) -> str:
            return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"

        def stream():
            yield frame("status", {"request_id": request_id, "stage": "started"})
            try:
                result = respond(request, request_id)
            except Exception:
                yield frame(
                    "error", {"request_id": request_id, "error": "request_failed"}
                )
                return
            yield frame("answer", result)
            yield frame("done", {"request_id": request_id})

        return StreamingResponse(
            stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache"},
        )

    return application


app = create_app()
