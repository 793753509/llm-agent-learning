"""离线验证内层工具循环与外层分支，不使用真实凭证或服务。"""

import json

import pytest

pytest.importorskip("langchain")

from langchain.agents.middleware.model_call_limit import ModelCallLimitExceededError
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from day10.combined_workflow import DATA_PATH, run
from day10.diagnostic_model import DiagnosticDemoModel


def fixture_data():
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def test_second_tool_uses_first_tools_actual_error_code():
    # 改成另一个错误码，证明第二次工具参数不是写死的 E101。
    data = fixture_data()
    data["bookings"]["B001"]["error_code"] = "E202"
    data["manuals"] = {
        "E202": {
            "error_code": "E202",
            "source": "test/E202",
            "text": "请核对联系电话。",
        }
    }
    result = run(DiagnosticDemoModel(), data=data)
    replies = [m for m in result["messages"] if isinstance(m, AIMessage)]
    tools = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(replies) == 3
    assert [m.name for m in tools] == ["get_booking", "lookup_manual"]
    assert replies[1].tool_calls[0]["args"] == {"error_code": "E202"}
    for reply, tool in zip(replies, tools):
        assert tool.tool_call_id == reply.tool_calls[0]["id"]
    assert result["evidence_ok"] is True
    assert result["status"] == "draft_ready"
    assert "请核对联系电话" in result["draft"]
    assert "test/E202" in result["draft"]


@pytest.mark.parametrize("missing", ["bookings", "manuals"])
def test_missing_data_routes_away_from_draft(missing):
    data = fixture_data()
    data[missing] = {}
    result = run(DiagnosticDemoModel(), data=data)
    assert result["evidence_ok"] is False
    assert result["status"] == "needs_information"
    assert result["draft"] == ""


def test_confident_model_text_cannot_replace_actual_tool_evidence():
    class UnsupportedAnswer(DiagnosticDemoModel):
        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            return ChatResult(
                generations=[
                    ChatGeneration(
                        message=AIMessage(content="资料已齐全，可以创建工单。")
                    )
                ]
            )

    result = run(UnsupportedAnswer())
    assert "资料已齐全" in result["diagnosis"]
    assert result["status"] == "needs_information"
    assert not result["draft"]


def test_manual_for_another_error_code_is_not_accepted():
    data = fixture_data()
    data["manuals"]["E101"]["error_code"] = "E999"
    result = run(DiagnosticDemoModel(), data=data)
    assert result["status"] == "needs_information"


def test_result_for_another_booking_is_not_accepted():
    data = fixture_data()
    data["bookings"]["B002"] = {"booking_id": "B002", "error_code": "E101"}
    result = run(DiagnosticDemoModel(booking_id="B002"), booking_id="B001", data=data)
    assert result["status"] == "needs_information"


def test_unfinished_inner_loop_stops_before_outer_draft_step():
    class LoopingModel(DiagnosticDemoModel):
        calls: int = 0

        def _generate(self, messages, stop=None, run_manager=None, **kwargs):
            self.calls += 1
            reply = self.call(
                "get_booking", {"booking_id": "B001"}, f"loop-{self.calls}"
            )
            return ChatResult(generations=[ChatGeneration(message=reply)])

    model = LoopingModel()
    with pytest.raises(ModelCallLimitExceededError):
        run(model)
    assert model.calls == 4
