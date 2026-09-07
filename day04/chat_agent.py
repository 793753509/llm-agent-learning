"""Day 04：多轮聊天。运行：uv run python -m day04.chat_agent

先读 ChatSession → chat() → chat_loop()。
Day 03 每次提问都新建历史；这里把完整对话轮次保存在 session 中。
配置、真实客户端和两个工具直接复用 Day 03，不再复制或增加抽象层。
"""

import json
from dataclasses import dataclass, field
from typing import Any

import openai
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

from day03.agent_core.client import OpenAIModelClient
from day03.agent_core.config import BASE_URL, MAX_STEPS, MODEL, load_api_key
from day03.agent_core.models import TokenUsage
from day03.agent_core.ports import ModelClient
from day03.agent_core.tools import TOOLS, execute_tool

MAX_TURNS = 5  # 保留最近 5 个完整用户轮次；这是轮数上限，不是精确 Token 上限。


@dataclass
class ChatSession:
    # 每个 turn = 用户消息 + 模型完整输出 + 工具结果 + 最终回答。
    turns: list[list[Any]] = field(default_factory=list)
    usage: TokenUsage = field(default_factory=TokenUsage)

    def reset(self) -> None:
        self.turns.clear()
        self.usage = TokenUsage()


class StudyTask(BaseModel):
    title: str
    objective: str
    minutes: int = Field(ge=5, le=240)


class StudyPlan(BaseModel):
    topic: str
    tasks: list[StudyTask] = Field(min_length=1)


def chat(
    question: str,
    session: ChatSession,
    client: ModelClient,
    max_steps: int = MAX_STEPS,
) -> str:
    """处理一次用户提问：内层仍是 Day 03 的模型 → 工具 → 模型循环。"""
    if not question.strip():
        raise ValueError("问题不能为空")

    history: list[Any] = []
    for previous_turn in session.turns:
        history.extend(previous_turn)

    turn: list[Any] = [{"role": "user", "content": question.strip()}]
    turn_usage = TokenUsage()

    for step in range(1, max_steps + 1):
        # 记忆的关键：旧历史 + 本次新增内容，一起发给模型。
        reply = client.create_response(input_items=history + turn, tools=TOOLS)
        turn.extend(reply.output_items)  # 包括 reasoning、工具请求、最终文本项。

        turn_usage.input_tokens += reply.usage.input_tokens
        turn_usage.output_tokens += reply.usage.output_tokens
        session.usage.input_tokens += reply.usage.input_tokens
        session.usage.output_tokens += reply.usage.output_tokens
        print(
            f"[请求 {step}] input={reply.usage.input_tokens}, "
            f"output={reply.usage.output_tokens}"
        )

        if not reply.tool_calls:
            if not reply.text:
                raise RuntimeError("模型没有返回文本或工具调用")
            # 只有完整结束的 turn 才保存；请求失败不会留下半截工具调用。
            session.turns.append(turn)
            if len(session.turns) > MAX_TURNS:
                session.turns.pop(0)  # 整轮删除，不会拆散工具请求与结果。
                print(f"[上下文] 已删除最早一轮，只保留最近 {MAX_TURNS} 轮")
            print(f"[本轮 Token] {turn_usage.total_tokens}")
            return reply.text

        for tool_call in reply.tool_calls:
            result = execute_tool(tool_call)
            print(f"[工具] {tool_call.name}({tool_call.arguments}) → {result}")
            turn.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": json.dumps(result, ensure_ascii=False),
                }
            )

    raise RuntimeError(f"超过最大执行步数：{max_steps}")


def chat_loop(client: ModelClient) -> None:
    """外层循环：持续读取问题；session 在循环外创建，所以能保留历史。"""
    session = ChatSession()
    print(f"模型：{MODEL}；命令：/history /usage /reset /quit /plan 主题")

    while True:
        question = input("\n你：").strip()
        if not question:
            print("问题不能为空")
            continue
        if question == "/quit":
            return
        if question == "/reset":
            session.reset()
            print("已清空本地历史和 Token 计数（不会退回已经消耗的额度）")
            continue
        if question == "/history":
            if not session.turns:
                print("历史为空")
            for index, turn in enumerate(session.turns, start=1):
                print(f"--- 保留的第 {index} 轮 ---")
                for item in turn:
                    print(item)
            continue
        if question == "/usage":
            print(
                f"[会话 Token] input={session.usage.input_tokens}, "
                f"output={session.usage.output_tokens}, total={session.usage.total_tokens}"
            )
            continue
        if question == "/plan":
            print("用法：/plan Python 基础")
            continue

        is_plan = question.startswith("/plan ")
        if question.startswith("/") and not is_plan:
            print("未知命令，可用：/history /usage /reset /quit /plan 主题")
            continue
        if is_plan:
            topic = question[len("/plan ") :].strip()
            question = (
                f"请为主题“{topic}”生成学习计划，只输出 JSON，不要 Markdown。"
                '格式：{"topic":"主题","tasks":[{"title":"任务名",'
                '"objective":"学习目标","minutes":30}]}。'
                "至少一项任务，minutes 必须是 5 到 240 的整数。"
            )

        try:
            answer = chat(question, session, client)
            if is_plan:
                # 普通文本 → JSON 字典 → Pydantic 校验；不是服务端严格输出模式。
                plan = StudyPlan.model_validate(json.loads(answer))
                print(json.dumps(plan.model_dump(), ensure_ascii=False, indent=2))
            else:
                print(f"助手：{answer}")
        except ValidationError as exc:
            print(f"学习计划未通过校验：{exc}")
        except openai.APIError as exc:
            print(f"模型请求失败：{type(exc).__name__}，请检查网络、Key 或额度")
        except (RuntimeError, ValueError) as exc:
            print(f"本次失败：{exc}")


def main() -> None:
    try:
        with OpenAI(
            api_key=load_api_key(),
            base_url=BASE_URL,
            timeout=30.0,
            max_retries=2,
        ) as sdk_client:
            chat_loop(OpenAIModelClient(sdk_client))
    except (EOFError, KeyboardInterrupt):
        print("\n已退出")
    except (RuntimeError, OSError, openai.APIError) as exc:
        print(f"启动失败：{type(exc).__name__}，请检查 Key 文件和配置")


if __name__ == "__main__":
    main()
