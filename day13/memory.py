"""显式保存偏好，跨进程读取；SQLite 文件就在本地。"""

import argparse
import json
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "memory.sqlite"
ALLOWED = {"style": {"简短", "详细"}, "language": {"中文", "英文"}}


class MemoryStore:
    def __init__(self, path: Path = DB_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with self.connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS memory ("
                "user_id TEXT, key TEXT, value TEXT, source TEXT, "
                "updated_at REAL, expires_at REAL, version INTEGER, "
                "PRIMARY KEY(user_id, key))"
            )

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path)
        try:
            with db:  # 成功提交，异常回滚；外层 finally 另外负责关闭连接。
                yield db
        finally:
            db.close()

    def remember(self, user_id: str, key: str, value: str, ttl: int = 86400) -> None:
        if not user_id.strip() or key not in ALLOWED or value not in ALLOWED[key]:
            raise ValueError("本课只保存 style=简短/详细、language=中文/英文")
        if ttl <= 0:
            raise ValueError("ttl 必须是正秒数")
        now = time.time()
        with self.connect() as db:
            db.execute(
                "INSERT INTO memory VALUES (?, ?, ?, ?, ?, ?, 1) "
                "ON CONFLICT(user_id,key) DO UPDATE SET value=excluded.value, "
                "source=excluded.source, updated_at=excluded.updated_at, "
                "expires_at=excluded.expires_at, version=memory.version+1",
                (user_id, key, value, "explicit_user_input", now, now + ttl),
            )

    def recall(self, user_id: str, now: float | None = None) -> list[dict]:
        now = time.time() if now is None else now
        with self.connect() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                "SELECT key,value,source,updated_at,expires_at,version FROM memory "
                "WHERE user_id=? AND expires_at>? ORDER BY key",
                (user_id, now),
            ).fetchall()
        return [dict(row) for row in rows]

    def forget(self, user_id: str, key: str) -> None:
        with self.connect() as db:
            db.execute("DELETE FROM memory WHERE user_id=? AND key=?", (user_id, key))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["remember", "list", "forget"])
    parser.add_argument("--user", default="alice", help="实验分区标签，不是登录身份")
    parser.add_argument("--key", default="style")
    parser.add_argument("--value", default="简短")
    parser.add_argument("--ttl", type=int, default=86400)
    parser.add_argument("--db", type=Path, default=DB_PATH)
    args = parser.parse_args()
    store = MemoryStore(args.db)
    if args.action == "remember":
        store.remember(args.user, args.key, args.value, args.ttl)
    elif args.action == "forget":
        store.forget(args.user, args.key)
    print(json.dumps(store.recall(args.user), ensure_ascii=False, indent=2))
