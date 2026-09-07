"""运行：uv run python -m day07.fusion_practice

给定两张人工排名表，手算并观察 RRF；不调用真实检索模型。
"""

from day05.rag_baseline import Chunk, SearchResult
from day07.fusion import rrf_fuse


def main() -> None:
    chunks = {
        name: Chunk(name, "手算示例", index, name)
        for index, name in enumerate("ABC", 1)
    }
    lexical = [SearchResult(chunks[name], 0.0) for name in "AB"]
    vector = [SearchResult(chunks[name], 0.0) for name in "BCA"]
    print("人工排名表：关键词 [A, B]；向量 [B, C, A]。这里只演示融合算法。")
    print("原始分数故意设为 0；RRF 只使用排名，rrf_k=60。")
    for candidate in rrf_fuse(lexical, vector):
        print(f"{candidate.chunk.id}: {candidate.rrf_score:.6f} 排名={candidate.ranks}")


if __name__ == "__main__":
    main()
