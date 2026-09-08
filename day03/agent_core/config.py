"""从 Day 02 移来的配置、提示词和 Key 读取函数。"""

import os
from pathlib import Path

DEFAULT_BASE_URL = (
    "https://llm-dvre3q31s582vei3.cn-beijing.maas.aliyuncs.com/compatible-mode/v1"
)
MODEL = os.getenv("LLM_MODEL", "qwen3.8-flash")
BASE_URL = os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL)
MAX_STEPS = 5


def load_api_key() -> str:
    for variable_name in ("DASHSCOPE_API_KEY", "ALIYUN_API_KEY"):
        if api_key := os.getenv(variable_name):
            return api_key

    project_root = Path(__file__).resolve().parents[2]
    key_file = project_root / "aliyun_api_key"

    if not key_file.is_file():
        raise RuntimeError(
            "未找到 API Key：请设置 DASHSCOPE_API_KEY，"
            "或在项目根目录创建 aliyun_api_key 文件。"
        )

    api_key = key_file.read_text(encoding="utf-8").strip()
    if not api_key:
        raise RuntimeError("aliyun_api_key 文件为空")

    return api_key


AGENT_INSTRUCTIONS = """
你是一个谨慎的命令行助手。

规则：
1. 涉及精确数学计算时必须使用 calculator。
2. 涉及当前日期或时间时必须使用 get_current_time。
3. 不要编造工具结果。
4. 工具返回 ok=false 时，向用户说明失败原因。
5. 只使用完成任务所需的工具。
6. 最终回答先给结论，再简要说明使用了什么信息。
"""
