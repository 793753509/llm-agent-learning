import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import openai
from openai import OpenAI


DEFAULT_BASE_URL = (
    "https://llm-dvre3q31s582vei3.cn-beijing.maas.aliyuncs.com/"
    "compatible-mode/v1"
)
BASE_URL = os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL)
MODEL = os.getenv("LLM_MODEL", "qwen3.8-flash")

BASE_INSTRUCTIONS = """
你是一名严谨、善于教学的计算机技术导师。
请围绕用户给出的技术主题，用中文严格按照下面的 Markdown 结构回答，所有部分都不能省略：

## 一句话定义
只用一句准确、容易记忆的话定义这个概念。

## 生活类比
使用一个贴近日常生活的类比，并说明类比中的事物分别对应什么。

## 最小代码示例
给出一个尽可能短、可以独立理解的代码示例。代码块必须标注语言，并在代码后用一两句话说明运行过程。

## 两个常见错误
必须恰好列出两个初学者常犯的错误，说明错误原因和正确做法。

## 三道自测题
必须恰好给出三道由浅入深的题目。先只列题目，然后在“参考答案”小节列出简短答案，方便学习者先自行思考。

不要编造不存在的 API 或语法；不确定时明确说明不确定。
""".strip()

SIMPLE_INSTRUCTIONS = """
当前是初学者模式：
- 尽量使用短句和常用词。
- 专业术语第一次出现时立即解释。
- 假设用户只会最基础的编程，不省略关键步骤。
""".strip()

INTERVIEW_INSTRUCTIONS = """
当前是面试模式：
- 在完成规定的五个部分后，额外增加“## 面试加练”。
- 给出三道常见面试题，每道题后紧跟一份简洁、准确的参考答案。
- 至少有一道题考查原理或取舍，而不只是背诵定义。
""".strip()


@dataclass
class StudyResult:
    answer: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None
    response_id: str | None


def load_api_key() -> str:
    """Load an Alibaba Cloud key from the environment or a local ignored file."""
    for variable_name in ("DASHSCOPE_API_KEY", "ALIYUN_API_KEY"):
        if api_key := os.getenv(variable_name):
            return api_key

    project_root = Path(__file__).resolve().parent.parent
    key_file = project_root / "aliyun_api_key"
    if not key_file.is_file():
        raise RuntimeError(
            "未找到阿里云 API Key：请设置 DASHSCOPE_API_KEY，"
            "或在项目根目录创建 aliyun_api_key 文件。"
        )

    api_key = key_file.read_text(encoding="utf-8").strip()
    if not api_key:
        raise RuntimeError("aliyun_api_key 文件为空。")

    return api_key


def create_client() -> OpenAI:
    """Create the API client without making a network request."""
    return OpenAI(
        api_key=load_api_key(),
        base_url=BASE_URL,
        timeout=30.0,
        max_retries=2,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="使用大模型学习一个技术概念。未提供主题时会进入交互输入。"
    )
    parser.add_argument(
        "topic",
        nargs="*",
        help="想学习的技术主题，例如：Python class",
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--simple",
        action="store_true",
        help="使用更适合初学者的语言讲解",
    )
    mode_group.add_argument(
        "--interview",
        action="store_true",
        help="在基础讲解后增加面试题和参考答案",
    )
    return parser.parse_args()


def get_topic(topic_parts: list[str]) -> str:
    topic = " ".join(topic_parts).strip()
    if topic:
        return topic

    try:
        return input("请输入想学习的技术主题：").strip()
    except EOFError:
        return ""


def build_instructions(simple: bool, interview: bool) -> str:
    instructions = [BASE_INSTRUCTIONS]
    if simple:
        instructions.append(SIMPLE_INSTRUCTIONS)
    if interview:
        instructions.append(INTERVIEW_INSTRUCTIONS)
    return "\n\n".join(instructions)


def ask_llm(
    client: OpenAI,
    topic: str,
    *,
    simple: bool = False,
    interview: bool = False,
) -> StudyResult:
    """Ask the model for a lesson and return data without printing to the terminal."""
    response = client.responses.create(
        model=MODEL,
        instructions=build_instructions(simple, interview),
        input=f"请讲解这个技术主题：{topic}",
    )

    answer = (response.output_text or "").strip()
    if not answer:
        raise RuntimeError("模型返回成功，但回答内容为空。")

    usage = response.usage
    return StudyResult(
        answer=answer,
        model=response.model or MODEL,
        input_tokens=getattr(usage, "input_tokens", None),
        output_tokens=getattr(usage, "output_tokens", None),
        total_tokens=getattr(usage, "total_tokens", None),
        response_id=getattr(response, "id", None),
    )


def format_token_count(value: int | None) -> str:
    return str(value) if value is not None else "服务商未返回"


def display_result(topic: str, result: StudyResult) -> None:
    print(f"\n=== 学习主题：{topic} ===\n")
    print(result.answer)
    print("\n--- 请求信息 ---")
    print(f"模型：        {result.model}")
    print(f"输入 Token： {format_token_count(result.input_tokens)}")
    print(f"输出 Token： {format_token_count(result.output_tokens)}")
    print(f"总 Token：   {format_token_count(result.total_tokens)}")
    if result.response_id:
        print(f"响应 ID：     {result.response_id}")


def print_api_error(exc: Exception) -> None:
    """Convert SDK exceptions into concise, actionable terminal messages."""
    if isinstance(exc, openai.AuthenticationError):
        message = "认证失败：请检查 DASHSCOPE_API_KEY 或 aliyun_api_key 文件。"
    elif isinstance(exc, openai.RateLimitError):
        message = "请求受到额度或频率限制：请检查百炼免费额度，或稍后重试。"
    elif isinstance(exc, openai.PermissionDeniedError):
        message = "请求被拒绝：请检查 API Key、模型权限和百炼额度。"
    elif isinstance(exc, openai.APITimeoutError):
        message = "请求超时：服务可能繁忙，请稍后重试。"
    elif isinstance(exc, openai.APIConnectionError):
        message = "无法连接模型服务：请检查网络和 LLM_BASE_URL。"
    elif isinstance(exc, openai.BadRequestError):
        message = "请求参数不被模型服务接受：请检查模型名或兼容接口。"
    elif isinstance(exc, openai.APIStatusError):
        message = f"模型服务请求失败，HTTP 状态码：{exc.status_code}。"
    else:
        message = f"调用模型失败：{exc}"

    print(f"错误：{message}", file=sys.stderr)

    request_id = getattr(exc, "request_id", None)
    if request_id:
        print(f"request_id：{request_id}", file=sys.stderr)


def main() -> int:
    args = parse_args()
    topic = get_topic(args.topic)
    if not topic:
        print(
            "错误：学习主题不能为空。示例：python hello_llm.py --simple Python class",
            file=sys.stderr,
        )
        return 2

    try:
        client = create_client()
        result = ask_llm(
            client,
            topic,
            simple=args.simple,
            interview=args.interview,
        )
    except (openai.OpenAIError, RuntimeError) as exc:
        print_api_error(exc)
        return 1

    display_result(topic, result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
