from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass(frozen=True)
class ScheduledJob:
    id: str
    name: str
    cron: str
    description: str


def _parse_time_of_day(value: str, default_hour: int, default_minute: int) -> tuple[int, int]:
    parts = value.strip().split(":")
    if len(parts) != 2:
        return default_hour, default_minute
    try:
        hour = int(parts[0])
        minute = int(parts[1])
    except ValueError:
        return default_hour, default_minute
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return default_hour, default_minute
    return hour, minute


def _parse_optional_int(value: Optional[str]) -> Optional[int]:
    if value is None or value.strip() == "":
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed > 0 else None


def default_jobs() -> List[ScheduledJob]:
    return [
        ScheduledJob("collect-sources", "Collect Sources", "*/15 * * * *", "Collect and normalize source updates."),
        ScheduledJob("enrich-content", "Enrich Content", "*/20 * * * *", "Run framework mapping and executive enrichment."),
        ScheduledJob("daily-brief", "Daily Brief", "0 6 * * *", "Generate executive daily brief."),
        ScheduledJob("weekly-board-report", "Weekly Board Report", "0 7 * * MON", "Generate weekly board report."),
        ScheduledJob("monthly-report", "Monthly Executive Report", "0 8 1 * *", "Generate monthly executive report."),
    ]


class DailyPipelineScheduler:
    """Lightweight UTC daily scheduler for running the executive pipeline."""

    def __init__(self, job_runner: Callable[[Optional[int]], Dict[str, Any]]) -> None:
        self._job_runner = job_runner
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

        self.enabled = str(os.getenv("EXEC_DAILY_REFRESH_ENABLED", "true")).strip().lower() in {"1", "true", "yes", "on"}
        self.hour_utc, self.minute_utc = _parse_time_of_day(os.getenv("EXEC_DAILY_REFRESH_TIME_UTC", "06:00"), 6, 0)
        self.max_sources = _parse_optional_int(os.getenv("EXEC_DAILY_REFRESH_MAX_SOURCES"))

        self.last_run_at: Optional[str] = None
        self.last_result: Optional[Dict[str, Any]] = None
        self.last_error: Optional[str] = None
        self.next_run_at: Optional[str] = self._next_run_iso()

    def _next_run_iso(self, now: Optional[datetime] = None) -> str:
        current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
        scheduled = current.replace(hour=self.hour_utc, minute=self.minute_utc, second=0, microsecond=0)
        if scheduled <= current:
            scheduled = scheduled + timedelta(days=1)
        return scheduled.isoformat()

    def _seconds_until_next_run(self) -> float:
        target = datetime.fromisoformat(self._next_run_iso())
        now = datetime.now(timezone.utc)
        return max((target - now).total_seconds(), 0.0)

    def _run_once(self) -> None:
        started = datetime.now(timezone.utc).isoformat()
        try:
            result = self._job_runner(max_sources=self.max_sources)
            with self._lock:
                self.last_run_at = started
                self.last_result = result if isinstance(result, dict) else {"result": result}
                self.last_error = None
                self.next_run_at = self._next_run_iso()
        except Exception as exc:  # pragma: no cover - defensive runtime guard
            with self._lock:
                self.last_run_at = started
                self.last_error = str(exc)
                self.next_run_at = self._next_run_iso()

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            with self._lock:
                self.next_run_at = self._next_run_iso()
                target = self.next_run_at

            if not target:
                if self._stop_event.wait(timeout=30.0):
                    return
                continue

            now = datetime.now(timezone.utc)
            scheduled = datetime.fromisoformat(target)
            wait_seconds = max((scheduled - now).total_seconds(), 0.0)

            if self._stop_event.wait(timeout=wait_seconds):
                return

            self._run_once()

    def start(self) -> None:
        if not self.enabled:
            return
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self.next_run_at = self._next_run_iso()
            self._thread = threading.Thread(target=self._run_loop, name="executive-daily-scheduler", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=2.0)

    def record_manual_run(self, result: Dict[str, Any]) -> None:
        with self._lock:
            self.last_run_at = datetime.now(timezone.utc).isoformat()
            self.last_result = result
            self.last_error = None
            self.next_run_at = self._next_run_iso()

    def runtime_status(self) -> Dict[str, Any]:
        with self._lock:
            running = bool(self._thread and self._thread.is_alive())
            return {
                "enabled": self.enabled,
                "running": running,
                "schedule": {
                    "timezone": "UTC",
                    "timeOfDay": f"{self.hour_utc:02d}:{self.minute_utc:02d}",
                    "maxSources": self.max_sources,
                },
                "lastRunAt": self.last_run_at,
                "nextRunAt": self.next_run_at,
                "lastError": self.last_error,
                "lastResult": self.last_result,
            }


def scheduler_status(
    health_fn: Callable[[], Dict[str, str]] | None = None,
    runtime: Optional[Dict[str, Any]] = None,
) -> Dict[str, object]:
    health_payload = health_fn() if health_fn else {"status": "ready"}
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "jobs": [job.__dict__ for job in default_jobs()],
        "health": health_payload,
        "runtime": runtime or {},
    }
