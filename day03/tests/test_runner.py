import json

import pytest

from day03.agent_core.errors import EmptyQuestionError, MaxStepsExceededError
from day03.agent_core.models import ModelReply, TokenUsage, ToolCall
from day03.agent_core.runner import run_agent
from day03.agent_core.tools import TOOLS
from day03.tests.fakes import FakeModelClient


def test_direct_answer() -> None:
    fake = FakeModelClient([ModelReply(text="你好")])
    result = run_agent("请打招呼", client=fake, tools=TOOLS)
    assert result.answer == "你好"
    assert result.used_tools == []


def test_tool_call_then_answer() -> None:
    call = ToolCall(
        call_id="call_123",
        name="calculator",
        arguments={"operation": "multiply", "a": 6, "b": 7},
    )
    # 模拟 response.output 中的一项，下一轮需要把它和工具结果一起回传。
    output_item = {
        "type": "function_call",
        "call_id": call.call_id,
        "name": call.name,
        "arguments": json.dumps(call.arguments),
    }
    fake = FakeModelClient(
        [
            ModelReply(
                tool_calls=[call],
                output_items=[output_item],
                usage=TokenUsage(100, 20),
            ),
            ModelReply(text="6 × 7 = 42", usage=TokenUsage(120, 10)),
        ]
    )

    result = run_agent("计算 6 × 7", client=fake, tools=TOOLS)

    assert result.answer == "6 × 7 = 42"
    assert result.used_tools == ["calculator"]
    assert result.usage.total_tokens == 250
    assert len(fake.calls[0]["input_items"]) == 1

    history = fake.calls[1]["input_items"]
    assert len(history) == 3  # 用户问题 + 模型工具调用 + 工具执行结果
    assert history[1] == output_item
    assert history[2]["type"] == "function_call_output"
    assert history[2]["call_id"] == "call_123"
    assert json.loads(history[2]["output"])["result"] == 42


def test_empty_question() -> None:
    with pytest.raises(EmptyQuestionError):
        run_agent("", client=FakeModelClient([]), tools=TOOLS)


def test_max_steps() -> None:
    call = ToolCall("call_1", "calculator", {"operation": "add", "a": 1, "b": 2})
    fake = FakeModelClient([ModelReply(tool_calls=[call])])
    with pytest.raises(MaxStepsExceededError):
        run_agent("一直计算", client=fake, tools=TOOLS, max_steps=1)
