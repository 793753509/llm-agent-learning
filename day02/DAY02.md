# Day 02：Function Calling 与第一个 Agent Loop

> 今日主题：工具定义、工具调用、结果回传、循环与安全边界\
> 建议用时：4～6 小时\
> 当前模型：qwen3.8-flash\
> 最终项目：一个会计算、会查询时区时间的命令行 Agent

## 1. 今天的唯一目标

Day 01 的程序只能完成一次普通模型调用：

~~~text
用户问题 → 模型 → 文本回答
~~~

Day 02 要把它升级为：

~~~text
用户问题
    ↓
模型判断是否需要工具
    ↓
Python 执行工具
    ↓
工具结果返回模型
    ↓
模型生成最终答案
~~~

今天结束时，你应该能独立解释并实现：

- 什么是 Function Calling；
- 模型为什么不能直接执行 Python 函数；
- 如何使用 JSON Schema 描述工具参数；
- 如何识别 response.output 中的 function_call；
- call_id 为什么必须原样回传；
- function_call_output 是什么；
- 如何写一个有最大步数的 Agent Loop；
- 为什么工具参数永远不能无条件信任；
- 如何记录每一步执行轨迹。

---

## 2. 先复习 Day 01

开始之前，确保你理解下面这些代码元素：

| 元素 | 作用 |
| --- | --- |
| OpenAI(...) | 创建 SDK 客户端 |
| api_key | 身份认证 |
| base_url | 决定调用哪个模型服务 |
| model | 选择具体模型 |
| instructions | 定义模型的工作方式 |
| input | 用户本次任务 |
| response.output_text | 最终文本输出 |
| response.usage | Token 用量 |

如果这些概念仍然模糊，先回看 Day 01 的第 2～5 节。

---

## 3. Function Calling 到底是什么

Function Calling 也叫 Tool Calling。

它不是让模型直接执行你的 Python 代码，而是让模型输出一份结构化的“工具调用建议”。

例如，用户问：

~~~text
现在上海几点？
~~~

模型看到可用工具后，可能返回：

~~~json
{
  "type": "function_call",
  "name": "get_current_time",
  "arguments": {
    "timezone": "Asia/Shanghai"
  }
}
~~~

接下来真正发生的事情是：

1. 模型选择 get_current_time。
2. 模型生成参数 Asia/Shanghai。
3. Python 程序读取并验证参数。
4. Python 程序调用 datetime 和 zoneinfo。
5. Python 程序把结果交回模型。
6. 模型把结构化结果整理成人类可读答案。

最重要的一句话：

> 模型只提出调用请求，应用程序决定是否执行并负责真正执行。

---

## 4. 工具调用的五步流程

官方 Function Calling 的核心流程可以记成五步：

~~~text
1. 把用户问题和工具描述发给模型
2. 模型返回工具调用请求
3. 应用执行真实函数
4. 应用把工具结果发回模型
5. 模型返回最终答案，或者继续请求工具
~~~

用程序表示：

~~~text
request(tools + user_input)
        ↓
response.output
        ↓
发现 function_call？
   ├── 否 → 返回 output_text
   └── 是
        ↓
解析 arguments
        ↓
验证并执行 Python 函数
        ↓
追加 function_call_output
        ↓
再次 request
~~~

这已经是一个最小 Agent 的核心结构。

---

## 5. Function、Tool 和 Agent 的关系

### Function

真实存在的 Python 函数，例如：

~~~python
def get_current_time(timezone: str) -> dict:
    ...
~~~

### Tool Definition

告诉模型这个函数叫什么、什么时候使用、参数是什么。

~~~python
{
    "type": "function",
    "name": "get_current_time",
    "description": "获取指定 IANA 时区的当前时间。",
    "parameters": {...},
    "strict": True,
}
~~~

### Tool Call

模型生成的一次调用请求，包括：

- 工具名称；
- JSON 参数；
- call_id。

### Tool Output

应用执行函数后返回给模型的结果。

### Agent

负责重复执行下面过程的程序：

~~~text
模型决策 → 工具执行 → 结果观察 → 模型继续决策
~~~

---

## 6. JSON Schema：模型和函数之间的合同

工具参数通常使用 JSON Schema 描述。

一个时间工具：

~~~python
{
    "type": "function",
    "name": "get_current_time",
    "description": "获取指定 IANA 时区的当前时间。涉及当前时间时使用。",
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
}
~~~

