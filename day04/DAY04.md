# Day 04：亲手写一个有多轮记忆、会调用工具的 Agent

> 今日目标：不背代码，能够说清一次提问如何经过“读取旧历史 → 请求模型 → 执行工具 → 回填结果 → 保存完整轮次”。

先完成核心练习，再阅读扩展功能；今天不增加异步、数据库、复杂异常体系或新的项目分层。

## 0. 学习顺序与运行方式

本课有两个文件，职责不同，不要混着对照函数名和字段：

| 文件 | 用途 | 当前范围 |
| --- | --- | --- |
| [agent_practice.py](agent_practice.py) | 主线：亲手填写、复盘核心流程 | 一个计算器、多轮历史、`/history`、`/reset`、`/quit` |
| [chat_agent.py](chat_agent.py) | 扩展：核心流程掌握后再读 | 复用 Day 03 的工具和客户端，增加整轮裁剪、Token 统计、`/plan` |

练习版直接调用 SDK 的 `client.responses.create()`，读取 `response.output`；扩展版通过 Day 03 客户端调用 `client.create_response()`，读取封装后的 `reply.output_items`。

练习版把模型输出转换成字典后存入历史；扩展版当前仍保留 SDK 对象和字典的混合列表，`/history` 逐项打印，不是统一的 JSON 展示。

学习顺序：

1. 第 1～4 节：分清变量、列表操作和两层循环。
2. 第 5～6 节：看懂模型响应，手推一次完整执行过程。
3. 第 7 节：填写或重新默写 TODO 1～7。
4. 第 8～10 节：看错例、核对参考答案、手动验收。
5. 第 11～12 节：了解扩展能力，回答自测题。

运行核心练习：

```bash
cd /path/to/llm-agent-learning  # 替换为你实际克隆到的目录
uv run python -m day04.agent_practice
```

PyCharm 配置：

- Module name：`day04.agent_practice`。
- Working directory：`/path/to/llm-agent-learning`。
- Interpreter：`/path/to/llm-agent-learning/.venv/bin/python`。

配置和密钥读取沿用已有实现，不要把密钥写进练习文件；真实运行会请求模型并可能消耗额度，文中的列表小实验不调用模型。

如果文件里仍有 `NotImplementedError`，它是在提醒你填写练习；如果已经写完，就用下面的状态推演和验收清单检查自己的实现。

## 1. 先分清：一次提问，不等于一次模型请求

先记住这个定义：

**一个 turn，是一次用户提问到最终回答的完整过程；其中可以有多次模型请求和多次工具执行。**

不要理解成“每个请求、每个响应都是一个 turn”。

| 名称 | 在这份练习中是什么意思 |
| --- | --- |
| `session` | 整个会话对象，多次用户提问共用它 |
| `session.turns` | 已经完成的多轮对话，外层列表每一项是一轮 |
| `turn` | 当前这一轮的列表，包含用户问题、模型输出和工具结果 |
| `history` | 将旧的完整轮次展开成一维列表，供本次请求使用 |
| `response` | 一次模型请求得到的完整响应对象 |
| `response.output` | 这次响应中的输出项列表 |
| `item` | 列表中的一个条目，例如推理条目、工具请求或助手消息 |

例如“25 乘 3 等于几”：

- 用户只提问一次，所以只产生一个 turn。
- 模型先请求计算器，再根据结果回答，可能需要两次模型请求。
- 两次响应分别包含多个 item，但最终仍然只保存一个完整 turn。

推理条目不保证每次都出现，工具也不保证每次只调用一个，不能把输出项数量写死。

## 2. session.turns、history、turn 各存什么？

### 2.1 session.turns：按完整轮次保存

练习中的会话类：

```python
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ChatSession:
    turns: list[list[dict[str, Any]]] = field(default_factory=list)
```

外层列表按轮次组织；内层列表按发生顺序保存消息和事件。

`default_factory=list` 表示每个会话各自创建一个新列表，不会和另一个会话共享默认列表。

下面只是结构示意，字符串用来代替真实的消息字典：

```python
session_turns = [
    ["第一轮用户问题", "第一轮助手回答"],
    ["第二轮用户问题", "第二轮助手回答"],
]

print(len(session_turns))     # 2 个完整轮次
print(len(session_turns[0]))  # 第一轮有 2 个条目
```

