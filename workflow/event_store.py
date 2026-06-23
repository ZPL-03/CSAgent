"""SQLite 工作流事件与快照存储。"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from core.paths import RUNTIME_DIR
from workflow.events import WorkflowEvent, utc_now_iso


class WorkflowEventStore:
    """记录工作流运行、事件和最新快照。"""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or (RUNTIME_DIR / "workflow_runtime.sqlite3")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    run_id TEXT PRIMARY KEY,
                    instruction TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    agent TEXT NOT NULL,
                    stage TEXT NOT NULL,
                    message TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_snapshots (
                    run_id TEXT PRIMARY KEY,
                    stage TEXT NOT NULL,
                    pending_confirmation TEXT,
                    state_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_workflow_events_run_id ON workflow_events(run_id)")

    def create_run(self, run_id: str, instruction: str, status: str = "running") -> None:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO workflow_runs(run_id, instruction, status, created_at, updated_at)
                VALUES (?, ?, ?, COALESCE((SELECT created_at FROM workflow_runs WHERE run_id = ?), ?), ?)
                """,
                (run_id, instruction, status, run_id, now, now),
            )

    def has_run(self, run_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM workflow_runs WHERE run_id = ? LIMIT 1",
                (run_id,),
            ).fetchone()
        return row is not None

    def update_run_status(self, run_id: str, status: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE workflow_runs SET status = ?, updated_at = ? WHERE run_id = ?",
                (status, utc_now_iso(), run_id),
            )

    @staticmethod
    def _snapshot_run_status(stage: str, pending_confirmation: Any) -> str:
        if stage == "completed":
            return "completed"
        if stage.endswith("_failed"):
            return "failed"
        if stage.startswith("paused"):
            return "paused"
        if pending_confirmation or stage.startswith("awaiting_"):
            return "waiting"
        return "running"

    def append_event(self, event: WorkflowEvent) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO workflow_events(run_id, event_type, agent, stage, message, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.run_id,
                    event.event_type,
                    event.agent,
                    event.stage,
                    event.message,
                    json.dumps(event.payload, ensure_ascii=False, default=str),
                    event.created_at,
                ),
            )
            conn.execute(
                "UPDATE workflow_runs SET updated_at = ? WHERE run_id = ?",
                (event.created_at, event.run_id),
            )

    def save_snapshot(self, run_id: str, state: Dict[str, Any]) -> None:
        stage = str(state.get("stage") or "")
        pending = state.get("pending_confirmation")
        run_status = self._snapshot_run_status(stage, pending)
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO workflow_snapshots(run_id, stage, pending_confirmation, state_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (run_id, stage, pending, json.dumps(state, ensure_ascii=False, default=str), now),
            )
            conn.execute(
                "UPDATE workflow_runs SET status = ?, updated_at = ? WHERE run_id = ?",
                (run_status, now, run_id),
            )

    def load_snapshot(self, run_id: str) -> Dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT state_json FROM workflow_snapshots WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"未找到工作流快照：{run_id}")
        return json.loads(row["state_json"])

    def list_runs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """按更新时间倒序列出最近工作流运行摘要。"""
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    r.run_id,
                    r.instruction,
                    r.status,
                    r.created_at,
                    r.updated_at,
                    s.stage,
                    s.pending_confirmation
                FROM workflow_runs r
                LEFT JOIN workflow_snapshots s ON s.run_id = r.run_id
                ORDER BY r.updated_at DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return [
            {
                "run_id": row["run_id"],
                "instruction": row["instruction"],
                "status": row["status"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "stage": row["stage"],
                "pending_confirmation": row["pending_confirmation"],
            }
            for row in rows
        ]

    def list_events(self, run_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT run_id, event_type, agent, stage, message, payload_json, created_at
                FROM workflow_events
                WHERE run_id = ?
                ORDER BY id
                """,
                (run_id,),
            ).fetchall()
        events = []
        for row in rows:
            payload = json.loads(row["payload_json"])
            events.append(
                {
                    "run_id": row["run_id"],
                    "event_type": row["event_type"],
                    "agent": row["agent"],
                    "stage": row["stage"],
                    "message": row["message"],
                    "payload": payload,
                    "created_at": row["created_at"],
                }
            )
        return events
