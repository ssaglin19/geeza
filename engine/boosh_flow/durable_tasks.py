"""Durable task plans with resume capability."""
import json
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TaskLease:
    task_id: str
    flow_id: str
    status: str  # pending, running, completed, failed
    created_at: float
    updated_at: float
    context: dict
    current_page: int
    current_step: int
    trace: list


class TaskStore:
    """SQLite-backed durable task store with lease semantics."""

    def __init__(self, db_path: str = "tasks.sqlite"):
        self.db = sqlite3.connect(db_path)
        self._init_schema()

    def _init_schema(self):
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id TEXT PRIMARY KEY,
                flow_id TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL,
                context TEXT NOT NULL,
                current_page INTEGER DEFAULT 0,
                current_step INTEGER DEFAULT 0,
                trace TEXT DEFAULT '[]'
            )
        """)
        self.db.commit()

    def create(self, task_id: str, flow_id: str, context: dict) -> TaskLease:
        now = time.time()
        lease = TaskLease(
            task_id=task_id,
            flow_id=flow_id,
            status="pending",
            created_at=now,
            updated_at=now,
            context=context,
            current_page=0,
            current_step=0,
            trace=[],
        )
        self.db.execute(
            "INSERT INTO tasks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (task_id, flow_id, "pending", now, now, json.dumps(context), 0, 0, "[]"),
        )
        self.db.commit()
        return lease

    def get(self, task_id: str) -> Optional[TaskLease]:
        row = self.db.execute(
            "SELECT * FROM tasks WHERE task_id = ?", (task_id,)
        ).fetchone()
        if not row:
            return None
        return TaskLease(
            task_id=row[0],
            flow_id=row[1],
            status=row[2],
            created_at=row[3],
            updated_at=row[4],
            context=json.loads(row[5]),
            current_page=row[6],
            current_step=row[7],
            trace=json.loads(row[8]),
        )

    def update(self, lease: TaskLease):
        lease.updated_at = time.time()
        self.db.execute(
            """UPDATE tasks SET status=?, updated_at=?, context=?,
               current_page=?, current_step=?, trace=? WHERE task_id=?""",
            (
                lease.status,
                lease.updated_at,
                json.dumps(lease.context),
                lease.current_page,
                lease.current_step,
                json.dumps(lease.trace),
                lease.task_id,
            ),
        )
        self.db.commit()

    def list_pending(self) -> list:
        rows = self.db.execute(
            "SELECT task_id FROM tasks WHERE status IN ('pending', 'running')"
        ).fetchall()
        return [self.get(row[0]) for row in rows]

    def acquire_lease(self, task_id: str, timeout: float = 300.0) -> bool:
        """Acquire a lease on a task. Returns True if acquired."""
        lease = self.get(task_id)
        if not lease:
            return False
        if lease.status == "running" and time.time() - lease.updated_at < timeout:
            return False  # someone else has it
        lease.status = "running"
        self.update(lease)
        return True

    def release_lease(self, task_id: str, status: str = "pending"):
        lease = self.get(task_id)
        if lease:
            lease.status = status
            self.update(lease)


def resume_task(store: TaskStore, task_id: str, engine, driver) -> list:
    """Resume a task from its last checkpoint."""
    lease = store.get(task_id)
    if not lease:
        return [{"event": "TASK_NOT_FOUND", "task_id": task_id}]

    if not store.acquire_lease(task_id):
        return [{"event": "LEASE_CONFLICT", "task_id": task_id}]

    events = []
    try:
        # Reconstruct context
        ctx = lease.context.copy()

        # Resume from checkpoint
        flow = engine.load_flow(lease.flow_id)
        for i, page in enumerate(flow.pages):
            if i < lease.current_page:
                continue  # already done
            for j, step in enumerate(page.steps):
                if i == lease.current_page and j < lease.current_step:
                    continue  # already done
                # Execute step
                result = engine.execute_step(step, driver, ctx, events)
                lease.current_step = j + 1
                store.update(lease)
                if result == "aborted":
                    lease.status = "failed"
                    store.update(lease)
                    return events
                elif result == "completed":
                    lease.status = "completed"
                    store.update(lease)
                    return events
            lease.current_page = i + 1
            lease.current_step = 0
            store.update(lease)

        lease.status = "completed"
        store.update(lease)
        return events
    finally:
        store.release_lease(task_id, lease.status)
