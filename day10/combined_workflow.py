"""外层 LangGraph 控制草稿流程，内层 LangChain Agent 连续使用只读工具。"""

import argparse
import json
from pathlib import Path
from typing import TypedDict

from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain.tools import tool
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, ToolMessage
from langgraph.graph import END, START, StateGraph

from day09.langchain_agent import print_messages, real_model
from day10.diagnostic_model import DiagnosticDemoModel

DATA_PATH = Path(__file__).with_name("booking_data.json")
PROMPT = """你是预约排查助手。先查指定预约记录，再用返回的错误码查处理手册。
只根据实际工具结果整理原因与建议，并保留来源。记录或手册缺失时说明信息不足。
你只有只读工具。不要声称已经创建工单、完成审批或修改预约。
"""


class State(TypedDict):
    booking_id: str
    question: str
    messages: list[BaseMessage]
    diagnosis: str
    evidence_ok: bool
    source: str
    draft: str
    status: str


def make_tools(data: dict) -> list:
    @tool
    def get_booking(booking_id: str) -> dict:
        """按预约编号读取模拟预约记录及失败错误码。"""
        record = data["bookings"].get(booking_id)
        return (
            {"ok": True, **record}
            if record
            else {"ok": False, "error": "booking_not_found"}
        )

    @tool
    def lookup_manual(error_code: str) -> dict:
        """根据错误码读取对应处理手册，返回原文及来源。"""
        manual = data["manuals"].get(error_code)
        return (
            {"ok": True, **manual}
            if manual
            else {"ok": False, "error": "manual_not_found"}
        )

    return [get_booking, lookup_manual]


def check_evidence(state: State) -> dict:
    # 依据真实 ToolMessage 检查，不信任模型文字中的“我查到了”。
    results = {}
    for message in state["messages"]:
        if isinstance(message, ToolMessage) and message.status == "success":
            data = json.loads(message.content)
            if isinstance(data, dict) and data.get("ok") is True:
                results[message.name] = data
    booking = results.get("get_booking", {})
    manual = results.get("lookup_manual", {})
    ready = bool(
        booking.get("booking_id") == state["booking_id"]
        and booking.get("error_code")
        and manual.get("error_code") == booking.get("error_code")
        and manual.get("text")
        and manual.get("source")
        and state["diagnosis"].strip()
    )
    return {"evidence_ok": ready, "source": manual.get("source", "")}


def prepare_draft(state: State) -> dict:
    return {
        "draft": f"预约：{state['booking_id']}\n排查：{state['diagnosis']}\n依据：{state['source']}",
        "status": "draft_ready",
    }


def needs_information(state: State) -> dict:
    return {"draft": "", "status": "needs_information"}


def build_workflow(model: BaseChatModel, data: dict):
    diagnostic_agent = create_agent(
        model=model,
        tools=make_tools(data),
        system_prompt=PROMPT,
        middleware=[ModelCallLimitMiddleware(run_limit=4, exit_behavior="error")],
    )

    def diagnose(state: State) -> dict:
        result = diagnostic_agent.invoke(
            {"messages": [{"role": "user", "content": state["question"]}]},
            config={"recursion_limit": 30},
        )
        return {
            "messages": result["messages"],
            "diagnosis": result["messages"][-1].text,
        }

    graph = StateGraph(State)
    graph.add_node("diagnose", diagnose)
    graph.add_node("check_evidence", check_evidence)
    graph.add_node("prepare_draft", prepare_draft)
    graph.add_node("needs_information", needs_information)
    graph.add_edge(START, "diagnose")
    graph.add_edge("diagnose", "check_evidence")
    graph.add_conditional_edges(
        "check_evidence",
        lambda state: "ready" if state["evidence_ok"] else "missing",
        {"ready": "prepare_draft", "missing": "needs_information"},
    )
    graph.add_edge("prepare_draft", END)
    graph.add_edge("needs_information", END)
    return graph.compile()


def run(
    model: BaseChatModel, booking_id: str = "B001", data: dict | None = None
) -> dict:
    if not booking_id.strip():
        raise ValueError("预约编号不能为空")
    if data is None:
        data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return build_workflow(model, data).invoke(
        {
            "booking_id": booking_id,
            "question": f"排查预约 {booking_id} 失败的原因，参考手册为人工协助准备工单草稿。",
            "messages": [],
            "diagnosis": "",
            "evidence_ok": False,
            "source": "",
            "draft": "",
            "status": "new",
        },
        config={"recursion_limit": 10},
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--booking-id", default="B001")
    parser.add_argument(
        "--missing-manual", action="store_true", help="在内存中移除手册，观察失败分支"
    )
    parser.add_argument(
        "--ask-model", action="store_true", help="改用现有配置的真实模型"
    )
    args = parser.parse_args()
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if args.missing_manual:
        data["manuals"] = {}
    print("输入资料：", DATA_PATH)
    print(
        "模式：", "真实模型" if args.ask_model else "预设工具选择；工具和框架真实执行"
    )
    try:
        model = (
            real_model()
            if args.ask_model
            else DiagnosticDemoModel(booking_id=args.booking_id)
        )
        result = run(model, args.booking_id, data)
    except Exception as exc:
        raise SystemExit(
            f"运行失败：{type(exc).__name__}；请检查依赖、配置、输入和调用上限。"
        ) from None
    print("内层 Agent 消息：")
    print_messages(result["messages"])
    print("外层证据检查：", result["evidence_ok"])
    print("外层最终状态：", result["status"])
    print("待审核草稿：", result["draft"] or "未生成，需补充信息")
    print("本课仅在内存准备并打印草稿；保存、暂停审批和写入将在 Day 11 学习。")


if __name__ == "__main__":
    main()
