"""Protocol 只约定：传进来的客户端需要有 create_response 方法。"""

from typing import Any, Protocol

from day03.agent_core.models import ModelReply


class ModelClient(Protocol):
    def create_response(
        self,
        *,
        input_items: list[Any],
        tools: list[Any],
    ) -> ModelReply: ...
