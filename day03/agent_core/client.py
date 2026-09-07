"""调用真实模型，并把 SDK 回复整理成我们自己的 dataclass。"""

import json
from typing import Any

from openai import OpenAI

from day03.agent_core.config import AGENT_INSTRUCTIONS, MODEL
from day03.agent_core.models import ModelReply, TokenUsage, ToolCall


class OpenAIModelClient:
    def __init__(self, sdk_client: OpenAI) -> None:
        self.sdk_client = sdk_client

    def create_response(
        self,
        *,
        input_items: list[Any],
        tools: list[Any],
    ) -> ModelReply:
        response = self.sdk_client.responses.create(
            model=MODEL,
            instructions=AGENT_INSTRUCTIONS,
            input=input_items,
            tools=tools,
        )

        tool_calls = []
        for item in response.output:
            if item.type == "function_call":
                tool_calls.append(
                    ToolCall(
                        call_id=item.call_id,
                        name=item.name,
                        arguments=json.loads(item.arguments),
                    )
                )

        usage = TokenUsage()
        if response.usage:
            usage.input_tokens = response.usage.input_tokens
            usage.output_tokens = response.usage.output_tokens

        return ModelReply(
            text=response.output_text,
            tool_calls=tool_calls,
            usage=usage,
            output_items=list(response.output),
        )
