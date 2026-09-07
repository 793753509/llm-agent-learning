# Day 01：从调用大模型到理解一次完整请求

> 今日主题：LLM API 基础、Prompt 基础、响应解析与错误处理\
> 建议用时：3～5 小时\
> 当前模型：qwen3.8-flash\
> 当前程序：hello_llm.py

## 1. 今天只完成一个目标

今天不要急着学习 LangChain、向量数据库、多 Agent 或 MCP。

今天的目标是：

> 能独立写出一个 Python 程序，将用户问题发送给大模型，读取回答和 Token 用量，并能通过 Prompt 控制回答格式。

完成后，你应该能回答下面这些问题：

- 模型、模型服务商、SDK、API 分别是什么？
- base_url、api_key、model 分别控制什么？
- instructions 和 input 有什么区别？
- 为什么同一个问题可能得到不同答案？
- Token 是什么，为什么 Agent 工程师必须关注 Token？
- 为什么一个会调用模型的程序还不算 Agent？

---

## 2. 建立第一张心智地图

当前程序的完整调用过程如下：

~~~text
用户输入问题
    ↓
hello_llm.py
    ↓
OpenAI Python SDK
    ↓
阿里云 OpenAI 兼容接口
    ↓
qwen3.8-flash
    ↓
模型生成 Response
    ↓
Python 提取 output_text 和 usage
    ↓
终端显示结果
~~~

几个概念不要混淆：

| 概念 | 当前项目中的例子 | 作用 |
| --- | --- | --- |
| 模型 | qwen3.8-flash | 负责理解和生成文本 |
| 服务商 | 阿里云百炼 | 托管模型并提供网络接口 |
| API 协议 | OpenAI 兼容接口 | 规定请求和响应的数据格式 |
| SDK | openai Python 包 | 帮你在 Python 中方便地调用 API |
| 应用代码 | hello_llm.py | 组织 Prompt、调用模型、处理结果 |

可以把它类比成：

~~~text
模型       = 发动机
API        = 发动机的控制接口
SDK        = 方向盘、油门和仪表盘
你的程序   = 整辆车
Agent      = 能看路、做决策、使用工具并持续行动的司机
~~~

## 3. LLM 和 Agent 的区别

一个普通 LLM 调用通常是：

~~~text
输入 → 模型 → 输出
~~~

一个最小 Agent 通常是：

~~~text
目标
  ↓
模型判断下一步
  ↓
选择并调用工具
  ↓
读取工具结果
  ↓
继续判断
  ↓
达到目标或触发停止条件
~~~

因此可以先记住这个近似公式：

~~~text
Agent = LLM + Tools + Loop + State + Guardrails
~~~

- LLM：负责理解、推理和决策。
- Tools：搜索、计算、读文件、调用业务 API 等。
- Loop：执行“思考—行动—观察—再思考”的循环。
- State：保存当前任务和历史信息。
- Guardrails：限制危险操作、错误输入和无限循环。

今天只学好公式里的 LLM。第二天再加入第一个 Tool 和 Loop。

---

## 4. 精读当前 hello_llm.py

打开 hello_llm.py，按下面顺序阅读。

### 4.1 配置

重点找到：

~~~python
BASE_URL = os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL)
MODEL = os.getenv("LLM_MODEL", "qwen3.8-flash")
~~~

- BASE_URL 决定请求发给哪个服务商。
- MODEL 决定请求使用哪个模型。
- 环境变量让程序可以在不改代码的情况下切换配置。

### 4.2 密钥加载

程序依次尝试：

1. DASHSCOPE_API_KEY 环境变量
2. ALIYUN_API_KEY 环境变量
3. 项目根目录的 aliyun_api_key 文件

密钥只负责身份认证，不决定具体使用哪个模型。

### 4.3 创建客户端

~~~python
client = OpenAI(
    api_key=load_api_key(),
    base_url=BASE_URL,
    timeout=30.0,
    max_retries=2,
)
~~~

理解每个参数：

- api_key：证明调用者身份。
- base_url：模型服务入口。
- timeout：一次请求最多等待多久。
- max_retries：遇到部分临时错误时最多自动重试多少次。

### 4.4 发起请求

~~~python
response = client.responses.create(
    model=MODEL,
    instructions="...",
    input=prompt,
)
~~~

- model：本次请求使用的模型。
- instructions：应用开发者给模型的长期角色和行为约束。
- input：用户本次提出的具体任务。

可以暂时这样理解：

~~~text
instructions = 你应该怎样工作
input        = 你这次要完成什么
~~~

### 4.5 读取响应

重点关注：

~~~python
response.output_text
response.status
response.model
response.usage.input_tokens
response.usage.output_tokens
response.usage.total_tokens
~~~

不要直接打印整个 response 作为正式产品的输出。完整对象适合调试，面向用户时应提取真正需要的字段。

### 4.6 错误处理

当前程序处理了：

- AuthenticationError：密钥无效。
- RateLimitError：调用过快或额度受限。
- PermissionDeniedError：没有模型权限或免费额度停止。
- APIConnectionError：网络连接失败。
- APIStatusError：其他 HTTP/API 错误。

