"""预设排查替身：工具顺序由人编写，第二次参数从真实工具结果中读取。"""

import json
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class DiagnosticDemoModel(BaseChatModel):
    booking_id: str = "B001"

    @property
    def _llm_type(self) -> str:
        return "scripted-booking-diagnosis"

    def bind_tools(self, tools: Any, **kwargs: Any) -> "DiagnosticDemoModel":
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
            reply = self.call("get_booking", {"booking_id": self.booking_id}, "booking")
        elif isinstance(last, ToolMessage):
            data = json.loads(last.content)
            if not data.get("ok"):
                reply = AIMessage(content="预设排查：未取得所需记录或手册，信息不足。")
            elif last.name == "get_booking":
                reply = self.call(
                    "lookup_manual", {"error_code": data["error_code"]}, "manual"
                )
            else:
                reply = AIMessage(
                    content=f"预设排查：{data['text']} 来源：{data['source']}"
                )
        else:
            raise RuntimeError("预设替身只支持本课的预约排查流程")
        return ChatResult(generations=[ChatGeneration(message=reply)])

    @staticmethod
    def call(name: str, args: dict, call_id: str) -> AIMessage:
        return AIMessage(
            content="",
            tool_calls=[
                {"name": name, "args": args, "id": call_id, "type": "tool_call"}
            ],
        )
