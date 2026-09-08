# Day 03：把一个脚本拆成能离线测试的模块

> 今天保留 Day 02 的工具循环，只把相关代码分开，并用预设回复测试它。
> 主线先读本页；Python 写法不熟时再查 [语法速查](PYTHON_REFERENCE.md)。

## 1. 为什么已经能运行，还要拆文件？

假设你只改了“怎样处理工具结果”，却必须每次连接模型才能检查，还可能因回复不同而难以复现问题。
我们希望循环、工具和网络请求可以分别检查。

```text
入口组装对象 → runner 运行循环 → client 请求模型
                     ↓
                  tools 执行工具
```

测试时把真实 client 换成 Fake（测试替身），让它按预先写好的顺序返回回复。工具和循环仍执行实际代码。

## 2. 文件分别从哪来？

这些文件都已随课程提供；今天先对照读，不必从空目录重写：

| 文件 | 谁负责什么 |
|---|---|
| [mini_agent.py](mini_agent.py) | 读取用户输入、创建客户端、打印结果 |
| [config.py](agent_core/config.py) | 从 Day 02 移来的模型配置、提示词和 Key 读取 |
| [client.py](agent_core/client.py) | 请求真实服务，把 SDK 回复整理成内部数据 |
| [runner.py](agent_core/runner.py) | Day 02 的循环，改为通过参数接收 client |
| [tools.py](agent_core/tools.py) | 计算器、时钟、工具说明和执行函数 |
| [models.py](agent_core/models.py)、[ports.py](agent_core/ports.py) | 保存数据的类，以及客户端方法约定 |
| [tests/](tests/) | 人工编写的测试；Fake 回复与预期值也由人提供 |
| [playground.py](playground.py) | 个人语法练习，与参考助手入口分开 |

今天没有评估 JSON 文件或数据库。pytest 把检查结果打印在终端；测试中的回复不来自真实模型。

## 3. 先跑一个离线测试

从项目根目录执行：

```bash
uv run pytest -q -s day03/tests/test_runner.py::test_tool_call_then_answer
```

`pytest` 运行测试函数；`-q` 缩短汇总，`-s` 让程序的过程打印显示出来。

打开 [test_runner.py](tests/test_runner.py) 中同名函数，看三件事：

1. 准备两次预设回复：先要求计算 6×7，再返回“42”。
2. 把 Fake 传入 `run_agent()`，实际执行计算器。
3. 用 `assert` 核对答案、调用次数、历史和用量累计。

预设答案“42”和测试里的 Token 数是人工数据。通过只说明循环正确处理了这组回复，不代表真实模型必然选对工具。

## 4. 三个 Python 概念，足够读主线

**dataclass：把相关数据打包。**
`ToolCall` 保存调用编号、工具名和参数；`ModelReply` 保存一轮回复；`AgentResult` 保存最终结果。
普通字典用 `item["name"]` 读字段，数据类用 `item.name`。

**依赖注入：把需要的对象作为参数传进来。**

```python
# 调用方式节选，client 由入口准备。
result = run_agent(question, client=client, tools=TOOLS)
```

runner 只管调用这个 client。入口传真实客户端就联网，测试传 Fake 就按预设回复运行。

**Protocol：约定客户端提供什么方法。**
`ModelClient` 约定 `create_response(input_items=..., tools=...)` 返回 `ModelReply`。
真实客户端和 Fake 都提供这个方法，因此 runner 不必为测试重写一套循环。类型标注帮助人和检查工具理解代码，本身不做完整运行时校验。

## 5. 一轮数据怎样走？

```text
SDK response.output
  → client 保留完整输出到 reply.output_items
  → client 解析工具参数到 ToolCall.arguments 字典
  → runner 追加完整输出，调用 execute_tool
  → runner 把工具结果转成 JSON 字符串，再请求 client
```

注意两个方向：模型工具参数从 JSON 字符串变成字典；工具结果从字典变成 JSON 字符串。

本课内部字段叫 `input_items`，发给 SDK 时仍是 `input=input_items`。变量名由我们取，接口字段名由 SDK 约定，不能混着改。

`used_tools` 记录尝试调用的工具名，包含失败调用。`usage` 累加收到的输入/输出 Token；当前入门数据类以 0 为初始值，未单独标记服务缺失用量，不能拿缺失值当真实零成本。Day 15 再专门处理用量范围。

## 6. 真实运行与离线测试是两个入口

```bash
# 离线：运行现有基础测试，不需要 Key。
uv run pytest -q day03/tests

# 联网：沿用 Day 01/02 的模型服务配置。
uv run python -m day03.mini_agent "精确计算 6 乘以 7"
```

模块方式 `-m day03.mini_agent` 从项目根目录找到入口。不要直接运行 `runner.py`，它只定义循环函数。

入口执行时才创建客户端并读取 Key；导入 `models.py` 或 `runner.py` 不会调用 API。
失败分为输入为空、模型回复无效、超过步数等情况，定义在 [errors.py](agent_core/errors.py)。工具内部失败则通过结果回传给循环。

## 7. 用已有检查帮助修改

```bash
uv run ruff check day03
uv run mypy day03
```

Ruff 查未使用导入等常见问题；mypy 查类型约定。它们不证明业务正确，仍需运行测试。
个人练习可能尚未通过这些检查，先定位报错文件，区分正在填写的练习与参考模块。

一个测试最简单的结构是：**准备输入 → 调用函数 → 核对预期**。不要把预期值直接设成被测函数刚刚返回的值。

## 8. 真实项目里一般怎么做？

把模型请求、业务工具和流程控制分开后，可以先用 Fake 稳定检查流程，再用少量真实调用检查接口与模型行为。
例如测试订单查询失败，Fake 负责固定“模型要查订单”，工具替身负责返回超时，再检查助手有没有错误地宣布成功。

小项目不需要为了分层增加很多接口。这里保留一个客户端约定，是因为“真实调用与离线测试”已经有明确的替换需求。

## 9. 自测与完成标准

1. Fake 的回复由谁生成？通过测试证明了什么？
2. `tools.py` 已收到字典，为什么不用再 `json.loads()`？
3. 若只改工具实现，应先看哪组测试？

<details>
<summary>参考答案</summary>

1. 由测试作者提前编写；证明程序对这组输入的处理符合预期，不是模型能力评分。
2. `client.py` 已完成解析，再解析字典会类型错误。
3. 先运行 `day03/tests/test_tools.py`，再检查受影响的循环路径。

</details>

能运行离线测试、指出 Day 02 各段代码去了哪里、解释一次参数与结果转换，就完成主线。

[上一课：Day 02](../day02/DAY02.md) · [下一课：Day 04](../day04/DAY04.md)
