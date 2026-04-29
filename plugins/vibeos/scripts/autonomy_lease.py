"""Shared file lease guard for VibeOS long-run autonomy drivers."""

from __future__ import annotations

import json
import os
import socket
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.2.0"


class LeaseConflict(RuntimeError):
    """Raised when another autonomy driver owns the active run lease."""

    def __init__(self, lease: dict[str, Any], path: Path):
        self.lease = lease
        self.path = path
        super().__init__(f"active autonomy lease exists at {path}")


def iso_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def parse_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def lease_path(project_dir: Path) -> Path:
    return project_dir / ".vibeos/autonomy/run-lease.json"


def last_lease_path(project_dir: Path) -> Path:
    return project_dir / ".vibeos/autonomy/last-lease.json"


def conflict_path(project_dir: Path) -> Path:
    return project_dir / ".vibeos/autonomy/lease-conflict.json"


def is_stale(lease: dict[str, Any], now: datetime) -> bool:
    expires_at = lease.get("expires_at")
    if not expires_at:
        return False
    try:
        return parse_iso(str(expires_at)) <= now
    except ValueError:
        return False


def lease_payload(project_dir: Path, operation: str, ttl_seconds: int, owner: str) -> dict[str, Any]:
    acquired = datetime.now(timezone.utc).replace(microsecond=0)
    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "token": uuid.uuid4().hex,
        "owner": owner or f"{socket.gethostname()}:{os.getpid()}",
        "pid": os.getpid(),
        "operation": operation,
        "project_dir": str(project_dir),
        "acquired_at": acquired.isoformat().replace("+00:00", "Z"),
        "expires_at": (acquired + timedelta(seconds=ttl_seconds)).isoformat().replace("+00:00", "Z"),
        "ttl_seconds": ttl_seconds,
    }


class AutonomyLease:
    def __init__(self, project_dir: Path, operation: str, ttl_seconds: int, owner: str = ""):
        self.project_dir = project_dir
        self.operation = operation
        self.ttl_seconds = ttl_seconds
        self.owner = owner
        self.path = lease_path(project_dir)
        self.payload: dict[str, Any] = {}
        self.recovered_stale_lease: dict[str, Any] | None = None

    def acquire(self) -> "AutonomyLease":
        if self.ttl_seconds < 1:
            raise ValueError("lease ttl must be >= 1 second")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.payload = lease_payload(self.project_dir, self.operation, self.ttl_seconds, self.owner)
        while True:
            try:
                fd = os.open(str(self.path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            except FileExistsError:
                existing = load_json(self.path, {})
                if is_stale(existing, datetime.now(timezone.utc)):
                    self.recovered_stale_lease = existing
                    try:
                        self.path.unlink()
                    except FileNotFoundError:
                        pass
                    continue
                raise LeaseConflict(existing, self.path) from None
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self.payload, handle, indent=2, sort_keys=True)
                handle.write("\n")
            return self

    def release(self, status: str = "released") -> None:
        current = load_json(self.path, {})
        released_at = iso_now()
        if current.get("token") == self.payload.get("token"):
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
        evidence = dict(self.payload)
        evidence.update(
            {
                "released_at": released_at,
                "release_status": status,
                "lease_file": str(self.path),
            }
        )
        if self.recovered_stale_lease:
            evidence["recovered_stale_lease"] = self.recovered_stale_lease
        write_json(last_lease_path(self.project_dir), evidence)

    def report(self) -> dict[str, Any]:
        report = dict(self.payload)
        report["lease_file"] = str(self.path)
        if self.recovered_stale_lease:
            report["recovered_stale_lease"] = self.recovered_stale_lease
        return report

    def __enter__(self) -> "AutonomyLease":
        return self.acquire()

    def __exit__(self, exc_type: Any, _exc: Any, _traceback: Any) -> None:
        self.release("error" if exc_type else "released")


def conflict_report(project_dir: Path, operation: str, conflict: LeaseConflict) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": iso_now(),
        "project_dir": str(project_dir),
        "operation": operation,
        "summary": {
            "status": "lease_conflict",
            "reason": "another autonomy driver owns the active run lease",
            "lease_file": str(conflict.path),
        },
        "active_lease": conflict.lease,
    }
