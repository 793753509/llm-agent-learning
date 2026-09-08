import json
import operator
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import openai
from openai import OpenAI


DEFAULT_BASE_URL = (
    "https://llm-dvre3q31s582vei3.cn-beijing.maas.aliyuncs.com/"
    "compatible-mode/v1"
)
MODEL = os.getenv("LLM_MODEL", "qwen3.8-flash")
BASE_URL = os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL)
MAX_STEPS = 5


def load_api_key() -> str:
    for variable_name in ("DASHSCOPE_API_KEY", "ALIYUN_API_KEY"):
        if api_key := os.getenv(variable_name):
            return api_key

    project_root = Path(__file__).resolve().parent.parent
    key_file = project_root / "aliyun_api_key"

    if not key_file.is_file():
        raise RuntimeError(
            "未找到 API Key：请设置 DASHSCOPE_API_KEY，"
            "或在项目根目录创建 aliyun_api_key 文件。"
        )

    api_key = key_file.read_text(encoding="utf-8").strip()
    if not api_key:
        raise RuntimeError("aliyun_api_key 文件为空")

    return api_key


client = OpenAI(
    api_key=load_api_key(),
    base_url=BASE_URL,
    timeout=30.0,
    max_retries=2,
)


OPERATIONS = {
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
    except ZoneInfoNotFoundError:
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


TOOLS = [
    {
        "type": "function",
        "name": "calculator",
        "description": (
            "执行两个数字的加、减、乘、除。"
            "用户要求精确计算时必须调用，不要自行心算。"
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


TOOL_HANDLERS = {
    "calculator": calculator,
    "get_current_time": get_current_time,
}


AGENT_INSTRUCTIONS = """
你是一个谨慎的命令行助手。

规则：
1. 涉及精确数学计算时必须使用 calculator。
2. 涉及当前日期或时间时必须使用 get_current_time。
3. 不要编造工具结果。
4. 工具返回 ok=false 时，向用户说明失败原因。
5. 只使用完成任务所需的工具。
6. 最终回答先给结论，再简要说明使用了什么信息。
"""


def execute_tool(tool_call) -> str:
    handler = TOOL_HANDLERS.get(tool_call.name)

    if handler is None:
        return json.dumps(
            {
                "ok": False,
                "error": f"未知工具：{tool_call.name}",
            },
            ensure_ascii=False,
        )

    try:
        arguments = json.loads(tool_call.arguments)
        result = handler(**arguments)
    except json.JSONDecodeError:
        result = {
            "ok": False,
            "error": "工具参数不是合法 JSON",
        }
    except TypeError as exc:
        result = {
            "ok": False,
            "error": f"工具参数错误：{exc}",
        }
    except Exception as exc:
        result = {
            "ok": False,
            "error": f"工具执行失败：{type(exc).__name__}",
        }

    return json.dumps(result, ensure_ascii=False)


def print_usage(response) -> None:
    if not response.usage:
        return

    print(
        "[tokens] "
        f"input={response.usage.input_tokens}, "
        f"output={response.usage.output_tokens}, "
        f"total={response.usage.total_tokens}, "
        f"response={response.output}"
    )


def run_agent(question: str) -> str:
    input_items = [
        {
            "role": "user",
            "content": question,
        }
    ]

    for step in range(1, MAX_STEPS + 1):
        print(f"\n[step {step}] 请求模型")

        print("模型input：", input_items)

        response = client.responses.create(
            model=MODEL,
            instructions=AGENT_INSTRUCTIONS,
            input=input_items,
            tools=TOOLS,
        )
        print_usage(response)

        input_items += response.output

        tool_calls = [
            item
            for item in response.output
            if item.type == "function_call"
        ]

        if not tool_calls:
            if not response.output_text:
                raise RuntimeError("模型没有返回文本或工具调用")
            return response.output_text

        for tool_call in tool_calls:
            print(
                f"[tool] name={tool_call.name} "
                f"arguments={tool_call.arguments}"
            )

            tool_result = execute_tool(tool_call)
            print(f"[tool result] {tool_result}")

            input_items.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": tool_result,
                }
            )



    raise RuntimeError(f"超过最大执行步数：{MAX_STEPS}")


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        question = input("请输入问题：").strip()

    if not question:
        print("问题不能为空")
        raise SystemExit(1)

    try:
        answer = run_agent(question)
    except openai.AuthenticationError:
        print("认证失败：请检查阿里云 API Key")
        raise SystemExit(1)
    except openai.APIConnectionError:
        print("无法连接模型服务，请检查网络")
        raise SystemExit(1)
    except openai.APIStatusError as exc:
        print(f"API 请求失败：HTTP {exc.status_code}")
        print(f"request_id：{exc.request_id or '未提供'}")
        raise SystemExit(1)
    except RuntimeError as exc:
        print(f"Agent 执行失败：{exc}")
        raise SystemExit(1)

    print("\n--- 最终回答 ---")
    print(answer)


if __name__ == "__main__":
    main()