有工具调用的轮次会更长，不一定只有问答两项。

### 2.2 history：展开旧历史

```python
history = []

for previous_turn in session_turns:
    history.extend(previous_turn)

print(history)
# ["第一轮用户问题", "第一轮助手回答", "第二轮用户问题", "第二轮助手回答"]
```

`history` 不是特殊语法，也不是一个新的长期存储；它只是本次 `chat()` 中临时整理出来的旧历史。

在本次 `chat()` 的模型循环中，它保持不变；下一次用户提问时，再从最新的 `session.turns` 重新构建。

### 2.3 turn：当前正在进行的一轮

每次进入 `chat()` 都新建一个 `turn`，最初只放当前用户消息：

```python
turn = [
    {"role": "user", "content": question}
]
```

之后依次加入模型输出和工具结果；不要把旧历史也复制进 `turn`。

模型得到最终回答后，才执行：

```python
session.turns.append(turn)
return response.output_text
```

`append` 保存的是这个列表的引用，不是深拷贝；这里随后立即返回，下一次提问会新建另一个 `turn`。

正常完成前不要把当前轮次保存到 `session.turns`，否则会留下半截过程或重复保存。

### 2.4 模型的“记忆”在哪里？

这里的历史保存在 Python 进程内存中的 `session.turns`，不是模型永久记住了这些内容。

每次请求都把需要的历史重新发给模型；退出并重新运行程序，本地会话就重新开始。

`/reset` 清空本地历史，不会退回已消耗的额度，也不代表删除了服务商可能保存的数据。

## 3. 三个列表操作：append、extend、+

这些是普通 Python 列表操作；先用字符串做一个不需要模型的实验：

```python
items = ["推理摘要", "工具请求"]

first = ["用户问题"]
first.append(items)
print(first)
# ["用户问题", ["推理摘要", "工具请求"]]：增加了一个列表元素，多了一层

second = ["用户问题"]
second.extend(items)
print(second)
# ["用户问题", "推理摘要", "工具请求"]：把两个元素逐个加入

third = ["用户问题"]
for item in items:
    third.append(item)
print(third)
# ["用户问题", "推理摘要", "工具请求"]：与 extend 的结果相同
```

因此，在代码中：

- `history.extend(previous_turn)`：展开旧轮次，得到一维历史。
- `turn.append(item)`：追加一个当前条目。
- `session.turns.append(turn)`：把整轮作为一个元素保存，保持二维结构。

### history + turn 会不会越加越重复？

```python
history = ["旧消息"]
turn = ["当前问题"]

first_input = history + turn
second_input = history + turn

print(first_input)   # ["旧消息", "当前问题"]
print(second_input)  # ["旧消息", "当前问题"]
print(history)       # ["旧消息"]：没有被修改
```

`+` 创建新列表，不修改两边原来的列表；这里不是深拷贝，但我们只是在拼接，不修改里面已有的消息。

不同请求会重复携带已有上下文，这是为了让模型知道之前发生了什么；不等于同一次请求里重复加入同一条记录。

不要在每次模型循环中改成 `history.extend(turn)`，否则会反复把整个当前轮次追加进旧历史。

## 4. 两层循环：什么时候继续，什么时候返回？

| 位置 | 循环的任务 | 什么时候结束 |
| --- | --- | --- |
| `main()` 中的 `while` | 等待用户一个接一个地提问 | 用户输入 `/quit`，或中断程序 |
| `chat()` 中的 `for` | 为当前这一个问题，反复请求模型、执行工具 | 得到最终回答后 `return`；或异常、达到步骤上限 |

三个变量的创建位置尤其重要：

- `session`：在外层 `while` 之前创建一次。
- `history` 和 `turn`：每次进入 `chat()` 时创建一次。
- `tool_calls`：每次收到模型响应后重新创建，只处理这次新增的工具请求。

模型要求工具时：执行工具，把结果加进 `turn`，让内层循环继续。

模型给出最终回答时：保存完整 turn，`return` 回到 `main()`，由外层循环等待下一个问题。

`continue` 只进入它所在循环的下一次迭代，不会离开 `chat()`；`return` 才会结束当前函数。

内层最多请求模型 5 次只是防止错误循环，不是历史最多保存 5 轮；核心练习目前没有历史裁剪。

