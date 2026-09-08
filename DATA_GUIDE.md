# 文件与数据：从哪里来，运行后到哪里去？

课程中的业务资料、门店、用户和工单均为虚构。先区分三种来源：**人提前写好的输入、程序运行生成的结果、外部服务或下载的模型**。

## 1. 最容易混淆的例子：Day 08

```text
人编写 rag_cases.json：问题 + 应找到的资料编号
人编写 day05/knowledge/：被搜索的原文
                 ↓
运行 day08.eval_retrieval：调用检索器，对照标准证据评分
                 ↓
程序写 reports/lexical-k1.json：实际找到什么 + 得分
```

`cases` 是测试用例，`dataset` 是一组用例；`report` 是执行后的报告。
`lexical` 表示关键词检索，`k1` 表示每题最多返回一块。修改成绩单不会提高检索能力；修改代码或输入后，重新运行才会得到新成绩。

## 2. 各课的数据来源和产物

下表的路径均相对项目根目录。运行生成的文件首次运行前可能不存在。

| 课程 | 预先提供或由你输入 | 程序产生什么 |
|---|---|---|
| 01 | 主题、hello_llm.py 中的提示词、你的服务配置 | 服务返回回答与用量，打印到终端 |
| 02 | 问题、mini_agent.py 中的工具说明 | 模型工具请求、本地工具结果、最终回答 |
| 03 | tests/ 中人工编写的 Fake 回复与断言 | pytest 的通过/失败结果；助手另走真实服务 |
| 04 | 逐轮输入的问题 | 内存 session；退出后不保存历史 |
| 05 | [knowledge/](day05/knowledge/) 中两份原文 | 内存 chunks、匹配分、选中原文与 Prompt |
| 06 | Day 05 原文；vector_basics.py 中人工向量 | build_index 生成 data/qdrant/ 与 data/index.json；模型权重下载到 data/models/ |
| 07 | [knowledge.json](day07/knowledge.json) 中六块门店资料 | 当前进程的两路排名、内存向量库和 Prompt |
| 08 | [rag_cases.json](day08/datasets/rag_cases.json)，含人工标准证据 | eval_retrieval 生成 reports/lexical-k1.json、lexical-k2.json |
| 09 | langchain_agent.py 的 EXAMPLES 与 demo_model.py 预设回复；Day 05 原文 | LangChain 实际执行乘法/检索并打印消息；--ask-model 才请求真实服务，不生成报告 |
| 10 | graph_demo 的 a/b；两间教室桌椅数；booking_data.json 的虚构预约/手册与预设排查替身 | 状态、容量汇总；组合实验的工具消息、证据检查和草稿，只打印，不保存工单 |
| 11 | 你输入的草稿和审批决定 | data/checkpoints.sqlite、data/tickets.sqlite |
| 12 | [tickets.py](day12/tickets.py) 中 T001/T002 静态记录 | MCP 请求结果，打印；不自动新增工单 |
| 13 | 你明确输入的偏好 | data/memory.sqlite |
| 14 | [agent_cases.json](day14/datasets/agent_cases.json) 中人工输入和答案 | eval_agent 生成 reports/baseline.json 或 fault.json |
| 15 | 固定本地检索/乘法；源码中假设的费用数据 | logs/随机编号.jsonl，实际计时；假设费用只打印 |
| 16 | gateway.py 中人工编写的 ATTACKS 用例 | 实际工具结果与比较结果，只打印 |
| 17 | Day 05 原文；--tamper 可故意改坏摘录 | 内存证据、审核结果与摘录，只打印 |
| 18 | 你发送的 HTTP JSON；Day 05 原文 | JSON/SSE 响应，内存会话计数 |
| 19 | [design/](day19/design/) 中人工编写的四份设计稿 | 阅读与修改设计，本课没有生成脚本 |
| 20 | Day 07 门店资料、Day 12 静态工单、用户命令 | capstone/data/ 中偏好、审批与日志 |
| 21 | verify.py 中人工编写的检查条件 | 临时测试状态；reports/local.json 与 local.md，--hybrid 则另写 hybrid 文件 |
| 22 | [demo.md](day22/demo.md)、[interview.md](day22/interview.md) 参考稿 | 你根据实际结果整理作品说明，不自动发布 |

## 3. JSON 中几个常见字段

| 字段 | 来源和含义 |
|---|---|
| `question`、`a`、`b` | 人提供的测试输入 |
| `relevant_chunk_ids` | 人读过原文后标出的标准证据 |
| `expected` | 人编写的预期结果 |
| `purpose` | 这道题想检查什么，仅作说明，不参与判分 |
| `retrieved`、`answer`、`events` | 被测程序实际返回的资料、答案或执行轨迹 |
| `checks`、`passed`、`mean` | 评估程序对照预期后计算的结果 |
| `dataset`、`generated_at` | 这份报告读了哪套题、何时生成 |

Day 07 的 `north/booking.md#1` 是 JSON 中的逻辑来源编号，正文就在同条记录的 `text`，不对应一个必须存在的 Markdown 文件。
Day 05/08 的 `hours.md#1` 则来自实际 Markdown 文件按空行切出的第一块。两套编号不能混用。

## 4. 改了数据之后怎么做？

- 改 Day 05 原文：重新审核 Day 08 标注；若使用 Day 06 向量库，再运行 build_index。
- 改评估用例：保留唯一 id，人工确认预期，重新运行对应评估程序。
- 重新运行评估：同名报告更新；要前后对比，先自行保留旧报告或使用版本管理。
- 重新练审批/偏好：使用新的任务编号或临时数据目录，不必删除旧练习记录。

真实项目常从用户问题和失败记录中整理用例，由了解业务的人标注，再定期回归。课堂用少量手写数据，把这条来源链完整展示出来。

[返回总路线](README.md)
