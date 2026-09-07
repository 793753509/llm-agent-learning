"""Day 03 的内部数据模型；导入本模块不会读取密钥或调用模型 API。"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    """一次工具调用请求；arguments 是已经解析好的 Python 字典。"""

    call_id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class TokenUsage:
    """记录输入和输出 Token 数量。"""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """使用 usage.total_tokens 读取，每次都根据当前数值计算。"""
        return self.input_tokens + self.output_tokens


@dataclass
class ModelReply:
    """模型一轮回复；usage 也是每次创建一个新对象，不与其他回复共享。"""

    text: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: TokenUsage = field(default_factory=TokenUsage)
    # 保留 response.output 的完整内容，供下一轮原样回传（包含 reasoning 等项）。
    output_items: list[Any] = field(default_factory=list)


@dataclass
class AgentResult:
    """最终答案、累计 Token 和尝试调用的工具名称（含失败，不去重）。"""

    answer: str
    usage: TokenUsage
    # 与 tool_calls 一样，不让不同实例共享默认列表。
    used_tools: list[str] = field(default_factory=list)
