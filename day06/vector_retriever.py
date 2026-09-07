"""运行：uv run --group rag python -m day06.vector_retriever '无线网络怎么连接？'

默认只检索并展示 Prompt；加 --ask-model 才调用 Day 05 的生成函数。
"""

import argparse
import json
from time import perf_counter

from day05.rag_baseline import (
    KNOWLEDGE_DIR,
    build_prompt,
    generate_answer,
    load_documents,
    retrieve,
    split_documents,
)
from day06.vector_store import (
    COLLECTION,
    DB_PATH,
    MANIFEST_PATH,
    embed_query,
    index_metadata,
    load_embedder,
    search_vectors,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", nargs="?", default="无线网络怎么连接？")
    parser.add_argument("--top-k", type=int, default=2)
    parser.add_argument("--min-score", type=float, default=None)
    parser.add_argument("--ask-model", action="store_true")
    args = parser.parse_args()
    if not args.query.strip() or args.top_k < 1:
        parser.error("请输入非空问题，且 --top-k 至少为 1")
    if args.min_score is not None and not -1 <= args.min_score <= 1:
        parser.error("余弦分数阈值 --min-score 应在 -1 到 1 之间")
    if not MANIFEST_PATH.is_file():
        raise SystemExit(
            "还没有完整索引，请先运行：uv run --group rag python -m day06.build_index"
        )

    from qdrant_client import QdrantClient

    chunks = split_documents(load_documents(KNOWLEDGE_DIR))
    saved = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if saved != index_metadata(chunks):
        raise SystemExit("资料或 Embedding 配置已变化，请重新运行 day06.build_index")

    print("[对照] Day 05 的关键词结果：")
    for result in retrieve(args.query, chunks, args.top_k):
        print(f"  {result.chunk.id} 字面分数={result.score:.3f}")
    model = load_embedder()
    start = perf_counter()
    query_vector = embed_query(model, args.query)
    print(f"[问题向量] 维度={len(query_vector)} 前4项={query_vector[:4]}")
    client = QdrantClient(path=str(DB_PATH))
    try:
        results = search_vectors(
            client, COLLECTION, query_vector, args.top_k, args.min_score
        )
    finally:
        client.close()
    print(
        f"[向量检索] 问题编码与查询耗时 {perf_counter() - start:.3f}s（不含加载模型）"
    )
    for result in results:
        print(f"  {result.chunk.id} 余弦分数={result.score:.3f}\n{result.chunk.text}")
    if not results:
        print("没有达到检索条件的资料，不调用生成模型。")
        return
    prompt = build_prompt(args.query, results)
    print(f"\n[给生成模型的 input]\n{prompt}")
    if args.ask_model:
        print(generate_answer(prompt))
    else:
        print("\n已使用真实 Embedding 模型；尚未调用生成模型。")


if __name__ == "__main__":
    try:
        main()
    except ModuleNotFoundError:
        raise SystemExit("缺少 RAG 依赖，请运行 uv sync --locked --group rag") from None
