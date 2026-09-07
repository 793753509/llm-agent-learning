"""Day 04 填空练习：多轮对话 + 一个计算器，不看答案走通流程。

在 llm-agent-learning 目录运行：uv run python -m day04.agent_practice
配置沿用 Day 03；不需要安装新依赖，也不要把密钥写进这个文件。

按 TODO 1～7 填写，用你的代码替换对应的 NotImplementedError。
现在只是骨架，遇到“尚未完成”提示是正常的；填写后运行会消耗模型额度。
只练核心流程：不做异步、历史裁剪、文件存储、复杂异常处理。

手工验收（在同一次运行中依次输入）：
1. 我叫小明                  -> 模型正常回答，不必调用工具。
2. 我叫什么名字？            -> 应能根据历史回答“小明”。
3. 精确计算 25 乘 3          -> 调用 calculator，结果是 75。
4. 把结果再乘 5             -> 参数应为 a=75、b=5，结果是 375。
5. /history                 -> 四个完整轮次；计算轮包含工具请求和工具结果。
6. /reset，然后 /history    -> 历史变成 []。
7. 我叫什么名字？            -> 没有旧历史，不应知道你之前告诉它的名字。
8. /quit                    -> 退出。

自问：为什么 session 在 while 外创建？为什么 turn 每次重新创建？
为什么一轮用户对话可能需要请求模型两次？为什么结果要带 call_id？
"""

import json
import operator
from dataclasses import dataclass, field
from typing import Any, Callable

from openai import OpenAI

from day03.agent_core import tools
from day03.agent_core.config import BASE_URL, MODEL, load_api_key

INSTRUCTIONS = (
    "你是一个简洁的中文助手，根据提供的对话历史回答。"
    "需要计算加法或乘法时，必须调用 calculator，不要自行心算。"
    "收到工具结果后，用一句话回答用户。"
)

# 工具说明已经写好，不用填。它只告诉模型如何请求工具，不会执行计算。
TOOLS = [
    {
        "type": "function",
        "name": "calculator",
        "description": "执行两个数字的加法或乘法。",
        "parameters": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "multiply"],
                },
                "a": {"type": "number"},
                "b": {"type": "number"},
            },
            "required": ["operation", "a", "b"],
            "additionalProperties": False,
        },
        "strict": True,
    }
]


@dataclass
class ChatSession:
    # 外层每项是一轮；内层每项是一个消息、模型输出或工具结果字典。
    # 每轮包含：用户问题 + 所有模型输出 + 工具结果，直到最终回答。
    turns: list[list[dict[str, Any]]] = field(default_factory=list)


operations: dict[str, Callable[[float, float], float]] = {
        "add": operator.add,
    "multiply": operator.mul,
}

def calculator(operation: str, a: float, b: float) -> any:
    """TODO 1：add 返回 a+b；multiply 返回 a*b。普通 if 即可。"""
    if operation not in operations:
        return 0

    return operations[operation](a, b)


# 重要概念
# 1、turn：每一次请求大模型都有一个turn，每次响应也有一个turn，不管是大模型响应还是工具响应
# 2、 history：初始化turn，用于读取session中的turn
# 3、chat函数只会在没有任何工具调用要执行时才会退出，退出之前更新一下session就行了

def chat(question: str, session: ChatSession, client: OpenAI) -> str:
    """完成一次用户提问，返回最终回答；中间可以请求模型多次。"""
    # TODO 2：准备两个局部列表。
    # history：用循环和 extend，把 session.turns 展开成一维旧历史。
    # turn：新建列表，最初只有本次用户消息（role=user，content=question）。
    # 旧历史不要复制进 turn；此时也不要把 turn 加进 session.turns。

    # 1. 展开已经完成的历史轮次
    history: list[dict[str, Any]] = []
    for previous_turn in session.turns:
        history.extend(previous_turn)

    # 2. 创建当前轮次，最初只有用户问题
    turn: list[dict[str, Any]] = [
        {"role": "user", "content": question}
    ]

    for _ in range(5):  # 最多请求模型 5 次，避免写错后一直调用。
        # TODO 3：使用 client.responses.create(...) 请求模型。
        # 参数：model=MODEL、instructions=INSTRUCTIONS、tools=TOOLS。
        # input 应该是哪个旧列表与哪个新列表相加？结果用 response 接收。

        response = client.responses.create(
            model=MODEL,
            instructions=INSTRUCTIONS,
            input=history + turn,
            tools=TOOLS,
        )

        # TODO 4：记录模型的完整输出，并找出工具调用。
        # 遍历 response.output，用 item.to_dict(mode="json") 转成字典，
        # 逐个加入 turn；reasoning、function_call、message 都保留。
        # 另外从 response.output 筛选 item.type == "function_call" 的项。
        # 可把筛选出的 SDK 对象存进 tool_calls，方便用 .name 等属性读取。

        tool_calls = []
        for item in response.output:
            turn.append(item.to_dict(mode="json"))
            if item.type == "function_call":
                tool_calls.append(item)

        # TODO 5：如果没有工具调用，说明这次可以给出最终回答。
        # 将整个 turn 作为一项 append 到 session.turns。
        # 返回 response.output_text；最终回答已在 TODO 4 中加入 turn，勿重复。

        if not tool_calls:
            session.turns.append(turn)
            return response.output_text

        # TODO 6：否则，逐个执行工具，并把结果写回 turn。
        # 读取 tool_call.name，用 json.loads(tool_call.arguments) 解析参数。
        # 调用上面的 calculator()，可以 print 参数和结果，观察调用过程。
        # 创建工具结果字典：type 是 function_call_output，
        # call_id 使用本次 tool_call.call_id，output 使用 json.dumps(result)。
        # 把字典 append 到 turn，然后让 for 循环继续请求模型。
        # 注意：不要在这里保存 session.turns，也不要在这里 return。

        for tool_call in tool_calls:
            if tool_call.name != "calculator":
                raise ValueError(f"未知工具：{tool_call.name}")

            params = json.loads(tool_call.arguments)
            result = calculator(params["operation"], params["a"], params["b"])

            print(f"[工具] calculator({params}) → {result}")

            turn.append(
                {
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": json.dumps(result),
                }
            )




    raise RuntimeError("已请求模型 5 次，仍未得到最终回答，请检查循环逻辑")


def main() -> None:
    # 环境配置已接好。只复用配置，不复用已有 Agent，以便亲手实现整个流程。
    with OpenAI(
        api_key=load_api_key(),
        base_url=BASE_URL,
        timeout=30.0,
        max_retries=0,
    ) as client:
        session = ChatSession()  # 只创建一次；每个问题都使用同一个 session。
        print(f"模型：{MODEL}；命令：/history /reset /quit")

        while True:
            question = input("\n你：").strip()
            if not question:
                print("请输入问题")
                continue
            if question == "/quit":
                return
            if question == "/history":
                print(json.dumps(session.turns, ensure_ascii=False, indent=2))
                continue
            if question == "/reset":
                session.turns.clear()
                print("历史已清空")
                continue

            # TODO 7：把 question、同一个 session 和 client 传给 chat()。
            try:
                answer = chat(question, session, client)
                print(f"助手：{answer}")
            except (RuntimeError, ValueError) as exc:
                print(f"本次失败：{exc}")



if __name__ == "__main__":
    try:
        main()
    except NotImplementedError as exc:
        print(f"练习尚未完成：{exc}")
    except (EOFError, KeyboardInterrupt):
        print("\n已退出")
