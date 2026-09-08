"""复用 Day 18 的接口，回答函数换成项目引擎。"""

from day18.api import create_app

from .core import Engine

engine = Engine()  # 默认关键词、无模型调用；只启动一个本地 worker。
app = create_app(engine.answer)
