"""本地 JSONL 追踪：只记允许的结构字段，不记问题原文或工具参数。"""

import argparse
import json
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

LOG_DIR = Path(__file__).resolve().parent / "logs"
ALLOWED_STAGES = {"retrieve", "tool", "answer", "workflow"}


class Trace:
    def __init__(self, directory: Path = LOG_DIR):
        directory.mkdir(parents=True, exist_ok=True)
        self.trace_id = uuid4().hex
        self.path = directory / f"{self.trace_id}.jsonl"

    def write(self, event: dict) -> None:
        with self.path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(event, ensure_ascii=False) + "\n")

    @contextmanager
    def span(self, stage: str):
        if stage not in ALLOWED_STAGES:
            raise ValueError("未知阶段；不要把问题原文当阶段名")
        span_id = uuid4().hex
        start = time.perf_counter()
        base = {"trace_id": self.trace_id, "span_id": span_id, "stage": stage}
        self.write({**base, "event": "start"})
        try:
            yield
        except Exception as exc:
            self.write(
                {
                    **base,
                    "event": "error",
                    "error_type": type(exc).__name__,
                    "duration_ms": (time.perf_counter() - start) * 1000,
                }
            )
            raise
        else:
            self.write(
                {
                    **base,
                    "event": "end",
                    "duration_ms": (time.perf_counter() - start) * 1000,
                }
            )


def estimated_cost(
    usage: dict | None, input_price: float, output_price: float
) -> float | None:
    """价格由调用者指定，单位是“每百万 token 的同一种货币”。"""
    if usage is None:
        return None
    if input_price < 0 or output_price < 0:
        raise ValueError("价格不能为负")
    return (
        usage["input_tokens"] * input_price + usage["output_tokens"] * output_price
    ) / 1_000_000


if __name__ == "__main__":
    from day05.rag_baseline import (
        KNOWLEDGE_DIR,
        load_documents,
        retrieve,
        split_documents,
    )

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fail", action="store_true")
    args = parser.parse_args()
    trace = Trace()
    try:
        with trace.span("retrieve"):
            chunks = split_documents(load_documents(KNOWLEDGE_DIR))
            results = retrieve("周末几点关门？", chunks)
        with trace.span("tool"):
            if args.fail:
                raise TimeoutError("教学用模拟超时，不把本句写进日志")
            result = 25 * 3
    except TimeoutError:
        print("捕获到模拟超时，请检查 error 事件。")
    print("实际追踪文件：", trace.path)
    print(trace.path.read_text())
    print("本次没有模型调用：model_calls=0；真实 usage 未采集。")
    print(
        "假设输入1000、输出200，假设单价2和6：",
        estimated_cost({"input_tokens": 1000, "output_tokens": 200}, 2, 6),
    )
