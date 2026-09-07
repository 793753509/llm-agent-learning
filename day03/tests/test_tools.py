from day03.agent_core.models import ToolCall
from day03.agent_core.tools import calculator, execute_tool, get_current_time


def test_calculator() -> None:
    assert calculator("add", 6, 2)["result"] == 8
    assert calculator("subtract", 6, 2)["result"] == 4
    assert calculator("multiply", 6, 2)["result"] == 12
    assert calculator("divide", 6, 2)["result"] == 3


def test_divide_by_zero() -> None:
    assert calculator("divide", 1, 0) == {"ok": False, "error": "除数不能为 0"}


def test_unknown_operation() -> None:
    assert calculator("unknown", 1, 2)["ok"] is False


def test_current_time() -> None:
    result = get_current_time("Asia/Shanghai")
    assert result["ok"] is True
    assert result["timezone"] == "Asia/Shanghai"


def test_invalid_timezone() -> None:
    assert get_current_time("Invalid/Timezone")["ok"] is False


def test_execute_tool() -> None:
    call = ToolCall("call_1", "calculator", {"operation": "add", "a": 1, "b": 2})
    assert execute_tool(call)["result"] == 3