## 5. 看懂 response.output：内容与 Python 表示方式

### 5.1 服务端返回数据，SDK 创建对象

服务端返回 JSON，OpenAI SDK 将其解析成 Python 对象；使用这个 SDK，不代表底层必须是 OpenAI 模型。

你可能看到：

| 对象/条目 | 含义 |
| --- | --- |
| `ResponseReasoningItem` | 推理相关输出，日志中的 `summary` 是服务提供的摘要，不应当作完整内部思考 |
| `ResponseFunctionToolCall` | 模型请求执行某个工具，包含名称、参数和调用编号 |
| `ResponseOutputMessage` | 助手消息，`content` 中可以有文本块 |
| `function_call_output` 字典 | 你的 Python 程序执行工具后创建的结果记录 |

一次模型响应可以同时返回“推理条目 + 工具请求”，不是一个对象对应一次 API 请求。

`call_id` 用来关联工具请求和工具结果；条目自己的 `id` 不应拿来替代它。

工具请求里的 `status="completed"` 不表示你的本地工具已经执行成功，真正执行工具的是后面的 Python 代码。

### 5.2 为什么统一成字典？

SDK 对象用属性访问，字典用键访问：

```python
# tool_call 是 SDK 对象
name = tool_call.name
arguments = tool_call.arguments

# item_dict 是转换后的字典
item_dict = tool_call.to_dict(mode="json")
name = item_dict["name"]
```

`to_dict(mode="json")` 会递归转换成只包含 JSON 可表示数据的字典；返回值仍是字典，不是 JSON 字符串。

练习使用：

```python
tool_calls = []

for item in response.output:
    turn.append(item.to_dict(mode="json"))
    if item.type == "function_call":
        tool_calls.append(item)
```

同一次遍历完成两件事：把所有输出保存成字典，并把待执行的工具调用单独收集起来。

`turn` 中包含全部条目；`tool_calls` 只包含本次响应中的工具请求，保留 SDK 对象以便访问属性。

如果想整批加入，也可以等价地写：

```python
output_items = [
    item.to_dict(mode="json")
    for item in response.output
]
turn.extend(output_items)

tool_calls = [
    item for item in response.output
    if item.type == "function_call"
]
```

直接 `turn.append(response.output)` 会多一层列表；直接 `turn.extend(response.output)` 虽然层级正确，却没有把 SDK 对象转换成字典。

### 5.3 arguments 和 output 为什么还是字符串？

外层统一成字典，不意味着每个字段都要变成字典。

`tool_call.arguments` 是 JSON 字符串，执行工具前需要解析：

```python
params = json.loads(tool_call.arguments)
result = calculator(params["operation"], params["a"], params["b"])
```

工具结果中的 `output` 在这份练习里也使用字符串：

```python
tool_result = {
    "type": "function_call_output",
    "call_id": tool_call.call_id,
    "output": json.dumps(result),
}
turn.append(tool_result)
```

如果结果是数字 75，那么 `json.dumps(result)` 得到字符串 `"75"`；模型收到的是对应工具的结果记录，不是又一条用户消息。

