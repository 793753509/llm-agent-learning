"""跨进程暂停/恢复；写入本地模拟工单表，不对外发送任何内容。"""

import argparse
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

DATA_DIR = Path(__file__).resolve().parent / "data"


class State(TypedDict):
    operation_id: str
    draft: str
    digest: str
    approved: bool
    status: str


def fingerprint(draft: str) -> str:
    return hashlib.sha256(draft.encode()).hexdigest()


def review(state: State) -> dict:
    decision = interrupt(
        {
            "operation_id": state["operation_id"],
            "draft": state["draft"],
            "digest": state["digest"],
            "question": "是否写入这份本地模拟工单？",
        }
    )
    if (
        not isinstance(decision, dict)
        or type(decision.get("approved")) is not bool
        or decision.get("digest") != state["digest"]
    ):
        raise ValueError("审批格式错误，或审批对应的内容已变化")
    return {"approved": decision["approved"]}


def write_once(data_dir: Path, state: dict) -> None:
    """唯一 operation_id 让同一份本地写入可以安全重试。"""
    if state.get("approved") is not True:
        raise ValueError("尚未批准")
    if fingerprint(state["draft"]) != state["digest"]:
        raise ValueError("内容与审批摘要不一致")
    with closing(sqlite3.connect(data_dir / "tickets.sqlite")) as db, db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS tickets "
            "(operation_id TEXT PRIMARY KEY, draft TEXT, digest TEXT)"
        )
        old = db.execute(
            "SELECT digest FROM tickets WHERE operation_id=?", (state["operation_id"],)
        ).fetchone()
        if old and old[0] != state["digest"]:
            raise ValueError("同一个 operation_id 不能写不同内容")
        db.execute(
            "INSERT OR IGNORE INTO tickets VALUES (?, ?, ?)",
            (state["operation_id"], state["draft"], state["digest"]),
        )


def build_graph(checkpointer, data_dir: Path):
    def commit(state: State) -> dict:
        write_once(data_dir, state)
        return {"status": "created_locally"}

    def reject(state: State) -> dict:
        return {"status": "rejected"}

    builder = StateGraph(State)
    builder.add_node("review", review)
    builder.add_node("commit", commit)
    builder.add_node("reject", reject)
    builder.add_edge(START, "review")
    builder.add_conditional_edges(
        "review",
        lambda s: "commit" if s["approved"] else "reject",
        {"commit": "commit", "reject": "reject"},
    )
    builder.add_edge("commit", END)
    builder.add_edge("reject", END)
    return builder.compile(checkpointer=checkpointer)


def execute(
    action: str, task_id: str, draft: str = "", data_dir: Path = DATA_DIR
) -> dict:
    """本地单用户 CLI 是人工入口；不是远程鉴权接口。"""
    if action not in {"start", "show", "approve", "reject"}:
        raise ValueError("未知动作")
    if not task_id.strip() or len(task_id) > 80:
        raise ValueError("task-id 要有 1～80 个字符")
    data_dir.mkdir(parents=True, exist_ok=True)
    config = {"configurable": {"thread_id": task_id}}
    with SqliteSaver.from_conn_string(str(data_dir / "checkpoints.sqlite")) as saver:
        graph = build_graph(saver, data_dir)
        snapshot = graph.get_state(config)
        if action == "start":
            if snapshot.values:
                raise ValueError("task-id 已存在；用 show 查看，或为新草稿换一个 ID")
            if not draft.strip() or len(draft) > 1000:
                raise ValueError("草稿要有 1～1000 个字符")
            graph.invoke(
                {
                    "operation_id": task_id,
                    "draft": draft,
                    "digest": fingerprint(draft),
                    "approved": False,
                    "status": "waiting_approval",
                },
                config,
            )
        elif not snapshot.values:
            raise ValueError("没有这个任务；先 start")
        elif action in {"approve", "reject"} and snapshot.next:
            if any(task.interrupts for task in snapshot.tasks):
                graph.invoke(
                    Command(
                        resume={
                            "approved": action == "approve",
                            "digest": snapshot.values["digest"],
                        }
                    ),
                    config,
                )
            else:
                # 已批准后写入失败：只能重试既有决定，不能拿“reject”悄悄重试写入。
                if action != "approve" or not snapshot.values.get("approved"):
                    raise ValueError("流程已越过审批点；请查看状态")
                graph.invoke(None, config)
        final = graph.get_state(config)
        return {**final.values, "next": list(final.next)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["start", "show", "approve", "reject"])
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--draft", default="")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()
    try:
        result = execute(args.action, args.task_id, args.draft, args.data_dir)
    except (ValueError, OSError) as exc:
        raise SystemExit(str(exc)) from None
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
