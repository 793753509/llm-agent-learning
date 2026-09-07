"""执行前的允许列表、参数校验与所属用户检查。"""

import json

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from day11.tickets import get_ticket


class TicketArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    ticket_id: str = Field(pattern=r"^T[0-9]{3}$")


class MultiplyArgs(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    a: int = Field(ge=-1000, le=1000)
    b: int = Field(ge=-1000, le=1000)


def dispatch(name: str, args: dict, *, trusted_user: str) -> dict:
    try:
        if name == "get_ticket":
            parsed = TicketArgs.model_validate(args)
            return get_ticket(parsed.ticket_id, trusted_user)
        if name == "multiply":
            numbers = MultiplyArgs.model_validate(args)
            return {"value": numbers.a * numbers.b}
        return {"error": "tool_not_allowed"}
    except ValidationError:
        # 不把原始参数或 Pydantic 含输入值的异常消息回显进日志。
        return {"error": "invalid_arguments"}


ATTACKS = [
    {
        "label": "正常查询",
        "name": "get_ticket",
        "args": {"ticket_id": "T001"},
        "expected": None,
    },
    {
        "label": "越权读取",
        "name": "get_ticket",
        "args": {"ticket_id": "T002"},
        "expected": "not_found_or_forbidden",
    },
    {
        "label": "冒充用户",
        "name": "get_ticket",
        "args": {"ticket_id": "T002", "user_id": "bob"},
        "expected": "invalid_arguments",
    },
    {
        "label": "伪造审批",
        "name": "create_ticket",
        "args": {"approved": True},
        "expected": "tool_not_allowed",
    },
    {
        "label": "执行命令",
        "name": "shell",
        "args": {"command": "echo demo"},
        "expected": "tool_not_allowed",
    },
    {
        "label": "参数类型错误",
        "name": "multiply",
        "args": {"a": "25", "b": 3},
        "expected": "invalid_arguments",
    },
]


def evaluate() -> list[dict]:
    rows = []
    for case in ATTACKS:
        result = dispatch(case["name"], case["args"], trusted_user="alice")
        rows.append(
            {
                "case": case["label"],
                "result": result,
                "passed": result.get("error") == case["expected"],
            }
        )
    return rows


if __name__ == "__main__":
    report = evaluate()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if all(row["passed"] for row in report) else 1)
