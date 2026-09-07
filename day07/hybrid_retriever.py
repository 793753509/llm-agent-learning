"""运行：uv run --group rag python -m day07.hybrid_retriever

虚构的自习室门店资料：过滤 -> 关键词与真实向量检索 -> RRF -> 规则重排。
默认展示候选与 Prompt；加 --ask-model 才调用生成模型。
"""

import argparse
import json
from pathlib import Path
from time import perf_counter

from day05.rag_baseline import (
    Chunk,
    SearchResult,
    build_prompt,
    generate_answer,
    retrieve,
)
from day06.vector_store import (
    embed_query,
    embed_texts,
    load_embedder,
    search_vectors,
    write_collection,
)
from day07.fusion import Candidate, deduplicate_text, rrf_fuse, select_context
from day07.reranker import extract_codes, rerank

KNOWLEDGE_PATH = Path(__file__).resolve().parent / "knowledge.json"


def load_branch_chunks(branch: str) -> list[Chunk]:
    """先按 metadata 选择范围，再交给两个检索器；branch 是练习参数。"""
    records = json.loads(KNOWLEDGE_PATH.read_text(encoding="utf-8"))
    chunks = []
    for record in records:
        if record["branch"] == branch:
            chunks.append(
                Chunk(
                    id=record["id"],
                    source=record["source"],
                    index=record["index"],
                    text=record["text"],
                )
            )
    return chunks


def show_results(label: str, results: list[SearchResult]) -> None:
    print(label)
    for rank, result in enumerate(results, 1):
        print(f"  {rank}. {result.chunk.id} 分数={result.score:.3f}")


def show_candidates(label: str, query: str, candidates: list[Candidate]) -> None:
    print(label)
    for rank, candidate in enumerate(candidates, 1):
        matches = extract_codes(query) & extract_codes(candidate.chunk.text)
        print(f"  {rank}. {candidate.chunk.id} RRF={candidate.rrf_score:.6f}")
        print(f"     各路排名={candidate.ranks}；完整错误码命中={sorted(matches)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default="E101 预约失败怎么办？")
    parser.add_argument("--branch", choices=("north", "south"), default="north")
    parser.add_argument("--candidate-k", type=int, default=3)
    parser.add_argument("--top-k", type=int, default=2)
    parser.add_argument("--rrf-k", type=int, default=60)
    parser.add_argument("--max-chars", type=int, default=1200)
    parser.add_argument("--no-rerank", action="store_true")
    parser.add_argument("--ask-model", action="store_true")
    args = parser.parse_args()
    if not args.query.strip():
        parser.error("问题不能为空")
    if min(args.candidate_k, args.top_k, args.max_chars) < 1 or args.rrf_k < 0:
        parser.error("候选数、最终段数和字符预算必须为正数；--rrf-k 不能小于 0")

    # 1. 两路检索都只接触同一批门店资料，不能只过滤其中一路。
    chunks = load_branch_chunks(args.branch)
    print(f"[1 范围过滤] branch={args.branch}，选中 {len(chunks)} 块")
    print(f"  {[chunk.id for chunk in chunks]}")
    if not chunks:
        print("该范围没有资料，不调用模型。")
        return

    start = perf_counter()
    lexical = retrieve(args.query, chunks, args.candidate_k)
    show_results(f"[2a 关键词] {perf_counter() - start:.3f}s", lexical)

    from qdrant_client import QdrantClient

    model = load_embedder()
    # Day 07 只有六条资料，为观察流程每次建立一个内存库。
    # 它不会修改 Day 06 的持久化库；大知识库应复用已经建立的索引。
    vectors = embed_texts(model, [chunk.text for chunk in chunks])
    client = QdrantClient(":memory:")
    try:
        write_collection(client, "day07_demo", chunks, vectors)
        start = perf_counter()
        vector = search_vectors(
            client, "day07_demo", embed_query(model, args.query), args.candidate_k
        )
    finally:
        client.close()
    show_results(f"[2b 向量] 问题编码与查询 {perf_counter() - start:.3f}s", vector)

    fused = rrf_fuse(lexical, vector, args.rrf_k)
    show_candidates("[3 RRF 合并]", args.query, fused)
    reranked = fused if args.no_rerank else rerank(args.query, fused)
    label = "[4 重排已关闭]" if args.no_rerank else "[4 规则重排]"
    show_candidates(label, args.query, reranked)

    unique = deduplicate_text(reranked)
    print(f"[5 原文去重] {len(reranked)} -> {len(unique)} 块（只合并完全相同的原文）")
    selected, skipped = select_context(args.query, unique, args.top_k, args.max_chars)
    print(f"[6 上下文选择] {[result.chunk.id for result in selected]}")
    print(f"  因字符预算跳过：{skipped}")
    if not selected:
        print("没有可放进上下文的资料，不调用生成模型。")
        return
    prompt = build_prompt(args.query, selected)
    print(f"  input 字符数={len(prompt)}，预算={args.max_chars}（不是 Token 数）")
    print(f"\n{prompt}")
    if args.ask_model:
        print(generate_answer(prompt))
    else:
        print("\n已完成真实双路检索，尚未调用生成模型。")


if __name__ == "__main__":
    try:
        main()
    except ModuleNotFoundError:
        raise SystemExit("缺少 RAG 依赖，请运行 uv sync --locked --group rag") from None
