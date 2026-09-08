# Day 02：模型提出请求，Python 执行工具

> 今天让助手使用计算器和时间工具，观察“模型 → 工具 → 模型”的循环。
> 运行会请求真实模型；计算与读取时间由本地 Python 执行。

## 1. 为什么回答问题还要工具？

用户问“精确计算 125 乘 48”。模型可以生成一个数字，但程序可以执行乘法得到可核对的结果。
用户问“现在上海几点”，时间应来自当前时钟。

Function Calling（工具调用）的作用，是让模型用约定格式提出“调用哪个函数、传什么参数”。应用收到请求后执行函数，把结果送回模型，再生成回答。

```text
用户问题 → 模型提出 calculator 请求 → Python 算出 6000
                                      ↓
用户看到回答 ← 模型读取工具结果 ← 回传同一个 call_id
```

## 2. 谁写什么，谁生成什么？

| 内容 | 来源 |
|---|---|
| [mini_agent.py](mini_agent.py) | 课程提供的完整脚本 |
| `calculator`、`get_current_time` | 程序员写的普通 Python 函数 |
| `TOOLS` | 程序员写的工具说明，告诉模型名称和参数格式 |
| `TOOL_HANDLERS` | 本地“工具名 → 函数”的对应表 |
| 工具请求的名称、参数、`call_id` | 模型服务在运行时返回 |
| 工具结果 | Python 实际执行后产生 |
| 最终回答 | 模型根据结果生成；只打印，不自动保存文件 |

传入 `TOOLS` 只提供说明；本课的 SDK 不会替你执行这些本地函数。

## 3. 运行并看轨迹

在项目根目录运行，配置沿用 Day 01：

```bash
uv run python -m day02.mini_agent "请精确计算 125 乘以 48"
uv run python -m day02.mini_agent "现在上海几点？"
```

计算例应能观察到以下过程。这里是结构示意，参数顺序、措辞和调用编号以本次输出为准：

```text
[step 1] 请求模型
[tool] calculator，参数 operation=multiply、a=125、b=48
[tool result] ok=true、result=6000
[step 2] 请求模型
最终回答：125 × 48 = 6000
```

6000 来自 Python 乘法；当前时间来自机器时钟。若模型没有按要求调用工具，记录这次失败，不要只因最终数字正确就认定实验成功。

## 4. Schema 是工具参数的说明书

`TOOLS` 中的 `parameters` 使用 JSON Schema 描述输入。以计算器为例：

| 字段 | 约定 |
|---|---|
| `operation` | add、subtract、multiply、divide 之一 |
| `a`、`b` | 两个数字 |
| `required` | 哪些字段必须提供 |
| `additionalProperties: false` | 不接受额外字段 |

`strict=True` 请求服务按严格约束产生参数，具体支持情况取决于服务。它不能代替应用的参数与业务检查：例如除数为 0，虽然类型是数字，仍不能执行除法。

源码里的调用参数通常先是 JSON 字符串：

```python
arguments = json.loads(tool_call.arguments)
result = handler(**arguments)
```

`json.loads()` 把字符串变成字典；`**arguments` 把字典展开成命名参数。比如 `{"operation":"multiply","a":125,"b":48}` 相当于调用 `calculator(operation="multiply", a=125, b=48)`。

## 5. call_id 为什么必须原样带回？

假设模型连续提出两次计算。只有“结果是 6000”还不够，服务需要知道它对应哪次调用。

```python
# run_agent() 中的源码节选。
input_items.append({
    "type": "function_call_output",
    "call_id": tool_call.call_id,
    "output": tool_result,
})
```

`call_id` 是这次调用的关联编号，不能随意重造；`output` 是已经序列化好的工具结果字符串。
`type` 用来区分这是一条工具结果，而非用户又提了一个问题。

## 6. Agent Loop：为什么需要循环？

打开 `run_agent()`，按这个顺序读：

1. 把用户问题放入 `input_items`。
2. 带着当前历史和工具说明请求模型。
3. 把 `response.output` 的完整输出追加到历史。
4. 如果没有工具调用且有文字，返回最终回答。
5. 如果有工具调用，逐个执行并追加结果，进入下一次请求。

`response.output_text` 是便于阅读的文字；`response.output` 还可能包含工具请求及其他输出项。保留完整输出，才能让下一次请求接上刚才的过程。[官方工具调用流程](https://developers.openai.com/api/docs/guides/function-calling)

`MAX_STEPS=5` 是本课最多请求模型五次，达到上限仍未回答就报错。一次回复可能提出多个工具请求，因此它不等于最多执行五次工具。

这份入门脚本把客户端建在模块顶部，导入时就会读取配置。Day 03 会把创建客户端移到入口，便于离线测试。

## 7. 练习三个不同的分支

```bash
uv run python -m day02.mini_agent "用一句话解释 Python 列表"
uv run python -m day02.mini_agent "请用工具计算 10 除以 0"
uv run python -m day02.mini_agent "查询 Mars/Olympus 时区的当前时间"
```

第一题通常无需工具；后两题用来观察错误如何回到模型。模型可能先解释问题而不调用，因此同时检查实际工具记录。
工具失败会返回 `ok=false`；模型应说明失败，不能把错误包装成成功。

本课工具是有限的数学运算和时钟读取，没有开放任意命令执行。不要用 `eval()` 执行模型生成的文本。

## 8. 真实项目里一般怎么做？

例如订单助手，工具函数会调用订单接口，而不是这里的计算器。业务程序维护允许使用的工具、校验参数，并根据登录用户检查订单访问权；模型负责提出调用建议。

读取状态和修改订单的风险不同。需要人确认的修改，先准备具体内容，再经审批执行。Day 11 和 Day 16 会分别实现暂停审批与执行前检查。

## 9. 自测与完成标准

1. 模型返回 `calculator`，乘法已经执行了吗？
2. 为什么不能只把最终文字保留到下一轮？
3. 工具返回失败，是否应假装成功以便结束循环？

<details>
<summary>参考答案</summary>

1. 还没有，`execute_tool()` 才真正调用 Python 函数。
2. 会丢掉工具调用等过程项，结果也可能找不到对应请求。
3. 不应，把失败结果回传，让模型说明原因；循环仍受步数限制。

</details>

能追踪一笔“问题 → 参数 → 工具结果 → 最终回答”，并解释一条失败，就完成今天。

[上一课：Day 01](../day01/DAY01.md) · [下一课：Day 03](../day03/DAY03.md)
