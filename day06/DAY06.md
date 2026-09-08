# Day 06：把文字变成向量，再找回原文

> 今天只替换 Day 05 的搜索方法：先用人工数字理解相似度，再用真实本地模型建库与查询。
> Embedding 用来编码文字，生成模型用来写回答，两者分开运行。

## 1. 为什么要换一种找法？

资料写 wifi，问题却说“无线网络”。关键词可能因措辞不同而漏掉内容。
Embedding 模型把一段文本编码成数字列表，使相关文本有机会得到接近的表示，再按相似程度搜索。

```text
原文 → Embedding → 保存向量与原文
问题 → 同一编码方式 → 搜索相近向量 → 取回原文 → 可选生成回答
```

相关不代表必然正确。能否解决某个同义表达，要用实际题目测试。

## 2. 哪些是提供的，哪些是生成的？

| 文件或目录 | 来源与用途 |
|---|---|
| [Day 05 原文](../day05/knowledge/) | 人工编写，仍是今天被搜索的内容 |
| [vector_basics.py](vector_basics.py) | 人工数字练习，不调用模型 |
| [build_index.py](build_index.py) | 读取原文、计算向量、保存索引 |
| [vector_retriever.py](vector_retriever.py) | 编码问题、搜索已保存的库 |
| [vector_store.py](vector_store.py) | 两个入口共用的模型和数据库函数 |
| `day06/data/models/` | 首次加载时下载的模型权重缓存 |
| `day06/data/qdrant/`、`day06/data/index.json` | 建库程序生成的向量库和索引说明 |

`data/` 无需手建，已加入 Git 忽略。权重是下载的，向量是根据原文算出的，`index.json` 是建库记录，三者用途不同。
附带下载缓存默认在 `day06/data/huggingface/`；已配置 `HF_HOME` 时沿用你的设置。

## 3. 先手算一次，不使用模型

一个向量就是一组数，二维有两个数，512 维有 512 个数。
下面是为了手算**人工设计**的向量：

| 对象 | 向量 |
|---|---|
| 问题 | `[1, 0]` |
| 网络资料 | `[0.8, 0.6]` |
| 关门资料 | `[0, 1]` |

这三个向量长度都是 1，比较方向时可将对应位置相乘再相加：

```text
问题与网络资料：1×0.8 + 0×0.6 = 0.8
问题与关门资料：1×0   + 0×1   = 0
```

```bash
uv run python -m day06.vector_basics
```

应看到 0.800 和 0.000。这只验证给定数字的计算，没有证明模型理解了“网络”。
余弦相似度比较方向，理论范围 -1～1；分数不是回答正确率。
`normalize()` 先把向量长度变成 1，例如 `[3,4] → [0.6,0.8]`，再由 `cosine()` 做比较。

## 4. 真正的模型与数据库放在哪里？

