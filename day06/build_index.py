"""运行：uv run --group rag python -m day06.build_index

把 Day 05 的资料转成真实向量，保存到 day06/data/qdrant。
资料变化后重跑；不请求生成模型。
"""

import json

from day05.rag_baseline import KNOWLEDGE_DIR, load_documents, split_documents
from day06.vector_store import (
    COLLECTION,
    DATA_DIR,
    DB_PATH,
    MANIFEST_PATH,
    embed_texts,
    index_metadata,
    load_embedder,
    write_collection,
)


def main() -> None:
    from qdrant_client import QdrantClient

    chunks = split_documents(load_documents(KNOWLEDGE_DIR))
    if not chunks:
        raise ValueError("知识库为空；请先添加资料。旧索引没有改变。")
    print(f"[1 读取与切块] 共 {len(chunks)} 块，复用 Day 05 的资料")
    model = load_embedder()
    vectors = embed_texts(model, [chunk.text for chunk in chunks])
    for chunk, vector in zip(chunks, vectors):
        print(f"[2 向量] {chunk.id} 维度={len(vector)} 前4项={vector[:4]}")

    # 向量都计算成功后才开始替换索引；失败时不会留下有效的完成标记。
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.unlink(missing_ok=True)
    client = QdrantClient(path=str(DB_PATH))
    try:
        write_collection(client, COLLECTION, chunks, vectors)
        print(f"[3 保存] {client.count(COLLECTION, exact=True).count} 条记录")
    finally:
        client.close()
    MANIFEST_PATH.write_text(
        json.dumps(index_metadata(chunks), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"数据库位置：{DB_PATH}")
    print(f"索引说明：{MANIFEST_PATH}")
    print("下一步：uv run --group rag python -m day06.vector_retriever")


if __name__ == "__main__":
    try:
        main()
    except ModuleNotFoundError:
        raise SystemExit("缺少 RAG 依赖，请运行 uv sync --locked --group rag") from None
