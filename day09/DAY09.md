# Day 09：用 LangChain 接起模型与工具

> 今天把 Day 02 的工具循环交给 LangChain，再把 Day 05 的检索器包成工具。
> 先跑预设回复，确认谁在执行；有服务配置后再切换真实模型。下一课学习 LangGraph。

## 1. 为什么现在学 LangChain？

你已经知道如何请求模型、执行工具和检索资料。再搭第二个助手时，往往又要写一遍“找工具调用、执行、把结果送回模型”的循环。

LangChain 提供模型接口、工具封装和现成 Agent 循环，让这些通用代码可以复用。你仍然负责工具实际做什么、资料从哪里来，以及怎样判断结果正确。

| 名称 | 解决什么问题 | 本课对应什么 |
|---|---|---|
| LangChain | 怎样较快地接起模型和工具？ | `create_agent` 组织工具循环 |
| LangGraph | 怎样明确控制状态、分支和暂停恢复？ | 下一课从节点和边开始学习 |

LangChain 的 Agent 底层使用 LangGraph。以后需要自定义流程时，可以直接操作 LangGraph；两者也可以组合使用。[官方定位](https://docs.langchain.com/oss/python/concepts/products)

本课先使用现成循环；[下一课开头的关系图](../day10/DAY10.md)会说明，怎样从 LangChain 的 `create_agent` 过渡到自己定义 LangGraph 流程。

## 2. 先认识五个词

| 词或写法 | 简单含义 |
|---|---|
| `ChatOpenAI` | LangChain 的模型适配器，负责把统一消息格式转成服务请求 |
| `@tool` | 把 Python 函数包装成带名称、说明和参数约定的工具 |
| `create_agent` | 创建包含模型调用、工具执行和结果回传的 Agent |
| `invoke` | 运行这个模型、工具或 Agent；调用谁，执行的范围就不同 |
| `messages` | 消息列表，保存用户问题、模型工具请求、工具结果和最终回复 |

工具装饰后，用 `multiply.invoke({"a": 25, "b": 3})` 单独执行；这只运行乘法，不会调用模型。
`agent.invoke(...)` 则运行整个 Agent 循环，内部可能多次调用模型。

**工具循环**是指：请求模型，若它要求用工具，就执行工具、带着结果再次请求模型；直到模型不再要求工具而给出最终回答。这个循环由 `create_agent` 内部实现，所以本课主程序里看不到手写的 `while`。

## 3. 文件、问题和结果分别从哪来？

| 内容 | 来源与用途 |
|---|---|
| [langchain_agent.py](langchain_agent.py) | 课程参考代码，定义两个工具、Agent 入口与三个固定实验 |
| [demo_model.py](demo_model.py) | 人工编写的测试替身，预先指定工具请求，再用固定模板展示实际工具结果 |
| Day 03 的 `calculator` | 已有的普通 Python 计算函数，本课乘法工具复用它 |
| [Day 05 原文](../day05/knowledge/)与检索器 | 已有的真实本地文件和关键词检索实现 |
| 终端消息 | LangChain 本次执行后返回的消息；本课不保存评估报告或历史数据库 |

**预设回复不理解问题。** `--case` 选择人写好的问题和工具参数；乘法与文件检索真实执行，最终文字由固定模板拼接工具结果。它帮助检查框架流程，不能用于评价模型能力。

## 4. 先跑乘法，观察一次完整循环

从项目根目录执行，新增的 `langchain` 依赖组会安装 LangChain 及模型适配器：

```bash
uv run --group langchain python -m day09.langchain_agent --case math
```

首次需要安装依赖，之后实验本身无需 Key，也不请求模型服务。关键过程如下，省略部分 JSON 字段：

```text
用户：精确计算 25 乘 3。
工具请求：multiply，参数 a=25、b=3，编号 demo-call-1
工具结果：result=75，关联编号 demo-call-1
最终回复：预设回复实验结束，实际工具返回：……75……
```

这次循环中，替身会被调用两次：

```text
第一次调用替身：提出 multiply 请求
          ↓
LangChain 找到 multiply 并执行 Python 函数
          ↓
LangChain 把实际结果包装为 ToolMessage，再次调用替身
          ↓
第二次调用替身：用固定模板展示结果，不再请求工具，循环结束
```

工具调用名称和参数来自预设数据；数字 75 来自乘法代码；调用和结果之间的传递由 LangChain 完成。

如果第二次回复仍有工具请求，框架就继续执行并再次调用模型。因此一次 `agent.invoke()` 可以包含多次模型调用；本例执行一次工具，调用两次替身。

## 5. 看代码：哪些由框架接手了？

先在 `langchain_agent.py` 找两个工具。乘法的关键代码是：

```python
@tool
def multiply(a: Number, b: Number) -> dict:
    """精确计算两个 -1000 到 1000 之间整数的乘积。"""
    return calculator("multiply", a, b)
```

`Number` 是本课定义的类型约束：严格整数，范围 -1000～1000。函数名成为工具名，文档字符串说明用途，参数标注帮助生成 Schema；装饰器没有生成乘法算法。[工具说明](https://docs.langchain.com/oss/python/langchain/tools)

再看 `build_agent()` 中的主体，省略调用上限配置：

```python
agent = create_agent(
    model=model,
    tools=[multiply, search_knowledge],
    system_prompt=SYSTEM_PROMPT,
)
result = agent.invoke({
    "messages": [{"role": "user", "content": "精确计算 25 乘 3。"}]
})
```

本课运行接口依据 [LangChain Agent 文档](https://docs.langchain.com/oss/python/langchain/agents)，完整实现以源码为准。

| Day 02 自己写的部分 | 本课由谁负责 |
|---|---|
| 请求模型，读取工具名称和参数 | `create_agent` 与模型适配器 |
| 按名称找函数，执行后继续循环 | `create_agent` |
| 组织工具结果并关联调用编号 | LangChain 的工具消息 |
| 乘法、读文件、检索算法 | 我们编写的工具函数 |
| 权限、业务审批、效果评估 | 仍需应用设计，后续课程分别实现 |

“少写了循环”不等于“一次请求就完成”，也不等于工具一定选择正确。

## 6. 再把检索器变成一个工具

```bash
uv run --group langchain python -m day09.langchain_agent --case knowledge
uv run --group langchain python -m day09.langchain_agent --case missing
```

| 实验 | 人工预设的查询 | 工具实际结果 |
|---|---|---|
| knowledge | 周末几点关门？ | 返回 `hours.md#1` 等候选，可从原文看到周末 18:00 关门 |
| missing | WLAN 怎么用？ | `status=no_evidence`、`results=[]`，关键词没有匹配上 |

`search_knowledge()` 直接复用 Day 05 的读取、切块和检索函数，最多返回两块，并保留 `source` 和 `text`。
这使 Agent 可以把“搜索资料”当成一个工具，但检索算法没有变；Day 08 的 WLAN 失败也不会因换成 LangChain 自动消失。

注意 `missing` 的原文其实有网络说明。`no_evidence` 在本课只表示“此次没有找到候选”，不能理解成“知识库确定没有答案”。

## 7. 消息列表怎样读？

运行结束后的 `result["messages"]` 中，会依次出现：

| 消息类型 | 本次含义 |
|---|---|
| `HumanMessage` | 用户提出问题 |
| `AIMessage`，含 `tool_calls` | 模型或替身提出工具请求；不代表工具已经执行 |
| `ToolMessage` | 框架执行工具后得到的结果，`tool_call_id` 对应原请求编号 |
| `AIMessage`，无工具调用 | 本轮收尾回复 |

最后一句话只是过程的一部分。检查工具是否真正执行，要同时看请求和 `ToolMessage`。
本课每次启动新建 Agent，没有配置检查点，也没有把旧消息传入下一次运行，因此不会跨命令记住历史。

## 8. 有配置后再接真实模型

```bash
uv run --group langchain python -m day09.langchain_agent --ask-model "精确计算 12 乘 4。"
uv run --group langchain python -m day09.langchain_agent --ask-model "周末几点关门？请给来源。"
```

`--ask-model` 把 `DemoChatModel` 换成 `ChatOpenAI`，沿用 Day 03 的地址、模型名和 Key 读取方式。只有走这个分支才读取凭证和发送请求，会消耗相应服务额度。

本课显式设置 `use_responses_api=True`，与前面的 Responses 接口保持一致。适配器名称不是服务地址：请求仍发往你的 `LLM_BASE_URL`，不是自动改用 OpenAI 服务。配置的服务需要支持对应接口及工具调用。[适配器说明](https://docs.langchain.com/oss/python/integrations/chat/openai)

真实模型下，工具名称、参数和最终文字由服务返回。核对乘法参数与结果、引用是否来自检索原文；预设实验通过不能代替这一步。

源码还用 `ModelCallLimitMiddleware` 限制每次运行最多调用模型 4 次，超限报错；`middleware` 可以理解成围绕循环附加的控制逻辑。客户端每次尝试超时 30 秒、不自动重试，这些限制不是整个任务的总耗时上限。图步数保护另设为 30，也不等于模型调用次数。

## 9. 真实项目里怎样选？

如果需求是“一个模型配几个工具”，可以先用 `create_agent`。当需求变成“创建草稿 → 等人批准 → 再写入”，就需要明确的状态与恢复流程，下一课开始学习怎样用 LangGraph 表达。

原有检索器、业务函数和评估用例仍可以复用。框架主要帮助组织调用，资料质量、工具权限和失败检查还要继续处理。

## 10. 小练习与完成标准

1. 把 `EXAMPLES["math"]` 的问题和参数一起改成 12×4，预设实验应看到哪个工具结果？
2. 为什么 `--case missing` 的失败不会被 LangChain 自动修好？
3. 只看最终回复里有“75”，能否证明框架执行过乘法？
4. `multiply.invoke(...)` 与 `agent.invoke(...)` 的区别是什么？

<details>
<summary>参考答案</summary>

1. 48，由真实乘法产生，再被固定模板展示。预设数据不会从问题文字中自动提取新参数。
2. 仍使用相同关键词检索算法，没有增加语义匹配能力。
3. 不能，还要检查工具请求、参数以及对应的 ToolMessage。
4. 前者直接执行一个工具；后者运行模型与工具的循环。

</details>

能跑通三个预设实验、分清人工数据与实际执行、找到框架接手的循环，就完成主线。
复习名词见 [课程词汇表](../GLOSSARY.md#tools)；`demo_model.py` 的继承写法只作为测试替身参考，不要求今天背下来。

[上一课：Day 08](../day08/DAY08.md) · [下一课：Day 10](../day10/DAY10.md)
