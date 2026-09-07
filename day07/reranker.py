"""教学用规则重排：问题含错误码时，把包含相同完整错误码的候选排在前面。

这不是训练过的 Cross Encoder；没有错误码时保留 RRF 排名。
"""

import re

from day07.fusion import Candidate

CODE_PATTERN = re.compile(r"(?<![A-Za-z0-9_])E\d{3}(?![A-Za-z0-9_])", re.IGNORECASE)


def extract_codes(text: str) -> set[str]:
    return {code.upper() for code in CODE_PATTERN.findall(text)}


def rerank(query: str, candidates: list[Candidate]) -> list[Candidate]:
    query_codes = extract_codes(query)

    def priority(candidate: Candidate) -> tuple[int, float]:
        matches = query_codes & extract_codes(candidate.chunk.text)
        return len(matches), candidate.rrf_score

    return sorted(candidates, key=priority, reverse=True)
