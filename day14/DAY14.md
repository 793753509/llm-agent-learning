# Day 14：答案是 75，也可能没完成任务

> 今天给 Day 10 的工作流批作业：既看答案，也看有没有按要求调用工具。
> 先使用固定行为的程序，学会写判分规则，再把同样方法用于真实模型。

## 开始前：输入、程序和产物

| 内容 | 来源与用途 |
|---|---|
| [datasets/agent_cases.json](datasets/agent_cases.json) | 人工编写的四个测试用例，含输入、预期答案和 purpose 说明 |
| [eval_agent.py](eval_agent.py) | 读取用例，执行 Day 10 的 run()，对照规则评分 |
| `reports/baseline.json`、`reports/fault.json` | 程序生成的正常/故障报告，包含实际答案、轨迹和检查结果 |

## 1. 为什么不能只检查最终一句话？

你要求：“请用乘法工具计算 25 × 3。”

| 运行 | 最终答案 | 中间过程 | 今天是否合格 |
|---|---|---|---|
| A | 75 | 调用 multiply(a=25,b=3)，得到 75 | 合格 |
| B | 75 | 没有工具记录 | 不合格：未证明完成工具要求 |
| C | 75 | 调错参数，又碰巧给出 75 | 不合格：过程不对 |

对于只要求答案的任务，当然不必强制调用工具。
**评估规则由任务要求决定**，不能为了得分强行让所有问题都调用工具。

## 2. 跑两次，看一次通过、一次失败

```bash
uv run --group workflow python -m day14.eval_agent
uv run --group workflow python -m day14.eval_agent --fault
```

正常运行应有 4/4 通过。
加 `--fault` 后，程序故意删除工具事件，保留正确答案，应有 0/4 通过并以状态码 1 退出。
这是故障实验的预期结果，不是让你修复正常工作流。

`baseline` 表示正常基线，`fault` 表示故意注入故障。两份报告都由程序实际计算，重复运行会更新同名文件。报告位置：

```text
day14/reports/baseline.json  正常轨迹
day14/reports/fault.json     故意损坏的轨迹
```

报告的 `dataset` 标明题目文件，`workflow` 标明被测函数，`generated_at` 标明生成时间。
`scope` 写着 `scripted LangGraph workflow; no model calls`。
4/4 只说明这四个固定流程案例符合规则，不说明大模型的任务成功率是 100%。

## 3. 先读一道题

```json
{"id":"A1","a":25,"b":3,"expected":"75"}
```

这条记录来自 `datasets/agent_cases.json`，可类比单元测试用例。`purpose` 解释用例目的，不参与判分。

`a`、`b` 是输入；`expected` 是人工提供的标准答案，故意保存为字符串，因为 answer 是文字。
今天其他题覆盖 0、负数、换一组参数，不只反复测 25 × 3。

不要在判分时写 `expected = result['answer']`，那就变成学生自己给自己写标准答案。

## 4. 一条轨迹长什么样？

`events` 是执行记录，来自 Day 10：

```json
[
  {"node":"decide","action":"tool"},
  {"node":"tool","name":"multiply","args":{"a":25,"b":3},"result":75},
  {"node":"decide","action":"answer"}
]
```

逐项翻译：决定算一次 → 用这两个参数相乘 → 根据结果回答。
如果轨迹只能由模型自己写一段“我调用过工具”，可信度不够。
本例的工具事件由执行工具的 Python 函数记录。

## 5. grade 就是一个小阅卷函数

```python
tools = [event for event in events if event.get("node") == "tool"]
```

这行列表推导式相当于：逐个查看事件，只留下工具事件。
随后分五项检查：

| 检查名 | 通过条件 | 失败时优先看 |
|---|---|---|
| answer | 等于标准答案 | 最终输出 |
| tool_name | 恰好一次 multiply | 工具选择/次数 |
| tool_args | a、b 与题目相同 | 参数解析 |
| path | decide → tool → decide | 分支与循环 |
| budget | 工具≤1 次、事件≤3 条 | 重复执行 |

```python
passed = all(checks.values())
```

`all` 表示每项都为 True 才通过。
如果只输出一个总分，失败时还得重新猜原因；保留每项结果能直接定位。

## 6. 为什么答案对，fault 仍要失败？

打开 fault.json 的 A1，顶层 `answer` 保存实际答案“75”，`events` 是故意删掉工具记录后的轨迹。`checks` 内应看到：

```text
answer: true
tool_name: false
tool_args: false
path: false
budget: true
```

这道题顶层的 `passed` 为 false，因为并非所有 checks 都通过。

预算上限不代表任务完成：什么也不做也没有超预算。
这就是不能只挑一项容易通过的指标的原因。

## 7. 回归评估什么时候运行？

你把工具参数名 a 改成 left，或调整模型 Prompt 后，都可能使旧任务失效。
修改前跑一次 baseline；修改后对相同输入再跑一次，比较具体检查项。

固定测试集适合检查“原来会的事情有没有被改坏”。
如果反复针对这四题调代码，不能据此判断它会处理没见过的问题。
要另留新题，包含歧义输入、工具异常、用户改意图和资料不足等情况。

## 8. 接真实模型后怎样评？

不用第一天就安装复杂评估平台。沿着现有入口替换 `run()` 即可：

```text
固定题目 → 真实 Agent → 执行层记录的工具事件 + 最终回答 → grade
```

注意三点：

1. 真实模型可能选择不同但有效的步骤；别强制所有任务都走完全相同的路径。
2. 自由文字不能总用字符串完全相等；可先检查必要事实、引用，再人工核对语义。
3. 同题可能波动；记录模型/配置、运行次数、每次结果，而不是只展示最好的一次。

让另一个模型评分叫 model-as-judge。它也会错，需要人审样本、清晰规则和校准。
今天没有运行真实模型评估或 judge，报告里也没有替它们填分数。

## 9. 三个练习

1. 把 A1 的 expected 临时改为 "76"，哪些检查应该失败？
2. 在 A1 的轨迹里复制一次工具事件，哪些检查会受到影响？
3. “只查我的 T001”这个任务，至少要检查哪两项安全行为？

<details>
<summary>参考答案</summary>

1. answer 失败，其他过程检查仍可能通过；最后恢复标准答案。
2. 工具次数、参数的恰好一次条件、路径、预算都会失败。
3. 是否只访问获准的资源，越权时是否返回拒绝且没有泄露他人工单内容。

</details>

核心完成标准：亲眼见到“答案正确而任务失败”，能从 checks 指出原因。
代码顺序：命令行入口 → evaluate → grade。先掌握这三个函数，再扩展数据集。

[上一课：Day 13](../day13/DAY13.md) · [下一课：Day 15](../day15/DAY15.md)