### 每个字段的作用

| 字段 | 作用 |
| --- | --- |
| type | 工具类型，函数工具固定为 function |
| name | 工具唯一名称 |
| description | 告诉模型什么时候以及如何使用 |
| parameters | 参数 JSON Schema |
| properties | 所有允许出现的参数 |
| required | 必须提供的参数 |
| additionalProperties | 是否允许未声明参数 |
| strict | 是否要求模型严格遵守 Schema |

### 严格模式规则

当 strict 为 True 时：

- object 应设置 additionalProperties 为 False；
- properties 中的字段都应出现在 required；
- 可选字段可以使用包含 null 的类型表达。

当前 qwen3.8-flash 和阿里云兼容地址已经实测可以接受上面的严格模式。

### 好的 description

不要只写：

~~~text
获取时间
~~~

更好的写法：

~~~text
获取指定 IANA 时区的当前日期和时间。
当用户询问“现在几点”“今天日期”或需要实时判断时使用。
不要根据常识猜测当前时间。
~~~

工具描述会影响模型是否选择工具。

---

## 7. 第一个安全工具：计算器

不要使用 eval 执行模型生成的字符串。

危险示例：

~~~python
def calculator(expression: str):
    return eval(expression)
~~~

模型输出属于外部输入。eval 可能执行任意 Python 代码，因此不适合直接处理模型参数。

使用操作白名单：

~~~python
import operator
from typing import Any


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

    result = OPERATIONS[operation](a, b)
    return {
        "ok": True,
        "operation": operation,
        "a": a,
        "b": b,
        "result": result,
    }
~~~

对应的工具 Schema：

~~~python
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
}
~~~

---

## 8. 第二个安全工具：当前时间

使用 Python 标准库：

~~~python
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


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
~~~

为什么返回 dict 而不是一句话？

- 字段含义清晰；
- 模型更容易理解；
- 日志更容易分析；
- 以后可以增加更多字段；
- 成功和失败可以使用统一结构。

推荐所有工具都返回：

~~~json
{
  "ok": true,
  "data": {}
}
~~~

或者：

~~~json
{
  "ok": false,
  "error": "错误原因"
}
~~~

---

## 9. 工具注册表

不要写很多层 if/elif：

~~~python
if name == "calculator":
    ...
elif name == "get_current_time":
    ...
~~~

使用工具注册表：

~~~python
TOOL_HANDLERS = {
    "calculator": calculator,
    "get_current_time": get_current_time,
}
~~~

执行工具：

~~~python
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
~~~

这里要理解两点：

1. 工具失败不一定要立刻让整个 Agent 崩溃。
2. 可以把失败结果交回模型，让模型解释错误或尝试其他方案。

生产环境不要直接把内部堆栈、数据库信息或敏感路径返回给模型和用户。

---

## 10. response.output 里有什么

普通回答可能包含 message：

~~~text
response.output
└── item.type == "message"
~~~

工具调用可能包含 function_call：

~~~text
response.output
└── item.type == "function_call"
    ├── item.name
    ├── item.arguments
    └── item.call_id
~~~

筛选工具调用：

~~~python
tool_calls = [
    item
    for item in response.output
    if item.type == "function_call"
]
~~~

如果 tool_calls 为空，通常说明模型已经给出了最终文本。

---

## 11. 为什么必须保留 call_id

一次响应中可能出现多个工具调用。

call_id 用来建立对应关系：

~~~text
function_call(call_id=call_123)
             ↓
function_call_output(call_id=call_123)
~~~

回传结果：

~~~python
{
    "type": "function_call_output",
    "call_id": tool_call.call_id,
    "output": tool_result,
}
~~~

不要自己创建新的 call_id，也不要使用 response.id 代替 call_id。

---

## 12. Agent Loop 的核心代码

~~~python
def run_agent(question: str) -> str:
    input_items = [
        {
            "role": "user",
            "content": question,
        }
    ]

    for step in range(1, MAX_STEPS + 1):
        response = client.responses.create(
            model=MODEL,
            instructions=AGENT_INSTRUCTIONS,
            input=input_items,
            tools=TOOLS,
        )

        input_items += response.output

        tool_calls = [
            item
            for item in response.output
            if item.type == "function_call"
        ]

        if not tool_calls:
            return response.output_text

        for tool_call in tool_calls:
            tool_result = execute_tool(tool_call)

            input_items.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": tool_result,
                }
            )

    raise RuntimeError(f"超过最大执行步数：{MAX_STEPS}")
