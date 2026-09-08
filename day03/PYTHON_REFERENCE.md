# Python 速查：读到哪种写法，再查哪一项

这是 [Day 03](DAY03.md) 的选读页。例子只解释语法，输出为人工设计的预期值；以下代码块均可独立在 Python 中运行，不调用模型。

## 1. list、dict、set

```python
messages = ["用户问题", "助手回答"]  # 有顺序，可重复。
call = {"name": "multiply", "a": 6, "b": 7}  # 按键取值。
words = {"周", "末", "周"}  # 集合去重，不按位置取值。
print(messages[0])   # 用户问题
print(call["a"])     # 6
print(len(words))    # 2
```

`list[dict]` 是“每项为字典的列表”的类型标注；不会自动把错误输入变成字典。
`None` 表示当前没有值，与数字 0、空字符串和空列表都不同。

## 2. 引用和复制

```python
a = [1]
b = a
b.append(2)
print(a)  # [1, 2]：a、b 指向同一列表。
c = a.copy()
c.append(3)
print(a)  # [1, 2]：外层列表已分开。
```

`copy()` 是浅复制，内部若还有列表或字典，仍可能共享。测试 Fake 复制输入列表，是为了后续 append 不改变之前记录的列表长度。

## 3. append、extend、切片

```python
turns = []
turns.append(["问", "答"])
print(turns)  # [["问", "答"]]
history = []
history.extend(turns[0])
print(history)  # ["问", "答"]
print(history[:1])  # ["问"]：最多取前一项。
```

`append()` 和 `extend()` 修改原列表，返回值是 None，不要把它们的返回值当成新列表。
`left + right` 创建拼接后的新列表；`+=` 对列表则会把右侧各项追加进左侧。

## 4. 函数、命名参数和 ** 解包

```python
def multiply(a: int, b: int) -> int:
    return a * b

arguments = {"a": 6, "b": 7}
print(multiply(**arguments))  # 42，等价于 multiply(a=6, b=7)。
handler = multiply           # 保存函数，尚未执行。
print(handler(2, 3))         # 6，括号才是调用。
```

`def run(*, client)` 中的 `*` 要求后面的参数按名称传，例如 `run(client=fake)`。
默认列表要避免写成 `def f(items=[])`，否则多次调用会共用同一列表；改用 None，在函数内新建。

## 5. JSON 字符串与字典

```python
import json
text = '{"a": 6, "b": 7}'
arguments = json.loads(text)
print(arguments["a"])  # 6
output = json.dumps({"result": 42}, ensure_ascii=False)
print(type(output).__name__)  # str
```

`loads` 读入字符串，`dumps` 输出字符串。它们只处理 JSON 结构，不判断参数是否获准执行。
JSONL 则是一行一个完整 JSON 对象，常用于日志；Day 15 会实际写文件。

## 6. 列表推导式与集合交集

```python
rows = [{"id": "A", "score": 1}, {"id": "B", "score": 0}]
selected = [row["id"] for row in rows if row["score"] > 0]
print(selected)  # ['A']
found = set(selected) & {"A", "C"}
print(len(found))  # 1：既返回了、又属于标准证据的编号。
```

把列表推导式读成“逐个取 row，满足条件就把这一项放进新列表”。
`&` 求两个集合的交集，Day 05 用它数共同词，Day 08 用它数命中的正确块。

## 7. class 与 dataclass

```python
from dataclasses import dataclass, field

@dataclass
class Session:
    turns: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.turns)

session = Session()
session.turns.append("第一轮")
print(session.count)  # 1：property 按属性读取，不加括号。
```

`self` 是当前对象。`dataclass` 自动补构造等常用代码；`default_factory=list` 为每个对象创建自己的列表。
普通 class 则常用 `__init__()` 保存传入对象，例如客户端保存 SDK client。

## 8. Protocol 与类型标注

```python
from typing import Protocol

class Client(Protocol):
    def answer(self, question: str) -> str: ...

class Fake:
    def answer(self, question: str) -> str:
        return "预设回复"

def ask(client: Client) -> str:
    return client.answer("你好")

print(ask(Fake()))  # 预设回复
```

Protocol 约定方法形状，方便替换对象和类型检查；不是网络协议，也不是运行时权限检查。
`Any` 表示允许任意类型，使用时仍需知道实际对象是什么。Python 类型标注通常不替代运行时校验。

## 9. 模块、路径与入口

```python
from pathlib import Path

path = Path("day08/datasets/rag_cases.json")
print(path.name)  # rag_cases.json
print(path.parent)  # day08/datasets
```

相对路径相对当前工作目录。源码中 `Path(__file__).resolve()` 则从当前文件确定位置，便于跨目录读取资料。
`from day03.agent_core.models import ToolCall` 表示从指定模块导入名称。
模块顶层代码在首次导入时执行；放在 `if __name__ == "__main__":` 下的调用，只在该模块作为程序入口运行时执行。

## 10. 异常与 with

```python
try:
    value = int("不是数字")
except ValueError:
    print("需要输入整数")
```

`raise` 抛出失败，`except` 处理指定失败；不要把所有异常都转成“成功”。
`with` 常用于保证文件或连接在离开代码块时被清理。数据库提交、回滚和关闭是否自动发生，要看对应对象的约定。

## 11. async / await：后面读 MCP 时再看

```python
import asyncio

async def fetch() -> str:
    await asyncio.sleep(0)
    return "模拟结果"

print(asyncio.run(fetch()))
```

`async def` 定义异步函数，`await` 等待一个异步操作完成，`asyncio.run()` 运行最外层入口。
仅仅写 async 不会让各步骤自动并发；Day 12 的连接、初始化、调用存在依赖，仍按顺序执行。

[回到 Day 03](DAY03.md)
