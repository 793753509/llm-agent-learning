# Day 03：对照示例学习 Python，把 Day 02 拆成文件

> 今日主题：看懂 Day 02 的 Python 写法，并把脚本拆成可测试的模块
>
> 建议安排：先读主线，再按需补语法；Python 基础较弱时可以拆成 2～3 次学习
>
> 是否调用真实模型：运行助手时沿用 Day 02 的真实模型；运行测试时不需要
>
> 最终产物：一个不联网也能测试的 Agent Core

当前实现是 **Day 02 的教学拆分版**：先读 [文件对应关系与运行方式](README.md)，再对照本教材理解代码。
在项目根目录执行 `uv run python -m day03.mini_agent "计算 6 × 7"`，会调用你原来配置的阿里云模型。
只想离线学习时执行 `uv run pytest -q -s day03/tests/test_runner.py`。原有 `playground.py` 保持不变。
本次只要求看懂拆分和主流程；JSONL、异步等章节作为独立语法练习，不加入这个小助手。

### 本文代码怎么使用

- **完整离线示例**：包含所需 import，可在项目根目录的 Python 会话运行；也可逐段放到练习文件，用项目根目录作为导入路径运行。
- **源码节选**：用于对照指定的 `.py` 文件，不必单独复制运行；可能省略周围的变量定义。
- **错误示例**：故意展示错误，不要覆盖到项目源码里。
- 普通语法示例在同一小节内按顺序执行，不要把整篇教程拼成一个 Python 文件。
- 只有明确标注“真实运行”的命令会调用 API。Fake 示例不读取 Key，不请求模型。

Day 02 出现过这些写法；下面是**源码节选**，用来认出语法，不是一个完整程序：

```python
input_items.append({...})
input_items += response.output
handler = TOOL_HANDLERS.get(tool_call.name)
result = handler(**arguments)
if api_key := os.getenv(variable_name):
    return api_key
```

如果这些代码只能“照着运行”，还不能自己解释和修改，那么现在直接讲 `Protocol`、依赖注入和测试确实太快了。

因此 Day 03 分成两部分：

1. 先补齐写 Agent 必须掌握的 Python 语法；
2. 再把这些语法用于一个小型工程重构。

今天不要求记住所有语法。完成后，你应该能回答两个问题：

- 这一行 Python 代码对内存中的数据做了什么？
- 为什么要把代码放在这个文件和这个函数里？

---

## 1. 今天只围绕一个主线

目标不是再造一个 Agent 框架，而是看懂当前这些文件如何协作：

```text
mini_agent.py：读取问题、创建客户端
    ↓
runner.py：循环请求、执行工具、回传结果
    ├─ client.py：调用 SDK，得到 ModelReply
    └─ tools.py：执行计算器或时间工具
```

建议阅读顺序：

1. 先看第 2 节的运行方式，再看第 21 节，认出 Day 02 的代码分别搬到了哪里。
2. 看第 11 节的四个数据类：`ToolCall`、`TokenUsage`、`ModelReply`、`AgentResult`。
3. 看第 15～17 节，理解 `run_agent(..., client=..., tools=...)` 和 Fake。
4. 跟着第 22 节的完整离线示例，观察两轮输入列表和 Token 累计。
5. 看第 18、23、25 节，运行现有测试；不要求再扩展测试框架。

看不懂语法时再回查：

| 卡在哪里 | 去看哪里 |
| --- | --- |
| 列表为什么变了、`append` / `+=` | 第 4～5 节 |
| 字典怎么保存函数、`**arguments` | 第 6～7 节 |
| 字符串还是字典、类型标注 | 第 8～9 节 |
| `self`、构造函数、默认列表 | 第 10～11 节 |
| 导入路径、`main()`、异常 | 第 12～13 节 |
| Key 文件为什么用 `parents[2]` | 第 14 节的 Path 部分 |

JSONL、`*args/**kwargs`、set、异步以及面试拓展都可以后看。
第 20 节的 asyncio 是独立练习，**当前 `run_agent()` 和模型客户端仍然是同步的**。

---

## 2. 开始前确认环境

所有命令都在项目根目录执行：

```bash
cd /path/to/llm-agent-learning  # 替换为你实际克隆到的目录
```

确认 Python：

```bash
uv run python --version
```

确认正在使用项目虚拟环境：

```bash
uv run python -c "import sys; print(sys.executable)"
```

输出路径应该包含：

```text
llm-agent-learning/.venv/bin/python
```

在 PyCharm 中继续使用：

```text
/path/to/llm-agent-learning/.venv/bin/python
```

你已经有一个练习文件，可以继续使用，不需要重新创建：

```text
day03/playground.py
```

运行方式：

```bash
uv run python day03/playground.py
```

建议自己敲代码。每段代码运行前，先猜输出是什么。

如果练习文件中导入了 `day03.agent_core`，在根目录用模块方式运行：

```bash
uv run python -m day03.playground
```

当前助手的正式入口不是 `runner.py`，而是 `mini_agent.py`：

```bash
# 真实运行：沿用阿里云配置，可能消耗模型额度
uv run python -m day03.mini_agent "计算 6 × 7"
```

只想观察流程时先运行这个，不会调用 API：

```bash
uv run pytest -q -s day03/tests/test_runner.py
```

PyCharm 中，助手的运行目标使用 **Module name**：`day03.mini_agent`；
Working directory 填上面的项目根目录，解释器使用根目录的 `.venv/bin/python`。
`-m` 后写的是模块名，不带 `.py` 后缀。

---

## 3. Python 和 Go 的最小对照

你已经接触过 Go，可以先用下面的对应关系建立方向感。它们只是类比，并不完全等价。

| Python | 可以粗略类比 Go | 主要区别 |
| --- | --- | --- |
| `.py` 文件 | 一个源码文件 | Python 文件被 import 时会执行顶层代码 |
| package 目录 | Go package | Python 常用目录和 `__init__.py` 组织包 |
| `list[T]` | `[]T` | 运行时不强制所有元素类型一致 |
| `dict[K, V]` | `map[K]V` | Python 字典保持插入顺序 |
| `set[T]` | `map[T]struct{}` 的用途 | 只保存不重复元素 |
| `None` | `nil` 的部分用途 | `None` 是一个具体的单例对象 |
| `class` | `struct` 加方法 | Python 类还负责构造和运行时行为 |
| `@dataclass` | 常用数据 `struct` | 自动生成初始化、比较和显示方法 |
| `Protocol` | `interface` | 默认主要由类型检查器检查 |
| `Exception` | `error` 的部分用途 | Python 通过抛出和捕获异常传递失败 |
| type hint | 参数和返回类型 | 默认不影响运行，只帮助人和检查工具 |
| `async` / `await` | goroutine 相关并发能力 | asyncio 通常是单线程事件循环，不等同于 goroutine |

最重要的区别之一：

> Go 的类型主要由编译器强制；Python 的类型标注默认只是提示，程序运行时仍可能收到错误类型。

---

## 4. 变量保存的是对象引用

先看一个整数：

```python
a = 10
b = a
a = 20

print(a)
print(b)
```

输出：

```text
20
10
```

再看一个列表：

```python
a = [1, 2]
b = a
a.append(3)

print(a)
print(b)
```

输出：

```text
[1, 2, 3]
[1, 2, 3]
```

原因：

- `a = 20` 是让变量 `a` 改为指向另一个整数对象；
- `a.append(3)` 是修改 `a` 和 `b` 共同指向的列表对象。

可以用 `id()` 观察两个变量是否指向同一个对象：

```python
a = [1, 2]
b = a
print(id(a) == id(b))
```

输出是 `True`。

如果希望得到一个新的列表：

```python
a = [1, 2]
b = a.copy()
a.append(3)

print(a)
print(b)
```

输出：

```text
[1, 2, 3]
[1, 2]
```

这对 Agent 很重要，因为 `input_items` 就是一个不断被原地修改的列表。

### `None` 是什么

`None` 表示“没有值”：

```python
answer = None

if answer is None:
    print("还没有答案")
```

判断 `None` 推荐使用：

```python
value is None
value is not None
```

下面这些值在 `if` 中会被当作 `False`：

```python
False
None
0
""
[]
{}
set()
```

所以：

```python
question = ""

if not question:
    print("问题不能为空")
```

可以检查字符串是不是空的。但 `0` 也是假值；如果 `0` 是合法业务值，应明确判断 `value is None`。