~~~

### 为什么先追加 response.output

模型返回的内容不仅可能包含 function_call，也可能包含其他上下文信息。

把 response.output 保留下来，再附加 function_call_output，可以让下一次模型请求理解：

- 它刚才决定调用了什么；
- 参数是什么；
- 应用返回了什么；
- 下一步应该继续调用工具还是回答用户。

### 为什么必须设置 MAX_STEPS

模型可能：

- 重复调用同一个工具；
- 工具持续报错；
- 在多个工具之间来回切换；
- 永远不生成最终答案。

没有停止条件的 Agent 可能无限消耗 Token 和外部资源。

---

## 13. 建议的 Agent Instructions

~~~python
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
~~~

好的 Agent Prompt 应明确：

- 何时必须调用工具；
- 何时禁止猜测；
- 工具失败怎么办；
- 如何控制调用数量；
- 最终回答格式。

---

## 14. 完整参考实现

先自己完成，再展开参考实现。

<details>
<summary>展开 mini_agent.py 参考代码</summary>

~~~python
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
    "https://your-model-endpoint.example/"
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
        f"total={response.usage.total_tokens}"
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
~~~

</details>

---

## 15. 如何运行今日项目

建议创建：

~~~text
llm-agent-learning/
├── .venv/
├── pyproject.toml
├── uv.lock
├── aliyun_api_key
├── day01/
│   ├── DAY01.md
│   └── hello_llm.py
└── day02/
    ├── DAY02.md
    └── mini_agent.py
~~~

终端运行：

~~~bash
cd /path/to/llm-agent-learning  # 替换为你实际克隆到的目录
uv run python day02/mini_agent.py "现在上海几点？"
~~~

计算测试：

~~~bash
uv run python day02/mini_agent.py "请精确计算 125 乘以 48"
~~~

普通问题测试：

~~~bash
uv run python day02/mini_agent.py "用一句话解释 Python 装饰器"
~~~

第三个问题不需要实时数据或精确计算，模型应该直接回答，不应该调用工具。

---

## 16. 观察 Agent 的执行轨迹

运行：

~~~text
现在上海几点？
~~~

预期日志类似：

~~~text
[step 1] 请求模型
[tool] name=get_current_time arguments={"timezone":"Asia/Shanghai"}
[tool result] {"ok":true,"timezone":"Asia/Shanghai",...}

[step 2] 请求模型
--- 最终回答 ---
上海当前时间是……
~~~

这就是最小的 Agent Trace。

记录下面的信息：

| 字段 | 目的 |
| --- | --- |
| step | 判断循环执行了几轮 |
| response_id | 排查 API 请求 |
| tool name | 模型选择了哪个工具 |
| arguments | 模型生成了什么参数 |
| result | 应用执行结果 |
| input/output tokens | 观察每一轮成本 |
| elapsed time | 分析工具与模型延迟 |

注意：日志中不能输出 API Key、密码、Cookie 或完整用户隐私数据。

---

## 17. 必做实验

### 实验 1：需要工具

~~~text
现在东京几点？
~~~

预期：

- 模型调用 get_current_time；
- timezone 应为 Asia/Tokyo；
- 最终答案使用工具返回值。

### 实验 2：不需要工具

~~~text
解释什么是 Python 字典。
~~~

预期：

- 不调用任何工具；
- 第一步直接返回文本。

### 实验 3：精确计算

~~~text
请精确计算 12345 乘以 678。
~~~

预期：

- 调用 calculator；
- operation 为 multiply；
- a 和 b 正确；
- 最终结果来自工具。

### 实验 4：工具报错

~~~text
计算 10 除以 0。
~~~

预期：

- calculator 返回 ok=false；
- Agent 不崩溃；
- 最终回答明确说明除数不能为 0。

### 实验 5：非法时区

~~~text
请查询火星基地时区 Mars/Base 的当前时间。
~~~

预期：

- 工具返回未知时区；
- Agent 不编造时间；
- 最终回答解释无法查询。

### 实验 6：多个任务

~~~text
先计算 125 乘以 48，再告诉我上海当前时间。
~~~

观察：

- 模型是否一次请求多个工具；
- 是否分多轮调用；
- 两个工具结果是否都进入最终回答；
- 总 Token 是否明显增加。

---

## 18. 工具安全的六条底线

### 1. 永远验证参数

