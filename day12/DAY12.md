# Day 12：让两个 Python 程序用 MCP 查一张工单

> 今天不先背协议。你将启动一个客户端，由它启动服务端，真实调用 `get_ticket`。
> 服务端只读虚构数据，默认身份固定为 alice；不用模型、不用 API Key。

## 开始前：输入、程序和产物

| 内容 | 来源与用途 |
|---|---|
| [tickets.py](tickets.py) 的 T001/T002 | 人工编写的静态示例，不是从企业系统同步的 |
| [client.py](client.py)、[server.py](server.py) | 已提供的两个程序，由客户端启动服务端子进程 |
| 工单结果、工具菜单、说明资源 | 经 MCP 实际读取后打印；本课不生成工单数据库或报告文件 |

## 1. 原来函数就在项目里，为什么还要 MCP？

在同一个文件中，你可以直接写 `get_ticket("T001")`。
但如果工具由另一个程序提供，你需要回答：怎么发现工具？参数是什么？怎么发送请求？结果怎么返回？

MCP 给应用与工具服务约定了这些交互方式。
它不负责算出答案，也不要求工具代码内部必须调用大模型。

```text
用户问工单 → 应用决定查 get_ticket → MCP Client → MCP Server → 工单数据
                                                      ↓
用户看到状态 ← 应用整理结果 ← MCP 返回值 ← 运行 Python 函数
```

今天把“应用决定查工具”写死，让你先看到线路确实通了。
模型选工具属于 Day 02/04 学过的能力，两件事可以组合，但不是同一个概念。

## 2. 一条命令开始

```bash
uv run --group workflow python -m day12.client T001
```

成功输出里应有：

```text
tools: 包含 get_ticket、search_notes
ticket: id=T001，owner=alice，status=处理中
resource: 演示服务说明
```

客户端会启动子进程 `python -m day12.server`，完成后关闭连接并收回子进程。
无需先在另一个终端启动 Server，也无需配置端口。

再跑：

```bash
uv run --group workflow python -m day12.client T002
```

T002 属于 bob，返回 `not_found_or_forbidden`。不是查到一个 ID 就能读。

## 3. 四个文件分别干什么？

| 文件 | 可以先找的函数 | 职责 |
|---|---|---|
| tickets.py | get_ticket | 在虚构字典里查数据并检查 owner |
| server.py | 带装饰器的 get_ticket | 把函数登记为 MCP 工具 |
| client.py | interact | 连接、初始化、列工具、调用、读资源 |
| DAY12.md | 本文 | 对照每步输入输出 |

先看 tickets.py：它只有 T001、T002 两条记录。
服务端固定当前演示用户是 alice，因此客户端没有 `user_id` 参数可以随意冒充 bob。
这只是本地演示约定；远程服务必须真的验证身份，不能把固定字符串当登录系统。

## 4. 一次调用拆成六步

| 步骤 | 对应代码 | 看得见的含义 |
|---|---|---|
| 1 | StdioServerParameters | 告诉客户端怎样启动服务端 |
| 2 | stdio_client | 接通标准输入和标准输出的两条通道 |
| 3 | ClientSession | 在通道上建立一次协议会话 |
| 4 | initialize | 双方先确认协议会话信息与能力 |
| 5 | list_tools | 获得工具名、描述、参数 Schema |
| 6 | call_tool | 按名称传参数，获取结果 |

我们另外调用 `read_resource("study://rules")` 读取说明。

`stdio` 是进程的标准输入/输出；这里的数据由客户端写进去、服务端读出来。
它不是 HTTP，也不是向量数据库。MCP 还可使用其他传输方式，今天先用最容易观察的本地方式。

SDK 版本固定在 `<2` 的 v1 系列，接口以 [官方 v1 Python SDK](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x) 为准。

## 5. Server 上的装饰器在做什么？

```python
@mcp.tool()
def get_ticket(ticket_id: str) -> dict:
    return lookup_ticket(ticket_id, DEMO_USER)
```

把 `@mcp.tool()` 看成“把下面这个函数登记到工具菜单”。
参数类型 `str` 和函数说明用于描述工具输入；工具执行仍是普通 Python 函数。

客户端会收到类似这样的工具参数要求：

```json
{
  "type": "object",
  "properties": {"ticket_id": {"type": "string"}},
  "required": ["ticket_id"]
}
```

这是 Schema 的简化示意，实际输出可能还有 title 等字段。
模型以后可以根据这个菜单提出调用；应用仍需检查调用能不能执行。

## 6. Tool、Resource、Prompt 不要混在一起

| 类型 | 青禾例子 | 你如何使用 |
|---|---|---|
| Tool | get_ticket(ticket_id) | 传参数，请服务端执行一个动作 |
| Resource | study://rules | 按 URI 读取一份内容 |
| Prompt | “按模板写工单摘要” | 取一份可复用的提示模板 |

本例实际实现两个 Tool 和一个 Resource，没有实现 Prompt 模板。
工具也可以是只读查询；不能把“Tool”理解为“一定修改数据”。

## 7. async、await、async with 用人话解释

```python
async with ClientSession(read, write) as session:
    await session.initialize()
    result = await session.call_tool("get_ticket", {"ticket_id": "T001"})
```

- `async def` 定义可等待的函数。
- `await` 等待远端这一步完成，再使用结果。
- `async with` 进入连接上下文，离开时清理连接。
- 最外层 `asyncio.run(...)` 把异步入口跑起来。

不是加上 async 就会自动并发。这里几步有依赖，必须顺序执行。
`fetch()` 给整个操作设了 20 秒上限，避免教学命令无限等待。

## 8. 调试时最常踩的坑

| 现象 | 先检查 |
|---|---|
| ModuleNotFoundError: mcp | 命令有没有 `--group workflow` |
| Server 一直等待 | 你直接运行了 Server；试着运行 Client |
| 协议解析失败 | Server 是否往 stdout print 了调试文字 |
| T002 查不到 | 本课 alice 无权访问 bob 的记录，是预期结果 |
| 工具名改了就失败 | Client 的 call_tool 名称也要对应修改 |

Server 的 stdout 要留给协议消息。若需要日志，写 stderr。
工具返回的业务错误和协议调用错误也要区分：
T002 的 `error` 在工具结果中；工具执行异常则可能让 MCP 的 `isError` 为真。

## 真实场景里怎么用

真实场景中，工具服务可以包装公司已有的工单 API，多个应用按统一的工具说明访问它。业务身份和资源权限仍由服务校验。MCP 连接应用与工具服务，模型是否参与选择工具是应用的另一层逻辑。

## 9. 练习：改一处，做一个自己的实验

在 client.py 的 `call_tool` 那行临时改成：

```python
result = await session.call_tool("search_notes", {"query": "wifi 免费吗？"})
```

返回结果会从“工单对象”变成“资料列表”；变量 `ticket` 的名字也应改成 `notes`，避免误导。
先只观察，再恢复原文件，Day 20 会复用默认查工单入口。

思考：为什么要先 list_tools？为什么 get_ticket 不接受 user_id？

<details>
<summary>参考答案</summary>

list_tools 用来发现能力与输入约定；不是靠猜测另一个程序的函数。
user_id 应从可信身份上下文取得，而不是让模型在参数里随意声明自己是谁。

</details>

核心完成标准：能查 T001、观察 T002 被拒绝，并指出 Client/Server 各自运行在哪里。
进阶再学远程 Streamable HTTP、连接复用、认证与分页。本地 stdio 跑通不代表已做完这些能力。

[上一课：Day 11](../day11/DAY11.md) · [下一课：Day 13](../day13/DAY13.md)
