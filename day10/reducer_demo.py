"""两间教室先分别计算容量，再读取 subtotals 汇总；对比追加与替换。"""

import argparse
import json
import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph


class AppendState(TypedDict):
    subtotals: Annotated[list[int], operator.add]
    total: int


class ReplaceState(TypedDict):
    subtotals: list[int]
    total: int


def room_a(state: dict) -> dict:
    # 人工提供的桌椅数据；容量由节点实际计算。
    return {"subtotals": [25 * 3]}


def room_b(state: dict) -> dict:
    return {"subtotals": [12 * 4]}


def summarize(state: dict) -> dict:
    # 只读取此前保留下来的各间容量，没有另外保存或重算第一间。
    return {"total": sum(state["subtotals"])}


def run(use_reducer: bool = True) -> dict:
    schema = AppendState if use_reducer else ReplaceState
    graph = StateGraph(schema)
    graph.add_node("room_a", room_a)
    graph.add_node("room_b", room_b)
    graph.add_node("summarize", summarize)
    graph.add_edge(START, "room_a")
    graph.add_edge("room_a", "room_b")
    graph.add_edge("room_b", "summarize")
    graph.add_edge("summarize", END)
    return graph.compile().invoke({"subtotals": [], "total": 0})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replace", action="store_true", help="使用默认替换规则")
    args = parser.parse_args()
    print("更新规则：", "默认替换" if args.replace else "operator.add 追加")
    print(json.dumps(run(not args.replace), ensure_ascii=False, indent=2))