### 本节练习

先猜，再运行：

```python
history = []
copy_history = history
history.append("user message")

print(copy_history)
print(history is copy_history)
```

你应该能解释为什么输出是：

```text
['user message']
True
```

---

## 5. list：Agent 的步骤记录

Python 的 `list` 是有顺序、可修改的容器，可以粗略类比 Go 的 slice。

### 创建、读取和修改

```python
messages = ["第一条", "第二条"]

print(messages[0])
print(messages[-1])
print(len(messages))

messages[0] = "修改后的第一条"
print(messages)
```

索引从 `0` 开始，`-1` 表示最后一个元素。

### `append()`：追加一个元素

```python
items = ["user"]
items.append("function_call")
print(items)
```

输出：

```text
['user', 'function_call']
```

如果追加一个字典，整个字典只算一个元素：

```python
items = ["user"]
items.append(
    {
        "type": "function_call_output",
        "output": "42",
    }
)

print(len(items))
print(items[-1])
```

输出：

```text
2
{'type': 'function_call_output', 'output': '42'}
```

`append()` 原地修改列表，并返回 `None`：

```python
items = []
result = items.append("hello")

print(items)
print(result)
```

输出：

```text
['hello']
None
```

因此不要写：

```python
items = items.append("hello")
```

这会让 `items` 变成 `None`。

### `extend()` 和列表 `+=`：追加多个元素

```python
items = ["user"]
new_items = ["reasoning", "function_call"]

items.extend(new_items)
print(items)
```

输出：

```text
['user', 'reasoning', 'function_call']
```

在当前场景中：

```python
items += new_items
```

可以先理解为：

```python
items.extend(new_items)
```

### `append()` 和 `+=` 的区别

```python
items = ["user"]
output = ["reasoning", "function_call"]

items.append(output)
print(items)
```

输出：

```text
['user', ['reasoning', 'function_call']]
```

列表长度是 `2`，第二个元素又是一个列表。

而：

```python
items = ["user"]
items += output
print(items)
```

输出：

```text
['user', 'reasoning', 'function_call']
```

列表长度是 `3`。

| 写法 | 含义 |
| --- | --- |
| `items.append(x)` | 把 `x` 整体作为一个新元素 |
| `items.extend(xs)` | 把 `xs` 中的每个元素依次加入 |
| `items += xs` | 在当前列表场景中接近 `extend` |

### 对照 Day 02 和当前 Day 03

这两行的作用相同，只是变量来自不同地方（源码节选）：

```python
# Day 02：直接使用 SDK 回复
input_items += response.output

# Day 03：client.py 已把 SDK 回复包装成 ModelReply
input_items += reply.output_items
```

注意：Day 03 的 `tool_result` 是字典，追加历史前需要 `json.dumps()`。
下面是一个**完整离线示例**，用字典模拟一项模型工具请求：

<!-- runnable: history_growth -->
```python
import json

from day03.agent_core.models import ModelReply, ToolCall
from day03.agent_core.tools import execute_tool

call = ToolCall("call_123", "calculator", {"operation": "multiply", "a": 6, "b": 7})
reply = ModelReply(
    tool_calls=[call],
    output_items=[
        {
            "type": "function_call",
            "call_id": call.call_id,
            "name": call.name,
            "arguments": json.dumps(call.arguments),
        }
    ],
)

input_items = [{"role": "user", "content": "计算 6 × 7"}]
print(len(input_items))  # 1

input_items += reply.output_items
print(len(input_items))  # 2

tool_result = execute_tool(call)
input_items.append(
    {
        "type": "function_call_output",
        "call_id": call.call_id,
        "output": json.dumps(tool_result, ensure_ascii=False),
    }
)
print(len(input_items))  # 3
print(json.loads(input_items[-1]["output"])["result"])  # 42
```

三项依次是：用户问题、模型的工具请求、Python 的工具结果。
这里没有模拟 reasoning；真实模型如果还返回 reasoning 项，同样场景可能是 4 项而不是 3 项。
因此“长度是 3”是这个例子的条件，不是 Agent 的固定规则。

### 列表推导式

Day 02 有：

```python
tool_calls = [
    item
    for item in response.output
    if item.type == "function_call"
]
```

它等价于：

```python
tool_calls = []

for item in response.output:
    if item.type == "function_call":
        tool_calls.append(item)
```

这是 Day 02 的写法。当前 [client.py](agent_core/client.py) 用普通 `for` 循环筛选，并将每个 SDK 工具调用转换成 `ToolCall` 数据类；不是直接把 SDK 对象放进 `tool_calls`。初学阶段先读普通循环即可。

### 本节练习

1. 创建一个只包含用户消息的 `input_items`；
2. 使用 `+=` 加入两个模拟模型输出；
3. 使用 `append()` 加入一个工具结果；
4. 每一步打印长度和内容。

最终长度应该是 `4`。

---

## 6. dict 和 set

Python 的 `dict` 可以粗略类比 Go 的 `map`。

### 创建和读取 dict

```python
tool_data = {
    "name": "calculator",
    "arguments": {"operation": "multiply", "a": 6, "b": 7},
}

print(tool_data["name"])
print(tool_data["arguments"]["a"])
```

这里的 `tool_data` 是普通字典，所以用方括号取值。项目里的 `ToolCall` 是数据类，使用 `call.name` 和 `call.arguments`；不要把两种取值方式混用。

### `[]` 和 `.get()` 的区别

```python
handlers = {"calculator": "some function"}
```

使用不存在的 key：

```python
handlers["weather"]
```

会抛出 `KeyError`。而：

```python
handler = handlers.get("weather")
print(handler)
```

输出 `None`。也可以指定默认值：

```python
handler = handlers.get("weather", "unknown")
```

### 字典为什么能保存函数

Python 中函数也是对象，因此字典的 value 可以是函数。

```python
def add(a: float, b: float) -> float:
    return a + b


def multiply(a: float, b: float) -> float:
    return a * b


operations = {
    "add": add,
    "multiply": multiply,
}
```

注意这里写的是：

```python
"add": add
```

不是：

```python
"add": add()
```

`add` 表示函数对象本身；`add()` 表示立即调用函数。

下面两种写法等价：

```python
result = operations["multiply"](6, 7)
```

```python
selected_function = operations["multiply"]
result = selected_function(6, 7)
```

执行过程：

```text
operations["multiply"]
        ↓
取得 multiply 函数对象
        ↓
multiply(6, 7)
        ↓
42
```

### set：只关心是否存在

```python
unique_tools = {"calculator", "calculator", "get_current_time"}
print(unique_tools)
```

集合不会保存重复元素，适合去重和保存允许列表：

```python
allowed_tools = {"calculator", "get_current_time"}

if "delete_database" not in allowed_tools:
    print("不允许调用")
```

空集合必须写 `set()`，因为 `{}` 表示空字典。

这是 set 的独立语法示例。当前 `AgentResult.used_tools` **是列表，不是集合**：保留调用顺序，也保留重复工具名和失败尝试。上面的 `allowed_tools` 也不是当前 runner 中的权限检查。

---

## 7. 函数、参数和参数解包

先看当前 [tools.py](agent_core/tools.py) 中函数的签名（这里只看签名，不是新实现）：

```python
from typing import Any

def calculator(operation: str, a: float, b: float) -> dict[str, Any]:
    ...  # 函数体请对照 tools.py，不要用这里的省略号覆盖实现
```

| 部分 | 含义 |
| --- | --- |
| `def` | 定义函数 |
| `calculator` | 函数名 |
| `operation, a, b` | 参数 |
| `: str`、`: float` | 参数类型标注 |
| `-> dict[str, Any]` | 返回字典，key 是字符串，value 类型可以不同 |
| `return` | 把结果交给调用方 |

要运行计算，请**导入实际函数**，不要自己另写一个同名函数覆盖它。

**完整离线示例：**

<!-- runnable: calculator_calls -->
```python
from day03.agent_core.tools import calculator

# 位置参数：按顺序传入
first = calculator("add", 6, 7)

# 关键字参数：按参数名传入
second = calculator(operation="multiply", a=6, b=7)

print(first["result"])   # 13
print(second["result"])  # 42
```

实际函数会通过 `OPERATIONS[operation](a, b)` 选择加、减、乘、除，不是无论传什么都执行 `a + b`。

### `**arguments` 是什么

假设模型参数被解析成字典：

