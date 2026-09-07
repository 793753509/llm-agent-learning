"""把两张检索排名表按来源编号合并；不需要模型或数据库。"""

from dataclasses import dataclass, field

from day05.rag_baseline import Chunk, SearchResult, build_prompt


@dataclass
class Candidate:
    chunk: Chunk
    rrf_score: float = 0.0
    ranks: dict[str, int] = field(default_factory=dict)


def rrf_fuse(
    lexical: list[SearchResult],
    vector: list[SearchResult],
    rrf_k: int = 60,
) -> list[Candidate]:
    if rrf_k < 0:
        raise ValueError("rrf_k 不能小于 0")
    merged: dict[str, Candidate] = {}
    for route, results in (("关键词", lexical), ("向量", vector)):
        seen = set()
        rank = 0
        for result in results:
            chunk_id = result.chunk.id
            if chunk_id in seen:
                continue  # 同一路的重复结果不能多得一票。
            seen.add(chunk_id)
            rank += 1  # 本课排名从 1 开始。
            if chunk_id not in merged:
                merged[chunk_id] = Candidate(chunk=result.chunk)
            candidate = merged[chunk_id]
            candidate.rrf_score += 1 / (rrf_k + rank)
            candidate.ranks[route] = rank
    return sorted(merged.values(), key=lambda item: (-item.rrf_score, item.chunk.id))


def deduplicate_text(candidates: list[Candidate]) -> list[Candidate]:
    """只去除原文在合并空白后完全相同的块，不判断语义近似。"""
    seen = set()
    unique = []
    for candidate in candidates:
        key = " ".join(candidate.chunk.text.split())
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return unique


def select_context(
    query: str, candidates: list[Candidate], top_k: int, max_chars: int
) -> tuple[list[SearchResult], list[str]]:
    """按顺序装入完整块；预算统计整个 input 的字符数，不冒充 Token 数。"""
    if top_k < 1 or max_chars < 1:
        raise ValueError("top_k 和 max_chars 必须为正数")
    selected: list[SearchResult] = []
    skipped = []
    for candidate in candidates:
        if len(selected) == top_k:
            break
        result = SearchResult(chunk=candidate.chunk, score=candidate.rrf_score)
        if len(build_prompt(query, selected + [result])) > max_chars:
            skipped.append(candidate.chunk.id)
            continue
        selected.append(result)
    return selected, skipped