即使使用 strict，也要在应用层验证：

- 字符串长度；
- 数值范围；
- 枚举值；
- 文件路径；
- 用户权限；
- 资源是否存在。

### 2. 使用允许列表

计算器只允许四种操作，不允许任意代码。

文件工具应限制在指定工作目录，不能接受任意绝对路径。

### 3. 写操作需要额外确认

下面这些工具不能仅凭模型判断直接执行：

- 删除文件；
- 发送邮件或消息；
- 支付和退款；
- 修改数据库；
- 发布内容；
- 执行系统命令。

### 4. 设置超时

网络工具、数据库和外部进程都需要超时。

### 5. 限制循环次数

MAX_STEPS 是最基础的资源保护。

### 6. 记录审计信息

至少记录工具名、脱敏参数、结果状态和耗时。

---

## 19. 最容易出现的十个 Bug

### Bug 1：以为传入 tools 后 SDK 会自动执行函数

SDK 只把工具描述发给模型。执行函数是应用的责任。

### Bug 2：只读取 output_text

发生工具调用时，output_text 可能为空。必须检查 response.output。

### Bug 3：忘记 json.loads

tool_call.arguments 通常是 JSON 字符串，不是 Python dict。

### Bug 4：忘记保留 response.output

下一轮模型无法完整理解自己刚才的调用过程。

### Bug 5：call_id 使用错误

function_call_output 必须引用对应工具调用的 call_id。

### Bug 6：output 不是字符串

最稳妥的方式是使用 json.dumps 将工具结果转成 JSON 字符串。

### Bug 7：工具异常导致整个程序退出

把可恢复错误转换为 ok=false 的工具结果。

### Bug 8：使用 eval

不要执行模型生成的任意表达式或代码。

### Bug 9：没有最大步数

Agent 可能无限循环。

### Bug 10：工具描述模糊

模型可能不调用工具，或调用错误工具。description 是决策上下文的一部分。

---

## 20. 调试清单

模型没有调用工具时，依次检查：

- [ ] 模型是否支持 Function Calling
- [ ] tools 是否真的传入 responses.create
- [ ] name 是否清晰且唯一
- [ ] description 是否写明使用场景
- [ ] parameters 是否是合法 JSON Schema
- [ ] instructions 是否要求实时信息必须使用工具
- [ ] 用户问题是否真的需要工具

工具执行后模型没有最终回答时，检查：

- [ ] 是否把 response.output 加入 input_items
- [ ] 是否追加 function_call_output
- [ ] call_id 是否来自原工具调用
- [ ] output 是否为字符串
- [ ] 第二次请求是否继续传入 tools
- [ ] 是否出现新的 function_call
- [ ] 是否超过 MAX_STEPS

出现 HTTP 400 时，检查：

- [ ] strict 模式下是否设置 additionalProperties=False
- [ ] properties 是否全部进入 required
- [ ] 阿里云兼容接口是否支持该参数
- [ ] 模型名是否正确

---

## 21. 今日小项目：工具型命令行 Agent

### 最低要求

- [ ] 文件名为 mini_agent.py
- [ ] 提供 calculator 工具
- [ ] 提供 get_current_time 工具
- [ ] 使用严格 JSON Schema
- [ ] 使用工具注册表
- [ ] 能解析 function_call
- [ ] 能回传 function_call_output
- [ ] 最多执行 5 轮
- [ ] 工具参数和错误都有处理
- [ ] 显示工具调用轨迹
- [ ] 显示每轮 Token 用量
- [ ] 普通问题不会乱用工具

### 加分要求

- [ ] 记录每一步耗时
- [ ] 把 Trace 保存成 JSONL
- [ ] 给每次运行生成 run_id
- [ ] 为 calculator 写单元测试
- [ ] 增加人民币金额格式化工具
- [ ] 支持 --debug 开关控制日志

### 不要做

- 不要安装 LangChain；
- 不要连接数据库；
- 不要增加十几个工具；
- 不要让工具执行任意 shell；
- 不要把 API Key 写进 mini_agent.py。

---

## 22. 建议的单元测试

工具函数不依赖模型，可以直接测试。

~~~python
def test_calculator_multiply():
    result = calculator("multiply", 12, 3)
    assert result["ok"] is True
    assert result["result"] == 36


def test_calculator_divide_by_zero():
    result = calculator("divide", 10, 0)
    assert result["ok"] is False