```python
arguments = {
    "operation": "multiply",
    "a": 6,
    "b": 7,
}
```

下面两种写法等价：

```python
calculator(
    operation=arguments["operation"],
    a=arguments["a"],
    b=arguments["b"],
)
```

```python
calculator(**arguments)
```

`**` 把字典拆成关键字参数：

```text
{"operation": "multiply", "a": 6, "b": 7}
                       ↓
operation="multiply", a=6, b=7
```

对应 Day 02 与 Day 03 的写法（源码节选）：

```python
# Day 02：execute_tool 内先解析 JSON，再执行
result = handler(**arguments)

# Day 03：client.py 已完成解析，直接展开字典
return handler(**tool_call.arguments)
```

表示：

1. `handler` 是从字典中取出的函数；
2. `arguments` 是模型参数字典；
3. `**arguments` 把字典展开；
4. 最后真正执行函数。

### `*args` 和 `**kwargs`（选读）

先只记住：

- `*args` 收集额外位置参数，得到 tuple；
- `**kwargs` 收集额外关键字参数，得到 dict。

```python
def show(*args, **kwargs):
    print(args)
    print(kwargs)


show(1, 2, name="calculator", enabled=True)
```

输出：

```text
(1, 2)
{'name': 'calculator', 'enabled': True}
```

### 默认参数陷阱

不要写：

```python
def add_event(event: str, events: list[str] = []) -> list[str]:
    events.append(event)
    return events
```

这个空列表只在定义函数时创建一次，后面的调用会共享它。

正确写法：

```python
def add_event(
    event: str,
    events: list[str] | None = None,
) -> list[str]:
    if events is None:
        events = []

    events.append(event)
    return events
```

### `:=` 海象运算符

Day 02 和当前 `config.py` 的 `load_api_key()` 中都有（函数内节选）：

```python
if api_key := os.getenv(variable_name):
    return api_key
```

接近于：

```python
api_key = os.getenv(variable_name)

if api_key:
    return api_key
```

它在判断的同时完成赋值。初学阶段完全可以先用展开后的写法。

### 本节练习

写出 `subtract(a, b)`，把它放进 `operations` 字典，然后使用参数字典和 `**` 调用，验证 `10 - 3 == 7`。

---

## 8. JSON 字符串和 Python dict 不一样

Python dict：

```python
arguments = {
    "operation": "multiply",
    "a": 6,
    "b": 7,
}
```

它可以使用 `arguments["a"]` 读取。

JSON 字符串：

```python
arguments_json = '{"operation": "multiply", "a": 6, "b": 7}'
```

它只是字符串，需要先解析：

```python
import json

arguments = json.loads(arguments_json)
print(arguments["a"])
```

记忆方向：

```text
JSON string --json.loads--> Python object
Python object --json.dumps--> JSON string
```

```python
text = '{"ok": true, "result": 42}'
data = json.loads(text)
new_text = json.dumps(data, ensure_ascii=False)

print(type(text))      # str
print(type(data))      # dict
print(type(new_text))  # str
```

JSON 和 Python 的部分拼写不同：

| JSON | Python |
| --- | --- |
| `true` | `True` |
| `false` | `False` |
| `null` | `None` |

不要使用 `eval()` 解析模型返回的字符串。`eval()` 会把字符串当 Python 代码执行，存在严重安全风险。

### 在当前示例中，哪里是字符串，哪里是字典？

| 位置 | 类型 | 接下来做什么 |
| --- | --- | --- |
| SDK 的 `item.arguments` | JSON 字符串 | `client.py` 用 `json.loads()` 解析 |
| 自己的 `ToolCall.arguments` | Python 字典 | `tools.py` 用 `**` 展开 |
| `execute_tool()` 的返回值 | Python 字典 | `runner.py` 用 `json.dumps()` 序列化 |
| 历史中 `function_call_output["output"]` | JSON 字符串 | 交给下一轮模型 |

只记住：**解析发生在 client，执行发生在 tools，序列化回传发生在 runner。**
同名的 `arguments` 在 SDK 对象和内部数据类上类型不同；不要在 Day 03 的工具函数里再次 `json.loads(tool_call.arguments)`。

---

## 9. 类型标注：给人和工具看的合同

最基本的类型标注：

```python
def greet(name: str) -> str:
    return f"你好，{name}"
```

它表达：`name` 预期是字符串，函数预期返回字符串。

但是 Python 默认不会在运行时阻止：

```python
greet(123)
```

类型标注主要帮助：

- 阅读代码的人；
- PyCharm 自动补全；
- mypy 等静态类型检查工具；
- 大规模重构。

### 常见容器类型

```python
names: list[str] = ["calculator", "get_current_time"]

usage_data: dict[str, int] = {
    "input_tokens": 10,
    "output_tokens": 5,
}

allowed_tools: set[str] = {"calculator"}
```

Python 3.10 支持这种写法。这里的 `usage_data` 只是字典语法练习；项目实际用 `TokenUsage` 数据类保存用量。

### 多种可能类型

```python
answer: str | None = None
```

表示 `answer` 可以是 `str`，也可以是 `None`。

### `Any` 是什么

```python
from typing import Any

data: dict[str, Any]
```

`Any` 表示 value 可能是任意类型，而且类型检查器基本不会继续检查它。

SDK 返回值和动态 JSON 难以立刻精确描述时可以使用 `Any`，但不要把整个项目都写成 `Any`，否则类型标注会失去意义。

### Callable：描述一个函数

```python
from collections.abc import Callable

Operation = Callable[[float, float], float]
```

它表示“接收两个 float，返回一个 float 的可调用对象”。

```python
operations: dict[str, Operation] = {
    "add": add,
    "multiply": multiply,
}
```

Agent 工具的参数和返回结构可能不同，可以暂时使用：

```python
from collections.abc import Callable
from typing import Any

ToolHandler = Callable[..., dict[str, Any]]
```

这里的 `...` 表示参数形式不固定。这两个类型别名是帮助理解的写法，源码没有定义 `Operation` 或 `ToolHandler` 名称，而是直接在 `OPERATIONS`、`TOOL_HANDLERS` 的类型标注里写 `Callable[...]`。

---

## 10. class：数据和行为放在一起

下面把 `TokenUsage` 的核心行为手写展开，帮助理解 `self` 和构造函数。
这是**语法对照**，不是要求新增一个同名类，也不要覆盖 `models.py`；项目实际使用下一节的 dataclass。

<!-- runnable: manual_usage -->
```python
class TokenUsage:
    def __init__(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


usage = TokenUsage(input_tokens=100, output_tokens=20)
print(usage.input_tokens)  # 100
print(usage.total_tokens)  # 120
```

### `self` 是什么

`self` 指向正在操作的实例。`self.input_tokens = input_tokens` 的左侧是实例属性，右侧是传入的参数：

```text
TokenUsage(input_tokens=100, output_tokens=20)
    ↓
Python 创建实例，调用 __init__
    ↓
self.input_tokens = 100
self.output_tokens = 20
```

普通 Python 类可以在 `__init__` 中直接给实例增加属性，不需要像 Go struct 那样提前声明字段。
dataclass 则会读取类中的字段标注，自动生成类似的初始化代码。

当前 API 的名字是 **`usage.total_tokens`**，没有 `usage.total()` 方法。
`@property` 的意思下一节展开。

Python class 可以先类比为“Go struct 字段 + 绑定的方法 + 构造逻辑”。
今天只用简单的数据类和小包装类，不需要复杂继承。

---

## 11. dataclass：少写重复的数据类代码

`TokenUsage` 主要用来保存数据，可以改成：

```python
from dataclasses import dataclass


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
```

使用：

```python
usage = TokenUsage(input_tokens=100, output_tokens=20)

print(usage)
print(usage.total_tokens)
```

`@dataclass` 会生成常用代码，例如：

- `__init__`：初始化字段；
- `__repr__`：方便打印；
- `__eq__`：方便比较实例。

### `@property`

它让一个方法对外表现得像只读字段：

```python
usage.total_tokens
```

这里不需要写括号。

### dataclass 的默认列表使用 `default_factory`

```python
from dataclasses import dataclass, field

from day03.agent_core.models import TokenUsage


@dataclass
class AgentResult:
    answer: str
    usage: TokenUsage
    used_tools: list[str] = field(default_factory=list)
```

不要写：

```python
used_tools: list[str] = []
```

