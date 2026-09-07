"""评估 Day 09 的确定性工作流；不冒充真实模型能力评估。"""

import argparse
import json
from pathlib import Path

from day09.graph_demo import run

HERE = Path(__file__).resolve().parent


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
    return {"id": case["id"], "passed": all(checks.values()), "checks": checks}


def evaluate(fault: bool = False) -> dict:
    cases = json.loads((HERE / "datasets/agent_cases.json").read_text())
    rows = []
    for case in cases:
        result = run(case["a"], case["b"])
        if fault:
            # 故意损坏轨迹：答案保留，但抹掉工具执行记录。
            result["events"] = [e for e in result["events"] if e["node"] != "tool"]
        rows.append(grade(case, result))
    return {
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
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["passed"] == report["total"] else 1)
