"""最终项目的统一 CLI；写操作只写本地模拟库。"""

import argparse
import json
from pathlib import Path

from day10.approval import execute
from day12.memory import MemoryStore

from .core import DATA_DIR, Engine


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    commands = parser.add_subparsers(dest="command", required=True)
    ask = commands.add_parser("ask")
    ask.add_argument("question")
    ask.add_argument("--hybrid", action="store_true")
    ask.add_argument("--ask-model", action="store_true")
    draft = commands.add_parser("draft")
    draft.add_argument("task_id")
    draft.add_argument("text")
    for name in ("show", "approve", "reject"):
        command = commands.add_parser(name)
        command.add_argument("task_id")
    remember = commands.add_parser("remember")
    remember.add_argument("style", choices=["简短", "详细"])
    commands.add_parser("forget")
    args = parser.parse_args()
    if args.command == "ask":
        engine = Engine(args.data_dir, hybrid=args.hybrid, ask_model=args.ask_model)
        try:
            result = engine.answer(args.question)
        finally:
            engine.close()
    elif args.command in {"remember", "forget"}:
        store = MemoryStore(args.data_dir / "memory.sqlite")
        if args.command == "remember":
            store.remember("alice", "style", args.style)
        else:
            store.forget("alice", "style")
        result = store.recall("alice")
    else:
        result = execute(
            "start" if args.command == "draft" else args.command,
            args.task_id,
            getattr(args, "text", ""),
            args.data_dir / "approval",
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as exc:
        raise SystemExit(f"运行失败：{exc}") from None
    except OSError as exc:
        raise SystemExit(
            f"运行失败：{type(exc).__name__}；请核对参数、配置与本地状态。"
        ) from None
