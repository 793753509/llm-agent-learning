"""程序入口：在项目根目录运行 uv run python -m day03.mini_agent。"""

import sys

import openai
from openai import OpenAI

from day03.agent_core.client import OpenAIModelClient
from day03.agent_core.config import BASE_URL, MAX_STEPS, MODEL, load_api_key
from day03.agent_core.errors import AgentError
from day03.agent_core.runner import run_agent
from day03.agent_core.tools import TOOLS


def main() -> None:
    question = " ".join(sys.argv[1:]).strip()
    if not question:
        question = input("请输入问题：").strip()
    if not question:
        print("问题不能为空")
        raise SystemExit(1)

    try:
        # 运行 main() 时才读取 Key、创建客户端，import 文件时不做这些事。
        with OpenAI(
            api_key=load_api_key(),
            base_url=BASE_URL,
            timeout=30.0,
            max_retries=2,
        ) as sdk_client:
            client = OpenAIModelClient(sdk_client)
            print(f"[model] {MODEL}")
            result = run_agent(
                question,
                client=client,
                tools=TOOLS,
                max_steps=MAX_STEPS,
            )
    except openai.AuthenticationError:
        print("认证失败：请检查阿里云 API Key")
        raise SystemExit(1)
    except openai.APIConnectionError:
        print("无法连接模型服务，请检查网络")
        raise SystemExit(1)
    except openai.APIStatusError as exc:
        print(f"API 请求失败：HTTP {exc.status_code}")
        print(f"request_id：{exc.request_id or '未提供'}")
        raise SystemExit(1)
    except ValueError:
        print("模型返回的工具参数格式错误")
        raise SystemExit(1)
    except (AgentError, RuntimeError, OSError) as exc:
        print(f"Agent 执行失败：{exc}")
        raise SystemExit(1)

    print("\n--- 最终回答 ---")
    print(result.answer)
    print(
        f"[tokens] input={result.usage.input_tokens}, "
        f"output={result.usage.output_tokens}, total={result.usage.total_tokens}"
    )
    print(f"[tools] {result.used_tools}")


if __name__ == "__main__":
    main()
