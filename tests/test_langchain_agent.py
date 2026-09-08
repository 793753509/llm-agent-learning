"""Day 09 离线检查：真实框架执行工具，预设消息和 HTTP 回复均为人工样例。"""

import json

import pytest

pytest.importorskip("langchain")

from langchain.agents.middleware.model_call_limit import ModelCallLimitExceededError
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from day09.demo_model import DemoChatModel
from day09.langchain_agent import EXAMPLES, run


def test_framework_executes_changed_parameters_and_returns_matching_tool_result():
    model = DemoChatModel(tool_name="multiply", tool_args={"a": 12, "b": 4})
    messages = run("精确计算 12 乘 4。", model)["messages"]
    assert [type(message) for message in messages] == [
        HumanMessage,
        AIMessage,
        ToolMessage,
        AIMessage,
    ]
    call = messages[1].tool_calls[0]
    assert call["name"] == "multiply"
    assert messages[2].tool_call_id == call["id"]
    assert json.loads(messages[2].content)["result"] == 48
    assert messages[2].content in messages[-1].text
    assert not messages[-1].tool_calls


@pytest.mark.parametrize("case", ["knowledge", "missing"])
def test_search_tool_keeps_sources_and_reports_actual_empty_retrieval(case):
    example = EXAMPLES[case]
    model = DemoChatModel(
        tool_name=example["tool_name"], tool_args=example["tool_args"]
    )
    messages = run(example["question"], model)["messages"]
    result = json.loads(messages[2].content)
    if case == "knowledge":
        assert result["status"] == "candidates"
        assert result["results"][0]["source"] == "hours.md#1"
        assert "18:00" in result["results"][0]["text"]
    else:
        assert result == {"status": "no_evidence", "results": []}


@pytest.mark.parametrize("value", ["25", True, 1001])
def test_invalid_tool_arguments_do_not_execute_calculator(monkeypatch, value):
    from day09 import langchain_agent

    def unexpected_execution(*args, **kwargs):
        pytest.fail("无效参数不应进入业务计算")

    monkeypatch.setattr(langchain_agent, "calculator", unexpected_execution)
    model = DemoChatModel(tool_name="multiply", tool_args={"a": value, "b": 3})
    messages = run("无效参数实验", model)["messages"]
    result = next(message for message in messages if isinstance(message, ToolMessage))
    assert result.status == "error"


def test_repeated_tool_requests_stop_at_model_call_limit():
    class LoopingModel(DemoChatModel):
        calls: int = 0

        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            self.calls += 1
            reply = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "multiply",
                        "args": {"a": 2, "b": 3},
                        "id": f"loop-{self.calls}",
                        "type": "tool_call",
                    }
                ],
            )
            return ChatResult(generations=[ChatGeneration(message=reply)])

    model = LoopingModel(tool_name="multiply", tool_args={})
    with pytest.raises(ModelCallLimitExceededError):
        run("故意不停请求工具", model)
    assert model.calls == 4


def test_responses_adapter_round_trip_uses_mock_http_and_preserves_call_id():
    """本地模拟 HTTP 响应，测试真实适配器；不读取 Key，也不发送网络请求。"""
    httpx = pytest.importorskip("httpx")
    ChatOpenAI = pytest.importorskip("langchain_openai").ChatOpenAI
    requests = []

    def handle(request):
        assert request.url.path == "/v1/responses"
        body = json.loads(request.content)
        requests.append(body)
        if len(requests) == 1:
            output = [
                {
                    "id": "fc_fixture",
                    "type": "function_call",
                    "call_id": "call_fixture",
                    "name": "multiply",
                    "arguments": '{"a":12,"b":4}',
                    "status": "completed",
                }
            ]
        else:
            assert len(requests) == 2
            result = next(
                item for item in body["input"] if item["type"] == "function_call_output"
            )
            assert result["call_id"] == "call_fixture"
            assert json.loads(result["output"])["result"] == 48
            output = [
                {
                    "id": "msg_fixture",
                    "type": "message",
                    "role": "assistant",
                    "status": "completed",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "结果是 48。",
                            "annotations": [],
                        }
                    ],
                }
            ]
        return httpx.Response(
            200,
            json={
                "id": f"resp_fixture_{len(requests)}",
                "object": "response",
                "created_at": 0,
                "status": "completed",
                "model": "fixture-model",
                "output": output,
                "error": None,
                "usage": None,
            },
        )

    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        model = ChatOpenAI(
            model="fixture-model",
            api_key="fixture-not-a-real-key",
            base_url="https://fixture.invalid/v1",
            use_responses_api=True,
            max_retries=0,
            http_client=client,
        )
        messages = run("精确计算 12 乘 4。", model)["messages"]
    assert len(requests) == 2
    assert {tool["name"] for tool in requests[0]["tools"]} == {
        "multiply",
        "search_knowledge",
    }
    assert messages[-1].text == "结果是 48。"


def test_real_model_construction_uses_existing_config_without_network(monkeypatch):
    pytest.importorskip("langchain_openai")
    from day03.agent_core import config
    from day09.langchain_agent import real_model

    monkeypatch.setattr(config, "BASE_URL", "https://fixture.invalid/v1")
    monkeypatch.setattr(config, "MODEL", "fixture-model")
    monkeypatch.setattr(config, "load_api_key", lambda: "fixture-not-a-real-key")
    model = real_model()
    assert model.model_name == "fixture-model"
    assert model.openai_api_base == "https://fixture.invalid/v1"
    assert model.use_responses_api is True
    assert model.max_retries == 0


def test_arbitrary_question_requires_explicit_real_model_mode(monkeypatch, capsys):
    from day09.langchain_agent import main

    monkeypatch.setattr("sys.argv", ["langchain_agent", "这是任意新问题"])
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
    assert "预设回复不理解任意问题" in capsys.readouterr().err
