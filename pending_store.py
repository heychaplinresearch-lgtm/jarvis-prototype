"""
Jarvis Pending Store — SQLite-backed (prototype; production uses MySQL).

Persists pending confirmations across restarts. Each row is one pending action
waiting for a ✅ reaction from an authorized user.
"""
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

DB_PATH = os.path.expanduser("~/.hermes/jarvis_pending.sqlite")
EXPIRY_MINUTES = 15


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS pending_confirmations (
            pending_id      TEXT PRIMARY KEY,
            actor_slack_id  TEXT NOT NULL,
            intent_json     TEXT NOT NULL,
            before_json     TEXT,
            channel_id      TEXT NOT NULL,
            thread_ts       TEXT NOT NULL,
            message_ts      TEXT NOT NULL,
            created_at      TEXT NOT NULL,
            expires_at      TEXT NOT NULL,
            status          TEXT NOT NULL DEFAULT 'pending'
        )
    """)
    conn.commit()
    return conn


def write_pending(
    actor_slack_id: str,
    intent: dict[str, Any],
    before_state: dict[str, Any],
    channel_id: str,
    thread_ts: str,
    message_ts: str,
) -> str:
    """Store a pending confirmation. Returns the pending_id."""
    pending_id = f"jrv_p_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    # Expiry: 15 minutes from now
    from datetime import timedelta
    expires = (datetime.now(timezone.utc) + timedelta(minutes=EXPIRY_MINUTES)).isoformat()

    conn = _conn()
    conn.execute(
        """INSERT INTO pending_confirmations
           (pending_id, actor_slack_id, intent_json, before_json,
            channel_id, thread_ts, message_ts, created_at, expires_at, status)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        (pending_id, actor_slack_id, json.dumps(intent), json.dumps(before_state),
         channel_id, thread_ts, message_ts, now, expires, "pending"),
    )
    conn.commit()
    conn.close()
    return pending_id


def get_by_message_ts(message_ts: str) -> dict[str, Any] | None:
    """Look up a pending confirmation by the Slack message timestamp."""
    conn = _conn()
    row = conn.execute(
        "SELECT * FROM pending_confirmations WHERE message_ts=? AND status='pending'",
        (message_ts,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    now = datetime.now(timezone.utc).isoformat()
    if row["expires_at"] < now:
        expire_pending(message_ts)
        return None
    return dict(row)


def mark_executed(pending_id: str) -> None:
    conn = _conn()
    conn.execute(
        "UPDATE pending_confirmations SET status='executed' WHERE pending_id=?",
        (pending_id,)
    )
    conn.commit()
    conn.close()


def expire_pending(message_ts: str) -> None:
    conn = _conn()
    conn.execute(
        "UPDATE pending_confirmations SET status='expired' WHERE message_ts=? AND status='pending'",
        (message_ts,)
    )
    conn.commit()
    conn.close()


def list_pending() -> list[dict[str, Any]]:
    conn = _conn()
    now = datetime.now(timezone.utc).isoformat()
    rows = conn.execute(
        "SELECT * FROM pending_confirmations WHERE status='pending' AND expires_at > ?",
        (now,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    # smoke test
    pid = write_pending(
        actor_slack_id="U123",
        intent={"action": "quota_grant", "target_email": "test@heygen.com"},
        before_state={"tier": "free", "credits": 0},
        channel_id="C123",
        thread_ts="123.456",
        message_ts="123.789",
    )
    print(f"Written: {pid}")
    row = get_by_message_ts("123.789")
    print(f"Fetched: {row['pending_id']} status={row['status']}")