手动管理工具上下文时，应回传必要的完整模型输出，而不是只留下工具名称或答案文字；官方也明确要求保留随工具调用返回的相关 reasoning 项。[Function Calling](https://developers.openai.com/api/docs/guides/function-calling)

### 5.4 为什么不能只保存 output_text？

`response.output_text` 是 SDK 从输出中的文本块提取、拼接出来的字符串，不是完整响应；没有文本块时，它就是空字符串。

模型只返回工具请求时，保存这个空字符串就会丢掉工具名称、参数、`call_id` 和其他过程信息。

需要分两个阶段：

- 工具调用仍在进行：保留完整的当前过程，供下一次请求使用。
- 整轮已经结束：可以选择把旧历史简化成“用户问题 + 最终回答”，但会失去工具参数、原始结果等细节，这不是无损替换。

今天为了看清流程，保留完整 turn，不额外引入历史压缩逻辑。

## 6. 状态推演：25 × 3，再把结果乘 5

本节从一个空会话开始，不包含姓名测试的历史。

以下用符号表示真实字典，不能把这些符号字符串直接当作 API 消息；假设每次模型请求都返回一个推理条目，以便对应你看到的日志。

- `U`：用户消息。
- `R`：模型返回的推理条目。
- `F`：模型返回的工具请求。
- `O`：Python 创建的工具结果。
- `A`：模型最终回答。

### 6.1 第一轮用户问题：“25 乘 3 等于几？”

起点：`session.turns = []`，`history = []`。

| 执行到哪里 | 当前 turn | 已保存的 session.turns |
| --- | --- | --- |
| 创建用户消息 | `[U1]` | `[]` |
| 第一次模型请求返回摘要和工具请求 | `[U1, R1, F1]` | `[]` |
| 计算器得到 75，追加结果 | `[U1, R1, F1, O1]` | `[]` |
| 第二次模型请求返回摘要和最终回答 | `[U1, R1, F1, O1, R2, A1]` | `[]` |
| append 整轮，然后 return | 完整列表记作 `T1` | `[T1]` |

其中：

- 第一次请求：`input = [U1]`。
- 第二次请求：`input = [U1, R1, F1, O1]`。
- `F1` 的参数是 `multiply, 25, 3`，`O1` 的结果是 75。
- `F1.call_id` 和 `O1["call_id"]` 对应同一次工具调用。
- 最终回答早已通过保存 `response.output` 加入 `turn`，不要额外再追加一次 `output_text`。

按这个示例，6 个条目来自“1 个用户消息 + 第一次响应 2 项 + 工具结果 1 项 + 第二次响应 2 项”；只有两次模型请求，而不是六次。

### 6.2 第二轮用户问题：“把结果再乘 5”

再次调用 `chat()`，但传入的还是同一个 `session`。

1. 将 `session.turns = [T1]` 展开，得到 `history`，里面是上一轮的 6 个条目。
2. 创建新的 `turn = [U2]`，没有复用上一轮的列表。
3. 第一次请求发送 `history + [U2]`，共 7 个条目。
4. 模型从旧历史理解“结果”指 75，返回参数为 `multiply, 75, 5` 的工具请求。
5. 执行工具后，当前 `turn = [U2, R3, F2, O2]`。
6. 第二次请求发送 `history + turn`，共 10 个条目，模型看到结果 375。
7. 追加本次输出后保存整个 `T2`，得到 `session.turns = [T1, T2]`。

这里数的是输入列表条目，不是 Token；没有推理项或有多个工具调用时，条目数量也会不同。

“结果是 75”不是 Python 自动找出来的，而是模型读取你发过去的历史后理解的。

### 6.3 如果同一个问题需要第三次模型请求呢？

假设用户一次性要求“先算 25 × 3，再把结果乘 5”，模型决定分两次调用计算器：

| 模型循环 | 此次发送的 input |
| --- | --- |
| 第一次 | `history + [U]` |
| 第二次 | `history + [U, R1, F1, O1]` |
| 第三次 | `history + [U, R1, F1, O1, R2, F2, O2]` |

前两次的结果都要留在当前 `turn` 中，所以不能重置它；`history` 没有被修改，每次拼接不会自己多出重复项。

若模型第二次已经给出最终回答，就应立即返回，不会再发生第三次请求；不要为了“凑满 5 次循环”继续调用模型。

## 7. 动手练习：按 TODO 1～7 完成

现在回到 [agent_practice.py](agent_practice.py)，先不看下一节的完整答案。

| TODO | 你要实现什么 | 写完后自问 |
| --- | --- | --- |
| 1 | 加法、乘法计算器 | 字典中的函数能否被调用，或者能否用 if 完成？ |
| 2 | 展开 history，创建带用户消息的 turn | 哪个是旧历史，哪个是新列表？ |
| 3 | 请求模型 | input 是否包含 history 和当前 turn？ |
| 4 | 保存完整输出、筛选工具调用 | 历史是否统一为字典，是否保留了非工具输出？ |
| 5 | 保存完整轮次，返回最终回答 | 有没有误写成 continue？ |
| 6 | 解析参数、执行工具、回填结果 | 参数是否解析，call_id 是否正确，结果是否进入下一次请求？ |
| 7 | 外层调用 chat 并打印答案 | 是否始终传入同一个 session？ |

只完成核心流程即可，不必把扩展版的 Token 统计和 JSON 学习计划搬进练习。

如果已经写过一遍，可以先口头解释每一步，再遮住 `chat()` 的实现重新写一遍。

## 8. 常见错例：为什么会错？

### 8.1 except 后面没有代码

`except RuntimeError:` 后面如果没有缩进代码块，整个文件都会报 `IndentationError`，还没机会请求模型。

练习中可以写成：

```python
try:
    answer = chat(question, session, client)
    print(f"助手：{answer}")
except (RuntimeError, ValueError) as exc:
    print(f"本次失败：{exc}")
```

### 8.2 在模型循环里不断重建“只有用户问题”的输入

每次都发送 `[{"role": "user", "content": question}]`，旧历史和刚执行完的工具结果就都丢了。

正确做法是在循环外准备 `history` 和 `turn`，循环内始终发送 `history + turn`。

### 8.3 turn 初始为空，忘记保存用户问题

即使保存了助手回答，也会丢失问答对应关系；`turn` 的第一项应该是当前用户消息。

### 8.4 把 SDK 对象当成字典，或者直接对混合历史做 JSON 编码

`tool_call.get("name")` 用错了访问方式，SDK 对象应使用 `tool_call.name`。

统一历史时，先 `item.to_dict(mode="json")`，再存入 `turn`，这样 `json.dumps(session.turns)` 才能处理整个历史。

### 8.5 最终回答后 continue，而不是 return

这会继续内层循环，重复请求和保存，最后还可能达到步骤上限。

反复 `session.turns.append(turn)` 保存的是同一个列表的引用，也不是多个独立轮次；正确做法是只保存一次，然后立即返回。

### 8.6 执行了工具，却没有把结果追加进 turn

打印出 75 只是让终端上的人看见；模型要在下一次请求的 `input` 中收到 `function_call_output`，才知道工具执行了什么。

### 8.7 把所有旧工具请求再执行一遍

只执行本次 `response.output` 中新产生的工具请求，不要遍历整个 `history` 查找工具再执行。

旧工具请求和旧结果只是上下文，`/history` 也只是查看，不会重跑工具。

### 8.8 用小写 any 当类型、用 0 表示未知运算

小写 `any` 是 Python 内置函数；这里的返回值注解用 `float` 即可，`Any` 才是 typing 中的任意类型。

未知运算应明确报错，不应伪装成“计算结果为 0”；你使用 `operations[operation](a, b)` 调用字典中的函数，本身是正确的。

## 9. 参考答案：三个函数

先完成练习再看。保留练习文件顶部已有的 imports、`INSTRUCTIONS`、`TOOLS`、`ChatSession` 和运行入口，对照下面三个函数即可。

计算器这里用最直接的 if；继续使用你已有的函数映射字典也可以，只要未知运算明确报错。

这是用于熟悉流程的正常路径示例，不是覆盖所有 API 异常和异常响应的生产模板。

```python
def calculator(operation: str, a: float, b: float) -> float:
    if operation == "add":
        return a + b
    if operation == "multiply":
        return a * b
    raise ValueError(f"不支持的运算：{operation}")


def chat(question: str, session: ChatSession, client: OpenAI) -> str:
    # TODO 2：准备旧历史和当前轮次
    history: list[dict[str, Any]] = []
    for previous_turn in session.turns:
        history.extend(previous_turn)

    turn: list[dict[str, Any]] = [
        {"role": "user", "content": question}
    ]

    for _ in range(5):
        # TODO 3：旧历史 + 当前轮次一起发给模型
        response = client.responses.create(
            model=MODEL,
            instructions=INSTRUCTIONS,
            input=history + turn,
            tools=TOOLS,
        )

        # TODO 4：全部保存为字典，单独收集本次工具请求
        tool_calls = []
        for item in response.output:
            turn.append(item.to_dict(mode="json"))
            if item.type == "function_call":
                tool_calls.append(item)

        # TODO 5：正常结束时只保存一次，然后离开 chat()
        if not tool_calls:
            session.turns.append(turn)
            return response.output_text

        # TODO 6：执行工具，将结果加入当前 turn
        for tool_call in tool_calls:
            if tool_call.name != "calculator":
                raise ValueError(f"未知工具：{tool_call.name}")

            params = json.loads(tool_call.arguments)
            result = calculator(
                params["operation"],
                params["a"],
                params["b"],
            )
            print(f"[工具] calculator({params}) → {result}")

            turn.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": json.dumps(result),
                }
            )

        # 不 return：让下一次模型请求读到刚才追加的工具结果

    raise RuntimeError("已请求模型 5 次，仍未得到最终回答")


def main() -> None:
    with OpenAI(
        api_key=load_api_key(),
        base_url=BASE_URL,
        timeout=30.0,
        max_retries=0,
    ) as client:
        session = ChatSession()  # 在 while 外创建一次
        print(f"模型：{MODEL}；命令：/history /reset /quit")

        while True:
            question = input("\n你：").strip()
            if not question:
                print("请输入问题")
                continue
            if question == "/quit":
                return
            if question == "/history":
                print(json.dumps(session.turns, ensure_ascii=False, indent=2))
                continue
            if question == "/reset":
                session.turns.clear()
                print("历史已清空")
                continue

            # TODO 7：把同一个 session 交给 chat()
            try:
                answer = chat(question, session, client)
                print(f"助手：{answer}")
            except (RuntimeError, ValueError) as exc:
                print(f"本次失败：{exc}")
```

从头到尾复述一遍：外层收问题，内层读历史、发请求、存输出；有工具就执行并回填，没有工具就保存整轮并返回。

## 10. 手动验收：不需要新增测试目录

在核心练习的同一次运行中依次输入：

```text
我叫小明
我叫什么名字？
精确计算 25 乘 3
把结果再乘 5
/history
/reset
/history
我叫什么名字？
/quit
```

检查：

- [ ] 第二次提问能根据历史回答“小明”。
- [ ] 计算时确实出现工具执行日志，而不是只看到模型口头说“我调用了工具”。
- [ ] “把结果再乘 5”时，工具参数中的 a 是 75、b 是 5，结果是 375。
- [ ] reset 前保存了四个完整轮次；不要要求每轮固定六个条目。
- [ ] 工具请求和结果的 call_id 成对，当前轮次包含用户问题和最终回答。
- [ ] 最终回答后回到输入提示，不会继续重复请求同一个问题。
- [ ] reset 后 `/history` 显示 `[]`，后续请求不再包含旧姓名记录。
- [ ] 能区分 history 和 turn，解释为什么 turn 在内层循环中不重置。
- [ ] 两个 ChatSession 的默认列表互不共享。
- [ ] 达到模型请求上限会退出当前任务，不把未完成 turn 当成正常完成轮次保存。

模型可能猜名字，所以 reset 的可靠检查是历史是否真的清空，而不只是看它有没有碰巧答对。

`/history` 展示的是当时的记录，不会重新执行计算器，也不会刷新旧时间查询结果。

## 11. 扩展阅读：掌握核心流程后再看

以下功能属于 [chat_agent.py](chat_agent.py)，不是填空练习的必做项。

```bash
cd /path/to/llm-agent-learning  # 替换为你实际克隆到的目录
uv run python -m day04.chat_agent
```

PyCharm 相应把 Module name 改为 `day04.chat_agent`，工作目录和解释器不变。

### 11.1 整轮裁剪：为什么删除 turn，而不是随便删几个 item？

扩展版保留最近 `MAX_TURNS = 5` 个完整轮次：

```python
session.turns.append(turn)
if len(session.turns) > MAX_TURNS:
    session.turns.pop(0)
```

从 `[T1, T2, T3, T4, T5]` 加入 T6 后，变成 `[T2, T3, T4, T5, T6]`。

整轮删除不会把工具请求和结果拆开，也能保留问答的对应关系。

裁剪发生在本轮完成后：第六轮请求仍能带前五轮历史，第七轮才不再带第一轮。

这是轮数上限，不是精确 Token 上限；一轮特别长仍可能超出上下文容量，旧信息被删后也可能无法再被模型使用。

自动摘要和持久化重要事实以后再学；摘要不等于准确可靠的长期记忆。

### 11.2 Token 统计：一轮不止一次模型请求

扩展版打印每次请求用量和整轮累计用量，`/usage` 查看自启动或最近一次 reset 以来的会话累计值。

不要把第一次工具选择请求的用量，当作整轮总消耗；删除旧历史不会撤销已经发生的 Token 消耗。

核心练习没有 `/usage`；不要为了这一步先增加一套统计结构。

### 11.3 /plan：生成 JSON，再做本地校验

扩展版的 `/plan Python 基础` 是程序约定的命令，不是 Python 或模型自带语法。

程序把它转换成“请按指定格式生成学习计划”的提示，再用以下代码解析：

```python
plan = StudyPlan.model_validate(json.loads(answer))
```

`json.loads` 检查文本能否解析成 JSON；`StudyPlan.model_validate` 再检查字段和约束。

扩展版已定义 `StudyTask` 和 `StudyPlan`：至少有一个任务，每项任务的 minutes 在 5～240 之间。

这只是提示模型输出 JSON，再用 Pydantic 本地校验，不是服务端 Structured Outputs 的严格模式。

校验失败会提示错误，不自动修复或重试；原始问答已经由 chat 保存，所以仍可在历史里查看，但不会把错误计划当成有效 StudyPlan。

可以不花模型额度，直接验证范围错误：

```python
from pydantic import ValidationError
from day04.chat_agent import StudyPlan

try:
    StudyPlan.model_validate(
        {
            "topic": "Python",
            "tasks": [
                {"title": "练习", "objective": "理解循环", "minutes": 1}
            ],
        }
    )
except ValidationError as exc:
    print("minutes=1 被拒绝：", exc.errors()[0]["msg"])
```

项目已经声明 Pydantic 依赖，不需要为本节新增依赖或文件。

### 11.4 结构化输出、Function Calling、业务校验

结构化回答约束“答案长什么样”，例如学习计划有哪些字段；Function Calling 表达“请执行哪个工具、参数是什么”，执行者仍是你的程序。

两者不是互斥关系：工具参数也可以受严格 Schema 约束，但参数格式正确不代表已经执行了工具。[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)

Schema 只能验证其中已经声明的结构和约束，handler 还要检查未覆盖的业务规则、权限和实际状态，例如订单是否属于当前用户、余额是否足够。

不要因为模型输出“看上去是 JSON”就跳过解析，也不要把“通过 Schema”当成“执行一定安全且正确”。

### 11.5 本地历史、previous_response_id、Conversation

- 本地历史：应用自己保存和发送，可按需检查、裁剪和迁移；同时承担历史管理责任，后续输入也会增长。
- `previous_response_id`：引用服务端已有响应串联上下文，省去手工重发完整历史的工作，但依赖服务实现和响应的可用性。
- Conversation 对象：由服务端维护会话，需要另外考虑会话生命周期、删除和权限。

`previous_response_id` 不代表历史 Token 免费；OpenAI 官方说明，响应链中此前的输入仍会计入输入 Token。[Conversation State](https://developers.openai.com/api/docs/guides/conversation-state)

当前两个示例都使用本地历史；尚未验证你使用的阿里云兼容服务是否支持另外两种能力，不能因 SDK 有这些参数就认定服务支持。

这部分了解取舍即可，不要求切换实现或做服务商能力探测。

## 12. 六道自测题：一句话参考答案

1. **模型的“记忆”保存在哪里？**\
   模型依靠请求中的上下文表现出记忆，本项目把历史保存在本地内存的 session.turns 中并随请求发送。

2. **为什么不能只保存 output_text？**\
   工具调用过程中只保存文字会丢失名称、参数和 call_id，但一轮结束后可按需简化成用户问题与最终回答。

3. **previous_response_id 与本地历史有什么取舍？**\
   previous_response_id 依赖服务端保存上下文、管理更省事，本地历史则需要自行维护但更方便裁剪、持久化和迁移。

4. **为什么历史裁剪要以完整 turn 为单位？**\
   整轮裁剪能避免拆散问答及工具请求与结果，留下残缺的上下文。

5. **结构化输出与 Function Calling 有什么区别？**\
   结构化输出约束回答的数据格式，Function Calling 请求程序执行工具，两者可以结合使用。

6. **为什么 Schema 通过后 handler 仍要校验？**\
   满足已声明的结构和约束不等于满足权限、业务规则和实际数据条件，因此 handler 仍要检查。

完成标准：能够独立写出核心 chat 循环，并指着一次工具调用的历史说明每个条目是谁生成、何时加入、下次如何发送。