def test_get_current_time_invalid_timezone():
    result = get_current_time("Mars/Base")
    assert result["ok"] is False
~~~

为什么工具函数要单独测试？

- 模型输出具有一定不确定性；
- Python 函数应该是确定的；
- 出错时可以判断是模型决策错误还是工具实现错误；
- 单元测试不消耗模型 Token。

---

## 23. 实验记录模板

创建 experiment-notes.md：

| 用例 | 预期工具 | 实际工具 | 参数正确 | 轮数 | 总 Token | 最终答案正确 |
| --- | --- | --- | --- | ---: | ---: | --- |
| 上海时间 | get_current_time |  |  |  |  |  |
| 精确乘法 | calculator |  |  |  |  |  |
| 普通解释 | 无 |  |  |  |  |  |
| 除以零 | calculator |  |  |  |  |  |
| 多工具任务 | 两个工具 |  |  |  |  |  |

这张表是最简单的 Agent Eval。

不要只测试“看起来能工作”的用例，也要测试：

- 工具错误；
- 无需工具；
- 多工具；
- 参数边界；
- 提示注入；
- 超过最大步数。

---

## 24. 今日自测

先自己回答，再看答案。

1. Function Calling 是否会自动执行 Python 函数？
2. tools 参数中放的是函数本身还是函数描述？
3. tool_call.arguments 通常是什么类型？
4. 为什么要使用 JSON Schema？
5. strict=True 时应满足哪两个主要条件？
6. call_id 的作用是什么？
7. 为什么要把 response.output 加到下一轮输入？
8. function_call_output 的 output 应该是什么类型？
9. 为什么不能直接 eval 模型参数？
10. Agent Loop 为什么必须有 MAX_STEPS？
11. 工具失败时一定要让 Agent 退出吗？
12. 如何判断模型已经生成最终答案？

<details>
<summary>参考答案</summary>

1. 不会，应用程序负责执行。
2. 放工具的名称、描述和参数 Schema。
3. JSON 字符串。
4. 让模型按约定生成结构化参数，并方便应用验证。
5. additionalProperties=False，且 properties 字段全部出现在 required。
6. 把工具结果与具体工具调用对应起来。
7. 保留模型刚才的决策和上下文，尤其是工具调用信息。
8. 通常使用字符串，推荐 JSON 字符串。
9. 模型输出是不可信外部输入，eval 可能执行任意代码。
10. 防止无限循环和无限资源消耗。
11. 不一定；可恢复错误可以转成工具结果交回模型。
12. response.output 中没有 function_call，并且 response.output_text 非空。

</details>

---

## 25. 今日完成标准

做到下面这些，Day 02 才算完成：

- [ ] 能画出工具调用的五步流程
- [ ] 能解释模型与应用各自的职责
- [ ] 能独立写一个严格 JSON Schema
- [ ] 能安全实现 calculator
- [ ] 能实现 get_current_time
- [ ] 能识别 function_call
- [ ] 能解析 arguments
- [ ] 能正确回传 call_id
- [ ] 能实现最多 5 轮的 Agent Loop
- [ ] 完成 6 个必做实验
- [ ] 至少写 3 个工具单元测试
- [ ] 能解释为什么当前程序已经是微型 Agent

---

## 26. 明天学习什么

Day 03 将先补齐“Agent 所需的 Python 工程基础”：

- 使用 dataclass 表达内部数据；
- 使用类型标注和 Protocol 定义依赖边界；
- 把 SDK、Agent Loop、工具与终端交互拆开；
- 使用依赖注入构造不联网的 Fake Client；
- 使用 pytest、ruff 和 mypy 建立工程质量基线；
- 把当前脚本整理成可测试的 Agent Core。

完成工程化拆分后，Day 04 再进入多轮状态、上下文管理与结构化输出。

---

## 27. 官方资料

建议按下面顺序阅读：

1. [OpenAI Function Calling](https://developers.openai.com/api/docs/guides/function-calling)
2. [OpenAI Responses API](https://developers.openai.com/api/docs/guides/migrate-to-responses)
3. [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)

当前项目使用阿里云 OpenAI 兼容服务：

- 模型名继续使用 qwen3.8-flash；
- base_url 和 API Key 继续使用现有本地配置；
- 本文的严格工具 Schema 和基本 Agent Loop 已在当前兼容地址上实测成功；
- 如果后续遇到兼容差异，应以服务商实际支持的参数为准。
