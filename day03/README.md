# Day 03 导航

今天把 Day 02 的单文件助手拆成可测试模块。请先读 [主课程](DAY03.md)，遇到 Python 写法再查 [语法速查](PYTHON_REFERENCE.md)。

| 入口 | 用途 | 数据来源 |
|---|---|---|
| [mini_agent.py](mini_agent.py) | 运行真实助手 | 用户问题与模型服务回复 |
| [tests/test_runner.py](tests/test_runner.py) | 离线检查循环 | 人工编写的 Fake 回复与预期结果 |
| [agent_core/](agent_core/) | 客户端、循环、工具和数据类 | 从 Day 02 拆出的实现 |
| [playground.py](playground.py) | 个人练习 | 你自己填写的代码 |

从项目根目录运行：

```bash
uv run pytest -q -s day03/tests/test_runner.py::test_tool_call_then_answer
uv run python -m day03.mini_agent "精确计算 6 乘以 7"
```

第一条不联网；第二条沿用 Day 01/02 的配置并请求真实模型。测试通过说明程序处理预设回复符合要求，不代表真实模型必然作出相同决定。

[返回总路线](../README.md)
