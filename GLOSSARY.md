# 22 天课程关键词汇表

用于每天复习：**看到一个词，能说出它是什么、解决什么问题。** 覆盖课程主线、Python 速查和最终项目中涉及的概念、工具及常见数据字段；普通业务示例编号和逐个函数名不单独背诵。

★ 表示优先掌握。每天先看当天对应的一组，遮住解释，尝试用自己的话回答；忘记的词第二天再看。不需要每天从头背到尾。

“英文全称或原词”中，缩写会展开；Hit、Recall、Token 等本身就是英文单词，软件名称也不强行编造全称。涉及分数、限制和文件用途时，以本课程的实现为准。

| 学到哪里 | 复习哪组 |
|---|---|
| Day 01 | [模型与请求](#model) |
| Day 02～03 | [工具调用](#tools)、[Python 与工程基础](#python) |
| Day 04 | [会话与记忆](#memory) |
| Day 05～07 | [RAG 与检索](#retrieval) |
| Day 08 | [评估与测试](#evaluation)、[文件与字段](#data) |
| Day 09 | [工具调用](#tools)，重点复习 LangChain 与消息类型 |
| Day 10～11 | [工作流与审批](#workflow) |
| Day 12 | [MCP 与通信](#mcp) |
| Day 13～14 | [会话与记忆](#memory)、[评估与测试](#evaluation) |
| Day 15～16 | [日志与性能](#observability)、[权限与安全](#security) |
| Day 17～18 | [多角色协作](#roles)、[服务接口](#api) |
| Day 19～22 | [项目与交付](#delivery)，再复习文末的[易混概念](#comparison) |

<a id="model"></a>

## 1. 模型与请求

对应 [Day 01](day01/DAY01.md)。

| 关键词 | 英文全称或原词 | 一句话记忆 |
|---|---|---|
| ★ LLM | Large Language Model | 大语言模型，根据输入生成文本等输出。 |
| Generative Model | Generative Model | 生成模型；本课程用它生成回答或提出工具调用。 |
| ★ Prompt | Prompt | 提示词，即这次交给模型的要求、问题和相关内容。 |
| Instructions | Instructions | 指令；本课请求里的固定要求，如“用中文解释并给例子”。 |
| Input / Output | Input / Output | 输入与输出；程序送给模型的内容和模型服务返回的内容。 |
| ★ Token | Token | 模型处理文本的计量单位，不等于字数；输入和输出分别计数。 |
| Usage | Usage | 用量记录；服务没返回用量，不能当作零消耗。 |
| Context | Context | 上下文，即模型本次请求能参考的信息，如问题、历史和资料。 |
| Context Window | Context Window | 上下文窗口，即一次模型处理能容纳的 Token 范围，具体限制由模型规定。 |
| ★ API | Application Programming Interface | 应用程序编程接口，让一个程序按约定使用另一个程序的能力。 |
| API Key | Application Programming Interface Key | 调用服务的凭证，由服务商提供，不能写进公开示例。 |
| SDK | Software Development Kit | 软件开发工具包；课程用 SDK 简化向模型服务发请求的代码。 |
| Responses API | Responses API | 课程客户端使用的模型接口，返回文字、工具调用等输出项。 |
| Base URL | Base Uniform Resource Locator | 服务基础地址，决定请求发往哪里；使用某家 SDK 不代表请求一定发往该公司。 |
| Model Weights | Model Weights | 模型权重，即模型训练得到的参数；Day 06 下载它们以运行本地编码模型。 |
| Inference | Inference | 推理，即用已有模型处理输入、得到输出；不等于重新训练模型。 |
| Timeout / Retry | Timeout / Retry | 超时与重试；等得太久结束一次尝试，符合条件时再试。 |

<a id="tools"></a>

## 2. 工具调用

对应 [Day 02](day02/DAY02.md)、[Day 03](day03/DAY03.md)、[Day 09](day09/DAY09.md)。

| 关键词 | 英文全称或原词 | 一句话记忆 |
|---|---|---|
| ★ Agent | Agent | 智能体；本课程指围绕任务调用模型、使用工具并控制执行过程的应用。 |
| ★ Agent Loop | Agent Loop | 智能体循环：请求模型 → 执行工具 → 回传结果，直到完成或达到限制。 |
| Tool | Tool | 工具，如计算器、工单查询；实际能力由程序或外部服务提供。 |
| ★ Function Calling / Tool Calling | Function Calling / Tool Calling | 函数调用／工具调用：模型提出名称和参数，应用执行并回传结果。 |
| Tool Definition | Tool Definition | 工具定义，说明名称、用途和参数格式，本身不执行函数。 |
| Arguments | Arguments | 调用参数，如乘法的 `a=25`、`b=3`。 |
| Handler / Dispatch | Handler / Dispatch | 处理函数／分发；把工具名对应到实际执行的函数。 |
| `call_id` | Call Identifier | 一次工具调用的关联编号，回传结果时用它对应原调用。 |
| Tool Result | Tool Result | 工具实际执行后的结果，可能成功，也可能包含错误。 |
| JSON | JavaScript Object Notation | 一种文本数据格式，常用于表示参数、结果和报告。 |
| ★ JSON Schema | JavaScript Object Notation Schema | 描述 JSON 应有哪些字段、字段类型和约束的规则。 |
| Schema | Schema | 数据结构约定；格式符合约定，不代表业务操作一定允许执行。 |
| Strict Mode | Strict Mode | 严格模式；模型接口和本地校验器各有自己的约束，不能混为一层。 |
| Structured Output | Structured Output | 结构化输出，按固定字段组织结果，便于程序读取和校验。 |
| Serialization / Deserialization | Serialization / Deserialization | 序列化／反序列化，例如字典转 JSON 字符串，以及反向转换。 |
| Step Budget | Step Budget | 步数预算；Day 02 的 `MAX_STEPS` 限制模型请求次数，不等于工具调用总次数。 |
| ★ LangChain | LangChain（框架名） | 提供模型接口、工具封装和现成 Agent 循环；本课程 Day 09 实际使用。 |
| `langchain-core` / `langchain-openai` | LangChain Core / LangChain OpenAI Integration | 基础消息与模型类型／模型服务适配包，和高层 `langchain` 包分工不同。 |
| `ChatOpenAI` | ChatOpenAI（适配器类名） | 将 LangChain 消息转成模型服务请求；实际服务由配置地址决定。 |
| `@tool` / `create_agent` | Tool Decorator / Create Agent | 工具装饰器／创建 Agent；前者包装函数说明，后者组织模型与工具循环。 |
| `invoke` / `messages` | Invoke / Messages | 执行调用／消息列表；Agent 的返回消息能展示工具请求和实际结果。 |
| `HumanMessage` / `AIMessage` / `ToolMessage` | Human Message / Artificial Intelligence Message / Tool Message | 用户消息／模型消息／工具结果；AIMessage 也可以包含工具请求。 |
| `tool_calls` / `tool_call_id` | Tool Calls / Tool Call Identifier | 工具请求列表／结果对应的调用编号，用于检查同一次调用的输入和输出。 |
| Middleware | Middleware | 中间件，在循环周围加入控制逻辑；Day 09 用它限制模型调用次数。 |

<a id="memory"></a>

## 3. 会话与记忆

对应 [Day 04](day04/DAY04.md)、[Day 13](day13/DAY13.md)。

| 关键词 | 英文全称或原词 | 一句话记忆 |
|---|---|---|
| ★ Session | Session | 会话，把连续交互归在一起；具体保存什么由应用决定。 |
| ★ Turn | Turn | 一轮交互，从一次用户提问到最终回答，可能包含多次模型请求。 |
| ★ History | History | 对话历史；应用将它放入后续请求，模型才能参考之前的内容。 |
| Multi-turn Conversation | Multi-turn Conversation | 多轮对话，让后续提问能接着之前的内容继续。 |
| Short-term Memory | Short-term Memory | 短期记忆，如当前会话的历史；本课程 Day 04 保存在内存中。 |
| ★ Long-term Memory | Long-term Memory | 长期记忆，如跨进程保存的用户偏好；应用读取后才会影响行为。 |
| Preference | Preference | 用户偏好，如“回答简短”；Day 13 只保存明确提供的允许字段。 |
| TTL | Time To Live | 有效期；本课以秒计，超过期限的记忆不再参与读取。 |
| Remember / Recall（记忆操作） | Remember / Recall | 保存／读取记忆；Day 13 的 `recall()` 是读取偏好，不是计算 Recall 召回率。 |
| Expiration | Expiration | 过期，记录到期后不再生效，不代表数据库中的记录已物理删除。 |
| Forget | Forget | 遗忘操作；本课指主动删除一项已保存的偏好。 |
| User Isolation | User Isolation | 用户隔离，按用户区分记忆，避免把别人的偏好带入当前请求。 |
| `user_id` / `session_id` | User Identifier / Session Identifier | 用户编号／会话编号，分别标识“谁”和“哪段交互”。 |

<a id="retrieval"></a>

## 4. RAG 与检索

对应 [Day 05](day05/DAY05.md)、[Day 06](day06/DAY06.md)、[Day 07](day07/DAY07.md)。

| 关键词 | 英文全称或原词 | 一句话记忆 |
|---|---|---|
| ★ RAG | Retrieval-Augmented Generation | 检索增强生成：先找资料，再把资料交给模型帮助生成回答。 |
| Knowledge Base | Knowledge Base | 知识库，待查询的资料集合；课程最初只是几个本地文件。 |
| Document / Corpus | Document / Corpus | 文档／语料，单份原始资料及用于检索的资料集合。 |
| ★ Chunk / Chunking | Chunk / Chunking | 资料块／切块，把文档分成便于检索和放入上下文的小段。 |
| Chunk ID | Chunk Identifier | 资料块编号，如 `hours.md#1`；这里的 1 是块序号，不是检索排名。 |
| Query | Query | 查询，即用来搜索资料的问题或文本。 |
| ★ Retrieval / Retriever | Retrieval / Retriever | 检索／检索器，从资料集合中找候选内容的过程和实现。 |
| ★ Lexical Search | Lexical Search | 关键词检索，按词或字匹配；Day 05 用共同词字的比例打分。 |
| Tokenization | Tokenization | 切分文本单元；Day 05 的词字切分规则与生成模型的 Token 计数不同。 |
| BM25 | Best Matching 25 | 一种关键词相关性评分方法，考虑词频、词的稀有程度和文档长度；课程仅作扩展介绍。 |
| ★ Embedding | Embedding | 嵌入，将文本编码为向量，用来比较文本间的相关程度。 |
| Vector | Vector | 向量，一组数字；资料和问题都能被编码成向量。 |
| Dimension | Dimension | 维度，即一个向量包含多少个数；本课所用编码模型输出 512 维。 |
| Normalize | Normalize | 归一化；Day 06 将非零向量的长度变成 1，便于比较方向。 |
| Cosine Similarity | Cosine Similarity | 余弦相似度，比较向量方向的接近程度，分数不是答案正确率。 |
| ★ Vector Search / Semantic Search | Vector Search / Semantic Search | 向量检索／语义检索；本课按向量相似度搜索，帮助匹配不同措辞。 |
| Index / Indexing | Index / Indexing | 索引／建索引，为后续搜索组织数据；Day 06 建库时保存向量与原文对应关系。 |
| Vector Database | Vector Database | 向量数据库，保存向量及关联数据，并提供相似搜索等能力。 |
| Qdrant | Qdrant（产品名） | 本课程使用的向量数据库，既用到本地持久化模式，也用到内存模式。 |
| Collection | Collection | 集合；Qdrant 中一组按配置组织的记录。 |
| Point | Point | Qdrant 的一条记录，包含编号、向量以及附带数据。 |
| Payload / Metadata | Payload / Metadata | 附带数据／元数据；本课用它们保存原文、来源、门店等信息。 |
| FastEmbed | FastEmbed（库名） | 本课程调用本地 Embedding 模型、计算文本向量的库。 |
| BGE | BAAI General Embeddings | 本课程使用的嵌入模型系列，具体模型为 `bge-small-zh-v1.5`。 |
| BAAI | Beijing Academy of Artificial Intelligence | 北京智源人工智能研究院，BGE 的开发机构。 |
| Hugging Face / HF | Hugging Face（平台名） | 模型与相关资源平台；本课模型下载会使用相关缓存。 |
| ★ Hybrid Search | Hybrid Search | 混合检索，同时使用多种检索方法；本课组合关键词与向量搜索。 |
| Filter | Filter | 过滤，先按门店等条件缩小资料范围；过滤条件本身不等于身份授权。 |
| Candidate | Candidate | 候选资料，已被初步找出、还可能参与融合和重排的块。 |
| Rank / Score | Rank / Score | 排名／分数；排名是第几名，分数是某种方法算出的数值，两者不同。 |
| ★ RRF | Reciprocal Rank Fusion | 倒数排名融合，利用各路检索的排名合并结果；本课每路贡献 `1 / (rrf_k + rank)`。 |
| ★ Rerank / Reranker | Rerank / Reranker | 重排／重排器，对已有候选重新排序；Day 07 用错误码匹配规则。 |
| Deduplication | Deduplication | 去重，减少重复资料；本课按编号融合，再去除空白规整后相同的原文。 |
| ★ Top-k | Top-k | 最多取排名靠前的 k 条；可能因过滤或预算不足返回更少。 |
| `candidate-k` | Candidate Count Limit | 每一路检索最多先取多少条候选，是本课程的参数名。 |
| `rrf-k` | RRF Smoothing Constant | RRF 公式中的平滑常数，本课默认 60，不表示返回 60 条资料。 |
| `min-score` | Minimum Score | 最低分数阈值，过滤分数不足的候选；阈值需要结合检索方法和数据判断。 |
| Context Budget / `max-chars` | Context Budget / Maximum Characters | 上下文预算；Day 07 限制组装后 `input` 的字符数，不是 Token 数。 |
| Evidence / Source / Citation | Evidence / Source / Citation | 证据／来源／引用，分别是依据内容、内容出处和回答中指向出处的标记。 |
| Extractive Preview | Extractive Preview | 原文摘录预览，展示找到的资料；课程默认分支常停在这里，没有生成模型回答。 |
| No Evidence / Abstention | No Evidence / Abstention | 无证据／拒答；没找到候选与模型主动说明无法回答，是不同层的行为。 |

名称核对：[BM25 说明](https://devblogs.microsoft.com/azure-sql/two-hybrid-search/)、[BGE 官方说明](https://bge-model.com/bge/)、[BAAI 与 BGE](https://bge-model.com/)。RRF 的方法来源见[原始论文](https://cormack.uwaterloo.ca/cormacksigir09-rrf.pdf)。

<a id="evaluation"></a>

## 5. 评估与测试

对应 [Day 08](day08/DAY08.md)、[Day 14](day14/DAY14.md)、[Day 21](day21/DAY21.md)。

| 关键词 | 英文全称或原词 | 一句话记忆 |
|---|---|---|
| ★ Eval / Evals | Evaluation / Evaluations | 评估，拿实际表现与事先约定的要求比较。 |
| ★ Test Case / Dataset | Test Case / Dataset | 测试用例／数据集；一条输入和预期，以及这些用例的集合。 |
| Annotation / Ground Truth | Annotation / Ground Truth | 人工标注／参考标准；Day 08 由人确认每题应该找到哪些资料。 |
| Expected / Actual | Expected / Actual | 预期／实际，测试前写下的要求与运行后得到的结果。 |
| Metric | Metric | 指标，用一种明确规则描述某个方面的表现。 |
| ★ Hit@k | Hit at k | 前 k 条里有没有正确资料？有记 1，没有记 0。Hit 本身不是缩写。 |
| ★ Recall@k | Recall at k | 应该找到的资料找全了多少？前 k 条命中的不同正确块数 ÷ 应找块数。 |
| ★ RR@k | Reciprocal Rank at k | 第一条正确资料多靠前？其排名的倒数；前 k 条没有正确资料记 0。 |
| ★ MRR@k | Mean Reciprocal Rank at k | 多道题的 RR@k 平均值；Day 08 只平均四道有答案题。 |
| `@k` | At k | 只考察返回结果的前 k 条，排名从 1 开始。 |
| Mean / Average | Mean / Average | 平均值；Day 08 先逐题算分，再对有答案题取算术平均。 |
| Answerable / Unanswerable | Answerable / Unanswerable | 有答案／无答案，指原文中是否有依据，不是检索器这次是否成功。 |
| Baseline | Baseline | 基线，作为后续比较起点的一份方法或结果。 |
| Regression Test / Evaluation | Regression Test / Evaluation | 回归测试／评估，改动后重跑旧用例，检查原本能做的事是否仍正常。 |
| Pass Rate | Pass Rate | 通过率，通过用例数 ÷ 被评用例数；含义取决于每题的通过规则。 |
| Trajectory / Path | Trajectory / Path | 执行轨迹／路径，记录实际经过的节点、工具、参数和结果。 |
| Budget | Budget | 预算，如工具次数、总步数、时间或费用上限；未超预算不代表任务已完成。 |
| Fault Injection | Fault Injection | 故障注入，故意制造错误，检查程序或评估器能否正确发现和处理。 |
| Model-as-Judge | Model-as-Judge | 模型评审，让模型按标准判断回答；课程仅介绍，默认评估使用程序规则。 |
| Quality Gate / Threshold | Quality Gate / Threshold | 质量门槛／阈值，如平均 Recall 未达要求就让检查失败。 |
| Unit / Integration / Acceptance Test | Unit / Integration / Acceptance Test | 单元／集成／验收测试，分别检查局部逻辑、组件配合及需求是否满足。 |
| Scope | Scope | 评估范围，说明报告实际测了什么，避免把局部通过当作整体质量保证。 |

手算卡：应找 A、B，实际返回 X、A（X 无关）。**Hit@2＝1，Recall@2＝1/2，RR@2＝1/2。**

<a id="workflow"></a>

## 6. 工作流与审批

对应 [Day 10](day10/DAY10.md)、[Day 11](day11/DAY11.md)。

| 关键词 | 英文全称或原词 | 一句话记忆 |
|---|---|---|
| ★ Workflow | Workflow | 工作流，把任务拆成有顺序和分支的步骤；可以完全由规则驱动。 |
| LangGraph | LangGraph（框架名） | 课程用来组织状态、节点、分支以及暂停恢复的工作流框架。 |
| Graph / State Graph | Graph / State Graph | 图／状态图，用节点和连线描述状态怎样流转。 |
| Subgraph / Nested Workflow | Subgraph / Nested Workflow | 子图／嵌套流程；Day 10 在外层 diagnose 节点内运行 LangChain Agent 的完整工具循环。 |
| ★ State | State | 状态，流程当前保存的一组数据，如问题、工具结果和草稿。 |
| Node | Node | 节点，读取状态、做一件事并返回更新的函数。 |
| Edge / Conditional Edge | Edge / Conditional Edge | 边／条件边，决定做完一个节点后固定或按条件进入哪里。 |
| Reducer | Reducer | 状态合并规则；Day 10 把两间教室的容量列表追加后汇总，默认替换会丢掉第一间结果。 |
| Compile / Invoke | Compile / Invoke | 编译／调用；本课先组装可运行的图，再传入状态执行。 |
| Recursion Limit | Recursion Limit | 图执行的步数保护，防止流程不断循环；不是 Python 函数递归深度。 |
| ★ Checkpoint | Checkpoint | 检查点，保存流程快照，方便之后恢复执行。 |
| Persistence | Persistence | 持久化，把数据保存到磁盘等存储，让进程退出后仍能读取。 |
| Interrupt / Resume | Interrupt / Resume | 暂停／恢复，流程等待审批，之后带着决定继续运行。 |
| Human Approval | Human Approval | 人工审批，让人核对具体动作和内容后，决定批准或拒绝。 |
| Draft / Approve / Reject | Draft / Approve / Reject | 草稿／批准／拒绝；草稿还不是已经执行的业务结果。 |
| `thread_id` | Thread Identifier | 流程标识；Day 11 用它找到同一份待恢复的工作流。 |
| ★ Idempotency | Idempotency | 幂等，同一个动作重试多次，不产生重复的业务效果。 |
| `operation_id` | Operation Identifier | 动作编号，用来识别“同一笔写入”，配合唯一约束防止重复。 |
| Unique Constraint | Unique Constraint | 数据库唯一约束，阻止某个编号出现第二条记录。 |
| Digest / SHA-256 | Digest / Secure Hash Algorithm 256-bit | 摘要／256 位安全哈希算法；本课给草稿算指纹，核对批准内容是否被改动。 |
| Transaction / Commit / Rollback | Transaction / Commit / Rollback | 事务／提交／回滚，把一组数据库操作一起确认或撤销。 |

<a id="mcp"></a>

## 7. MCP 与通信

对应 [Day 12](day12/DAY12.md)。

| 关键词 | 英文全称或原词 | 一句话记忆 |
|---|---|---|
| ★ MCP | Model Context Protocol | 模型上下文协议，约定应用如何发现和使用工具、资源、提示模板等能力。 |
| Client / Server | Client / Server | 客户端／服务端，一方发起请求，一方提供能力；本课是两个 Python 程序。 |
| Protocol | Protocol | 协议，通信双方共同遵守的消息和交互规则。 |
| Transport | Transport | 传输方式，消息通过什么通道到达另一方。 |
| stdio | Standard Input / Output | 标准输入输出；Day 12 通过子进程的输入输出通道传 MCP 消息。 |
| stdin / stdout / stderr | Standard Input / Standard Output / Standard Error | 标准输入／输出／错误流；本课 stdout 留给协议，调试日志写 stderr。 |
| Subprocess | Subprocess | 子进程，由当前程序启动的另一个进程；本课客户端启动 MCP 服务端。 |
| Initialize / List Tools / Call Tool | Initialize / List Tools / Call Tool | 初始化／列工具／调工具，建立协议会话后发现能力，再按名称调用。 |
| MCP Tool | Model Context Protocol Tool | MCP 工具，服务端提供的可调用能力，如查询工单。 |
| MCP Resource | Model Context Protocol Resource | MCP 资源，可按地址读取的内容，如自习室规则。 |
| MCP Prompt | Model Context Protocol Prompt | MCP 提示模板，可复用的提示内容；本课程服务没有实现这一项。 |
| URI | Uniform Resource Identifier | 统一资源标识符，标识资源，如 `study://rules`。 |
| Streamable HTTP | Streamable HTTP（传输名称，HTTP 全称见接口组） | MCP 的另一种传输方式；课程 Day 12 使用的是 stdio。 |

<a id="security"></a>

## 8. 权限与安全

对应 [Day 16](day16/DAY16.md)，审批部分见 Day 11。

| 关键词 | 英文全称或原词 | 一句话记忆 |
|---|---|---|
| ★ Prompt Injection | Prompt Injection | 提示词注入，输入或资料夹带指令，诱导模型偏离原任务或约束。 |
| Guardrails | Guardrails | 防护约束，如工具白名单、参数校验、权限检查和执行预算。 |
| Tool Gateway | Tool Gateway | 工具网关，把工具请求集中到一个入口检查，再决定是否执行。 |
| Allowlist | Allowlist | 白名单，只允许明确列出的工具或字段进入后续流程。 |
| Validation | Validation | 校验，检查输入类型、范围、必填项和额外字段等是否符合要求。 |
| ★ Authentication / Authorization | Authentication / Authorization | 认证／授权，分别回答“你是谁”和“你能做什么”。 |
| Trusted Identity | Trusted Identity | 可信身份，由应用的身份机制提供，不能相信模型参数自称是某个用户。 |
| Ownership / Owner | Ownership / Owner | 资源归属／所有者；本课检查工单是否属于当前用户。 |
| Least Privilege | Least Privilege | 最小权限，只开放完成当前任务实际需要的能力和资源。 |
| Side Effect | Side Effect | 副作用，如写入工单；它会改变业务状态，需要考虑审批和重试。 |
| Data Leakage | Data Leakage | 数据泄露，向无权访问的人返回内容；报错对象也不能夹带私有正文。 |
| Redaction | Redaction | 脱敏，移除或遮盖不该进入日志、输出的敏感信息。 |

<a id="observability"></a>

## 9. 日志、用量与性能

对应 [Day 15](day15/DAY15.md)、[Day 21](day21/DAY21.md)。

| 关键词 | 英文全称或原词 | 一句话记忆 |
|---|---|---|
| Observability | Observability | 可观测性，通过日志、追踪和指标了解程序内部发生了什么。 |
| ★ Trace / Tracing | Trace / Tracing | 一次完整请求的追踪／记录过程，用来串起检索、工具等步骤。 |
| ★ Span | Span | 追踪中的一个步骤，记录它的开始、结束或失败及耗时。 |
| `trace_id` / `span_id` | Trace Identifier / Span Identifier | 整次追踪编号／步骤编号，用于把同一次执行的记录对应起来。 |
| Log / Event / Stage | Log / Event / Stage | 日志／事件／阶段，如检索阶段发生了一次 start 或 error 事件。 |
| JSONL | JSON Lines | 每行一条完整 JSON 数据的格式，本课用于追加日志。 |
| Latency / Duration | Latency / Duration | 延迟／耗时，完成请求或某一步花了多久，需要明确计时范围。 |
| First-token Latency | First-token Latency | 首 Token 延迟，从发起请求到收到第一个输出 Token 的时间；本课未采集。 |
| ★ p50 / p95 | 50th Percentile / 95th Percentile | 第 50／95 百分位，查看排序后约处在对应比例位置的耗时。 |
| Nearest-rank Method | Nearest-rank Method | 最近秩法；本课取排序后的第 `ceil(p × N)` 个值，p 用 0～1 表示。 |
| Warm Query / Cold Start | Warm Query / Cold Start | 热查询／冷启动，前者在引擎就绪后查询，后者还涉及初始化等准备。 |
| Concurrency / Lock | Concurrency / Lock | 并发／锁，多个请求重叠进行时，用锁保护不能同时修改的共享状态。 |
| Cost Estimate | Cost Estimate | 费用估算，按输入、输出用量和对应单价计算；Day 15 的单价是假设值。 |
| CPU | Central Processing Unit | 中央处理器；Day 06 在本机 CPU 上运行编码模型。 |

<a id="roles"></a>

## 10. 多角色协作

对应 [Day 17](day17/DAY17.md)。

| 关键词 | 英文全称或原词 | 一句话记忆 |
|---|---|---|
| Multi-Agent | Multi-Agent | 多智能体协作，让多个 Agent 分工完成任务；课程先用普通函数演示交接。 |
| Role | Role | 角色，用清楚的输入、职责和输出区分工作，如资料员、审核员、写作者。 |
| ★ Handoff | Handoff | 交接，把任务及继续处理所需的信息交给下一角色。 |
| Router | Router | 路由器，根据当前请求选择走哪条处理路线。 |
| Supervisor | Supervisor | 协调者，持续分配工作、检查进展并决定何时结束。 |
| Evidence Package | Evidence Package | 证据包，交接时携带原文、来源编号等可核对信息。 |
| Review | Review | 审核，检查交接内容；本课只核对引用与原文一致，未判断它是否回答问题。 |

<a id="api"></a>

## 11. 服务接口

对应 [Day 18](day18/DAY18.md)、[Day 20](day20/DAY20.md)。

| 关键词 | 英文全称或原词 | 一句话记忆 |
|---|---|---|
| HTTP | Hypertext Transfer Protocol | 超文本传输协议；课程客户端通过它调用本机网页接口。 |
| URL | Uniform Resource Locator | 统一资源定位符，描述访问地址，如 `http://127.0.0.1:8000/chat`。 |
| FastAPI | FastAPI（框架名） | 本课程用于定义 HTTP 路径、输入格式和返回内容的 Python 框架。 |
| ASGI | Asynchronous Server Gateway Interface | 异步服务器网关接口，是 Python Web 应用与服务器之间的一套调用约定。 |
| Uvicorn | Uvicorn（软件名） | 运行本课程 FastAPI 应用、监听 HTTP 请求的 ASGI 服务器。 |
| Endpoint / Route | Endpoint / Route | 接口端点／路由，例如 `/chat` 交给对应函数处理。 |
| GET / POST | GET / POST（HTTP 方法名） | 两种请求方法；本课 GET 查健康状态或订阅事件，POST 提交聊天输入。 |
| Request Body / Response | Request Body / Response | 请求体／响应，例如发入问题 JSON，再收到答案和来源 JSON。 |
| Health Check | Health Check | 健康检查，如访问 `/health` 确认服务能响应；不等于所有业务都正常。 |
| ★ SSE | Server-Sent Events | 服务端发送事件，通过一条持续的 HTTP 响应陆续把事件发给客户端。 |
| Streaming | Streaming | 流式输出，结果分批到达；本课流式发的是处理阶段事件，不是逐 Token 生成。 |
| EventSource | EventSource（浏览器接口名） | 浏览器接收 SSE 事件的接口；自定义 POST 流通常需用其他读取方式。 |
| `request_id` | Request Identifier | 请求编号，区分同一会话中每一次独立请求。 |
| Worker | Worker | 服务工作进程；本课的内存会话和锁不会自动在多个进程间共享。 |
| TestClient | TestClient（测试客户端类名） | 进程内请求 Web 应用的测试工具，不必实际监听网络端口。 |

<a id="python"></a>

## 12. Python 与工程基础

对应 [Day 03](day03/DAY03.md)、[Python 语法速查](day03/PYTHON_REFERENCE.md)。

| 关键词 | 英文全称或原词 | 一句话记忆 |
|---|---|---|
| list / dict / set | List / Dictionary / Set | 列表／字典／集合，分别适合保存有序项、按键取值和去重成员。 |
| str / int / float / bool | String / Integer / Floating-point Number / Boolean | 字符串／整数／浮点数／布尔值，是课程常用的数据类型。 |
| None | None | 表示没有值；它与数字 0、空列表、空字符串不同。 |
| append / extend | Append / Extend | 向列表追加一个对象／逐项追加另一组元素。 |
| Slice / Shallow Copy | Slice / Shallow Copy | 切片／浅复制，可取得部分或复制外层容器，内部可变对象仍可能共享。 |
| List Comprehension | List Comprehension | 列表推导式，用“逐项处理并筛选”的写法创建列表。 |
| Set Intersection | Set Intersection | 集合交集，找两组都包含的项；Day 08 用它统计正确块。 |
| Function / Keyword Argument | Function / Keyword Argument | 函数／命名参数，如 `multiply(a=25, b=3)` 明确传给哪个参数。 |
| Unpacking | Unpacking | 解包；`**arguments` 可把字典展开成命名参数。 |
| Class / Instance | Class / Instance | 类／实例，定义一类对象的结构与行为，再创建具体对象。 |
| dataclass | Data Class | 数据类，方便把相关字段放在一起，如一次工具调用的名称和参数。 |
| `default_factory` | Default Factory | 默认值工厂，如为每个会话分别创建新列表，避免共用可变默认值。 |
| Decorator / Property | Decorator / Property | 装饰器／属性；`@...` 为定义附加行为，`@property` 让方法像属性一样读取。 |
| Type Hint | Type Hint | 类型标注，帮助人和检查工具理解类型，通常不自动验证运行时数据。 |
| Protocol（Python） | Protocol | 结构接口约定，如客户端必须提供某个方法；这里不是网络通信协议。 |
| TypedDict / Annotated / Any | Typed Dictionary / Annotated / Any | 字典字段类型声明／类型附加信息／任意类型，都是读代码时用到的类型工具。 |
| ★ Dependency Injection | Dependency Injection | 依赖注入，把需要的对象传进来，便于替换真实客户端与测试替身。 |
| Fake | Fake | 测试替身，按人工预设返回结果，让测试稳定且无需请求模型。 |
| assert | Assert | 断言，检查条件是否成立，不成立就让相应测试失败。 |
| Module / Package / Import | Module / Package / Import | 模块／包／导入，用于组织代码并复用其中的定义。 |
| Entry Point / `__main__` | Entry Point / Main | 程序入口；`if __name__ == "__main__"` 下的代码在模块作为程序运行时执行。 |
| Path / Working Directory | Path / Working Directory | 路径／工作目录，相对路径从当前工作目录计算，不一定从源码目录计算。 |
| Exception / raise / except | Exception / Raise / Except | 异常／抛出／捕获，把失败明确地向外传递或在合适位置处理。 |
| Context Manager / with | Context Manager / With | 上下文管理器／with 语句，统一管理进入、退出时的资源或步骤收尾。 |
| Generator / yield | Generator / Yield | 生成器／产出值，函数可逐次提供内容；课程流式接口会用到它。 |
| async / await | Asynchronous / Await | 异步／等待异步操作，不代表所有步骤会自动并行执行。 |
| asyncio | Asynchronous Input/Output（模块用途） | Python 异步编程模块，课程用 `asyncio.run()` 启动异步入口。 |
| Pydantic | Pydantic（库名） | 定义数据模型并进行运行时校验，检查计划、工具参数和 HTTP 输入。 |
| pytest | pytest（工具名） | 执行 Python 测试并汇总通过与失败的工具。 |
| Ruff / mypy | Ruff / mypy（工具名） | 代码检查与格式化工具／静态类型检查工具，不能代替业务测试。 |

<a id="delivery"></a>

## 13. 项目与交付

对应 [总说明](README.md)、[Day 19](day19/DAY19.md)～[Day 22](day22/DAY22.md)。

| 关键词 | 英文全称或原词 | 一句话记忆 |
|---|---|---|
| CLI / UI | Command-Line Interface / User Interface | 命令行界面／用户界面，前者通过终端命令操作，后者是更广义的交互界面。 |
| Environment Variable | Environment Variable | 环境变量，由运行环境提供配置，如模型地址和服务凭证。 |
| Virtual Environment / venv | Virtual Environment | 虚拟环境，隔离项目所使用的 Python 依赖。 |
| Cache | Cache | 缓存，保留已下载或计算的内容供后续复用；本课会缓存模型文件。 |
| uv | uv（工具名） | 本课程用来管理 Python 环境、同步依赖并运行命令的工具。 |
| Dependency / Lockfile | Dependency / Lockfile | 依赖／锁文件，记录需要的库及其具体版本，帮助复现运行环境。 |
| Dependency Group | Dependency Group | 依赖组，按用途选择安装；本课有 `rag`、`workflow`、`api` 等组。 |
| SQL / SQLite | Structured Query Language / SQLite（数据库名） | SQL 是数据库查询语言；SQLite 是本课保存快照、工单和记忆的本地数据库。 |
| ID / UUID | Identifier / Universally Unique Identifier | 标识符／通用唯一标识符，用于区分资料、请求、记录等对象。 |
| Unix Timestamp | Unix Timestamp | Unix 时间戳，按距 1970-01-01 UTC 的时间表示时刻；本课记忆有效期用秒。 |
| UTC | Coordinated Universal Time | 协调世界时，报告用它标记生成时间，减少时区歧义。 |
| Git / `.gitignore` | Git（工具名）/ Git Ignore Rules | 版本管理工具／忽略规则；新增忽略规则不会移除已有历史中的文件。 |
| Markdown / README | Markdown（格式名）/ Read Me | 文档格式／项目说明文件，帮助读者理解用途、安装和验证方式。 |
| ★ ADR | Architecture Decision Record | 架构决策记录，写清为何做某个选择，以及接受了什么限制。 |
| Requirements / Acceptance Criteria | Requirements / Acceptance Criteria | 需求／验收标准，分别说明要解决什么问题，以及怎样证明已经做到。 |
| Capstone | Capstone Project | 综合结课项目；本课指复用前面模块的“青禾自习室助手”。 |
| Demo / JD | Demonstration / Job Description | 演示／岗位描述，分别用来展示实际能力和对照岗位要求。 |

<a id="data"></a>

## 14. 文件名与常见字段：它从哪来？

这些是本课程的命名约定，不是需要另装的软件。完整来源见 [文件与数据来源表](DATA_GUIDE.md)。

| 名称 | 英文原词或名称含义 | 一句话记忆 |
|---|---|---|
| `knowledge` | Knowledge | 待查询资料，由人准备；不是检索结果。 |
| ★ `rag_cases.json` | RAG Evaluation Cases | 人工编写的检索评估用例，包含问题和应找的资料编号。 |
| `agent_cases.json` | Agent Evaluation Cases | 人工编写的流程评估用例，包含输入和预期结果。 |
| `eval_retrieval.py` | Evaluate Retrieval | 逐题调用检索器并算分的程序，是报告的生成入口。 |
| ★ `lexical-k1.json` / `lexical-k2.json` | Lexical Retrieval, Top-1 / Top-2 Report | 程序生成的关键词检索报告，分别每题最多取 1／2 块资料。 |
| `baseline.json` / `fault.json` | Baseline / Fault Report | Day 14 的正常与故障分支报告，由同一评估程序实际执行后生成。 |
| `reports` / `logs` / `data` | Reports / Logs / Data | 评估结果／运行记录／本地状态等数据，具体内容由各课程序决定。 |
| `index.json` | Index Metadata | Day 06 建库生成的说明文件，记录模型、维度、资料摘要等，向量保存在 Qdrant 中。 |
| `question` / `purpose` | Question / Purpose | 用例的问题／出题目的；purpose 帮人理解用例，不参与评分。 |
| `relevant_chunk_ids` | Relevant Chunk Identifiers | 人工标注的正确资料块编号，是检索评估的参考标准。 |
| `retrieved` | Retrieved Chunks | 检索器这次实际返回的资料块编号。 |
| `dataset` / `retriever` | Dataset / Retriever | 报告记录的用例来源与被测检索实现。 |
| `generated_at` / `scope` | Generated At / Scope | 报告生成时间／评估范围，读分数前先确认这两项。 |
| `updated_at` / `expires_at` / `version` | Updated At / Expires At / Version | Day 13 记忆的更新时间／过期时间／版本号，帮助判断记录的新旧和有效性。 |
| `answerable_count` / `mean.rr` | Answerable Count / Mean Reciprocal Rank | 有答案题数量／RR 平均值；Day 08 的 mean.rr 就是 MRR@k。 |
| `returned_candidate_on_unanswerable` | Returned Candidate on Unanswerable Question | 无答案题是否仍返回候选资料；它不表示模型是否编造了回答。 |
| `checks` / `passed` / `events` | Checks / Passed / Events | 检查项／是否通过／实际事件，帮助解释流程评估为什么给出这个结果。 |
| `--hybrid` / `--ask-model` | Hybrid Retrieval / Ask Generative Model | 最终项目的两个独立开关，分别启用混合检索和生成模型回答。 |
| `EXAMPLES` / `DemoChatModel` | Examples / Demo Chat Model | Day 09 人工预设的问题和工具参数／测试替身，工具实际执行，收尾使用固定模板。 |

<a id="comparison"></a>

## 最后一分钟：把容易混淆的词分开

| 容易混淆 | 怎样记 |
|---|---|
| RAG / RRF / RR / MRR | RAG 是先检索再生成的流程；RRF 合并排名；RR 给单题排序打分；MRR 平均多题 RR。 |
| LangChain / LangGraph | 前者提供现成模型工具循环，后者让你直接控制状态和步骤；LangChain Agent 底层使用 LangGraph。 |
| Hit / Recall / RR | 找到了吗？找全了吗？第一条正确资料排得靠前吗？ |
| 检索阶段“召回” / Recall 指标 | 前者指找候选的动作，后者是找到的正确资料占应找资料的比例。 |
| Lexical / Vector / Hybrid | 按词字匹配／按向量相似度搜索／组合多种检索。 |
| Embedding / 生成模型 | 前者在本课把文本变成向量，后者生成回答或工具请求。 |
| RRF / Rerank | RRF 按多路排名合并；重排再按规则或模型重新比较已有候选。 |
| top-k / candidate-k / rrf-k | 最终最多取几条／各路先取几条／融合公式中的平滑常数。 |
| Session / History / Turn | 一段会话／已保留的历史／一次问题到最终回答的完整轮次。 |
| History / Memory / Checkpoint | 之前聊了什么／以后仍要使用的偏好或事实／流程停在哪里及当时状态。 |
| Schema / Authorization / Approval | 格式合不合法／当前用户有没有权限／具体动作有没有获批。 |
| Checkpoint / Idempotency | 前者帮助恢复流程，后者避免恢复或重试造成重复业务效果。 |
| `rag_cases.json` / `lexical-k1.json` | 前者是人写的题目和标准，后者是程序运行后生成的成绩。 |
| Trace / Span | 一整次请求／其中一个步骤。 |
| Token / 字符 | 两种不同计量；本课字符预算不能直接当作模型 Token 预算。 |
| SSE / 逐 Token 输出 | SSE 是传事件的方式，事件可以是处理阶段，也可以承载文本片段。 |

[返回课程总说明](README.md) · [查看文件与数据来源](DATA_GUIDE.md)
