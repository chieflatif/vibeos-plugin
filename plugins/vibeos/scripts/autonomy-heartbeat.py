#!/usr/bin/env python3
"""Record long-run VibeOS autonomy heartbeats and update session state."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.2.0"
DEFAULT_TARGET_HOURS = 24
DEFAULT_MAX_HOURS = 48
DEFAULT_HEARTBEAT_MINUTES = 30
DEFAULT_CHECKPOINT_MINUTES = 60
DEFAULT_AUDIT_MINUTES = 180
TERMINAL_STATUSES = {"complete", "paused", "blocked"}
CHECKPOINT_STATUSES = {"checkpoint", "audit", "complete"}
AUDIT_STATUSES = {"audit", "complete"}
REQUIRED_STOP_CONDITIONS = [
    "security_or_secret_risk",
    "destructive_or_irreversible_action",
    "unclear_product_decision",
    "repeated_gate_failure",
    "provider_or_session_limit",
    "repeated_no_progress_loop",
    "plan_complete",
]


def parse_iso(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def now_from_arg(value: str) -> datetime:
    if value:
        return parse_iso(value)
    return datetime.now(timezone.utc).replace(microsecond=0)


def iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "run"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def project_root_from_args(value: str) -> Path:
    if value:
        return Path(value).resolve()
    return Path(os.environ.get("PROJECT_ROOT", ".")).resolve()


def ensure_config(config: dict[str, Any], args: argparse.Namespace, timestamp: str, active: bool) -> dict[str, Any]:
    autonomy = config.setdefault("autonomy", {})
    long_run = autonomy.setdefault("long_run", {})
    long_run["active"] = active
    long_run.setdefault("created_at", timestamp)
    long_run["last_updated"] = timestamp
    long_run["target_hours"] = args.target_hours
    long_run["max_hours"] = args.max_hours
    long_run["heartbeat_interval_minutes"] = args.heartbeat_interval_minutes
    long_run["checkpoint_interval_minutes"] = args.checkpoint_interval_minutes
    long_run["audit_interval_minutes"] = args.audit_interval_minutes
    long_run["evidence_dir"] = ".vibeos/autonomy"
    stop_conditions = long_run.get("stop_conditions") or []
    for condition in REQUIRED_STOP_CONDITIONS:
        if condition not in stop_conditions:
            stop_conditions.append(condition)
    long_run["stop_conditions"] = stop_conditions
    return config


def session_id(session: dict[str, Any], timestamp: str) -> str:
    return str(session.get("session_id") or os.environ.get("CLAUDE_SESSION_ID") or timestamp.replace(":", "").replace("-", ""))


def run_id(session: dict[str, Any], timestamp: str, requested: str) -> str:
    if requested:
        return requested
    existing = session.get("long_run", {}).get("run_id")
    if existing:
        return str(existing)
    return f"longrun-{session_id(session, timestamp)}"


def heartbeat_payload(
    args: argparse.Namespace,
    timestamp: str,
    session: dict[str, Any],
    current_run_id: str,
) -> dict[str, Any]:
    completed_wos = session.get("completed_wos", [])
    if not isinstance(completed_wos, list):
        completed_wos = []
    payload = {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "run_id": current_run_id,
        "session_id": session_id(session, timestamp),
        "timestamp": timestamp,
        "status": args.status,
        "loop_iteration": args.iteration,
        "active_wo": args.wo or session.get("active_wo"),
        "summary": args.summary,
        "next_action": args.next_action,
        "blocker": args.blocker,
        "completed_wos_count": len(completed_wos),
        "checkpoint_required": args.status == "checkpoint",
        "audit_required": args.status == "audit",
    }
    return payload


def update_session(
    session: dict[str, Any],
    args: argparse.Namespace,
    timestamp: str,
    current_run_id: str,
    active: bool,
    heartbeat_path: Path,
) -> dict[str, Any]:
    session["session_id"] = session_id(session, timestamp)
    session["mode"] = "autonomous"
    session["active"] = active
    session.setdefault("started_at", timestamp)
    session["last_updated"] = timestamp
    if args.wo:
        session["active_wo"] = args.wo
    session.setdefault("completed_wos", [])
    session.setdefault("phase_checkpoints", [])

    long_run = session.setdefault("long_run", {})
    long_run["run_id"] = current_run_id
    long_run["active"] = active
    long_run.setdefault("started_at", timestamp)
    long_run["last_heartbeat_at"] = timestamp
    long_run["last_heartbeat_file"] = str(heartbeat_path)
    long_run["loop_iteration"] = args.iteration
    long_run["target_hours"] = args.target_hours
    long_run["max_hours"] = args.max_hours
    long_run["heartbeat_interval_minutes"] = args.heartbeat_interval_minutes
    long_run["checkpoint_interval_minutes"] = args.checkpoint_interval_minutes
    long_run["audit_interval_minutes"] = args.audit_interval_minutes
    long_run["status"] = args.status
    if args.status in CHECKPOINT_STATUSES:
        long_run["last_checkpoint_at"] = timestamp
    if args.status in AUDIT_STATUSES:
        long_run["last_audit_at"] = timestamp
    if args.status in TERMINAL_STATUSES:
        long_run["ended_at"] = timestamp
        long_run["stop_reason"] = args.blocker or args.status
        session["ended_at"] = timestamp
    else:
        long_run.pop("ended_at", None)
        long_run.pop("stop_reason", None)
        session.pop("ended_at", None)
        session.pop("paused_at", None)
    return session


def append_log(project_dir: Path, timestamp: str, payload: dict[str, Any]) -> None:
    log_path = project_dir / ".vibeos/build-log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    line = (
        f"[{timestamp}] long-run-autonomy {payload['run_id']} "
        f"{payload['status']} iteration={payload['loop_iteration']} "
        f"wo={payload.get('active_wo') or 'unknown'} summary={payload.get('summary') or 'heartbeat'}\n"
    )
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record a VibeOS long-run autonomy heartbeat.")
    parser.add_argument("--project-dir", default="", help="Project root. Defaults to PROJECT_ROOT or cwd.")
    parser.add_argument("--status", default="running", choices=["running", "checkpoint", "audit", "blocked", "paused", "complete"])
    parser.add_argument("--wo", default="", help="Active work order id or path.")
    parser.add_argument("--summary", default="", help="Short heartbeat summary.")
    parser.add_argument("--next-action", default="", help="Immediate next action.")
    parser.add_argument("--blocker", default="", help="Blocker or stop reason for terminal statuses.")
    parser.add_argument("--iteration", type=int, default=0, help="Long-run loop iteration number.")
    parser.add_argument("--run-id", default="", help="Existing run id. Defaults to session long_run.run_id.")
    parser.add_argument("--target-hours", type=int, default=DEFAULT_TARGET_HOURS)
    parser.add_argument("--max-hours", type=int, default=DEFAULT_MAX_HOURS)
    parser.add_argument("--heartbeat-interval-minutes", type=int, default=DEFAULT_HEARTBEAT_MINUTES)
    parser.add_argument("--checkpoint-interval-minutes", type=int, default=DEFAULT_CHECKPOINT_MINUTES)
    parser.add_argument("--audit-interval-minutes", type=int, default=DEFAULT_AUDIT_MINUTES)
    parser.add_argument("--now", default="", help="Override current time for tests, ISO-8601.")
    parser.add_argument("--json", action="store_true", help="Print heartbeat payload as JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.iteration < 0:
        print("[autonomy-heartbeat] FAIL: --iteration must be >= 0", file=sys.stderr)
        return 2
    if args.target_hours < 1 or args.max_hours < 1:
        print("[autonomy-heartbeat] FAIL: target and max hours must be positive", file=sys.stderr)
        return 2

    project_dir = project_root_from_args(args.project_dir)
    now = now_from_arg(args.now)
    timestamp = iso(now)
    active = args.status not in TERMINAL_STATUSES

    config_path = project_dir / ".vibeos/config.json"
    session_path = project_dir / ".vibeos/session-state.json"
    config = load_json(config_path, {})
    session = load_json(session_path, {})
    current_run_id = run_id(session, timestamp, args.run_id)

    heartbeat_dir = project_dir / ".vibeos/autonomy/heartbeats"
    heartbeat_file = heartbeat_dir / f"{slug(current_run_id)}-{timestamp.replace(':', '').replace('-', '')}.json"
    payload = heartbeat_payload(args, timestamp, session, current_run_id)
    write_json(heartbeat_file, payload)
    config = ensure_config(config, args, timestamp, active)
    session = update_session(session, args, timestamp, current_run_id, active, heartbeat_file)
    write_json(config_path, config)
    write_json(session_path, session)
    append_log(project_dir, timestamp, payload)

    if args.json:
        print(json.dumps({"status": "pass", "heartbeat": str(heartbeat_file), "payload": payload}, indent=2, sort_keys=True))
    else:
        print(f"[autonomy-heartbeat] PASS: wrote {heartbeat_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