工程师不能只写“成功路径”。网络、权限、配额和服务端错误都是正常的软件运行状态。

---

## 5. 必须掌握的五个基础概念

### 5.1 Prompt 不是随便问一句话

一个可控的 Prompt 通常包含：

~~~text
角色：你是谁
任务：要完成什么
上下文：有哪些已知信息
约束：不能做什么、长度多少
输出格式：最终结果长什么样
验收标准：怎样才算完成
~~~

推荐模板：

~~~text
你是一名【角色】。

任务：
【明确描述要完成的事情】

背景：
【提供必要上下文】

要求：
1. 【约束一】
2. 【约束二】
3. 不确定的信息必须明确标注。

输出格式：
【Markdown、JSON、表格或固定字段】

成功标准：
【如何判断回答可用】
~~~

### 5.2 模型生成结果，不是查询标准答案

模型根据上下文预测输出，因此：

- 同一问题可能得到不同措辞。
- 语言流畅不等于事实正确。
- Prompt 更清晰通常能提高稳定性，但不能保证绝对正确。
- 涉及实时或重要事实时，需要工具、数据源或人工校验。

### 5.3 Token 是模型处理文本的基本单位

Token 不完全等于“字”或“单词”。

一次请求通常包含：

~~~text
输入 Token = instructions + 用户输入 + 历史上下文 + 工具结果
输出 Token = 模型生成内容
总 Token   = 输入 Token + 输出 Token
~~~

Agent 往往会多轮调用模型和工具，所以 Token 会随着历史记录增长。必须尽早养成查看 usage 的习惯。

### 5.4 上下文不等于永久记忆

模型只知道本次请求中收到的内容。程序退出后，模型不会因为你刚才问过一个问题就自动记住它。

以后实现多轮对话时，需要由应用负责：

- 保存历史消息；
- 在下一次请求中重新提供必要历史；
- 或使用服务商支持的会话状态能力。

### 5.5 API 兼容不等于功能完全相同

当前阿里云接口兼容 OpenAI SDK 和 Responses API 的基本调用方式，但不同服务商在以下方面仍可能不同：

- 支持的模型名；
- 支持的请求参数；
- 错误码；
- Tool Calling 行为；
- 会话状态；
- Token 统计和计费方式。

写 Agent 时要把“接口协议”和“具体模型能力”分开理解。

---

## 6. 第一组练习：跑通并观察

### 练习 1：最小调用

在 PyCharm 中运行 hello_llm.py，输入：

~~~text
用一句话解释什么是大语言模型。
~~~

记录：

~~~text
模型：
状态：
输入 Token：
输出 Token：
总 Token：
模型回答：
~~~

终端运行方式：

~~~bash
cd /path/to/llm-agent-learning  # 替换为你实际克隆到的目录
uv run python day01/hello_llm.py "用一句话解释什么是大语言模型。"
~~~

### 练习 2：观察约束是否有效

依次执行三个 Prompt：

~~~text
解释 Python 装饰器。
~~~

~~~text
面向完全没有编程经验的人，用一个生活类比解释 Python 装饰器，不超过 100 字。
~~~

~~~text
解释 Python 装饰器。输出必须包含：一句话定义、一个类比、一个最小代码示例、一个常见错误。
~~~

比较：

- 哪一个结果最容易使用？
- 哪一个消耗的 Token 最多？
- 模型是否严格遵守格式？
- 哪些要求被忽略了？

### 练习 3：区分 instructions 和 input

暂时把 instructions 改为：

~~~text
你是一名面试官。回答时先提出一个问题，再给出参考答案和评分标准。
~~~

然后输入：

~~~text
Python 字典。
~~~

观察同一个 input 在不同 instructions 下如何改变输出。

完成后把 instructions 恢复为你喜欢的版本。

---

## 7. 第二组练习：写出可复用 Prompt

选择一个你熟悉的主题，例如 Python、Go、Docker 或后端开发。

### 练习 4：代码审查 Prompt

自己补全下面的模板：

~~~text
你是一名资深 Python 代码审查员。

任务：
审查我提供的代码。

重点检查：
1. 正确性
2. 异常处理
3. 可读性
4. 安全问题

输出格式：
- 问题级别
- 问题位置
- 原因
- 修改建议

如果没有发现问题，明确输出“未发现明显问题”。

代码：
【粘贴一段你自己的代码】
~~~

### 练习 5：结构化学习卡片

让模型把一个技术概念整理成以下格式：

~~~text
概念：
一句话解释：
使用场景：
最小示例：
常见错误：
自测题：
~~~

目标不是让模型写得越多越好，而是得到稳定、可复用的输出。

---

## 8. 今日小项目：命令行学习助手

在现有 hello_llm.py 基础上，把它变成一个“技术概念学习助手”。

### 必须实现

- 从命令行参数或 input() 获取主题。
- 回答必须包含：
  - 一句话定义；
  - 一个生活类比；
  - 一个最小代码示例；
  - 两个常见错误；
  - 三道自测题。
- 显示模型名和 Token 用量。
- 输入为空时给出明确提示。
- API 失败时不能只显示 Python 堆栈。

