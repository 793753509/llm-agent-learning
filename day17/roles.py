"""用普通函数模拟资料员→审核员→写作者的数据交接；没有调用多个模型。"""

import argparse
import json

from pydantic import BaseModel

from day05.rag_baseline import KNOWLEDGE_DIR, load_documents, retrieve, split_documents


class Evidence(BaseModel):
    source_id: str
    quote: str


class Review(BaseModel):
    approved: bool
    reason: str


def research(question: str) -> list[Evidence]:
    chunks = split_documents(load_documents(KNOWLEDGE_DIR))
    return [
        Evidence(source_id=r.chunk.id, quote=r.chunk.text)
        for r in retrieve(question, chunks, 1)
    ]


def review(evidence: list[Evidence]) -> Review:
    source = {c.id: c.text for c in split_documents(load_documents(KNOWLEDGE_DIR))}
    if not evidence:
        return Review(approved=False, reason="没有证据")
    if any(
        item.source_id not in source or item.quote != source[item.source_id]
        for item in evidence
    ):
        return Review(approved=False, reason="引用编号或原文不匹配")
    return Review(
        approved=True, reason="编号存在，摘录等于原文；尚未验证是否回答了问题"
    )


def write(evidence: list[Evidence]) -> str:
    return "资料摘录（请核对是否回答问题）：\n" + "\n".join(
        f"{item.quote} [来源: {item.source_id}]" for item in evidence
    )


def run(question: str, tamper: bool = False) -> dict:
    evidence = research(question)
    if tamper and evidence:
        evidence[0] = Evidence(source_id=evidence[0].source_id, quote="周末通宵开放。")
    verdict = review(evidence)
    # 单次交接，无无限“互相讨论”；审核失败立即停止。
    answer = write(evidence) if verdict.approved else "停止：" + verdict.reason
    return {
        "mode": "scripted role handoff",
        "evidence": [e.model_dump() for e in evidence],
        "review": verdict.model_dump(),
        "output": answer,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("question", nargs="?", default="周末几点关门？")
    parser.add_argument("--tamper", action="store_true")
    args = parser.parse_args()
    print(json.dumps(run(args.question, args.tamper), ensure_ascii=False, indent=2))