`default_factory=list` 表示每次创建实例时调用一次 `list()`，让每个实例得到自己的空列表。

### 今日需要理解的四个数据类

```python
"""Day 03 的内部数据模型；导入本模块不会读取密钥或调用模型 API。"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """一次工具调用请求；arguments 是已经解析好的 Python 字典。"""

    call_id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class TokenUsage:
    """记录输入和输出 Token 数量。"""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """使用 usage.total_tokens 读取，每次都根据当前数值计算。"""
        return self.input_tokens + self.output_tokens


@dataclass
class ModelReply:
    """模型一轮回复；usage 也是每次创建一个新对象，不与其他回复共享。"""

    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: TokenUsage = field(default_factory=TokenUsage)
    # 保留 response.output 的完整内容，供下一轮原样回传（包含 reasoning 等项）。
    output_items: list[Any] = field(default_factory=list)


@dataclass
class AgentResult:
    """最终答案、累计 Token 和尝试调用的工具名称（含失败，不去重）。"""

    answer: str
    usage: TokenUsage
    # 与 tool_calls 一样，不让不同实例共享默认列表。
    used_tools: list[str] = field(default_factory=list)
```

| 类型 | 代表什么 |
| --- | --- |
| `ToolCall` | 模型请求调用一次工具 |
| `ModelReply` | 模型本轮返回的文本、工具调用和本轮 Token 用量 |
| `TokenUsage` | Token 统计 |
| `AgentResult` | Agent 最终返回给调用者的结果 |

上面与当前 [models.py](agent_core/models.py) 的字段一致，直接导入这些类使用即可。

**注意：`AgentResult` 没有 `model` 字段。** 模型名由 `config.py` 的 `MODEL` 提供，入口单独打印；最终答案读取 `result.answer`，而不是把 `result` 当字符串。

`ModelReply.usage` 是一轮的统计，`AgentResult.usage` 是所有轮次相加的统计。
`TokenUsage` 本身也是可变对象，因此同样使用 `default_factory` 为每条回复单独创建。

`output_items` 保存 SDK 的完整 `response.output`，下一轮原样回传；`tool_calls` 则是从中挑出的工具请求，
便于执行 Python 函数。它们各有用途，不是需要分别生成的两份模型回复。

**完整离线示例：**

<!-- runnable: dataclass_fields -->
```python
from day03.agent_core.models import AgentResult, ModelReply, TokenUsage

first = ModelReply()
second = ModelReply()
first.usage.input_tokens = 100
print(second.usage.input_tokens)  # 0：不是同一个 TokenUsage 对象

result = AgentResult(answer="42", usage=TokenUsage(100, 20))
print(result.answer)              # 42
print(result.usage.total_tokens)  # 120
print(result.used_tools)          # []
```

---

## 12. 模块、包和 import

一个 `.py` 文件就是一个 module：

```text
tools.py
models.py
runner.py
```

一个组织 Python module 的目录通常是 package：

```text
agent_core/
├── __init__.py
├── models.py
├── tools.py
└── runner.py
```

`__init__.py` 可以暂时留空。它明确告诉读者和工具：这是一个 Python 包。

### 看懂 import

```python
from day03.agent_core.models import AgentResult
```

可以从右向左读：

```text
从 models 模块导入 AgentResult
models 属于 agent_core 包
agent_core 位于 day03 包中
```

### import 会执行顶层代码

假设 `bad_module.py` 是：

```python
print("正在执行模块顶层代码")


def hello() -> None:
    print("hello")
```

另一个文件只写：

```python
import bad_module
```

运行后仍会打印“正在执行模块顶层代码”。import 不只是读取函数声明，模块顶层语句会执行。

### 为什么不应在 import 时创建 API 客户端

Day 02 当前有：

```python
client = OpenAI(
    api_key=load_api_key(),
    base_url=BASE_URL,
)
```

它位于模块顶层，所以：

```python
import day02.mini_agent
```

也会立刻读取 API Key 并创建客户端。后果包括：

- 只想测试 `calculator()`，却因为没有 Key 导入失败；
- 工具函数和 SDK 被绑在一起；
- Fake Client 不容易替换真实客户端；
- 模块行为难以预测。

当前 Day 03 已经把创建动作放到 [mini_agent.py](mini_agent.py) 的 `main()` 里面。
下面是函数内部的**源码节选**；变量和 import 见原文件，运行它会读取 Key：

```python
with OpenAI(
    api_key=load_api_key(),
    base_url=BASE_URL,
    timeout=30.0,
    max_retries=2,
) as sdk_client:
    client = OpenAIModelClient(sdk_client)
    result = run_agent(question, client=client, tools=TOOLS, max_steps=MAX_STEPS)
```

`with ... as sdk_client` 把创建的 SDK 客户端绑定到变量；代码块退出时关闭客户端资源。
这里只是把创建动作移到入口，没有新增 `build_client()` 函数。

创建客户端本身不等于发出模型请求；真正请求发生在 `client.py` 的 `responses.create()`。
但 Day 02 的顶层创建会先读取 Key，所以仍然会影响导入和离线测试。

### `if __name__ == "__main__"`

```python
def main() -> None:
    print("启动程序")


if __name__ == "__main__":
    main()
```

直接运行文件时，`__name__` 是 `"__main__"`，所以会调用 `main()`。被其他文件 import 时，`__name__` 是模块名，不会自动调用 `main()`。

---

## 13. 异常：Python 如何表达失败

Go 经常显式返回：

```go
value, err := doSomething()
```

Python 常用异常表示无法正常继续的失败。

### 抛出和捕获异常

下面的 `divide()` 是独立语法示例，不是项目中的 `calculator()`。项目的除零处理会返回错误字典，不抛这个 `ValueError`。

```python
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("除数不能为 0")

    return a / b


try:
    result = divide(10, 0)
except ValueError as exc:
    print(f"计算失败：{exc}")
```

执行顺序：

```text
进入 try
   ↓
divide 抛出 ValueError
   ↓
立即跳到匹配的 except
   ↓
打印友好错误
```

### 当前项目实际定义的异常

[errors.py](agent_core/errors.py) 只有下面这些类：

```python
"""只保留课程中用到的三种流程错误。"""


class AgentError(Exception):
    """Agent 错误的共同父类。"""


class EmptyQuestionError(AgentError):
    pass


class InvalidModelReplyError(AgentError):
    pass


class MaxStepsExceededError(AgentError):
    pass
```

`pass` 表示类没有额外实现；用不同类名区分空问题、空回复、最大步数。
它们都继承 `AgentError`，因此入口可以统一捕获父类。

**完整离线示例：**

<!-- runnable: empty_question -->
```python
from day03.agent_core.errors import AgentError, EmptyQuestionError
from day03.agent_core.runner import run_agent
from day03.agent_core.tools import TOOLS
from day03.tests.fakes import FakeModelClient

try:
    run_agent("", client=FakeModelClient([]), tools=TOOLS)
except EmptyQuestionError:
    print("问题不能为空")
except AgentError as exc:
    print(f"Agent 执行失败：{exc}")
```

### 工具错误与流程异常不要混淆

| 情况 | 当前代码怎么处理 |
| --- | --- |
| 除零、未知运算、非法时区 | 工具返回 `{"ok": False, "error": "..."}` |
| 未知工具、参数调用失败 | `execute_tool()` 返回错误字典 |
| 问题为空、模型没文本也没工具调用、步数用完 | runner 抛出对应的 `AgentError` 子类 |
| API 认证、连接、HTTP 错误 | SDK 抛出异常，由入口捕获并提示 |

当前没有 `UnknownToolError` 或 `ToolArgumentsError` 这样的异常类，不需要额外创建。
工具错误字典会被回传给模型，让模型解释错误；不代表整个循环必须立即结束。

不要随意捕获异常后只返回 `None`。当前 `execute_tool()` 的兜底处理会返回明确的错误字典和异常类型，
这是简化教学处理，不是完整的生产故障处理方案。

---

## 14. Path：看懂 Key 文件的位置；JSONL 选读

### 当前 `config.py` 为什么用 `parents[2]`？

源码位于 `day03/agent_core/config.py`，所以：

```text
Path(__file__).resolve()   → .../llm-agent-learning/day03/agent_core/config.py
.parents[0]               → .../llm-agent-learning/day03/agent_core
.parents[1]               → .../llm-agent-learning/day03
.parents[2]               → .../llm-agent-learning
```

