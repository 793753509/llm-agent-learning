# Day 19：把前面的积木拼成一个能用的青禾助手

> 今天有完整参考代码，不要求你看着一张抽象目录图从零猜实现。
> 先依次跑通查询、MCP、偏好、审批、HTTP；每次只增加一条链路。

## 1. 今天到底要完成什么？

用同一个 CLI 完成：

```text
查北店 E101 的处理说明
查 alice 的 T001 工单
保存“简短”偏好，再看到更少的候选摘录
准备草稿 → 关掉进程 → 批准 → 重复批准仍不重复写入
```

最后启动同一引擎的 HTTP 接口。
这些都在 `capstone/`，它通过 import 复用前面课程的代码。

## 2. 准备环境，先不接模型

```bash
uv sync --locked --group workflow --group api
uv run --group workflow python -m capstone.main ask "E101 预约失败怎么办？"
```

输出应包含：

```text
route: retrieve
mode: extractive_preview
retrieval: lexical
sources 首项: north/booking.md#1
answer: 包含北店 E101 原文及来源
trace_id: 本次工作流编号
```

这是候选资料预览，需要核对原文是否回答问题；不是假装由模型生成的答案。
代码已经把北店 E101 精确匹配放到前面，重排算法来自 Day 07。

## 3. 一次问答经过哪些代码？

先开 `capstone/core.py`，从 `Engine.answer()` 开始看：

```text
检查问题长度
创建 Trace
把初始 State 交给 LangGraph
route_request 选择路线
search 或 tool 执行
把 response 加上 route 和 trace_id 返回
```

这里的 route_request 是正则/字符串规则，不是模型思考。
例如 `查工单 T001` 必须符合“查工单 + 空格 + T编号”的格式。
暂时先接受明确格式，能把错误限制在单独一层。

## 4. 连接真实 MCP 与计算工具

```bash
uv run --group workflow python -m capstone.main ask "查工单 T001"
uv run --group workflow python -m capstone.main ask "查工单 T002"
uv run --group workflow python -m capstone.main ask "计算 25 * 3"
```

T001：route=get_ticket，MCP 子进程真正被调用，显示处理中。
T002：返回 not_found_or_forbidden，不能看到 bob 的工单正文。
计算：route=multiply，result.value=75。

执行顺序是先 Day 15 检查工具参数/资源权限，再在允许时调用 Day 11 MCP。
服务端读取时仍检查 owner，不能只信客户端说“我已经检查过”。

当前一次请求只选一条路线、执行最多一个业务工具，不支持自由多步规划。

## 5. 保存一个偏好，观察输出真的变化

```bash
uv run --group workflow python -m capstone.main remember 简短
uv run --group workflow python -m capstone.main ask "E101 预约失败怎么办？"
uv run --group workflow python -m capstone.main forget
```

简短偏好生效后，知识查询最多取一条原文；默认最多两条。
这是一条可观察的规则，不依赖模型是否恰好按要求写得短。

项目使用 `capstone/data/memory.sqlite`，不会自动读取 Day 12 的练习数据库。
偏好一天后过期；可以再次 remember。这里只接入 style，未接入 language 或完整聊天历史。

减少上下文条数可能让需要多条证据的问题缺资料，这是当前实现的取舍，不能为了简短牺牲事实完整性而不评估。

## 6. 准备草稿，再明确批准

```bash
uv run --group workflow python -m capstone.main draft qh-001 "北店 E101 预约失败，请前台协助。"
uv run --group workflow python -m capstone.main show qh-001
uv run --group workflow python -m capstone.main approve qh-001
uv run --group workflow python -m capstone.main approve qh-001
```

依次看到 waiting_approval → 仍待审批 → created_locally → 仍已完成。
新建另一份草稿可用 `reject 新编号` 拒绝。
编号重复 start 会被拒绝；重新做实验就换 qh-002。

项目调用 Day 10 的 execute，因此保存、摘要核对、重复写入保护不需要再写一遍。

**这里新建的模拟工单只在本地表里，不会同步给 Day 11 的静态 T001/T002 数据。**
读写使用不同教学存储，是当前作品明确的限制。后续要统一工单服务才能支持“创建后立即用 MCP 查询”。

## 7. 加入真正的本地向量检索

