# LLM Agent Engineer：21 天 Python 求职实战路线

这是一条面向“大模型应用开发 / LLM Agent 开发 / RAG 工程”岗位的强化路线。

目标不是只会调用模型 API，而是能够独立完成一个可解释、可测试、可评估、可演示的 Agent 系统，并在面试中讲清楚它的架构和取舍。

## 适合投递的岗位

- 大模型应用开发工程师
- LLM 应用工程师
- AI Agent 开发工程师
- RAG 工程师
- AI 应用后端工程师

这条路线不针对模型训练、CUDA、分布式推理或算法研究岗位。

## 项目环境

```text
llm-agent-learning/
├── .venv/             # 本地环境，不提交
├── pyproject.toml     # 直接依赖，类似 go.mod
├── uv.lock            # 完整依赖锁，类似 go.sum
├── README.md          # 总路线与导航
├── day01/
├── day02/
├── ...
└── day21/
```

所有命令从项目根目录执行：

```bash
cd /path/to/llm-agent-learning  # 替换为你实际克隆到的目录
uv sync --locked
```

运行代码统一使用：

```bash
uv run python 路径/脚本.py
```

PyCharm 解释器统一选择：

```text
/path/to/llm-agent-learning/.venv/bin/python
```

## 21 天课程地图

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
| [Day 09](./day09/DAY09.md) | LangGraph 状态图与工作流 | 图式 Agent |
| [Day 10](./day10/DAY10.md) | Checkpoint、Interrupt、人工确认 | 可恢复工作流 |
| [Day 11](./day11/DAY11.md) | MCP 原理与 Python Server/Client | MCP 工具服务 |
| [Day 12](./day12/DAY12.md) | Session、短期记忆与长期记忆 | 可管理记忆系统 |
| [Day 13](./day13/DAY13.md) | Agent Evals 与回归测试 | 自动评估器 |
| [Day 14](./day14/DAY14.md) | Tracing、日志、Token、延迟和成本 | 可观测 Agent |
| [Day 15](./day15/DAY15.md) | Prompt Injection、权限与 Guardrails | 安全工具网关 |
| [Day 16](./day16/DAY16.md) | Multi-Agent、Handoff 与适用边界 | 多角色研究工作流 |

### 第四阶段：求职作品与面试

| 天数 | 主题 | 产物 |
|---|---|---|
| [Day 17](./day17/DAY17.md) | Agent API、流式输出与生产边界 | FastAPI 服务 |
| [Day 18](./day18/DAY18.md) | 最终项目需求与架构设计 | ADR、接口和评估设计 |
| [Day 19](./day19/DAY19.md) | 最终项目核心实现 | RAG + Tools + Session |
| [Day 20](./day20/DAY20.md) | 测试、评估、安全与性能验收 | 可量化质量报告 |
| [Day 21](./day21/DAY21.md) | README、演示、简历与面试 | 可投递作品包 |

## 为什么扩展到 21 天

七天足够做出 Demo，但岗位通常还要求：

- 扎实的 Python 工程能力；
- Embedding、向量数据库、混合检索和 Rerank；
- 至少一种 Agent 编排框架；
- MCP；
- 状态、记忆与人工确认；
- 测试、评估和可观测性；
- Prompt Injection 防护与工具权限；
- 能讲清楚业务目标和质量指标的完整项目。

因此课程把“会运行”扩展成“能落地、能验证、能面试”。

## 初学者怎样使用这套课程

Day 05～21 已按“具体问题 → 小实验 → 输入输出 → 代码解释 → 练习答案”组织。
先运行参考程序，看见结果，再改一处验证理解；不要求你看完定义就独立写整个系统。
课程天数是学习顺序，不是截止日期，一课分两三天完成也可以。

每课先完成“核心完成标准”，再考虑进阶部分。建议顺序：

1. 用一句话说清今天要解决的问题。
2. 从项目根目录执行文档给出的命令，对照预期结果。
3. 按文档指定顺序读函数，跟踪一条数据的变化。
4. 改一个输入或开关，先猜结果，再运行。
5. 做练习后查看参考答案，用自己的话解释一次失败。

### Day 08～21 的小实验导航

| 课程 | 你会亲眼观察到 |
|---|---|
| [Day 08](./day08/DAY08.md) | 找到一条正确资料，不代表找全了 |
| [Day 09](./day09/DAY09.md) | 状态经过检查、计算、回答三个节点 |
| [Day 10](./day10/DAY10.md) | 关掉程序，再批准同一份草稿 |
| [Day 11](./day11/DAY11.md) | 两个 Python 进程真正通过 MCP 查工单 |
| [Day 12](./day12/DAY12.md) | 偏好保存、覆盖、过期与删除 |
| [Day 13](./day13/DAY13.md) | 答案正确，但缺少工具记录仍不合格 |
| [Day 14](./day14/DAY14.md) | 一次请求的步骤用时与错误日志 |
| [Day 15](./day15/DAY15.md) | 合法工具名仍可能被权限检查拒绝 |
| [Day 16](./day16/DAY16.md) | 三个角色交接证据，错误摘录被拦下 |
| [Day 17](./day17/DAY17.md) | HTTP 请求与阶段 SSE 事件 |
| [Day 18](./day18/DAY18.md) | 一条用户请求对应哪些模块和存储 |
| [Day 19](./day19/DAY19.md) | 前面的小模块组成统一 CLI 与 API |
| [Day 20](./day20/DAY20.md) | 一键执行本地验收并读真实报告 |
| [Day 21](./day21/DAY21.md) | 五分钟演示、作品说明和有答案的自测 |