`parents` 从 0 开始；同样的 `parents[2]` 换到不同深度的文件里，结果会不同。
不能把放在 `playground.py` 中的 `__file__` 当成 `config.py` 的位置。

**完整离线示例：** 不读取 Key 内容，只观察实际模块的路径。

<!-- runnable: config_path -->
```python
from pathlib import Path

from day03.agent_core import config

config_file = Path(config.__file__).resolve()
project_root = config_file.parents[2]
key_file = project_root / "aliyun_api_key"

print(config_file.name)  # config.py
print(project_root.name)  # llm-agent-learning
print(key_file.name)  # aliyun_api_key
```

`Path` 对象之间的 `/` 用来拼接路径，不是数学除法。
`load_api_key()` 先找 `DASHSCOPE_API_KEY`、`ALIYUN_API_KEY` 环境变量，再读这个文件。
此处不需要创建新 Key，也不要把密钥打印到教程或终端日志。

### 文件读写和 `with`（选读）

下面只使用临时目录，不依赖某个文件提前存在，也不会覆盖项目中的文件：

<!-- runnable: temporary_file -->
```python
from pathlib import Path
from tempfile import TemporaryDirectory

with TemporaryDirectory() as temp_dir:
    sample_file = Path(temp_dir) / "sample.txt"
    sample_file.write_text("hello", encoding="utf-8")
    text = sample_file.read_text(encoding="utf-8")
    print(text)  # hello
```

这里的 `with` 在结束时清理临时目录。对普通文件使用 `with path.open(...)` 会在结束时关闭文件；
对 SDK 客户端使用 `with OpenAI(...) as sdk_client` 会关闭客户端资源。
先理解为“进入时拿到资源，退出时负责收尾”。

### JSONL 是什么（选读，不需要实现）

JSON 可以保存一个完整对象：

```json
{"question": "6 × 7 等于多少", "answer": "42"}
```

JSONL 是每一行保存一个独立 JSON 值；用于日志时通常每行都是一个对象：

```text
{"event": "model_called", "step": 1}
{"event": "tool_called", "name": "calculator"}
{"event": "agent_finished", "answer": "42"}
```

它可以用于后续的日志或评估数据，但**当前助手没有 JSONL 功能，没有 `storage.py` 或 `append_jsonl()`**。
本节了解概念即可，不要往当前工程补这些模块。

---

## 15. 依赖注入：就是把 client 当参数传进来

先对照 Day 02 和当前 Day 03（函数签名节选）：

```python
# Day 02：函数直接使用文件里的全局 client，返回字符串
def run_agent(question: str) -> str:
    ...

# Day 03：调用者传入 client 和 tools，返回 AgentResult
def run_agent(
    question: str,
    *,
    client: ModelClient,
    tools: list[Any],
    max_steps: int = 5,
) -> AgentResult:
    ...
```

签名中的 `*` 表示后面的参数要写名字，实际调用是：

```python
result = run_agent(question, client=client, tools=TOOLS)
```

不要写旧教程中的 `run_agent(question, fake_client)`；当前第二个位置参数是不允许的。

**完整离线示例：**

<!-- runnable: injected_fake -->
```python
from day03.agent_core.models import ModelReply
from day03.agent_core.runner import run_agent
from day03.agent_core.tools import TOOLS
from day03.tests.fakes import FakeModelClient

fake = FakeModelClient([ModelReply(text="你好")])
result = run_agent("请打招呼", client=fake, tools=TOOLS)

print(result.answer)              # 你好
print(result.usage.total_tokens)  # 0：这次没有设置模拟用量
```

runner 不关心客户端从哪里得到答案，只调用 `client.create_response(...)`。
实际运行由 `mini_agent.py` 传入 `OpenAIModelClient`；测试传入 `FakeModelClient`。

这就是依赖注入：**需要的对象由调用者传进来，而不是在函数里面固定创建。**
不需要框架，也不需要再加一层工厂函数。

---

## 16. Protocol：只约定当前项目的这一个方法

先看 [ports.py](agent_core/ports.py) 的实际定义：

```python
"""Protocol 只约定：传进来的客户端需要有 create_response 方法。"""

from typing import Any, Protocol

from day03.agent_core.models import ModelReply


class ModelClient(Protocol):
    def create_response(
        self,
        *,
        input_items: list[Any],
        tools: list[Any],
    ) -> ModelReply: ...
```

这次不再另外定义“传入 question，返回 str”的同名接口。
项目只有这一套约定：**传入历史和工具，返回 `ModelReply`。**

逐项解释：

- `class ModelClient(Protocol)`：这里定义的是能力约定，不是用它发请求。
- `create_response`：要求实现有这个方法。
- `self`：调用该方法的实例，调用时不需要自己传。
- `*`：后面两个参数必须写名字。
- `input_items`：整段对话历史，不是单独的问题字符串。
- `tools`：工具描述列表。
- `-> ModelReply`：返回一个包含文本、工具请求、Token 用量和原始输出的数据对象。
- `...`：Protocol 这里不写具体实现。省略号单独一行或放在冒号后，含义相同。

两个实现的位置：

| 类 | 在哪里 | 真正做什么 |
| --- | --- | --- |
| `OpenAIModelClient` | [client.py](agent_core/client.py) | 调用 SDK，再整理成 `ModelReply` |
| `FakeModelClient` | [tests/fakes.py](tests/fakes.py) | 从预设回复列表中取出一个 `ModelReply` |

两者不需要显式继承 `ModelClient`。只要方法签名、参数名和返回类型兼容，类型检查器就接受。
不是“随便有一个同名方法就行”，也不是 Python 运行时自动做完整数据校验。

**完整离线示例：** 这次直接调用客户端，先不经过 runner。

<!-- runnable: protocol_call -->
```python
from day03.agent_core.models import ModelReply
from day03.agent_core.ports import ModelClient
from day03.tests.fakes import FakeModelClient

client: ModelClient = FakeModelClient([ModelReply(text="你好")])
reply = client.create_response(
    input_items=[{"role": "user", "content": "请打招呼"}],
    tools=[],
)

print(reply.text)        # 你好
print(reply.tool_calls)  # []
```

`client: ModelClient` 是类型标注，不会创建一个 `ModelClient` 实例；
右侧真正创建的是 `FakeModelClient`。

类比 Go：`ModelClient` 类似一个小 interface，真实客户端和 Fake 是满足它的两种实现。
今天理解这个替换关系即可。

---

## 17. Fake Client：不联网测试 Agent

Fake 是行为可控的测试替身：

```python
from typing import Any

from day03.agent_core.models import ModelReply


class FakeModelClient:
    def __init__(self, replies: list[ModelReply]) -> None:
        self.replies = replies.copy()
        self.calls: list[dict[str, Any]] = []

    def create_response(
        self,
        *,
        input_items: list[Any],
        tools: list[Any],
    ) -> ModelReply:
        # 只复制外层列表，避免后续 append 改变已记录的历史长度。
        self.calls.append({"input_items": input_items.copy(), "tools": tools})
        return self.replies.pop(0)
```

逐行理解：

- `replies.copy()` 避免后续 `pop()` 修改调用者自己的列表；
- `self.calls` 保存每次调用记录；
- `self.calls.append(...)` 让测试可以检查 Agent 传了什么；
- `pop(0)` 从预设回复最前面取出一个回复并移除。

以后可以预设：

```text
Fake 第一次回复：请求调用 calculator
Python：执行 calculator，得到 42
Fake 第二次回复：最终文本是“结果为 42”
```

整个测试无需联网，也不消耗真实模型额度。

注意两点：

- 当前构造方式是 `FakeModelClient([ModelReply(text="你好")])`，不是 `FakeModelClient(answer="你好")`。
- `input_items.copy()` 只复制外层列表，不会隔离内部字典的修改；本示例只需要防止后续 `append` 改变已记录的列表长度。

Fake 的 `replies` 每调用一次就少一项。用完之后继续调用会触发 `pop(0)` 的 `IndexError`，
所以测试要为每次模型调用准备一条回复；当前没有另外包装“Fake 用完”的专用异常。
第 22 节会给出两轮调用的完整例子。

---

## 18. pytest：直接运行现有测试

### 当前开发依赖已经配置好

`pyproject.toml` 已经包含 `pytest`、`ruff` 和 `mypy`，不用重复安装或新建虚拟环境。
在另一台电脑克隆项目后，可以从根目录执行 `uv sync --locked` 同步环境。