### 建议实现

- 增加 --simple 模式，输出面向初学者的解释。
- 增加 --interview 模式，输出面试题和参考答案。
- 把 instructions 提取成常量。
- 把模型调用和终端交互拆成不同函数。

### 暂时不要实现

- 数据库；
- Web 页面；
- 多轮记忆；
- Agent 框架；
- 向量数据库；
- 多模型自动切换。

### 验收命令

~~~bash
uv run python day01/hello_llm.py "Python 生成器"
~~~

最终回答至少应包含：

~~~text
一句话定义
生活类比
代码示例
常见错误
自测题
~~~

---

## 9. 实验记录模板

新建 experiment-notes.md，每次实验记录一行：

| 实验 | Prompt 改动 | 输出变化 | 输入 Token | 输出 Token | 是否满足要求 |
| --- | --- | --- | ---: | ---: | --- |
| 1 | 原始问题 |  |  |  |  |
| 2 | 增加角色 |  |  |  |  |
| 3 | 增加格式约束 |  |  |  |  |
| 4 | 增加成功标准 |  |  |  |  |

Agent 工程不是“凭感觉调 Prompt”，而是固定输入、修改一个变量、观察结果并记录。

---

## 10. 常见误区

### 误区 1：能聊天就是 Agent

错误。现在的程序只有一次模型调用，没有工具、循环和任务状态。

### 误区 2：Prompt 越长越好

错误。冗余和冲突的要求可能降低效果，还会增加 Token。

### 误区 3：模型回答很自信，所以一定正确

错误。表达流畅和事实正确是两件事。

### 误区 4：把 API Key 写进 Python 最方便

短期方便，长期非常危险。密钥应使用环境变量、密钥管理服务或被 Git 忽略的本地开发文件。

### 误区 5：直接学习框架最快

如果不了解请求、响应、Token 和错误处理，换一个模型或框架就很容易卡住。先理解底层调用，再学框架会更快。

---

## 11. 今日自测

不要看答案，先自己回答：

1. base_url 的作用是什么？
2. api_key 和 model 有什么区别？
3. instructions 和 input 分别应该放什么？
4. response.output_text 是什么？
5. input_tokens 为什么会随着多轮对话增加？
6. 为什么 LLM 调用不是 Agent？
7. Agent 中 Tool 的作用是什么？
8. 为什么必须处理 APIConnectionError？
9. API 兼容为什么不代表能力完全相同？
10. 一个高质量 Prompt 至少应该包含哪些信息？

<details>
<summary>参考答案</summary>

1. 决定请求发送到哪个模型服务接口。
2. api_key 用于认证，model 用于选择具体模型。
3. instructions 描述长期行为约束，input 描述本次任务。
4. 从响应对象中提取出的主要文本回答。
5. 历史上下文需要再次发送给模型，也会占用输入 Token。
6. 它没有工具、执行循环、状态和安全边界。
7. 让模型能够获取外部信息或执行真实操作。
8. 网络失败是正常运行状态，程序需要给出可理解的错误并决定是否重试。
9. 不同服务商可能只兼容部分参数和功能，模型能力与错误码也可能不同。
10. 任务、必要上下文、约束、输出格式和成功标准。

</details>

---

## 12. 今日完成标准

全部做到才算完成 Day 01：

- [ ] 能在 PyCharm 中独立运行 hello_llm.py
- [ ] 能解释一次请求的完整链路
- [ ] 能解释 base_url、api_key、model
- [ ] 能区分 instructions 和 input
- [ ] 完成三组不同 Prompt 的对比实验
- [ ] 记录每次请求的 Token 用量
- [ ] 完成命令行学习助手
- [ ] 能解释为什么它目前还不是 Agent
- [ ] API Key 没有写入代码或提交到 Git

---

## 13. 今天不需要背的内容

下面这些只要知道存在即可：

- Transformer 数学原理；
- Attention 公式；
- 模型训练和微调；
- LangChain、LlamaIndex；
- Embedding 和向量数据库；
- MCP；
- 多 Agent；
- Agent 评测体系。

你的目标是成为 Agent Engineer，不是第一天就训练基础模型。

---

## 14. 明天学习什么

Day 02 将把普通 LLM 程序升级成第一个真正的微型 Agent：

~~~text
用户提出问题
    ↓
模型决定是否调用工具
    ↓
Python 执行工具
    ↓
把工具结果交回模型
    ↓
模型生成最终答案
~~~

计划实现两个工具：

- calculator：执行受控数学计算；
- get_current_time：获取指定时区时间。

Day 02 的核心是 Function Calling 和 Agent Loop。

---

## 15. 官方资料

按顺序阅读，不要一次性看完所有文档：

1. [OpenAI Developer Quickstart](https://developers.openai.com/api/docs/quickstart)
2. [OpenAI Prompt Engineering](https://developers.openai.com/api/docs/guides/prompt-engineering)
3. [OpenAI Function Calling](https://developers.openai.com/api/docs/guides/function-calling)——今天只看概念，明天实作

当前项目使用阿里云兼容服务，因此示例中的服务地址和模型名称以本地 hello_llm.py 为准。
