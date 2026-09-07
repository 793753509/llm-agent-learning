"""真实 LangGraph + 写死的决策，先看懂调度，再接模型。"""

import argparse
import json
import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


class State(TypedDict):
    a: int
    b: int
    tool_result: int | None
    answer: str
    need_tool: bool
    events: Annotated[list[dict], operator.add]


def decide(state: State) -> dict:
    if state["tool_result"] is None:
        return {"need_tool": True, "events": [{"node": "decide", "action": "tool"}]}
    return {
        "need_tool": False,
        "answer": str(state["tool_result"]),
        "events": [{"node": "decide", "action": "answer"}],
    }


def multiply(state: State) -> dict:
    result = state["a"] * state["b"]
    return {
        "tool_result": result,
        "events": [
            {
                "node": "tool",
                "name": "multiply",
                "args": {"a": state["a"], "b": state["b"]},
                "result": result,
            }
        ],
    }


def route(state: State) -> str:
    return "tool" if state["need_tool"] else "end"


def build_graph():
    builder = StateGraph(State)
    builder.add_node("decide", decide)
    builder.add_node("tool", multiply)
    builder.add_edge(START, "decide")
    builder.add_conditional_edges("decide", route, {"tool": "tool", "end": END})
    builder.add_edge("tool", "decide")
    return builder.compile()


def run(a: int = 25, b: int = 3) -> dict:
    return build_graph().invoke(
        {
            "a": a,
            "b": b,
            "tool_result": None,
            "answer": "",
            "need_tool": False,
            "events": [],
        },
        config={"recursion_limit": 6},
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("a", type=int, nargs="?", default=25)
    parser.add_argument("b", type=int, nargs="?", default=3)
    args = parser.parse_args()
    print(json.dumps(run(args.a, args.b), ensure_ascii=False, indent=2))
