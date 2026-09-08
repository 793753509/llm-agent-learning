"""人工预设工具请求的测试替身；不是语言模型，不理解任意自然语言。"""

from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class DemoChatModel(BaseChatModel):
    """先提出指定工具调用，收到真实工具结果后用固定模板展示它。"""

    tool_name: str
    tool_args: dict[str, Any]

    @property
    def _llm_type(self) -> str:
        return "course-scripted-demo"

    def bind_tools(self, tools: Any, **kwargs: Any) -> "DemoChatModel":
        # create_agent 会提供工具说明；本替身的调用名称和参数已由人指定。
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        last = messages[-1]
        if isinstance(last, HumanMessage):
            reply = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": self.tool_name,
                        "args": self.tool_args,
                        "id": "demo-call-1",
                        "type": "tool_call",
                    }
                ],
            )
        elif isinstance(last, ToolMessage):
            reply = AIMessage(content=f"预设回复实验结束，实际工具返回：{last.content}")
        else:
            raise RuntimeError("预设实验只支持用户输入 → 一次工具调用 → 展示结果")
        return ChatResult(generations=[ChatGeneration(message=reply)])
