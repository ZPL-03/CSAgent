"""有限元仿真作业队列。"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from core.paths import RUNTIME_DIR
from workflow.events import utc_now_iso


class SimulationJobQueue:
    """记录候选进入有限元校核后的作业状态。"""

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
                CREATE TABLE IF NOT EXISTS simulation_jobs (
                    job_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    session_candidate_id TEXT NOT NULL,
                    formal_candidate_id TEXT,
                    status TEXT NOT NULL,
                    candidate_json TEXT NOT NULL,
                    result_json TEXT,
                    error_message TEXT,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_simulation_jobs_run_id ON simulation_jobs(run_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_simulation_jobs_status ON simulation_jobs(status)")

    def enqueue(self, run_id: str, candidate: Dict[str, Any]) -> str:
        """登记待校核候选并返回作业编号。"""

        session_candidate_id = str(candidate.get("candidate_id") or candidate.get("session_candidate_id") or "").strip()
        if not session_candidate_id:
            raise ValueError("仿真作业缺少会话候选编号")
        job_id = f"{run_id}:{session_candidate_id}"
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO simulation_jobs(
                    job_id, run_id, session_candidate_id, formal_candidate_id, status,
                    candidate_json, result_json, error_message, created_at, started_at, finished_at, updated_at
                )
                VALUES (
                    ?, ?, ?, COALESCE((SELECT formal_candidate_id FROM simulation_jobs WHERE job_id = ?), NULL),
                    ?, ?, NULL, NULL,
                    COALESCE((SELECT created_at FROM simulation_jobs WHERE job_id = ?), ?),
                    NULL, NULL, ?
                )
                """,
                (
                    job_id,
                    run_id,
                    session_candidate_id,
                    job_id,
                    "queued",
                    json.dumps(candidate, ensure_ascii=False, default=str),
                    job_id,
                    now,
                    now,
                ),
            )
        return job_id

    def mark_running(self, job_id: str) -> None:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE simulation_jobs
                SET status = ?, started_at = COALESCE(started_at, ?), updated_at = ?
                WHERE job_id = ?
                """,
                ("running", now, now, job_id),
            )

    def mark_success(self, job_id: str, result: Dict[str, Any]) -> None:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE simulation_jobs
                SET status = ?, formal_candidate_id = ?, result_json = ?, error_message = NULL,
                    finished_at = ?, updated_at = ?
                WHERE job_id = ?
                """,
                (
                    "success",
                    str(result.get("candidate_id") or ""),
                    json.dumps(result, ensure_ascii=False, default=str),
                    now,
                    now,
                    job_id,
                ),
            )

    def mark_failed(self, job_id: str, error_message: str) -> None:
        now = utc_now_iso()
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE simulation_jobs
                SET status = ?, error_message = ?, finished_at = ?, updated_at = ?
                WHERE job_id = ?
                """,
                ("failed", error_message, now, now, job_id),
            )

    def list_jobs(self, run_id: str | None = None) -> List[Dict[str, Any]]:
        sql = """
            SELECT job_id, run_id, session_candidate_id, formal_candidate_id, status,
                   candidate_json, result_json, error_message, created_at, started_at, finished_at, updated_at
            FROM simulation_jobs
        """
        params: tuple[Any, ...] = ()
        if run_id:
            sql += " WHERE run_id = ?"
            params = (run_id,)
        sql += " ORDER BY created_at, job_id"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        jobs = []
        for row in rows:
            candidate = json.loads(row["candidate_json"]) if row["candidate_json"] else {}
            result = json.loads(row["result_json"]) if row["result_json"] else None
            jobs.append(
                {
                    "job_id": row["job_id"],
                    "run_id": row["run_id"],
                    "session_candidate_id": row["session_candidate_id"],
                    "formal_candidate_id": row["formal_candidate_id"],
                    "status": row["status"],
                    "candidate": candidate,
                    "result": result,
                    "error_message": row["error_message"],
                    "created_at": row["created_at"],
                    "started_at": row["started_at"],
                    "finished_at": row["finished_at"],
                    "updated_at": row["updated_at"],
                }
            )
        return jobs