## 技术选择原则

- Python 为唯一主线语言；
- 先手写底层 Agent Loop，再学习 LangGraph；
- RAG 先建立关键词基线，再增加 Embedding 和 Rerank；
- 只重点学习一个编排框架，不堆砌框架名称；
- 模型服务通过配置切换，不把业务逻辑绑死在单一供应商；
- 评估先于优化，没有固定评估集就不随意改 Prompt；
- 生产部署只讲 Agent 特有边界，Docker、CI/CD、Kubernetes 等通用能力不重复展开。

## 依赖管理

依赖组已经写好，按当天文档运行即可；不要重复 uv add：

```bash
uv sync --locked                                    # 基础课程
uv sync --locked --group workflow                   # LangGraph / MCP
uv sync --locked --group api                        # FastAPI / Uvicorn
uv sync --locked --group rag                        # 本地 Embedding / Qdrant
uv sync --locked --group workflow --group api --group rag
```

运行用到可选依赖的命令时也带上对应 `--group`。uv 的同步可能移除本次未选择的可选组。
Day 08、12、14、15、16 的核心实验只需基础依赖；其余按各课命令执行。
本机 Intel Python 对 cryptography 采用兼容 wheel 的版本约束，避免额外编译 Rust。
后续你确实新增库时，再使用 `uv add` 并同时更新 pyproject.toml 与 uv.lock。

## 配置自己的模型服务

默认离线实验无需模型 Key。Day 01～04 和显式 `--ask-model` 的实验会请求模型。
发布版中的 `your-model-endpoint.example` 是占位地址，请按你的服务填写环境变量：

```bash
export LLM_BASE_URL='填写服务商实际的兼容接口地址'
export LLM_MODEL='填写该服务支持的模型名'
export DASHSCOPE_API_KEY='填写自己的 API Key'
```

可参考根目录 `.env.example` 的字段。代码不会自动加载 `.env`；请在终端或 IDE 的环境变量设置中填写。
不要把 Key 写进 Python 文件或提交到 Git。接口需要支持课程使用的 Responses / 工具调用能力。

## 模型兼容原则

当前项目使用 OpenAI Python SDK 连接 OpenAI-compatible 服务。不同服务商可能只兼容部分 API 能力。

每学习一个新功能，都要区分：

1. OpenAI 官方 API 是否支持；
2. 当前兼容服务是否实现；
3. SDK 是否只是在客户端提供类型封装；
4. 功能不兼容时是否有手动实现或其他模型可替代。

不要把“接口地址兼容”误认为“所有高级能力完全一致”。

## 求职前的硬性完成标准

### 代码

- 不看教程能写出 Agent Loop；
- 会使用类型标注、dataclass、Protocol、async 和依赖注入；
- 核心逻辑不依赖终端或全局变量；
- 单元测试无需联网；
- API、工具、RAG 和状态模块职责清晰。

### RAG

- 能解释并实现加载、切块、Embedding、索引、检索、Rerank 和引用；
- 会计算 Recall@k、MRR 等检索指标；
- 能根据失败案例判断问题在检索还是生成；
- 至少实际使用一种向量数据库。

### Agent

- 会 Function Calling、结构化输出和多轮状态；
- 会 LangGraph 状态图、Checkpoint 和 Interrupt；
- 能实现并调用一个 MCP Server；
- 能解释什么时候不该使用 Multi-Agent；
- 对写操作有确认、允许列表和幂等保护。

### 工程质量

- 有固定评估集和回归报告；
- 有 request_id、trace、Token、延迟和工具事件；
- 能处理超时、重试、上下文增长和并发 session；
- 能说明 Prompt Injection、数据泄露和权限边界。

### 作品

- GitHub 仓库不包含密钥；
- README 能让别人独立运行；
- 有架构图、API 示例和已知限制；
- 有 3～5 分钟演示；
- 有量化评估结果；
- 能完整解释一个失败案例和改进过程。

## 最终项目

[青禾自习室助手](./capstone/README.md) 已提供可运行参考实现：
默认关键词资料预览、可选本地混合检索与生成模型、MCP 虚构工单查询、有限计算、
显式偏好、SQLite 审批与本地幂等、HTTP、阶段 SSE 和本地验收报告。

```bash
uv run --group workflow python -m capstone.main ask "E101 预约失败怎么办？"
uv run --group workflow --group api python -m day20.verify
```

当前是固定身份、有限规则路由的教学工作流；没有完整多轮历史、真实企业认证、
公网部署或真实模型质量评估。上面的求职能力清单是继续练习的目标，不是参考版已全部达成的声明。
先沿课程理解并运行，再逐步扩展成自己的作品。

## 安全提醒

- 不提交 `api_key`、`aliyun_api_key`、`.env` 或运行日志；
- 不在异常、trace 和评估数据中记录完整密钥；
- 公开项目前检查 Git 历史；
- 曾经公开展示过的密钥应撤销并重新生成；
- 不用真实客户数据做公开作品。

## 参考资料

- [OpenAI Responses API](https://developers.openai.com/api/reference/python/resources/responses)
- [OpenAI Conversation State](https://developers.openai.com/api/docs/guides/conversation-state)
- [OpenAI Agents SDK](https://developers.openai.com/api/docs/guides/agents)
- [OpenAI Evals](https://developers.openai.com/api/docs/guides/evals)

完成 Day 21 后就开始投递，不需要等到“什么都会”。投递、面试和继续迭代项目应该并行进行。
