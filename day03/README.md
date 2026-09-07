# Day 03：把 Day 02 拆成文件

这一版只做一件事：把 `day02/mini_agent.py` 中已经跑通的助手，拆成容易阅读的几个文件。

仍然使用你的阿里云模型、原来的提示词、计算器和时间工具。没有额外演示模式、JSONL 模块或复杂边界检查。
`dataclass` 用来保存数据，`Protocol` 用来约定客户端的方法；Fake 只在测试里使用。

## 1. Day 02 的代码分别去了哪里？

| Day 02 的内容 | Day 03 的位置 |
| --- | --- |
| 模型名、地址、提示词、`load_api_key()` | [config.py](agent_core/config.py) |
| `client.responses.create()` 和回复整理 | [client.py](agent_core/client.py) |
| 计算器、时间、工具 schema、`execute_tool()` | [tools.py](agent_core/tools.py) |
| `run_agent()` 的循环 | [runner.py](agent_core/runner.py) |
| 读取输入、创建客户端、异常提示、输出答案 | [mini_agent.py](mini_agent.py) |
| 新的数据类 | [models.py](agent_core/models.py) |
| 客户端方法约定 | [ports.py](agent_core/ports.py) |
| 三种基本流程错误 | [errors.py](agent_core/errors.py) |

建议先对照 Day 02 看 `tools.py`，然后看 `runner.py`，最后看 `client.py` 和入口。
不必先研究所有类型标注。

详细教程 [DAY03.md](DAY03.md) 已按这套实现统一，可以这样读：

- 第 11 节：四个数据类的实际字段（`AgentResult` 没有 `model` 字段）；
- 第 15～17 节：同一套 `ModelClient` / `FakeModelClient` 接口；
- 第 22 节：可整段运行的离线两轮示例，检查历史和 Token 累计；
- 第 18、25 节：当前存在的测试名称和运行命令。

标为“源码节选”的代码用于对照文件；标为“完整离线示例”的代码已补齐 import，可单独运行。
JSONL、异步和面试拓展都是选读，不需要添加到这个助手。

## 2. 运行真实助手

在项目根目录执行：

```bash
cd /path/to/llm-agent-learning  # 替换为你实际克隆到的目录
uv run python -m day03.mini_agent "精确计算 12345 * 678"
```

不传问题时，会通过 `input()` 提示输入：

```bash
uv run python -m day03.mini_agent
```

注意：这和 Day 02 一样会发起真实 API 请求，可能消耗你的模型额度。
继续读取 `DASHSCOPE_API_KEY`、`ALIYUN_API_KEY`，或项目根目录的 `aliyun_api_key` 文件，
不需要另配一套 Key。仍支持 `LLM_MODEL` 和 `LLM_BASE_URL` 环境变量。

PyCharm 运行配置选择 **Module name**：`day03.mini_agent`；
工作目录是项目根目录，解释器使用根目录的 `.venv/bin/python`。
不要直接把 `runner.py` 作为入口。

## 3. 新增的概念只看这三点

**dataclass：把数据打包。**

`ToolCall` 保存一次工具请求；`ModelReply` 保存一轮回复；
`TokenUsage` 保存用量；`AgentResult` 保存最后的答案和累计用量。
`default_factory=list` 为每个实例单独创建列表。

**Protocol：约定一个方法。**

`run_agent()` 要求传入的 `client` 有签名兼容的 `create_response(input_items=..., tools=...)` 方法，并返回 `ModelReply`。
真实客户端请求 API，Fake 返回预设答案；runner 的调用写法不用变。

**拆分：每个文件放一种相关的代码。**

`client.py` 负责解析 SDK 回复，`tools.py` 执行工具，`runner.py` 决定下一步做什么。
它们通过普通的函数调用和对象传递协作，没有额外框架。

## 4. 循环仍然是 Day 02 的循环

```text
用户问题 → 请求模型 → 追加模型完整输出
                      ├─ 没有工具请求：返回答案
                      └─ 有工具请求：执行工具、追加结果，再请求模型
```

关键的一行只是改了变量名：

```python
# Day 02
input_items += response.output

# Day 03
input_items += reply.output_items
```

`output_items` 保留 SDK 的完整输出，`tool_calls` 是从中取出的工具请求。
保留完整输出、通过相同的 `call_id` 回传工具结果，遵循
[官方工具调用流程](https://developers.openai.com/api/docs/guides/function-calling)。
这一步不能简单地只保留最终文本，否则会丢掉工具请求或 reasoning 等项。

工具参数在 `client.py` 里由 JSON 字符串转成字典，因此 `tools.py` 直接执行
`handler(**tool_call.arguments)`。工具结果再由 runner 转成 JSON 字符串回传。

学习版保留了每轮输入和工具结果的 `print()`，没有增加日志系统。
最大轮数也沿用 Day 02：循环结束还没有最终答案时抛出异常。

## 5. 离线学习和验证

只看流程、不消耗模型额度：

```bash
uv run pytest -q -s day03/tests/test_runner.py
```

运行全部基础测试：

```bash
uv run pytest -q day03/tests
```

总共 13 个直观测试，保留在 `test_models.py`、`test_tools.py`、`test_runner.py`。
最值得看的是 `test_tool_call_then_answer()`：在它只模拟一次工具调用、没有 reasoning 项的条件下，
检查历史从 1 项变成 3 项，以及工具结果是否为 42。测试里的 250 Token 是人为设置的用量总和，不是真实消耗。

直接运行这个测试并查看日志：

```bash
uv run pytest -q -s day03/tests/test_runner.py::test_tool_call_then_answer
```

Ruff 和 mypy 仍可以运行，但先读懂主流程即可：

```bash
uv run ruff check day03
uv run mypy day03
```

原来的 `playground.py` 和 Day 02 没有修改。
更详细的 Python 语法说明仍在 [DAY03.md](DAY03.md)，JSONL 和异步部分只作为独立练习。

## 旧版备份

上一版额外的 demo、JSONL、异步演示和边界测试已从 Day 03 移除。
修改前的完整目录临时备份在：

```text
/private/tmp/day03-before-simplify.simZ2O/day03
```

如需找回旧代码，可以从那里复制；临时目录可能被系统清理，需长期保留时请另行存放。
