"""最简单的测试替身：按顺序返回预先准备好的回复，不联网。"""

from typing import Any

from day03.agent_core.models import ModelReply


class FakeModelClient:
    def __init__(self, replies: list[ModelReply]) -> None:
        self.replies = replies.copy()
        self.calls: list[dict[str, Any]] = []

    def create_response(
        self,
        *,
        input_items: list[Any],
        tools: list[Any],
    ) -> ModelReply:
        # 只复制外层列表，避免后续 append 改变已记录的历史长度。
        self.calls.append({"input_items": input_items.copy(), "tools": tools})
        return self.replies.pop(0)