`openai` 是运行依赖；测试和检查工具放在开发依赖里，二者都由 `uv.lock` 锁定。

### 先读一个实际测试

下面就是 [test_tools.py](tests/test_tools.py) 中的 `test_calculator()`：

```python
from day03.agent_core.tools import calculator

def test_calculator() -> None:
    assert calculator("add", 6, 2)["result"] == 8
    assert calculator("subtract", 6, 2)["result"] == 4
    assert calculator("multiply", 6, 2)["result"] == 12
    assert calculator("divide", 6, 2)["result"] == 3
```

`assert` 后的表达式为 `True`，表示这条检查通过；否则 pytest 会报告失败。
它测试的是导入的实际工具，不是在测试文件里再写一个计算器。

### Arrange、Act、Assert

可以把当前的乘法断言拆成三步理解；这只是帮助阅读，不要求改写测试文件。

**完整离线示例：**

<!-- runnable: arrange_act_assert -->
```python
from day03.agent_core.tools import calculator

# Arrange：准备输入
operation = "multiply"
a = 6
b = 2

# Act：调用实际函数
result = calculator(operation, a, b)

# Assert：检查结果
assert result["ok"] is True
assert result["result"] == 12
```

### 测试异常：写全实际参数

下面与 [test_runner.py](tests/test_runner.py) 中的 `test_empty_question()` 一致：

```python
import pytest

from day03.agent_core.errors import EmptyQuestionError
from day03.agent_core.runner import run_agent
from day03.agent_core.tools import TOOLS
from day03.tests.fakes import FakeModelClient


def test_empty_question() -> None:
    with pytest.raises(EmptyQuestionError):
        run_agent("", client=FakeModelClient([]), tools=TOOLS)
```

含义是：代码必须抛出 `EmptyQuestionError`，否则测试失败。
空问题在请求模型之前就被拒绝，所以 Fake 可以准备零条回复。

### 运行命令：这些名称都存在于当前项目

运行全部 13 个测试：

```bash
uv run pytest -q day03/tests
```

只运行一个文件：

```bash
uv run pytest -q day03/tests/test_tools.py
```

只运行一个实际测试：

```bash
uv run pytest -q day03/tests/test_tools.py::test_calculator
```

看两轮 Agent 的过程输出：

```bash
uv run pytest -q -s day03/tests/test_runner.py::test_tool_call_then_answer
```

`-q` 减少输出，`-s` 让 `print()` 日志显示出来。pytest 默认会捕获这些日志，并不是 runner 没有执行。

### `tmp_path`（选读，不在当前测试中）

将来需要测试文件读写时，pytest 可提供临时目录：

```python
from pathlib import Path

def test_write_text(tmp_path: Path) -> None:
    sample_file = tmp_path / "sample.txt"
    sample_file.write_text("hello", encoding="utf-8")
    assert sample_file.read_text(encoding="utf-8") == "hello"
```

这只是独立语法例子，当前目录没有这个测试，也不需要为它新增文件。
我们没有文件日志功能，因此不再要求编写 `test_append_jsonl`。

---

## 19. ruff 和 mypy 分别检查什么

### Ruff

Ruff 主要检查未使用 import、未定义变量、常见代码错误和格式。

```bash
uv run ruff check day03
```

只检查格式，不改文件：

```bash
uv run ruff format --check day03
```

需要调整格式时再执行：

```bash
uv run ruff format day03
```

不要看到 `--fix` 就盲目执行。先读懂错误，再决定是否自动修复。

### mypy

mypy 检查类型标注是否自洽。

错误示例：

```python
def total(a: int, b: int) -> int:
    return "42"
```

函数承诺返回 `int`，实际返回了 `str`。

运行：

```bash
uv run mypy day03
```

| 工具 | 它回答的问题 |
| --- | --- |
| pytest | 程序行为符合预期吗？ |
| ruff | 有明显错误或风格问题吗？ |
| mypy | 类型之间是否自洽？ |

三者互相补充，不能互相替代。

本项目 mypy 已启用 strict 模式。上面的错误示例是故意不符合类型标注的，不要把它当成项目正确实现。
Ruff 的格式化配置排除了教学 Markdown 和原有 `playground.py`，所以不会自动改它们的排版；
`playground.py` 仍参与代码检查和类型检查。

---

## 20. async/await：独立语法练习（选读）

本节在自己的 `playground.py` 中练习即可，当前助手继续使用 Day 02 的同步流程。

今天不需要成为 asyncio 专家，只要理解它为什么经常出现在 Agent 服务中。

### 同步等待

```python
import time


def fetch(name: str) -> str:
    print(f"开始：{name}")
    time.sleep(1)
    print(f"完成：{name}")
    return name


start = time.perf_counter()
fetch("A")
fetch("B")
elapsed = time.perf_counter() - start

print(f"耗时：{elapsed:.2f} 秒")
```

两个任务依次等待，总耗时接近 2 秒。

### 异步并发等待

```python
import asyncio
import time


async def fetch(name: str) -> str:
    print(f"开始：{name}")
    await asyncio.sleep(1)
    print(f"完成：{name}")
    return name


async def main() -> None:
    start = time.perf_counter()

    results = await asyncio.gather(
        fetch("A"),
        fetch("B"),
    )

    elapsed = time.perf_counter() - start
    print(results)
    print(f"耗时：{elapsed:.2f} 秒")


asyncio.run(main())
```

总耗时应该接近 1 秒。

逐个理解：

- `async def` 定义协程函数；
- `await` 表示当前任务等待时可以运行其他任务；
- `asyncio.gather` 并发等待多个协程；
- `asyncio.run` 创建事件循环并运行最外层协程。

异步适合 I/O 等待，例如模型 API、数据库、向量库和多个外部工具。它不会让纯 CPU 计算自动变快。

与 goroutine 的最小区别：

- goroutine 由 Go runtime 调度；
- asyncio 任务通常运行在单线程事件循环；
- Python 协程要在合适位置显式 `await` 才会让出执行权；
- 阻塞函数放进 asyncio 代码仍可能阻塞事件循环。

想练异步时做上面的实验即可。本次拆分版仍使用同步 `OpenAI`、普通 `def create_response()` 和 `def run_agent()`，不用把它们改成 async。

---

## 21. 今日项目：只把 Day 02 拆成几个文件

保留 `day02/mini_agent.py` 不动，在 Day 03 做同一个助手，不增加业务功能。

```text
day03/
├── __init__.py
├── DAY03.md
├── README.md
├── playground.py
├── mini_agent.py          # 程序入口：输入、创建客户端、输出
├── agent_core/
│   ├── __init__.py
│   ├── config.py          # 原来的模型名、地址、提示词、读取 Key
│   ├── client.py          # 原来的 responses.create()
│   ├── models.py          # dataclass：工具调用、回复、用量、结果
│   ├── ports.py           # Protocol：客户端需要哪个方法
│   ├── errors.py          # 空问题、空回复、步数超限
│   ├── tools.py           # 原来的工具函数、schema、注册表
│   └── runner.py          # 原来的 for 循环
└── tests/
    ├── __init__.py
    ├── fakes.py
    ├── test_models.py
    ├── test_tools.py
    └── test_runner.py
```

### 第一步：认出 Day 02 的代码去了哪里

先打开 `tools.py`。你会发现 `OPERATIONS`、`calculator()`、`get_current_time()`、
`TOOLS` 和 `TOOL_HANDLERS` 基本就是 Day 02 的内容。

再看 `config.py`：模型名、阿里云地址、提示词和读取 Key 的规则都保持不变。
只是文件更深了一层，所以寻找项目根目录改用 `Path(__file__).resolve().parents[2]`。

### 第二步：用 dataclass 保存数据

四个类仍然是 `ToolCall`、`ModelReply`、`TokenUsage` 和 `AgentResult`，定义见第 11 节。

重点只看两个例子：

```python
from day03.agent_core.models import ModelReply, ToolCall

call = ToolCall(
    call_id="call_123",
    name="calculator",
    arguments={"operation": "multiply", "a": 6, "b": 7},
)
print(call.name)  # calculator
```

在同一个练习会话里接着执行：

```python
first = ModelReply()
second = ModelReply()
first.tool_calls.append(call)

assert len(first.tool_calls) == 1
assert second.tool_calls == []
```

### 第三步：用一个很小的类包装 SDK

