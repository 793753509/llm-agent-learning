"""Day 02 的 Agent 循环，改为通过参数接收客户端。"""

import json
from typing import Any

from day03.agent_core.errors import (
    EmptyQuestionError,
    InvalidModelReplyError,
    MaxStepsExceededError,
)
from day03.agent_core.models import AgentResult, TokenUsage
from day03.agent_core.ports import ModelClient
from day03.agent_core.tools import execute_tool


def run_agent(
    question: str,
    *,
    client: ModelClient,
    tools: list[Any],
    max_steps: int = 5,
) -> AgentResult:
    if not question.strip():
        raise EmptyQuestionError("问题不能为空")

    # 和 Day 02 一样：历史中既有字典，也有 SDK 返回的对象，所以用 Any。
    input_items: list[Any] = [{"role": "user", "content": question}]
    usage = TokenUsage()
    used_tools: list[str] = []

    for step in range(1, max_steps + 1):
        # 学习版保留过程输出，方便观察 input_items 的变化。
        print(f"\n[step {step}] 请求模型")
        print("模型 input：", input_items)
        reply = client.create_response(input_items=input_items, tools=tools)

        usage.input_tokens += reply.usage.input_tokens
        usage.output_tokens += reply.usage.output_tokens

        # 对应 Day 02 的 input_items += response.output，不自己重建模型回复。
        input_items += reply.output_items

        if not reply.tool_calls:
            if not reply.text:
                raise InvalidModelReplyError("模型没有返回文本或工具调用")
            return AgentResult(
                answer=reply.text,
                usage=usage,
                used_tools=used_tools,
            )

        for tool_call in reply.tool_calls:
            tool_result = execute_tool(tool_call)
            used_tools.append(tool_call.name)
            print(f"[tool] {tool_call.name}，参数：{tool_call.arguments}")
            print(f"[tool result] {tool_result}")
            input_items.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": json.dumps(tool_result, ensure_ascii=False),
                }
            )

    raise MaxStepsExceededError(f"超过最大执行步数：{max_steps}")
