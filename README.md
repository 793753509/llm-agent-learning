# LLM Agent：22 天 Python 实战课程

这套课程从一次模型请求开始，逐步学习工具调用、RAG、工作流和服务接口，最后组成一个“青禾自习室助手”。22 天表示学习顺序，可以按自己的进度完成。

Day 09 新增 LangChain 入门，放在 RAG 评估之后、LangGraph 之前；原 Day 09～21 已顺延为 Day 10～22，目录与运行命令同步更新。

## 先知道自己在做什么

每课先回答四件事：**为什么需要它、输入从哪来、运行哪个程序、结果由谁生成**。然后做一个小实验，最后用一小段说明它在真实项目中的用途。

- `.py` 是课程已提供的参考代码，文档只解释关键片段，不必复制整份实现。
- `knowledge` 是待查询资料；`datasets/*_cases.json` 是人工编写的测试用例。
- `reports` 是程序运行后写出的评估结果；修改用例或代码后应重新生成。
- `data`、`logs` 通常保存本地运行状态，具体是否持久化以各课说明为准。

不清楚某个文件从哪里来时，查 [文件与数据来源表](DATA_GUIDE.md)。例如 `rag_cases.json` 是“考题”，`eval_retrieval.py` 是“执行和评分程序”，`lexical-k1.json` 是“关键词检索每题最多一块的成绩单”。

每天复习时可用 [课程关键词汇表](GLOSSARY.md)：按主题整理缩写、英文全称和一句话解释，★ 标出优先掌握项，末尾对照容易混淆的概念。

## 准备环境

使用 Python 3.10+ 和 uv。所有命令都在项目根目录执行：这个目录同时包含 `pyproject.toml`、`README.md` 和 `day01`～`day22`。

```bash
uv sync --locked
uv run python -m day01.hello_llm --help
```

`python -m day05.rag_baseline` 表示运行 `day05/rag_baseline.py`。不要先进入 day05 再执行，否则 Python 可能找不到外层包。
PyCharm 的工作目录同样选择项目根目录，解释器选择该目录下的 `.venv/bin/python`，运行方式选 Module name。

`pyproject.toml` 声明依赖，`uv.lock` 固定具体版本。课程已定义可选依赖组，按当天命令使用即可：

| 依赖组 | 用途 | 安装方式 |
|---|---|---|
| 基础 | SDK、Pydantic、开发检查工具 | `uv sync --locked` |
| `rag` | 本地 Embedding、Qdrant | `uv sync --locked --group rag` |
| `langchain` | LangChain Agent、模型适配器 | `uv sync --locked --group langchain` |
| `workflow` | LangGraph、MCP | `uv sync --locked --group workflow` |
| `api` | FastAPI、Uvicorn、HTTP 测试 | `uv sync --locked --group api` |

运行时也带当天需要的 `--group`。同一终端做跨课程验证时可同时选多个组，避免同步时移除尚需使用的依赖。

## 哪些实验会请求模型？

| 路径 | 模型参与方式 |
|---|---|
| Day 01～04 的助手 | 请求你配置的生成模型；Day 03 的 Fake 测试离线 |
| Day 05、08、10～22 默认实验 | 不调用生成模型，使用本地资料、规则或模拟业务数据 |
| Day 09 默认实验 | LangChain 执行真实工具，模型消息由预设替身提供；`--ask-model` 切换真实服务 |
| Day 06 的真实建库、Day 07 的混合检索 | 本地 Embedding 计算；首次需要下载权重 |
| `--ask-model` | 把问题与选定证据发给生成服务 |
| 最终项目 `--hybrid` | 开启本地向量检索，可与 `--ask-model` 分别使用 |

`lexical` 表示按词或字匹配的关键词检索；`vector` 表示向量检索；`hybrid` 表示组合两种检索。
“用了模型”需要区分是文本编码还是生成回答；跑通确定性流程也不等于测过真实模型质量。

模型配置沿用项目原有的阿里云服务：Key 从 `DASHSCOPE_API_KEY`、`ALIYUN_API_KEY` 或根目录 `aliyun_api_key` 文件读取；地址和模型可用 `LLM_BASE_URL`、`LLM_MODEL` 设置。默认地址不保证适用于其他账号，按你开通的服务配置。
OpenAI Python SDK 负责客户端通信，实际服务由地址决定；兼容接口未必支持所有官方能力。
密钥文件、`.env` 和本地状态已被 Git 忽略，不要把真实凭证放进示例或测试数据。

## 22 天课程地图

### 第一阶段：底层原理与 Python 工程能力

| 天数 | 主题 | 产物 |
|---|---|---|
| [Day 01](./day01/DAY01.md) | 模型请求、Prompt、Token、异常处理 | 命令行学习助手 |
| [Day 02](./day02/DAY02.md) | Function Calling、JSON Schema、Agent Loop | 工具型 Agent |
| [Day 03](./day03/DAY03.md) | Python 初学者 Agent 工程基础 | 可测试的 Agent Core |
| [Day 04](./day04/DAY04.md) | 多轮状态、上下文与结构化输出 | 多轮会话 Agent |

