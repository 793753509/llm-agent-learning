"""本地作品验收：实际执行核心路径，报告明确区分范围与限制。"""

import argparse
import json
import math
import platform
import sqlite3
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from fastapi.testclient import TestClient

from capstone.core import ROOT, Engine
from day08.eval_retrieval import evaluate as evaluate_retrieval
from day08.eval_retrieval import metrics
from day10.approval import execute, write_once
from day12.memory import MemoryStore
from day13.eval_agent import evaluate as evaluate_agent
from day14.tracing import Trace, estimated_cost
from day15.gateway import evaluate as evaluate_gateway
from day16.roles import run as run_roles
from day17.api import create_app


def verify(hybrid: bool = False) -> dict:
    rows = []

    def check(name: str, condition: bool) -> None:
        rows.append({"name": name, "passed": bool(condition)})

    with tempfile.TemporaryDirectory(prefix="qinghe-verify-") as temp:
        folder = Path(temp)
        engine = Engine(folder / "app", hybrid=hybrid)
        try:
            answer = engine.answer("E101 预约失败怎么办？")
            check("北店 E101 排在首位", answer["sources"][0] == "north/booking.md#1")
            check(
                "门店范围仅北店", all(s.startswith("north/") for s in answer["sources"])
            )
            check("默认不调用生成模型", answer["mode"] == "extractive_preview")
            check("乘法工具", engine.answer("计算 25 * 3")["result"] == {"value": 75})
            check(
                "真实 MCP 查询 T001",
                engine.answer("查工单 T001")["result"]["status"] == "处理中",
            )
            denied = engine.answer("查工单 T002")["result"]
            check("越权无正文", denied == {"error": "not_found_or_forbidden"})
            check(
                "聊天不能直接写工单",
                engine.answer("创建工单 北店预约失败")["mode"] == "approval_required",
            )
            store = engine.memory
            store.remember("alice", "style", "简短")
            check(
                "偏好影响摘录数量",
                len(engine.answer("E101 预约失败怎么办？")["sources"]) == 1,
            )
            reopened = MemoryStore(store.path)
            check("记忆重新打开可读", reopened.recall("alice")[0]["value"] == "简短")
            check("记忆分用户", reopened.recall("bob") == [])
            check(
                "记忆到期不可读",
                reopened.recall("alice", now=time.time() + 90000) == [],
            )
            store.forget("alice", "style")
            check("记忆可删除", store.recall("alice") == [])

            approval_dir = folder / "approval"
            execute("start", "approved", "北店预约失败", approval_dir)
            check("未审批不产生工单表", not (approval_dir / "tickets.sqlite").exists())
            # 使用新的进程恢复，验证没有靠当前 Python 对象保留状态。
            resumed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "day10.approval",
                    "approve",
                    "--task-id",
                    "approved",
                    "--data-dir",
                    str(approval_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=20,
            )
            check(
                "跨进程恢复审批",
                resumed.returncode == 0
                and json.loads(resumed.stdout)["status"] == "created_locally",
            )
            completed = execute("approve", "approved", data_dir=approval_dir)
            write_once(approval_dir, completed)  # 模拟写入成功但快照未完成后的重放。
            with closing(sqlite3.connect(approval_dir / "tickets.sqlite")) as db:
                count = db.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
            check("重复审批及写入重放只有一条", count == 1)
            changed = {**completed, "draft": "另一份草稿"}
            try:
                write_once(approval_dir, changed)
                blocked = False
            except ValueError:
                blocked = True
            check("草稿变动使原审批失效", blocked)
            execute("start", "rejected", "另一个问题", approval_dir)
            check(
                "可拒绝审批",
                execute("reject", "rejected", data_dir=approval_dir)["status"]
                == "rejected",
            )

            with TestClient(create_app(engine.answer)) as client:
                check("健康接口", client.get("/health").status_code == 200)
                check(
                    "空问题返回422",
                    client.post(
                        "/chat", json={"session_id": "s1", "question": " "}
                    ).status_code
                    == 422,
                )

                def request(_):
                    return client.post(
                        "/chat", json={"session_id": "s1", "question": "计算 2 * 3"}
                    ).json()

                with ThreadPoolExecutor(max_workers=4) as pool:
                    replies = list(pool.map(request, range(4)))
                check(
                    "同会话并发计数不丢失",
                    sorted(r["turn"] for r in replies) == [1, 2, 3, 4],
                )
                events = client.post(
                    "/events", json={"session_id": "s2", "question": "E101 怎么办？"}
                ).text
                check(
                    "SSE事件顺序",
                    events.index("event: status")
                    < events.index("event: answer")
                    < events.index("event: done"),
                )

            def fail(_):
                raise RuntimeError("private-test-marker")

            with TestClient(create_app(fail)) as client:
                error = client.post(
                    "/chat", json={"session_id": "s1", "question": "测试"}
                )
                check(
                    "接口异常不回显原文",
                    error.status_code == 500
                    and "private-test-marker" not in error.text,
                )
                events = client.post(
                    "/events", json={"session_id": "s1", "question": "测试"}
                ).text
                check(
                    "SSE失败不发done",
                    "event: error" in events and "event: done" not in events,
                )

            trace = Trace(folder / "trace")
            try:
                with trace.span("tool"):
                    raise TimeoutError("private-test-marker")
            except TimeoutError:
                pass
            log = trace.path.read_text()
            check(
                "追踪记录错误且不写异常原文",
                '"event": "error"' in log and "private-test-marker" not in log,
            )
            check("缺失usage不虚报零费用", estimated_cost(None, 2, 6) is None)
            check("权限网关六例", all(r["passed"] for r in evaluate_gateway()))
            check(
                "角色交接拒绝篡改",
                run_roles("周末几点关门？", True)["review"]["approved"] is False,
            )
            check(
                "Recall和Hit区分",
                metrics(["C", "A"], {"A", "B"}, 2)
                == {"hit": 1.0, "recall": 0.5, "rr": 0.5},
            )
            agent = evaluate_agent()
            check("固定工作流四例通过", agent["passed"] == 4)
            check("故意缺失工具轨迹四例失败", evaluate_agent(True)["passed"] == 0)

            times = []
            for _ in range(10):
                start = time.perf_counter()
                engine.answer("E101 预约失败怎么办？")
                times.append((time.perf_counter() - start) * 1000)
            times.sort()
            latency = {
                "samples": 10,
                "unit": "ms",
                "method": "nearest rank",
                "scope": "warm local knowledge query, includes graph/logging; excludes setup, MCP, generation and HTTP",
                "p50": times[math.ceil(0.5 * len(times)) - 1],
                "p95": times[math.ceil(0.95 * len(times)) - 1],
            }
        finally:
            engine.close()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "local teaching integration checks; not live model quality or production load test",
        "hybrid": hybrid,
        "passed": sum(r["passed"] for r in rows),
        "total": len(rows),
        "python": platform.python_version(),
        "versions": {name: version(name) for name in ("langgraph", "mcp", "fastapi")},
        "checks": rows,
        "latency": latency,
        "day08_retrieval": evaluate_retrieval(1),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hybrid", action="store_true")
    args = parser.parse_args()
    # 未预期异常直接让命令失败，不会留下伪装成功的本次报告。
    report = verify(args.hybrid)
    stem = "hybrid" if args.hybrid else "local"
    out = ROOT / "day20/reports" / f"{stem}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    lines = [
        f"# 本地验收：{report['passed']}/{report['total']}",
        "",
        report["scope"],
        "",
        "生成时间：" + report["generated_at"],
        "",
        f"混合检索：{report['hybrid']}；Python：{report['python']}",
        "",
        "| 检查 | 结果 |",
        "|---|---|",
    ]
    lines.extend(
        f"| {r['name']} | {'通过' if r['passed'] else '失败'} |"
        for r in report["checks"]
    )
    lines.extend(
        [
            "",
            "延迟范围：" + report["latency"]["scope"],
            "",
            f"10 次热运行：p50={report['latency']['p50']:.2f} ms，p95={report['latency']['p95']:.2f} ms。",
            "",
            "这份报告未测真实模型回答质量、模型费用、跨主机认证或公网并发。",
            "",
        ]
    )
    out.with_suffix(".md").write_text("\n".join(lines))
    print(f"{report['passed']}/{report['total']} 通过；报告：{out}")
    raise SystemExit(0 if report["passed"] == report["total"] else 1)
