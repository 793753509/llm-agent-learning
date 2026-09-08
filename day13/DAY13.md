# Day 13：让助手记住“我喜欢简短回答”，也能忘掉它

> 今天只存两种明确偏好。先用 SQLite 跑通保存、跨进程读取、更新和删除。
> 不自动从聊天中猜测隐私，也不需要向量库或生成模型。

## 开始前：输入、程序和产物

| 内容 | 来源与用途 |
|---|---|
| [memory.py](memory.py) | 已提供的保存、查询和删除程序 |
| user、key、value | 你明确输入的用户标签、偏好名和取值 |
| `data/memory.sqlite` | 首次运行自动建库，之后读取或更新；不是模型自身的记忆 |

## 1. 这次真的需要“长期记忆”吗？

你今天说：“以后回答尽量简短。”明天开一个新会话，仍希望这个偏好生效。
把它放在一轮聊天的列表里不够，因为换会话就没有了。

我们显式保存一条记录：

```text
用户 alice 的 style 偏好 = 简短
来源 = 用户明确输入
有效期 = 从保存起 86400 秒
```

“长期”表示可以跨会话、跨进程保存，不代表永不过期。

## 2. 先区分三种容易混淆的东西

| 要保存什么 | 例子 | 在本项目哪里学 |
|---|---|---|
| 会话历史 | “刚才说的那家店”指北店 | Day 04，多轮消息 |
| 流程快照 | 工单草稿等批准，还没写入 | Day 11，checkpoint |
| 长期偏好 | alice 喜欢简短回答 | 今天，memory 表 |

它们都可能存数据库，但用途不同。
RAG 的营业时间资料又是另一类：公共业务知识，不是“alice 的个人偏好”。

## 3. 亲手存下第一条记忆

```bash
uv run python -m day13.memory remember --user alice --key style --value 简短
uv run python -m day13.memory list --user alice
uv run python -m day13.memory list --user bob
```

前两次应显示 style=简短；bob 的列表应为空（假设你还没给 bob 存过）。
每条命令是独立进程。仍能读到，说明不是仅保存在 Python 变量中。

文件在 `day13/data/memory.sqlite`，是你的本地文件，不在模型服务商服务器。
本课的 `--user` 是实验分区标签，允许你扮演不同用户观察数据；它不是认证方式。

## 4. 一条记录的字段逐个解释

| 字段 | 示例 | 为什么要有 |
|---|---|---|
| user_id | alice | 区分记录属于谁 |
| key | style | 偏好的名称 |
| value | 简短 | 偏好的取值 |
| source | explicit_user_input | 知道它来自明确指令 |
| updated_at | 保存时间 | 知道何时更新 |
| expires_at | 过期时间 | 太旧的偏好可以停止使用 |
| version | 1 | 更新后便于辨认版本 |

时间在 JSON 中用 Unix 秒数表示，是一个时间点，不是剩余秒数。
`expires_at = updated_at + ttl`；ttl 的单位在本课是秒。

## 5. 用户改主意了怎么办？

```bash
uv run python -m day13.memory remember --user alice --key style --value 详细
```

结果应只剩当前 style=详细，version 增加 1。
不会把“简短”和“详细”两条互相冲突的偏好一起送给模型。

数据库的规则是：

```sql
PRIMARY KEY(user_id, key)
```

把 `(alice, style)` 看成一个抽屉标签。更新相同标签，就是换掉抽屉里的当前值。
本例保留版本号但不保留完整历史；不是审计系统。

## 6. 为什么先限制只存两种偏好？

```python
ALLOWED = {
    "style": {"简短", "详细"},
    "language": {"中文", "英文"},
}
```

`key not in ALLOWED` 会拒绝未知种类；value 也必须在对应选项里。
这样初学者可以看清数据结构，不必同时处理“从任意文本推断记忆”的复杂问题。

试试不支持的值：

```bash
uv run python -m day13.memory remember --key password --value abc
```

应报错，不写入。不要用真实密码做实验。
这说明允许列表在代码中生效，不是期望模型自行遵守。

## 7. 删除与过期是两回事

显式忘记：

```bash
uv run python -m day13.memory forget --user alice --key style
uv run python -m day13.memory list --user alice
```

style 从表里删除；若还保存了 language，它会继续存在。

过期实验：

```bash
uv run python -m day13.memory remember --user alice --key style --value 简短 --ttl 1
```

手动等两秒，再 list。style 不应出现在读取结果里。
过期行仍可能在表中，只是查询过滤掉了；需要物理清理时另做删除任务。
删除数据库当前行也不等于清除了所有备份，本例没有实现备份管理。

## 8. 程序是怎样读取的？

打开 memory.py，先读 `recall()` 的查询：

```sql
WHERE user_id=? AND expires_at>?
```

意思是“只取这个用户、尚未过期的记录”。
`?` 是参数占位符，值单独传入，不用字符串拼接 SQL。

核心调用方式是：

```python
store = MemoryStore()
preferences = store.recall("alice")
```

这一步只是从本地读数据，模型还看不到。
如果想影响回答，应用必须选择相关偏好，放入本次模型输入；或者像 Day 20 那样用偏好控制显示条数。
**写进数据库不会自动改变模型本身，也不是给模型重新训练。**

## 9. 练习：拿纸画三个抽屉

依次写入：

```text
alice / style / 简短
bob / style / 详细
alice / language / 中文
alice / style / 详细
```

1. 最后有几条当前记录？
2. alice 的 style 第几版？假设实验开始是空库。
3. 删除 alice 的 style 会影响 bob 吗？

<details>
<summary>参考答案</summary>

1. 三条，因为最后一次更新同一 user_id/key。
2. 第 2 版。
3. 不会。删除 SQL 同时匹配 user_id 和 key。

</details>

可以加 `--db /tmp/qinghe-memory-practice.sqlite` 使用新的实验库。

## 真实场景里怎么用

例如客服助手，可保存用户明确选择的回复语言，在新会话中读出并放入请求。常见起点是只保存少量有明确用途的偏好，同时提供更新、过期和删除；并不需要一开始就自动总结所有聊天。

## 10. 今天的终点

能保存、另启进程读取、覆盖、按用户区分、过期和删除，就够了。
代码阅读顺序：命令行入口 → remember → recall → forget → 建表部分。

进阶再考虑：哪些聊天事实适合保存、记忆冲突如何问用户、多人身份校验、备份删除、长文本检索。
本课不把“存所有聊天”当成记忆方案，也不要求初学者先部署向量数据库。

[上一课：Day 12](../day12/DAY12.md) · [下一课：Day 14](../day14/DAY14.md)
