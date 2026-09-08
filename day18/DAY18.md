# Day 18：让浏览器或 curl 也能向你的助手提问

> 今天把已有 Python 函数包成 HTTP 接口，并观察一段真正的 SSE 事件流。
> 服务默认只返回本地资料摘录，不调用模型。先会请求和响应，再做产品界面。

## 开始前：输入、程序和产物

| 内容 | 来源与用途 |
|---|---|
| [api.py](api.py) | 已提供的接口程序；ChatRequest 定义请求字段 |
| question、session_id | 由你在 curl 请求中填写，服务按约定校验 |
| answer、sources | 服务从 Day 05 原文检索后生成的摘录与来源 |
| 会话计数、request_id | 服务运行时在内存维护或生成，不写数据库 |

## 1. 从终端函数到接口，多了哪一步？

以前你运行脚本，在终端看结果。
现在网页可以发请求给持续运行的服务：

```text
浏览器/curl → HTTP 请求 → FastAPI → answer_question → 资料检索
浏览器/curl ← JSON 响应 ← FastAPI ← 摘录和来源
```

HTTP 是程序之间传请求的方式。JSON 是本课请求和响应的数据格式。
FastAPI 帮我们接收请求、校验数据、调用 Python 函数、发送响应。

## 2. 先启动，再另开一个终端请求

终端 A，从项目根目录运行：

```bash
uv run --group api uvicorn day18.api:app --host 127.0.0.1 --port 8000
```

命令持续运行是正常的；按 Ctrl+C 停止。
`day18.api:app` 的意思是“导入 day18/api.py 中的 app 对象”。

浏览器打开 [交互文档](http://127.0.0.1:8000/docs)，可以直接点接口、Try it out、填数据、Execute。

终端 B：

```bash
curl http://127.0.0.1:8000/health
curl -X POST http://127.0.0.1:8000/chat -H 'Content-Type: application/json' -d '{"session_id":"s1","question":"周末几点关门？"}'
```

第二次请求应返回 mode=extractive_preview、周末原文、sources 包含 hours.md#1、turn=1。
重复请求 s1，turn 增加。换成 s2，从 1 开始。

## 3. 请求体不要凭空猜

```json
{"session_id":"s1","question":"周末几点关门？"}
```

| 字段 | 意义 | 限制 |
|---|---|---|
| session_id | 给这次会话起个标签 | 1～40 个字母、数字、下划线或短横线 |
| question | 本次要查的问题 | 去除首尾空格后 1～200 字符 |

`ChatRequest(BaseModel)` 写出这份输入约定。
Pydantic 校验失败时，FastAPI 会返回 422，业务函数不会运行。
请求体的用法见 [FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)。

试试空问题：

```bash
curl -X POST http://127.0.0.1:8000/chat -H 'Content-Type: application/json' -d '{"session_id":"s1","question":"   "}'
```

这次应看到 422 错误说明，不是成功答案。

## 4. 返回的字段分别有什么用？

```text
mode：当前是资料摘录预览
answer：找到的原文，仍需核对是否回答问题
sources：原文编号
request_id：这一次请求的随机编号
session_id：你传入的会话标签
turn：这个会话成功处理了几次请求
```

request_id 每次不同；session_id 可以跨请求相同。
不能把每条请求的 request_id 都当成新会话，否则无法关联多轮。

目前只存会话计数，没有存完整聊天历史，也没有实现“那它呢”的指代解析。
有 session_id 字段，不等于已经会多轮对话。
重启服务后计数清零，因为 sessions 只是内存字典。

## 5. 三个接口各做一件事

| 接口 | 方法 | 用途 |
|---|---|---|
| /health | GET | 看服务是否正在响应 |
| /chat | POST | 一次性取得完整 JSON |
| /events | POST | 按事件逐段读取处理状态和答案 |

health 返回 ok 只说明进程能处理这个接口，不证明模型或所有工具都可用。
本课没有后台数据库连接检查，也没有生产就绪探针。

## 6. 亲眼看 SSE

```bash
curl -N -X POST http://127.0.0.1:8000/events -H 'Content-Type: application/json' -d '{"session_id":"s3","question":"wifi 免费吗？"}'
```

`-N` 让 curl 尽快显示收到的内容，不先攒一大块。
你会依次看到：

```text
event: status
data: {"stage":"started", ...}

event: answer
data: {"answer":"...", ...}

event: done
data: {...}
```

上面省略了一些字段，真实返回是合法 JSON。
一条事件以空行结束，event 标记类型，data 携带内容。

本例用 StreamingResponse 和生成器逐个 yield 事件。
这是**阶段流式输出**：开始、完整答案、结束。不是大模型逐 token 生成。
SSE 的基本形式见 [FastAPI SSE 教程](https://fastapi.tiangolo.com/tutorial/server-sent-events/)。

## 7. 为什么流式错误可能还是 HTTP 200？

流已经开始发送后，响应头通常已经发出，不能再改成另一个状态码。
因此出错时，程序发送 `event: error`，不再发 done。
客户端要检查事件类型，不能只看到 200 就认定整次任务成功。

本例没有断点续传、事件重放，也不提供浏览器原生 EventSource 的 GET 接口。
要在网页发 POST 读取这条流，可用 fetch 流式读取；先用 curl 学会协议即可。

## 8. 同时有人提问怎么办？

普通 `def` 路由中的同步工作由框架在线程池里执行。
每个 session 有自己的锁，使同一会话的请求串行，避免 turn 同时修改。
不同 session 可以各自处理；最多保留 100 个，超过会拒绝新会话。

这个限制是为了教学程序有明确容量，不是生产会话管理方案。
多个 worker 有不同内存，锁也不同；若要跨进程一致，需要共享存储和并发控制。
本课一次只启动一个 worker。

## 9. 哪些能力还没有完成？

服务固定用于本机教学，绑定 127.0.0.1，默认演示用户 alice。
没有登录鉴权、生产限流、重试队列、断线取消正在执行的业务或持久化会话。
不要为了给别人演示就直接改成公网监听；先完成这些能力的设计与验证。

`create_app(answer_fn=...)` 留了可替换的回答函数。
Day 20 会把它换成最终项目入口，因此 API 不必重写一遍。

## 真实场景里怎么用

网页聊天框通常把问题发给后端接口，后端复用已有业务函数，再用 JSON 或事件流把结果交回页面。真实身份、会话持久化和模型流式输出可以逐项加入；今天先验证 HTTP 这层是否正确接上现有检索函数。

## 10. 三个小练习

1. 发两次 s1，再发一次 s2，解释 turn 为何不同。
2. 在请求里加一个未声明的 user_id，应该成功吗？
3. /events 已收到 status，随后收到 error，这次请求算成功吗？

<details>
<summary>参考答案</summary>

1. 各 session 分开计数；已有会话从原值继续。
2. 不成功，extra=forbid 会拒绝额外字段；更不构成登录。
3. 不算，流已开始但业务失败，要看事件结果。

</details>

核心完成标准：启动服务、成功查询、触发 422、读懂三个 SSE 事件。
代码阅读顺序：ChatRequest → answer_question → create_app 内的三个路由 → respond 的锁。

[上一课：Day 17](../day17/DAY17.md) · [下一课：Day 19](../day19/DAY19.md)
