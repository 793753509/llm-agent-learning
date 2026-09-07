"""用几个 assert 理解 dataclass 和 default_factory。"""

from day03.agent_core.models import AgentResult, ModelReply, TokenUsage, ToolCall


def test_model_reply_has_independent_tool_call_lists() -> None:
    first = ModelReply()
    second = ModelReply()
    first.tool_calls.append(
        ToolCall(
            call_id="call_1",
            name="calculator",
            arguments={"a": 1, "b": 2},
        )
    )
    assert len(first.tool_calls) == 1
    assert second.tool_calls == []


def test_token_usage_total() -> None:
    usage = TokenUsage(input_tokens=100, output_tokens=20)
    assert usage.total_tokens == 120


def test_agent_result_stores_answer() -> None:
    result = AgentResult(answer="42", usage=TokenUsage(), used_tools=["calculator"])
    assert result.answer == "42"
    assert result.used_tools == ["calculator"]
