"""虚构工单；ID 不是访问凭证，读取时还要检查所属用户。"""

TICKETS = {
    "T001": {
        "id": "T001",
        "owner": "alice",
        "status": "处理中",
        "title": "北店 E101 预约失败",
    },
    "T002": {
        "id": "T002",
        "owner": "bob",
        "status": "已完成",
        "title": "南店 WiFi 咨询",
    },
}


def get_ticket(ticket_id: str, user_id: str) -> dict:
    ticket = TICKETS.get(ticket_id)
    if ticket is None or ticket["owner"] != user_id:
        return {"error": "not_found_or_forbidden"}
    return dict(ticket)
