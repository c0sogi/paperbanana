"""In-process lifecycle tracking for long-running MCP figure generation."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, TypeVar
from uuid import uuid4

_T = TypeVar("_T")
_ACTIVE_STATUSES = {"queued", "running", "cancelling"}
_TERMINAL_STATUSES = {"completed", "failed", "cancelled"}
_IMAGE_EXTENSIONS = ("png", "jpg", "jpeg", "webp")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe(payload: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(payload, default=str))


@dataclass
class FigureSession:
    session_id: str
    operation: str
    run_id: str
    run_dir: str
    status: str = "queued"
    created_at: str = field(default_factory=_utc_now)
    started_at: str | None = None
    updated_at: str = field(default_factory=_utc_now)
    finished_at: str | None = None
    cancel_requested_at: str | None = None
    progress_event: str | None = None
    progress: dict[str, Any] = field(default_factory=dict)
    current_iteration: int | None = None
    total_iterations: int | None = None
    final_image_path: str | None = None
    error: str | None = None
    task: asyncio.Task[Any] | None = field(default=None, repr=False)


class FigureSessionStore:
    """Track tasks owned by one running MCP server process."""

    def __init__(self) -> None:
        self._sessions: dict[str, FigureSession] = {}

    def create(self, *, operation: str, run_id: str, run_dir: str) -> FigureSession:
        session = FigureSession(
            session_id=f"figure_{uuid4().hex[:12]}",
            operation=operation,
            run_id=run_id,
            run_dir=str(Path(run_dir).resolve()),
        )
        self._sessions[session.session_id] = session
        return session

    def progress(self, session_id: str, event: str, payload: dict[str, Any]) -> None:
        session = self._sessions.get(session_id)
        if session is None or session.status in _TERMINAL_STATUSES:
            return
        session.progress_event = event
        session.progress = _json_safe(payload)
        if isinstance(payload.get("iteration"), int):
            session.current_iteration = payload["iteration"]
        if isinstance(payload.get("total_iterations"), int):
            session.total_iterations = payload["total_iterations"]
        session.updated_at = _utc_now()

    def set_final_image(self, session_id: str, path: str) -> None:
        session = self._sessions[session_id]
        session.final_image_path = str(Path(path).resolve())
        session.updated_at = _utc_now()

    async def run(
        self,
        session: FigureSession,
        awaitable: Awaitable[_T],
        *,
        propagate: bool,
    ) -> _T | None:
        session.task = asyncio.current_task()
        session.status = "running"
        session.started_at = _utc_now()
        session.updated_at = session.started_at
        try:
            result = await awaitable
        except asyncio.CancelledError:
            self._finish(session, "cancelled")
            if propagate:
                raise
            return None
        except Exception as exc:
            session.error = f"{type(exc).__name__}: {exc}"
            self._finish(session, "failed")
            if propagate:
                raise
            return None
        else:
            self._finish(session, "cancelled" if session.cancel_requested_at else "completed")
            return result
        finally:
            session.task = None

    def start_background(self, session: FigureSession, awaitable: Awaitable[Any]) -> None:
        task = asyncio.create_task(
            self.run(session, awaitable, propagate=False),
            name=session.session_id,
        )
        session.task = task

        def _mark_cancelled_if_never_started(done: asyncio.Task[Any]) -> None:
            if done.cancelled() and session.status not in _TERMINAL_STATUSES:
                self._finish(session, "cancelled")
                session.task = None

        task.add_done_callback(_mark_cancelled_if_never_started)

    async def cancel(self, session_id: str) -> dict[str, Any]:
        session = self._sessions.get(session_id)
        if session is None:
            return {"cancelled": False, "error": f"Unknown figure session: {session_id}"}
        if session.status in _TERMINAL_STATUSES:
            return {
                "cancelled": False,
                "error": f"Session is already {session.status}",
                "session": self.snapshot(session),
            }
        if session.task is None or session.task.done():
            self._finish(session, "failed")
            session.error = "Session task is no longer available"
            return {
                "cancelled": False,
                "error": session.error,
                "session": self.snapshot(session),
            }

        session.status = "cancelling"
        session.cancel_requested_at = _utc_now()
        session.updated_at = session.cancel_requested_at
        session.task.cancel()
        await asyncio.sleep(0)
        return {"cancelled": True, "session": self.snapshot(session)}

    def get(self, session_id: str) -> dict[str, Any] | None:
        session = self._sessions.get(session_id)
        return self.snapshot(session) if session else None

    def list(self, *, include_finished: bool = False) -> list[dict[str, Any]]:
        sessions = list(self._sessions.values())
        if not include_finished:
            sessions = [session for session in sessions if session.status in _ACTIVE_STATUSES]
        sessions.sort(key=lambda session: session.created_at, reverse=True)
        return [self.snapshot(session) for session in sessions]

    def snapshot(self, session: FigureSession) -> dict[str, Any]:
        latest_image = session.final_image_path or self._find_latest_image(session.run_dir)
        return {
            "session_id": session.session_id,
            "operation": session.operation,
            "status": session.status,
            "run_id": session.run_id,
            "run_dir": session.run_dir,
            "created_at": session.created_at,
            "started_at": session.started_at,
            "updated_at": session.updated_at,
            "finished_at": session.finished_at,
            "cancel_requested_at": session.cancel_requested_at,
            "progress_event": session.progress_event,
            "progress": session.progress,
            "current_iteration": session.current_iteration,
            "total_iterations": session.total_iterations,
            "latest_image_path": latest_image,
            "final_image_path": session.final_image_path,
            "error": session.error,
        }

    def clear(self) -> None:
        """Clear terminal test state; callers must cancel active sessions first."""
        self._sessions.clear()

    @staticmethod
    def _finish(session: FigureSession, status: str) -> None:
        now = _utc_now()
        session.status = status
        session.updated_at = now
        session.finished_at = now

    @staticmethod
    def _find_latest_image(run_dir: str) -> str | None:
        root = Path(run_dir)
        if not root.is_dir():
            return None
        candidates: list[Path] = []
        for ext in _IMAGE_EXTENSIONS:
            candidates.extend(root.glob(f"final_output.{ext}"))
            candidates.extend(root.glob(f"iter_*/output.{ext}"))
            candidates.extend(root.glob(f"candidate_*/iter_*/output.{ext}"))
        existing = [path for path in candidates if path.is_file()]
        if not existing:
            return None
        latest = max(existing, key=lambda path: path.stat().st_mtime)
        return str(latest.resolve())


figure_sessions = FigureSessionStore()
