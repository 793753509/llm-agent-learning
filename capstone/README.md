# 青禾自习室助手：可运行的学习作品

帮助北店值班人员查预约资料、读取自己的模拟工单，并在人工批准后把草稿写入本地表。
数据全部虚构。默认返回资料摘录，不调用生成模型；规则路由与模型决策在课程中明确区分。

## 文件与数据从哪里来

| 内容 | 来源 |
|---|---|
| [main.py](main.py)、[core.py](core.py)、[api.py](api.py) | 课程提供的 CLI、业务引擎与 HTTP 入口 |
| [门店资料](../day07/knowledge.json)、[静态工单](../day12/tickets.py) | 人工编写的输入，默认固定北店、alice |
| `capstone/data/` | 运行生成的偏好、审批和日志，自动建目录并保存在本机 |
| [本地验收报告](../day21/reports/local.md) | 运行 day21.verify 后生成；不是手工填写的成绩 |

`lexical` 表示关键词检索，`hybrid` 表示混合检索；`--ask-model` 另行控制是否请求生成模型。
完整来源关系见 [数据指南](../DATA_GUIDE.md)。

## 安装与最短演示

从 **llm-agent-learning 项目根目录** 运行，不要先 cd capstone：

```bash
uv sync --locked --group workflow --group api
uv run --group workflow python -m capstone.main ask "E101 预约失败怎么办？"
uv run --group workflow python -m capstone.main ask "查工单 T001"
uv run --group workflow --group api python -m day21.verify
```

需要 Python 3.10+ 和 uv。版本由根目录 uv.lock 锁定。
第一次安装依赖需要网络；默认演示不需要模型 Key，不访问外部业务系统。
MCP 客户端通过 stdio 启动本地 Python 子进程。

第一条查询输出原文与 north/booking.md#1 来源；T001 返回处理中。
最后一条运行本地验收，报告见 [local.md](../day21/reports/local.md)。
每次以你本次成功执行后写出的报告为准。

## 可以继续操作

```bash
uv run --group workflow python -m capstone.main ask "查工单 T002"
uv run --group workflow python -m capstone.main ask "计算 25 * 3"
uv run --group workflow python -m capstone.main remember 简短
uv run --group workflow python -m capstone.main ask "E101 预约失败怎么办？"
uv run --group workflow python -m capstone.main forget
uv run --group workflow python -m capstone.main draft readme-001 "北店 E101 预约失败，请前台协助。"
uv run --group workflow python -m capstone.main show readme-001
uv run --group workflow python -m capstone.main approve readme-001
uv run --group workflow python -m capstone.main approve readme-001
```

T002 属于 bob，应拒绝且不返回正文。简短偏好使候选资料最多一段，默认最多两段。
草稿先是 waiting_approval，批准后 created_locally，重复批准不会重复写入。
重新演示时换新的草稿 ID；同一个 ID 不覆盖旧草稿。拒绝用 `reject 任务编号`。

## HTTP 与阶段流

```bash
uv run --group workflow --group api uvicorn capstone.api:app --host 127.0.0.1 --port 8000
```

在另一个终端：

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/chat -H 'Content-Type: application/json' -d '{"session_id":"s1","question":"E101 预约失败怎么办？"}'
curl -N -X POST http://127.0.0.1:8000/events -H 'Content-Type: application/json' -d '{"session_id":"s1","question":"查工单 T001"}'
```

交互文档：[本机 /docs](http://127.0.0.1:8000/docs)。
SSE 是 status → answer → done 的阶段事件；失败时发送 error。
HTTP 默认关键词、无生成模型，审批仅在本地 CLI 操作。

## 可选真实向量与生成模型

```bash
uv run --group workflow --group rag python -m capstone.main ask "E101 预约失败怎么办？" --hybrid
uv run --group workflow python -m capstone.main ask "E101 预约失败怎么办？" --ask-model
uv run --group workflow --group api --group rag python -m day21.verify --hybrid
```

--hybrid 使用 Day 06 的本地 Embedding 缓存和内存 Qdrant，执行 RRF 与错误码规则重排。
首次可能下载模型权重。--ask-model 复用 Day 03 的配置与密钥读取、Day 05 的生成函数，
把问题与选中资料送给配置的模型服务并消耗 API 额度。两个开关可组合。
没有真实模型配置也可完成所有默认实验。

## 架构与存储

```text
CLI / HTTP → LangGraph 固定路由 → 北店检索 → 原文或可选生成
                              → 参数/权限检查 → MCP 或乘法
CLI 草稿 → SQLite checkpoint → 人工审批 → 本地唯一写入
```

代码复用 Day 07、11、12、13、15、16、18 的模块。完整设计见 [Day 19](../day19/DAY19.md)。

数据默认写入 capstone/data：memory.sqlite、approval/ 下的两个 SQLite 库、logs/ 下的追踪文件。
该目录不提交。HTTP 会话计数只在内存；每个 workflow 有 trace_id。
学习时可在子命令前用 `--data-dir /tmp/qinghe-practice` 指定独立数据目录。

## 真实边界

- 路由是固定规则，一次查询最多执行一个业务工具，没有自主多步规划。
- 默认是候选资料预览，相关候选不保证能回答问题。
- 生成分支有引用指令，但没有完成真实回答语义与引用支持性评估。
- 身份固定为 alice；不是企业认证、多租户平台或公网服务。
- 审批为单用户串行本地流程，未验证多进程同时批准；外部写入需外部幂等支持。
- MCP 查询 T001/T002 静态数据；批准后的本地新工单不会自动出现在该数据中。
- session 只有计数，未存完整历史；SSE 不是逐 token 流，无断点续传。
- 验收是小规模本地检查，10 次热查询计时不代表生产容量或模型准确率。

演示见 [五分钟脚本](../day22/demo.md)，自测见 [面试问答](../day22/interview.md)。