`client.py` 中的 `OpenAIModelClient` 做两件事：

1. 调用原来的 `sdk_client.responses.create(...)`；
2. 将结果整理成 `ModelReply`，让 runner 读取固定的几个字段。

`__init__` 只把传入的 SDK 客户端保存到 `self.sdk_client`。

`json.loads(item.arguments)` 现在发生在这里，因此 `execute_tool()` 中的参数已经是字典，
直接执行 `handler(**tool_call.arguments)`，不再重复解析 JSON。

### 第四步：Protocol 只约定一个方法

```python
from typing import Any, Protocol

from day03.agent_core.models import ModelReply


class ModelClient(Protocol):
    def create_response(
        self,
        *,
        input_items: list[Any],
        tools: list[Any],
    ) -> ModelReply:
        ...
```

意思仅仅是：“传给 runner 的对象，要能通过这个方法返回一轮回复。”

真实运行传入 `OpenAIModelClient`，测试传入 `FakeModelClient`。二者都不需要显式继承这个 Protocol。
`Any` 用在 SDK 边界：历史列表里既有自己写的字典，也有 SDK 返回的对象。

### 第五步：读懂原来的循环

`runner.py` 保持 Day 02 的顺序：

```text
创建 input_items，放入用户问题
    ↓
请求模型
    ↓
input_items += reply.output_items
    ↓
没有工具请求 → 返回最终答案
有工具请求   → 执行工具，append 结果，进入下一轮
```

其中：

```python
input_items += reply.output_items
```

就是原来的：

```python
input_items += response.output
```

工具结果仍然用同样的方式回传：

```python
input_items.append(
    {
        "type": "function_call_output",
        "call_id": tool_call.call_id,
        "output": json.dumps(tool_result, ensure_ascii=False),
    }
)
```

这里没有深拷贝、动态权限表、重复 ID 检测或复杂的参数验证。
学习版保留了 `print()` 过程日志，方便直接观察列表的变化；没有增加日志框架。
`max_steps` 也沿用 Day 02：循环结束还没有最终答案就报错，不引入特别的“最后一轮”策略。

### 第六步：从入口组装起来

`mini_agent.py` 中创建真实 SDK 客户端，再传给自己的小包装类。下面是 `with OpenAI(...) as sdk_client:` 块内的节选，完整创建过程见第 12 节或入口文件：

```python
client = OpenAIModelClient(sdk_client)
result = run_agent(question, client=client, tools=TOOLS, max_steps=MAX_STEPS)
print(result.answer)
```

`main()` 被调用时才读取 Key、创建客户端；仅仅 import 文件不会发起 API 请求。

---

## 22. 完整离线示例：用 Fake 看两轮调用

下面按 [test_tool_call_then_answer()](tests/test_runner.py) 中的流程展开。
可以整段运行：**不会调用 API，也不用 Key**，不要创建或替换真实客户端。

<!-- runnable: two_round_agent -->
```python
import json

from day03.agent_core.models import ModelReply, TokenUsage, ToolCall
from day03.agent_core.runner import run_agent
from day03.agent_core.tools import TOOLS
from day03.tests.fakes import FakeModelClient

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

print(result.answer)
print(result.usage.total_tokens)
print(result.used_tools)
```

除了 runner 打印的过程日志，最后会输出：

```text
6 × 7 = 42
250
['calculator']
```

### 第一步：准备两种不同用途的数据

`call` 是 `ToolCall` 数据类，参数是字典，用来真正调用 Python 工具。
`output_item` 模拟 SDK 原始输出项，参数是 JSON 字符串，用来放进对话历史。

真实运行时，这两者都由 `client.py` 从 SDK 回复整理出来；Fake 没有 SDK，所以测试手动准备。

### 第二步：第一轮执行工具

第一次调用 Fake，得到第一条 `ModelReply`：

- `tool_calls=[call]` 表示需要调用计算器。
- `output_items=[output_item]` 先追加到历史。
- `execute_tool(call)` 实际算出 42，runner 再追加 `function_call_output`。

因此第二次请求的三项输入是：用户问题、模型请求、工具结果。
`fake.calls[0]` 和 `fake.calls[1]` 保存的是两次**发出请求时**的历史，不是同一个列表引用。

### 第三步：第二轮返回答案

第二条 `ModelReply` 只有预设文本，没有工具调用，runner 返回 `AgentResult`。
答案虽然是预设的，但测试还检查了工具输出中的 `result == 42`，不是只看最终文本。

### 第四步：累计 Token

测试人为设置了两轮用量：

```text
input_tokens：100 + 120 = 220
output_tokens：20 + 10 = 30
total_tokens：220 + 30 = 250
```

这只是验证加法，不代表 Fake 消耗了真实 Token。真实运行时这些数字来自 SDK 的 `response.usage`。

### 为什么真实运行可能不是三项？

这个测试只模拟了一项工具调用。真实 SDK 输出还可能有 reasoning 或文本项，
`reply.output_items` 会保留它们，所以历史长度不固定。

