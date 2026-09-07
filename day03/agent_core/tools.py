"""从 Day 02 移来的两个工具：计算器和当前时间。"""

import operator
from collections.abc import Callable
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from day03.agent_core.models import ToolCall

OPERATIONS: dict[str, Callable[[float, float], float]] = {
    "add": operator.add,
    "subtract": operator.sub,
    "multiply": operator.mul,
    "divide": operator.truediv,
}


def calculator(operation: str, a: float, b: float) -> dict[str, Any]:
    if operation not in OPERATIONS:
        return {
            "ok": False,
            "error": f"不支持的运算：{operation}",
        }

    if operation == "divide" and b == 0:
        return {
            "ok": False,
            "error": "除数不能为 0",
        }

    return {
        "ok": True,
        "operation": operation,
        "a": a,
        "b": b,
        "result": OPERATIONS[operation](a, b),
    }


def get_current_time(timezone: str) -> dict[str, Any]:
    try:
        current_time = datetime.now(ZoneInfo(timezone))
    except (ZoneInfoNotFoundError, ValueError):
        return {
            "ok": False,
            "error": f"未知时区：{timezone}",
        }

    return {
        "ok": True,
        "timezone": timezone,
        "iso_time": current_time.isoformat(timespec="seconds"),
        "date": current_time.strftime("%Y-%m-%d"),
        "time": current_time.strftime("%H:%M:%S"),
    }


TOOLS: list[Any] = [
    {
        "type": "function",
        "name": "calculator",
        "description": (
            "执行两个数字的加、减、乘、除。用户要求精确计算时必须调用，不要自行心算。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "要执行的运算",
                },
                "a": {
                    "type": "number",
                    "description": "第一个数字",
                },
                "b": {
                    "type": "number",
                    "description": "第二个数字",
                },
            },
            "required": ["operation", "a", "b"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "get_current_time",
        "description": (
            "获取指定 IANA 时区的当前日期和时间。"
            "当用户询问当前时间或日期时使用，不要猜测。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "IANA 时区，例如 Asia/Shanghai",
                }
            },
            "required": ["timezone"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


TOOL_HANDLERS: dict[str, Callable[..., dict[str, Any]]] = {
    "calculator": calculator,
    "get_current_time": get_current_time,
}


def execute_tool(tool_call: ToolCall) -> dict[str, Any]:
    handler = TOOL_HANDLERS.get(tool_call.name)
    if handler is None:
        return {"ok": False, "error": f"未知工具：{tool_call.name}"}

    try:
        # client.py 已经把 JSON 字符串解析成字典，这里直接展开参数。
        return handler(**tool_call.arguments)
    except TypeError:
        return {"ok": False, "error": "工具参数错误，请检查参数名称和类型"}
    except Exception as exc:
        return {"ok": False, "error": f"工具执行失败：{type(exc).__name__}"}
