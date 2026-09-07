"""Day 06/07 共用的小函数：本地 Embedding、Qdrant 写入和查询。

先看 build_index.py / vector_retriever.py 的 main()，再回来读相关函数。
RAG 依赖单独安装：uv sync --locked --group rag
"""

import hashlib
import json
import os
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import TYPE_CHECKING, Any
from uuid import NAMESPACE_URL, uuid5

from day05.rag_baseline import Chunk, SearchResult
from day06.vector_basics import normalize

if TYPE_CHECKING:
    from fastembed import TextEmbedding
    from qdrant_client import QdrantClient

DATA_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DATA_DIR / "qdrant"
MODEL_CACHE = DATA_DIR / "models"
MANIFEST_PATH = DATA_DIR / "index.json"
COLLECTION = "day06_study_room"
MODEL_NAME = "BAAI/bge-small-zh-v1.5"
DIMENSION = 512
QUERY_PREFIX = "为这个句子生成表示以用于检索相关文章："

# 附带的下载缓存也保存在课程目录内；尊重用户已经设置的 HF_HOME。
os.environ.setdefault("HF_HOME", str(DATA_DIR / "huggingface"))


def load_embedder() -> "TextEmbedding":
    from fastembed import TextEmbedding

    print(f"[模型] {MODEL_NAME}；CPU 本地计算；首次使用需要下载权重。")
    return TextEmbedding(
        model_name=MODEL_NAME,
        cache_dir=str(MODEL_CACHE),
        threads=2,
    )


def embed_texts(model: "TextEmbedding", texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    vectors = []
    for vector in model.embed(texts):
        values = vector.tolist()
        if len(values) != DIMENSION:
            raise ValueError(f"模型应输出 {DIMENSION} 维，实际得到 {len(values)} 维")
        vectors.append(normalize(values))
    return vectors


def embed_query(model: "TextEmbedding", query: str) -> list[float]:
    if not query.strip():
        raise ValueError("问题不能为空")
    # 使用相同模型；短问题按 BGE 的建议添加检索前缀，文档不加。
    return embed_texts(model, [QUERY_PREFIX + query])[0]


def write_collection(
    client: "QdrantClient",
    collection: str,
    chunks: list[Chunk],
    vectors: list[list[float]],
) -> None:
    from qdrant_client import models

    if len(chunks) != len(vectors) or not chunks:
        raise ValueError("每个 chunk 必须对应一个向量，且资料不能为空")
    if len({chunk.id for chunk in chunks}) != len(chunks):
        raise ValueError("资料编号重复")
    if any(len(vector) != DIMENSION for vector in vectors):
        raise ValueError("向量维度不匹配")

    # 只替换调用方明确指定的教学 collection；这是全量重建。
    if client.collection_exists(collection):
        client.delete_collection(collection)
    client.create_collection(
        collection_name=collection,
        vectors_config=models.VectorParams(
            size=DIMENSION, distance=models.Distance.COSINE
        ),
    )
    points = []
    for chunk, vector in zip(chunks, vectors):
        points.append(
            models.PointStruct(
                id=str(uuid5(NAMESPACE_URL, chunk.id)),
                vector=vector,
                payload=asdict(chunk),
            )
        )
    client.upsert(collection_name=collection, points=points, wait=True)


def search_vectors(
    client: "QdrantClient",
    collection: str,
    query_vector: list[float],
    top_k: int,
    min_score: float | None = None,
) -> list[SearchResult]:
    if top_k < 1:
        raise ValueError("top_k 必须至少为 1")
    points = client.query_points(
        collection_name=collection,
        query=query_vector,
        limit=top_k,
        with_payload=True,
        score_threshold=min_score,
    ).points
    results = []
    for point in points:
        if point.payload is None:
            raise ValueError("检索结果没有原文 payload，请重建索引")
        chunk = Chunk(**point.payload)
        results.append(SearchResult(chunk=chunk, score=point.score))
    # 本课同分时按来源编号排列，方便重复运行时核对。
    return sorted(results, key=lambda result: (-result.score, result.chunk.id))


def index_metadata(chunks: list[Chunk]) -> dict[str, Any]:
    snapshot = json.dumps([asdict(chunk) for chunk in chunks], ensure_ascii=False)
    return {
        "embedding_model": MODEL_NAME,
        "fastembed_version": version("fastembed"),
        "vector_dimension": DIMENSION,
        "query_prefix": QUERY_PREFIX,
        "normalize": True,
        "chunker_version": "day05-blank-lines-v1",
        "document_hash": hashlib.sha256(snapshot.encode("utf-8")).hexdigest(),
        "chunk_count": len(chunks),
    }