本课用 FastEmbed 在本机 CPU 运行 `BAAI/bge-small-zh-v1.5`，输出 512 维向量。每个数是模型学到的表示，不能把某一维直接叫作“网络程度”。[模型说明](https://huggingface.co/BAAI/bge-small-zh-v1.5)

Qdrant 使用本地模式，库文件在电脑里，无需单独启动数据库服务。它保存向量、原文与来源，搜索后再把原文取回来。[本地模式说明](https://github.com/qdrant/qdrant-client#local-mode)

首次下载依赖和权重需要网络；文本编码在本地。只有后面的 `--ask-model` 才把选中的原文发给生成服务。

## 5. 先建库，再查询

在项目根目录运行：

```bash
uv sync --locked --group rag
uv run --group rag python -m day06.build_index
uv run --group rag python -m day06.vector_retriever "无线网络怎么连接？"
```

建库时检查：四块资料、每块 512 维、保存四条记录。查询时检查：问题也是 512 维、结果是否包含 `services.md#2`、最终 input 中是否有“连接方式请咨询前台”。

程序会打印实际小数与耗时，重点先看来源与内容。默认最多取两块，第二块可能无关。
这道中文问题也可能被关键词检索找到，因为“网络、连接”等字有重合；单个成功例不能证明向量一定更好。

如果没有 `index.json`，查询会提示先建库；如果原文或记录的编码配置变化，会提示重建。
重复运行 build_index 会替换本课 collection，重新生成索引说明。

## 6. 索引到底存了什么？

| 名称 | 对应内容 |
|---|---|
| collection | 装这批记录的容器，本课名为 `day06_study_room` |
| point | 一条记录，包含 ID、向量和附带资料 |
| payload | 附带的原文、来源和块编号 |
| index.json | 模型名、维度、切块规则、资料摘要等建库信息 |

`index.json` 中的摘要由程序对当前资料计算，用于发现变化，不需要你手写。
数据库点 ID 使用 UUID，payload 中仍保留可读的 `hours.md#1` 供引用。

建库代码的关键关系：

```python
# build_index.py 源码节选。
chunks = split_documents(load_documents(KNOWLEDGE_DIR))
model = load_embedder()
vectors = embed_texts(model, [chunk.text for chunk in chunks])
```

`chunks[0].text` 对应 `vectors[0]`，四段原文得到四个向量。
`write_collection()` 把对应关系一起保存；只有向量、没有原文，就无法给后续回答提供资料。

## 7. 提问时又做了什么？

`embed_query()` 为新问题算向量，`search_vectors()` 用它查询已建好的库，返回原文和分数。
文档和问题要使用兼容的编码方式。本课用同一 BGE 模型，按模型建议只给短问题加检索前缀，原文直接编码。

`limit=top_k` 限制结果数量，`with_payload=True` 要求带回原文与来源。
结果仍转成 Day 05 的 `SearchResult`，所以组装 Prompt 的函数不用重写。

## 8. 用两次对照理解局限

```bash
uv run --group rag python -m day06.vector_retriever "wifi 免费吗？" --top-k 1
uv run --group rag python -m day06.vector_retriever "WLAN 怎么用？" --top-k 1
```

每次都会打印关键词结果作对照。记录两种方法找到什么、第一块是否能回答；这个中文编码器对英文缩写也可能表现不好，以实际结果为准。

即使知识库没有答案，向量搜索也可能返回相对最近的一块。可尝试 `--min-score 0.9` 观察阈值过滤，但 0.9 只是实验参数，不能当作通用标准。

需要生成回答时再运行：

```bash
uv run --group rag python -m day06.vector_retriever "无线网络怎么连接？" --top-k 1 --ask-model
```

应依据原文说明“咨询前台”，不能编造 wifi 密码。成功检索与正确生成仍需分别检查。

## 9. 真实项目里一般怎么做？

常见做法是资料变更时更新索引，用户提问时只编码新问题并查询，而不是每次把所有资料重新编码。
原文、来源、版本和访问范围一起保存，避免查到过期或无权使用的内容。

换 Embedding 模型后通常要重新编码相关资料，不能只因维度相同就混用旧向量。
本课全量重建和本地模式便于观察；更大数据再考虑增量更新、服务部署和索引版本。

## 10. 卡点、练习与完成标准

| 现象 | 先检查 |
|---|---|
| 找不到 day06 模块 | 是否从项目根目录运行 |
| 缺 fastembed 或 qdrant_client | 命令是否带 `--group rag` |
| 权重下载失败 | 网络与缓存；不要改成随机向量假装成功 |
| 提示索引过期 | 重新运行 build_index |
| 本地库被占用 | 是否还有另一个进程打开同一库 |

自测：关闭查询进程后，哪些数据还在？模型权重、库文件、index.json 还在；本次问题向量等内存变量结束。
能指出“原文 → 向量 → 库记录 → 原文”每一步的函数，就完成今天。

[上一课：Day 05](../day05/DAY05.md) · [下一课：Day 07](../day07/DAY07.md)
