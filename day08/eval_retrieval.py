"""Day 08：评估 Day 05 的关键词检索，不请求生成模型。"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from day05.rag_baseline import KNOWLEDGE_DIR, load_documents, retrieve, split_documents

HERE = Path(__file__).resolve().parent
CASES_PATH = HERE / "datasets" / "rag_cases.json"  # 人工编写的测试用例。


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


def evaluate(k: int = 1, cases_path: Path = CASES_PATH) -> dict:
    chunks = split_documents(load_documents(KNOWLEDGE_DIR))
    cases = json.loads(cases_path.read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        raise ValueError("评估集必须是非空的题目列表")
    known_ids = {chunk.id for chunk in chunks}
    case_ids = set()
    rows = []
    for case in cases:
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            raise ValueError("每道题需要字符串 id")
        if not case["id"].strip() or case["id"] in case_ids:
            raise ValueError("题目 id 不能为空或重复")
        case_ids.add(case["id"])
        if not isinstance(case.get("question"), str) or not case["question"].strip():
            raise ValueError(f"{case['id']} 需要非空 question")
        labels = case.get("relevant_chunk_ids")
        if not isinstance(labels, list) or not all(isinstance(x, str) for x in labels):
            raise ValueError(f"{case['id']} 的 relevant_chunk_ids 必须是编号列表")
        if len(labels) != len(set(labels)):
            raise ValueError(f"{case['id']} 的标准证据编号重复")
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
    if not answerable:
        raise ValueError("至少需要一道有答案题才能计算本课的平均分")
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset": str(cases_path.resolve().relative_to(HERE.parent))
        if cases_path.resolve().is_relative_to(HERE.parent)
        else str(cases_path.resolve()),
        "knowledge": "day05/knowledge/",
        "retriever": "day05.rag_baseline.retrieve",
        "scope": "lexical (关键词) retrieval only; teaching cases; no generation",
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
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"题目（人工编写）：{CASES_PATH}")
    print(f"资料（人工编写）：{KNOWLEDGE_DIR}")
    print(f"检索方法：lexical（关键词）；每题最多 {args.top_k} 块")
    for row in report["cases"]:
        print(row["id"], row["question"], "->", row["retrieved"])
    print(json.dumps(report["mean"], indent=2))
    print("完整报告：", path)
    if report["mean"]["recall"] < args.min_recall:
        raise SystemExit("未达到本次设置的 Recall 门槛")


if __name__ == "__main__":
    main()
