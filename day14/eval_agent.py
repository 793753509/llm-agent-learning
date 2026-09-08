"""评估 Day 10 的确定性工作流；不冒充真实模型能力评估。"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from day10.graph_demo import run

HERE = Path(__file__).resolve().parent
CASES_PATH = HERE / "datasets" / "agent_cases.json"


def grade(case: dict, result: dict) -> dict:
    events = result["events"]
    tools = [event for event in events if event.get("node") == "tool"]
    checks = {
        "answer": result["answer"] == case["expected"],
        "tool_name": len(tools) == 1 and tools[0].get("name") == "multiply",
        "tool_args": len(tools) == 1
        and tools[0].get("args")
        == {
            "a": case["a"],
            "b": case["b"],
        },
        "path": [event["node"] for event in events] == ["decide", "tool", "decide"],
        "budget": len(tools) <= 1 and len(events) <= 3,
    }
    return {
        "id": case["id"],
        "input": {"a": case["a"], "b": case["b"]},
        "expected": case["expected"],
        "answer": result["answer"],
        "events": events,
        "passed": all(checks.values()),
        "checks": checks,
    }


def evaluate(fault: bool = False, cases_path: Path = CASES_PATH) -> dict:
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        raise ValueError("评估集必须是非空的题目列表")
    ids = set()
    rows = []
    for case in cases:
        if (
            not isinstance(case, dict)
            or not isinstance(case.get("id"), str)
            or not case["id"].strip()
            or case["id"] in ids
            or type(case.get("a")) is not int
            or type(case.get("b")) is not int
            or not isinstance(case.get("expected"), str)
        ):
            raise ValueError("每道题需要唯一非空 id、整数 a/b 和字符串 expected")
        ids.add(case["id"])
        result = run(case["a"], case["b"])
        if fault:
            # 故意损坏轨迹：答案保留，但抹掉工具执行记录。
            result["events"] = [e for e in result["events"] if e["node"] != "tool"]
        rows.append(grade(case, result))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": str(cases_path.resolve().relative_to(HERE.parent))
        if cases_path.resolve().is_relative_to(HERE.parent)
        else str(cases_path.resolve()),
        "workflow": "day10.graph_demo.run",
        "scope": "scripted LangGraph workflow; no model calls",
        "fault": fault,
        "passed": sum(row["passed"] for row in rows),
        "total": len(rows),
        "cases": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fault", action="store_true")
    args = parser.parse_args()
    report = evaluate(args.fault)
    path = HERE / "reports" / ("fault.json" if args.fault else "baseline.json")
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"题目（人工编写）：{CASES_PATH}")
    print(f"被测程序：day10.graph_demo.run；故障注入：{args.fault}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"程序生成的报告：{path}")
    raise SystemExit(0 if report["passed"] == report["total"] else 1)