保留完整 `response.output`、再用相同的 `call_id` 追加工具结果，符合
[OpenAI 官方工具调用流程](https://developers.openai.com/api/docs/guides/function-calling)。
这里核对的是回传格式，不是切换模型；本项目仍使用你已有的阿里云配置。

### 最大步数怎样理解？

`max_steps` 数的是**模型请求轮数**，不是工具函数数量。
当前实现和 Day 02 一样：一轮收到工具调用就执行它，循环用完仍没有最终文本才抛 `MaxStepsExceededError`。

所以 `max_steps=1` 时：

- 如果第一轮直接有答案，可以正常返回；
- 如果第一轮要求调用工具，会执行工具，但没有第二轮拿最终答案，随后报步数超限。

当前没有“最后一轮不执行工具”的特殊策略；看 `test_max_steps()` 时按上述顺序理解。

---

## 23. 本次只保留基础测试

当前共有 13 个测试函数，分在三个文件：

- `test_models.py`：默认列表互不共享、Token 求和、结果对象；
- `test_tools.py`：四则运算、除零、未知运算、时区、工具执行；
- `test_runner.py`：直接回答、调用工具后回答、空问题、最大步数。

```bash
uv run pytest -q day03/tests
```

不需要真实 Key，不调用真实模型。本次不增加 JSONL 测试、并发测试或大量边界用例。
先能独立解释这些测试，再考虑增加更多情况。

---

## 24. 初学者最常见的错误

### 把函数写成函数调用

错误：

```python
OPERATIONS = {"add": add()}
```

正确：

```python
OPERATIONS = {"add": add}
```

### 接住 append 的返回值

错误：

```python
input_items = input_items.append(new_item)
```

正确：

```python
input_items.append(new_item)
```

### 混淆 SDK 参数与内部参数

SDK 回复里是 `item.arguments` 字符串，只有 `client.py` 在这里解析：

```python
arguments = json.loads(item.arguments)
```

到了当前 `execute_tool(tool_call)`，`tool_call.arguments` 已是字典，
直接 `handler(**tool_call.arguments)`。再次调用 `json.loads()` 反而会报类型错误。

### 忘记调用函数的括号

```python
from day03.agent_core.tools import TOOL_HANDLERS

handler = TOOL_HANDLERS["calculator"]
result = handler  # 仍然只是函数对象
result = handler(operation="add", a=1, b=2)  # 才是调用
```

`add` 是 `OPERATIONS` 的 key，不是 `TOOL_HANDLERS` 的 key。两个字典分别处理“运算名”和“工具名”。

### 把类型标注当运行时校验

类型标注不会自动验证模型输入。当前示例有 JSON 解析和少量工具检查，但不做完整 schema 校验；不要把这段教学代码理解为已经覆盖所有非法输入。

### 在 import 时运行程序

读取 Key、调用 API、`input()` 都不应放在核心模块顶层，应放进 `main()` 或明确构造函数。

### 测试里调用真实模型

单元测试应该确定、快速、便宜。真实模型调用属于集成测试，应单独运行。

### 用 `except Exception` 隐藏所有错误

捕获后什么也不说明，会让问题难以定位。当前工具执行入口会回传 `ok=False` 和错误类型，便于教学观察；这里只讲清它做了什么，不要求新增日志框架或完整错误体系。

### 一开始过度抽象

今天只需要数据对象、工具模块、一个 Protocol、一个 runner 和一个 Fake，不需要十层基类。

---

## 25. 今日验收命令

```bash
uv run pytest -q day03/tests
```

```bash
uv run ruff check day03
```

```bash
uv run ruff format --check day03
```

```bash
uv run mypy day03
```

```bash
uv run python -c "import day03.agent_core.runner; print('safe import')"
```

如果 mypy 暂时出现第三方类型问题，先确保自己定义的模块没有明显错误，不要用大量 `Any` 或 `# type: ignore` 把问题全部盖住。

---

## 26. 今日验收标准

### Python 语法

- [ ] 能解释变量为什么可能指向同一个可变对象；
- [ ] 能解释 `append`、`extend` 和列表 `+=`；
- [ ] 能解释字典为什么可以保存函数；
- [ ] 能把 `handler(**arguments)` 展开成长写法；
- [ ] 能区分 JSON 字符串和 Python dict；
- [ ] 能解释 `None`、空字符串和 `0` 的区别；
- [ ] 能解释类型标注为什么不是运行时校验。

### Python 工程

- [ ] 知道 module 和 package 的区别；
- [ ] import `agent_core` 不读取 API Key、不发网络请求；
- [ ] 工具函数不依赖 `input()` 或 `print()`；
- [ ] runner 通过参数接收客户端；
- [ ] Fake Client 可以在 runner 的参数位置替换真实客户端；
- [ ] 能区分 SDK 的 `OpenAI` 和自己的 `OpenAIModelClient`；
- [ ] 能解释 `output_items` 与 `tool_calls` 为什么同时存在；
- [ ] 领域异常有明确名字。

### 测试与质量

- [ ] 基础离线测试通过；
- [ ] 能读懂直接回答、工具调用、空问题和最大步数的测试；
- [ ] 最大步骤限制有测试；
- [ ] ruff 检查通过；
- [ ] 主要 mypy 检查通过；
- [ ] 没有使用 `eval()`；
- [ ] 没有把 Key 写进代码或测试数据。

只有能用自己的话逐项解释，才算完成，不只是命令显示绿色。

---

## 27. 自测题与答案

先口头回答：

1. `items.append([1, 2])` 和 `items += [1, 2]` 有何区别？
2. 为什么 `append()` 后一般不重新赋值？
3. `TOOL_HANDLERS["calculator"]` 取出的是什么？
4. `handler(**arguments)` 中两个星号做了什么？
5. `json.loads()` 和 `json.dumps()` 的方向是什么？
6. 类型标注会在运行时自动拒绝错误参数吗？
7. `@dataclass` 减少了哪些代码？
8. 为什么 list 字段使用 `field(default_factory=list)`？
9. 为什么在模块顶层创建 API Client 会影响测试？
10. 依赖注入最简单的实现是什么？
11. Python Protocol 可以类比 Go 的什么？
12. Fake Client 解决了真实模型测试的哪些问题？
13. pytest、ruff、mypy 分别检查什么？
14. 当前 `run_agent()` 和 `create_response()` 是同步还是异步？
15. `AgentResult` 有 `model` 字段吗？模型名在哪里打印？
16. 为什么 Day 03 的 `execute_tool()` 不再解析 JSON？
17. `output_items` 与 `tool_calls` 分别给谁使用？

参考答案：

1. `append` 把整个列表作为一个元素；列表 `+=` 把右侧元素逐个加入。
2. 它原地修改列表并返回 `None`。
3. 一个函数对象。
4. 把字典展开为关键字参数。
5. `loads` 从 JSON 字符串到 Python 对象；`dumps` 方向相反。
6. 不会，默认主要供 IDE 和静态检查器使用。
7. 初始化、显示和比较等常见方法。
8. 确保每个实例得到独立的新列表。
9. import 会执行模块顶层代码。
10. 把依赖对象作为参数从外部传入。
11. interface，但 Protocol 默认主要用于静态类型检查。
12. 避免网络、额度、随机性和慢请求，并可模拟错误和多轮回复。
13. 行为测试、代码检查、类型检查。
14. 都是同步函数；asyncio 只是独立选读练习。
15. 没有。模型名由 `config.py` 的 `MODEL` 提供，在 `mini_agent.py` 中单独打印。
16. `client.py` 已把 SDK 的参数字符串解析为 `ToolCall.arguments` 字典。
17. 前者保存完整模型输出并追加到历史；后者是解析好的工具请求，用来执行 Python 函数。

---

## 28. 面试题（选读，不作为本次实现要求）

1. 为什么 Agent Loop 不应直接依赖 OpenAI SDK 的具体客户端？
2. 如何在不调用真实模型的情况下测试一次工具调用？
3. `dict[str, Callable]` 在工具路由中有什么作用？
4. 为什么模型生成的 JSON 即使符合 Schema，应用侧仍需校验？
5. 什么是 import side effect？
6. dataclass 和普通 dict 分别适合什么场景？
7. Protocol 与抽象基类有什么区别？
8. 为什么最大步骤限制是 Agent 的安全边界？
9. 哪些失败适合返回工具错误，哪些适合抛异常？
10. async 模型客户端会带来什么收益和新问题？

合格回答应包含具体代码、工程后果、项目中的做法和做法的局限。

---

## 29. 用当前代码复习：完整离线速查示例

这段可以独立运行，只导入已有模块，不会请求 API。

<!-- runnable: quick_reference -->
```python
import json

from day03.agent_core.models import ModelReply, TokenUsage, ToolCall
from day03.agent_core.runner import run_agent
from day03.agent_core.tools import OPERATIONS, TOOL_HANDLERS, TOOLS, execute_tool
from day03.tests.fakes import FakeModelClient

# 一个工具内部的“运算名 → 函数”
operation = OPERATIONS["multiply"]
assert operation(6, 7) == 42

# “工具名 → 函数”：calculator 需要 operation、a、b 三个参数
handler = TOOL_HANDLERS["calculator"]
arguments = {"operation": "multiply", "a": 6, "b": 7}
assert handler(**arguments)["result"] == 42

# 内部 ToolCall 的 arguments 已经是字典
call = ToolCall("call_123", "calculator", arguments)
tool_result = execute_tool(call)
output = json.dumps(tool_result, ensure_ascii=False)
assert json.loads(output)["result"] == 42

# append 加一个元素，+= 加右侧列表里的每个元素
items = ["user"]
items += ["function_call"]
items.append("function_call_output")
assert len(items) == 3

# property 不用括号
usage = TokenUsage(input_tokens=100, output_tokens=20)
assert usage.total_tokens == 120

# 正确的 Fake 构造与 runner 调用
fake = FakeModelClient([ModelReply(text="你好")])
result = run_agent("请打招呼", client=fake, tools=TOOLS)
assert result.answer == "你好"
```

---

## 30. 推荐阅读顺序

不需要一次读完所有官方文档，遇到对应问题再查：

1. [Python 3.10 官方教程](https://docs.python.org/3.10/tutorial/)
2. [Python 数据结构](https://docs.python.org/3.10/tutorial/datastructures.html)
3. [Python 函数定义与参数](https://docs.python.org/3.10/tutorial/controlflow.html#defining-functions)
4. [Python Modules](https://docs.python.org/3.10/tutorial/modules.html)
5. [Python Errors and Exceptions](https://docs.python.org/3.10/tutorial/errors.html)
6. [dataclasses](https://docs.python.org/3.10/library/dataclasses.html)
7. [typing](https://docs.python.org/3.10/library/typing.html)
8. [asyncio](https://docs.python.org/3.10/library/asyncio.html)
9. [pytest 文档](https://docs.pytest.org/en/stable/)
10. [Ruff 文档](https://docs.astral.sh/ruff/)
11. [mypy 文档](https://mypy.readthedocs.io/en/stable/)
12. [uv 依赖管理](https://docs.astral.sh/uv/concepts/projects/dependencies/)

阅读时带着问题找答案，不要试图从第一页背到最后一页。

---

## 31. 完成 Day 03 后应该得到什么

```text
数据结构
    保存状态

函数和工具注册表
    执行确定性能力

dataclass
    描述内部数据合同

Protocol
    描述外部依赖所需的最小能力

依赖注入
    把真实实现或 Fake 传给核心逻辑

runner
    负责 Agent 流程

pytest
    证明行为正确

ruff + mypy
    尽早发现低级错误和类型问题
```

完成标准不是“理解所有 Python”，而是：

> 你已经能看懂 Agent 项目中的核心 Python 写法，并能把依赖网络的脚本拆成可离线测试的程序。