### 第二阶段：RAG 完整链路

| 天数 | 主题 | 产物 |
|---|---|---|
| [Day 05](./day05/DAY05.md) | RAG、加载、切块与关键词基线 | 可观察的本地 RAG |
| [Day 06](./day06/DAY06.md) | 从手算向量到本地语义检索 | 可观察的本地向量库 |
| [Day 07](./day07/DAY07.md) | 用门店和错误码理解过滤、混合检索与重排 | 可逐步检查的混合检索 |
| [Day 08](./day08/DAY08.md) | RAG 评估与错误分析 | 检索评估集与报告 |

### 第三阶段：Agent 岗位核心能力

| 天数 | 主题 | 产物 |
|---|---|---|
| [Day 09](./day09/DAY09.md) | LangChain 模型接口、工具封装与 Agent 循环 | 复用乘法和检索工具的助手 |
| [Day 10](./day10/DAY10.md) | LangGraph 状态图、Reducer 与 LangChain 协作 | 内层 Agent 排查、外层业务分支 |
| [Day 11](./day11/DAY11.md) | Checkpoint、Interrupt、人工确认 | 可恢复工作流 |
| [Day 12](./day12/DAY12.md) | MCP 原理与 Python Server/Client | MCP 工具服务 |
| [Day 13](./day13/DAY13.md) | Session、短期记忆与长期记忆 | 可管理记忆系统 |
| [Day 14](./day14/DAY14.md) | Agent Evals 与回归测试 | 自动评估器 |
| [Day 15](./day15/DAY15.md) | Tracing、日志、Token、延迟和成本 | 可观测 Agent |
| [Day 16](./day16/DAY16.md) | Prompt Injection、权限与 Guardrails | 安全工具网关 |
| [Day 17](./day17/DAY17.md) | Multi-Agent、Handoff 与适用边界 | 多角色研究工作流 |

### 第四阶段：求职作品与面试

| 天数 | 主题 | 产物 |
|---|---|---|
| [Day 18](./day18/DAY18.md) | Agent API、流式输出与生产边界 | FastAPI 服务 |
| [Day 19](./day19/DAY19.md) | 最终项目需求与架构设计 | ADR、接口和评估设计 |
| [Day 20](./day20/DAY20.md) | 最终项目核心实现 | RAG + Tools + Session |
| [Day 21](./day21/DAY21.md) | 测试、评估、安全与性能验收 | 可量化质量报告 |
| [Day 22](./day22/DAY22.md) | README、演示、简历与面试 | 可投递作品包 |

## 每课怎么学

1. 看开头的背景与文件表，分清课程提供的数据和运行生成的数据。
2. 执行核心命令，观察实际输入、输出和变化。
3. 从入口函数追踪一条数据，只读该路径需要的代码。
4. 修改一个输入或参数，先猜结果，再运行核对。
5. 做小练习，用自己的话解释一次失败。

源码节选用于对照 `.py` 文件，不一定含完整 import；标为“完整可运行”的例子才可单独执行。模型回答、时间和耗时会变化，文中明确标注为示意的数字不作为实测成绩。
Python 写法可按需查 [语法速查](day03/PYTHON_REFERENCE.md)，不必在 Day 03 一次背完。

## 最终项目和检查入口

[青禾自习室助手](capstone/README.md) 复用前面的模块，提供资料查询、模拟工单查询、偏好保存、草稿审批和本机 API。

```bash
uv run --group workflow python -m capstone.main ask "E101 预约失败怎么办？"
uv run --group workflow --group api python -m day21.verify
```

Day 21 在临时目录运行集成检查，并生成真实报告。它检查固定路径，不是生产负载测试，也没有替你测真实生成模型的回答质量。

修改课程后可以运行：

```bash
uv run --group workflow --group api pytest -q
uv run --group langchain pytest -q tests/test_langchain_agent.py tests/test_combined_workflow.py
uv run --group workflow --group api python -m day21.verify
```

课程后半段通过确定性小实验学习流程保存、协议、权限与评估，再说明如何接回模型。这是逐项学习的参考作品；真实项目还应使用实际业务样本、可信身份和相应运行环境来验证。

## 学完后应能解释什么

- 模型负责生成或提出调用，应用负责数据、执行、权限与状态。
- RAG 的资料、检索结果和最终回答分别从哪里来。
- 一组测试用例怎样产生可追溯的报告，失败应该查哪一层。
- 作品实际实现了什么、哪些结果已经验证、哪些能力还需要继续做。

Day 22 会帮助你把这些证据整理成演示与项目说明。先讲清自己的实现，再根据具体岗位要求补足差距。