你已经完成 Day 06 的模型下载后，可以运行：

```bash
uv run --group workflow --group rag python -m capstone.main ask "E101 预约失败怎么办？" --hybrid
```

这会复用 Day 06 的本地 Embedding 模型、建立北店内存 Qdrant 索引，
再执行关键词 + 向量 → RRF → 错误码规则重排 → 上下文选择。

第一次可能需要下载权重或加载模型；这仍不是生成模型回答。
当前只有几条资料，为教学每次 CLI 启动重建内存索引。大语料应复用持久化索引。

## 8. 什么时候才调用真正的生成模型？

在你已配好 Day 03 模型服务的前提下：

```bash
uv run --group workflow python -m capstone.main ask "E101 预约失败怎么办？" --ask-model
```

也可以同时打开两个开关：

```bash
uv run --group workflow --group rag python -m capstone.main ask "E101 预约失败怎么办？" --hybrid --ask-model
```

`--ask-model` 复用 Day 05 的生成函数，请求当前配置的服务，会消耗相应 API 额度。
问题与选中资料会进入这次请求；不是把整个本地数据库上传。

生成分支仍需要人工核对引用和拒答。现有自动报告没有测真实回答语义、费用和引用支持性。
只开 --hybrid 与只开 --ask-model 的作用不同，请自己画出两个开关的位置。

## 9. 同一引擎接 HTTP

```bash
uv run --group workflow --group api uvicorn capstone.api:app --host 127.0.0.1 --port 8000
```

若 Day 17 的服务还占着 8000，先 Ctrl+C 停止那个服务。
另一个终端请求：

```bash
curl -X POST http://127.0.0.1:8000/chat -H 'Content-Type: application/json' -d '{"session_id":"s1","question":"E101 预约失败怎么办？"}'
```

API 默认用关键词、无生成模型，复用 Day 17 的 /health、/chat、/events。
现在问题里若写“创建工单”，只返回去 CLI 准备审批的提示，不会执行写入。
API session 仅计数，不意味着能理解“那它呢”。

## 10. 看一次实际数据流

| 位置 | 此时有什么 | 模型是否参与 |
|---|---|---|
| question | E101 预约失败怎么办？ | 无 |
| chunks | 仅北店原文 | 无 |
| candidates | 关键词结果或双路融合结果 | hybrid 使用本地 Embedding |
| results | 去重并放得进预算的原文 | 无 |
| answer | 摘录，或根据原文生成的回答 | 仅 ask-model 调用生成模型 |

`1200` 是 input 字符预算，不是 token 预算，沿用 Day 07 的实现。
没有任何候选时返回 no_evidence，不请求生成模型；但有候选也不保证资料中存在答案。

## 11. 出错时按入口排查

| 问题 | 优先检查 |
|---|---|
| 缺少 langgraph/mcp | 运行命令是否带 --group workflow |
| 缺少 fastembed/qdrant | hybrid 时是否带 --group rag |
| 工单查询变成资料检索 | 是否按“查工单 T001”格式输入 |
| 检索结果与教程数量不同 | 是否还保存了简短偏好 |
| 查询服务不可用 | 先用 MCP client 单独查 T001 |
| 草稿 ID 冲突 | show 原任务，或换新 ID |

CLI 默认把数据写到 capstone/data。想单独练习：

```bash
uv run --group workflow python -m capstone.main --data-dir /tmp/qinghe-my-practice ask "E101 怎么办？"
```

`--data-dir` 放在子命令 ask/draft 之前。

## 12. 今天的练习与终点

1. 能否在不打开生成模型的情况下使用真实向量库？
2. 为什么查到 T001 不等于实现了企业登录？
3. 给 route_request 加一个新规则前，先写哪种测试输入？

<details>
<summary>参考答案</summary>

1. 可以，只开 --hybrid。
2. 身份固定为 alice，没有验证真实用户凭证。
3. 至少写一个命中新规则的输入，以及一个不应误命中的旧输入，跑回归检查。

</details>

核心完成标准：查询、MCP、偏好、审批、HTTP 都跑一遍；能指出每段复用哪一天。
真实模型生成作为有配置后再做的扩展，不阻碍你先学会整个工程链路。

[上一课：Day 18](../day18/DAY18.md) · [下一课：Day 20](../day20/DAY20.md)
