"""Day 08：评估 Day 05 的关键词检索，不请求生成模型。"""

import argparse
import json
from pathlib import Path

from day05.rag_baseline import KNOWLEDGE_DIR, load_documents, retrieve, split_documents

HERE = Path(__file__).resolve().parent


def metrics(retrieved: list[str], relevant: set[str], k: int) -> dict:
    if k < 1 or not relevant:
        raise ValueError("k 要大于 0；无答案题请单独统计")
    selected = retrieved[:k]
    found = set(selected) & relevant
    first_rank = next(
        (rank for rank, item in enumerate(selected, 1) if item in relevant), None
    )
    return {
        "hit": float(bool(found)),
        "recall": len(found) / len(relevant),
        "rr": 1 / first_rank if first_rank else 0.0,
    }


def evaluate(k: int = 1) -> dict:
    chunks = split_documents(load_documents(KNOWLEDGE_DIR))
    cases = json.loads((HERE / "datasets/rag_cases.json").read_text())
    known_ids = {chunk.id for chunk in chunks}
    rows = []
    for case in cases:
        relevant = set(case["relevant_chunk_ids"])
        if not relevant <= known_ids:
            raise ValueError(f"{case['id']} 标注了不存在的块，请检查资料是否改动")
        selected = [r.chunk.id for r in retrieve(case["question"], chunks, k)]
        row = {**case, "retrieved": selected}
        if relevant:
            row.update(metrics(selected, relevant, k))
        else:
            # 这里只能测有没有返回候选；不等于模型有没有拒答。
            row["returned_candidate_on_unanswerable"] = bool(selected)
        rows.append(row)
    answerable = [r for r in rows if r["relevant_chunk_ids"]]
    return {
        "scope": "lexical retrieval only; 5 teaching cases; no generation",
        "top_k": k,
        "answerable_count": len(answerable),
        "unanswerable_count": len(rows) - len(answerable),
        "mean": {
            name: sum(row[name] for row in answerable) / len(answerable)
            for name in ("hit", "recall", "rr")
        },
        "cases": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-k", type=int, default=1)
    parser.add_argument("--min-recall", type=float, default=0.0)
    args = parser.parse_args()
    if args.top_k < 1 or not 0 <= args.min_recall <= 1:
        parser.error("top-k >= 1，min-recall 在 0～1 之间")
    report = evaluate(args.top_k)
    path = HERE / "reports" / f"lexical-k{args.top_k}.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    for row in report["cases"]:
        print(row["id"], row["question"], "->", row["retrieved"])
    print(json.dumps(report["mean"], indent=2))
    print("完整报告：", path)
    if report["mean"]["recall"] < args.min_recall:
        raise SystemExit("未达到本次设置的 Recall 门槛")


if __name__ == "__main__":
    main()
