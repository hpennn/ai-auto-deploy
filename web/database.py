"""
SQLite database for user payment tracking
"""

import os
import sqlite3
import time
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "app.db")


def _ensure_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_conn() -> sqlite3.Connection:
    _ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            paid_type TEXT NOT NULL DEFAULT 'free',
            paid_at TEXT,
            expires_at TEXT
        );
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            paid_type TEXT,
            created_at TEXT NOT NULL,
            paid_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
    """)
    conn.commit()
    conn.close()


def get_user(user_id: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def upsert_user(user_id: str, paid_type: str, paid_at: str = None, expires_at: str = None):
    conn = get_conn()
    conn.execute(
        """INSERT INTO users (user_id, paid_type, paid_at, expires_at)
           VALUES (?, ?, ?, ?)
           ON CONFLICT(user_id) DO UPDATE SET
             paid_type = excluded.paid_type,
             paid_at = excluded.paid_at,
             expires_at = excluded.expires_at""",
        (user_id, paid_type, paid_at, expires_at),
    )
    conn.commit()
    conn.close()


def is_paid(user_id: str) -> bool:
    user = get_user(user_id)
    if not user:
        return False
    pt = user["paid_type"]
    if pt == "permanent":
        return True
    if pt == "yearly" and user.get("expires_at"):
        from datetime import datetime
        try:
            exp = datetime.fromisoformat(user["expires_at"])
            return exp.timestamp() > time.time()
        except Exception:
            return False
    if pt == "monthly" and user.get("expires_at"):
        from datetime import datetime
        try:
            exp = datetime.fromisoformat(user["expires_at"])
            return exp.timestamp() > time.time()
        except Exception:
            return False
    return False


def create_order(order_id: str, user_id: str, amount: float, paid_type: str):
    from datetime import datetime
    conn = get_conn()
    conn.execute(
        "INSERT INTO orders (order_id, user_id, amount, status, paid_type, created_at) VALUES (?, ?, ?, 'pending', ?, ?)",
        (order_id, user_id, amount, paid_type, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def update_order_status(order_id: str, status: str):
    from datetime import datetime
    conn = get_conn()
    conn.execute(
        "UPDATE orders SET status = ?, paid_at = ? WHERE order_id = ?",
        (status, datetime.now().isoformat() if status == "paid" else None, order_id),
    )
    conn.commit()
    conn.close()


def get_order(order_id: str) -> Optional[dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


init_db()
