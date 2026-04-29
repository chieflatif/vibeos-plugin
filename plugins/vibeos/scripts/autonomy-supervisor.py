#!/usr/bin/env python3
"""Plan the next VibeOS long-run autonomy loop action."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.2.0"
TERMINAL_STATUSES = {"complete", "paused", "blocked"}
DEFAULT_POLICY = {
    "max_duration_hours": 48,
    "max_loop_iterations": 512,
    "supervisor_poll_interval_minutes": 15,
    "resume_backoff_minutes": 15,
    "stale_heartbeat_multiplier": 3,
    "checkpoint_grace_multiplier": 2,
    "audit_grace_multiplier": 2,
}


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


def minutes_between(start: str, now: datetime) -> float:
    return (now - parse_iso(start)).total_seconds() / 60


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


def project_root(value: str) -> Path:
    if value:
        return Path(value).resolve()
    return Path(os.environ.get("PROJECT_ROOT", ".")).resolve()


def load_policy(project_dir: Path) -> dict[str, Any]:
    data = load_json(project_dir / ".vibeos/reference/autonomy/long-run-autonomy-policy.json", {})
    policy = dict(DEFAULT_POLICY)
    if isinstance(data, dict):
        policy.update(data.get("policy", data))
    return policy


def active_long_run(config: dict[str, Any], session: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    config_long_run = config.get("autonomy", {}).get("long_run", {})
    session_long_run = session.get("long_run", {})
    merged = dict(config_long_run)
    merged.update({k: v for k, v in session_long_run.items() if v is not None})
    active = bool(config_long_run.get("active") or session_long_run.get("active"))
    return merged, active


def heartbeat_files(project_dir: Path, run_id: str) -> list[tuple[Path, dict[str, Any]]]:
    heartbeat_dir = project_dir / ".vibeos/autonomy/heartbeats"
    if not heartbeat_dir.exists():
        return []
    files = []
    for path in heartbeat_dir.glob("*.json"):
        data = load_json(path, {})
        if not run_id or data.get("run_id") == run_id:
            files.append((path, data))
    return files


def latest_heartbeat(project_dir: Path, run_id: str) -> tuple[Path | None, dict[str, Any]]:
    latest_path = None
    latest_data: dict[str, Any] = {}
    latest_time: datetime | None = None
    for path, data in heartbeat_files(project_dir, run_id):
        timestamp = data.get("timestamp")
        if not timestamp:
            continue
        try:
            parsed = parse_iso(str(timestamp))
        except ValueError:
            continue
        if latest_time is None or parsed > latest_time:
            latest_time = parsed
            latest_path = path
            latest_data = data
    return latest_path, latest_data


def command_plan(project_dir: Path, action: str, run: dict[str, Any], next_iteration: int, reason: str) -> list[str]:
    active_wo = run.get("active_wo") or "unknown"
    if action == "record_heartbeat":
        return [
            f'python3 ".vibeos/scripts/autonomy-heartbeat.py" --status running --iteration {next_iteration} --wo "{active_wo}" --summary "{reason}" --next-action "continue build loop"',
        ]
    if action == "run_checkpoint":
        return [
            f'python3 ".vibeos/scripts/autonomy-heartbeat.py" --status checkpoint --iteration {next_iteration} --wo "{active_wo}" --summary "{reason}" --next-action "run checkpoint gates and audits"',
            'bash ".vibeos/scripts/gate-runner.sh" pre_commit --continue-on-failure --project-dir "."',
            'bash ".vibeos/scripts/gate-runner.sh" full_audit --continue-on-failure --project-dir "."',
        ]
    if action == "run_audit":
        return [
            f'python3 ".vibeos/scripts/autonomy-heartbeat.py" --status audit --iteration {next_iteration} --wo "{active_wo}" --summary "{reason}" --next-action "run session audit"',
            'bash ".vibeos/scripts/gate-runner.sh" session_end --continue-on-failure --project-dir "."',
        ]
    if action == "stop":
        return [
            f'python3 ".vibeos/scripts/autonomy-heartbeat.py" --status blocked --iteration {next_iteration} --wo "{active_wo}" --summary "{reason}" --blocker "loop_or_runtime_limit" --next-action "session audit"',
            'python3 ".vibeos/scripts/validate-long-run-autonomy.py" --project-dir "." --require-closed',
        ]
    if action == "continue_build":
        return [
            'bash ".vibeos/scripts/detect-runtime-capabilities.sh" --project-dir "."',
            'continue with the next eligible Work Order using the VibeOS build flow',
        ]
    return []


def plan_action(project_dir: Path, now: datetime) -> dict[str, Any]:
    config = load_json(project_dir / ".vibeos/config.json", {})
    session = load_json(project_dir / ".vibeos/session-state.json", {})
    policy = load_policy(project_dir)
    run, active = active_long_run(config, session)
    timestamp = iso(now)

    if not run:
        action = "not_configured"
        reason = "long-run autonomy is not configured"
        next_iteration = 0
        return render_plan(project_dir, timestamp, action, reason, {}, None, {}, next_iteration, [])

    run_id = str(run.get("run_id") or "")
    status = str(run.get("status") or "")
    last_path, latest = latest_heartbeat(project_dir, run_id)
    latest_iteration = int(latest.get("loop_iteration") or run.get("loop_iteration") or 0)
    next_iteration = latest_iteration + 1

    if not active or status in TERMINAL_STATUSES:
        action = "closed"
        reason = f"long-run autonomy is not active; status={status or 'inactive'}"
        return render_plan(project_dir, timestamp, action, reason, run, last_path, latest, next_iteration, [])

    max_iterations = int(run.get("max_loop_iterations") or policy.get("max_loop_iterations") or 512)
    if latest_iteration >= max_iterations:
        action = "stop"
        reason = f"loop iteration limit reached ({latest_iteration} >= {max_iterations})"
        return render_plan(project_dir, timestamp, action, reason, run, last_path, latest, next_iteration, command_plan(project_dir, action, run, next_iteration, reason))

    started_at = run.get("started_at")
    max_hours = float(run.get("max_hours") or policy.get("max_duration_hours") or 48)
    if started_at and (minutes_between(str(started_at), now) / 60) >= max_hours:
        action = "stop"
        reason = f"max runtime reached ({max_hours:g} hours)"
        return render_plan(project_dir, timestamp, action, reason, run, last_path, latest, next_iteration, command_plan(project_dir, action, run, next_iteration, reason))

    heartbeat_interval = float(run.get("heartbeat_interval_minutes") or 30)
    checkpoint_interval = float(run.get("checkpoint_interval_minutes") or 60)
    audit_interval = float(run.get("audit_interval_minutes") or 180)

    if not latest:
        action = "record_heartbeat"
        reason = "no heartbeat exists for the active long-run session"
        return render_plan(project_dir, timestamp, action, reason, run, last_path, latest, next_iteration, command_plan(project_dir, action, run, next_iteration, reason))

    heartbeat_age = minutes_between(str(latest["timestamp"]), now)
    stale_after = heartbeat_interval * float(policy.get("stale_heartbeat_multiplier", 3))

    last_audit = run.get("last_audit_at")
    audit_age = minutes_between(str(last_audit), now) if last_audit else None
    if audit_age is None and started_at and minutes_between(str(started_at), now) >= audit_interval:
        action = "run_audit"
        reason = "audit cadence is due"
        return render_plan(project_dir, timestamp, action, reason, run, last_path, latest, next_iteration, command_plan(project_dir, action, run, next_iteration, reason))
    if audit_age is not None and audit_age >= audit_interval:
        action = "run_audit"
        reason = f"audit cadence is due ({audit_age:.1f} minutes since last audit)"
        return render_plan(project_dir, timestamp, action, reason, run, last_path, latest, next_iteration, command_plan(project_dir, action, run, next_iteration, reason))

    last_checkpoint = run.get("last_checkpoint_at")
    checkpoint_age = minutes_between(str(last_checkpoint), now) if last_checkpoint else None
    if checkpoint_age is None and started_at and minutes_between(str(started_at), now) >= checkpoint_interval:
        action = "run_checkpoint"
        reason = "checkpoint cadence is due"
        return render_plan(project_dir, timestamp, action, reason, run, last_path, latest, next_iteration, command_plan(project_dir, action, run, next_iteration, reason))
    if checkpoint_age is not None and checkpoint_age >= checkpoint_interval:
        action = "run_checkpoint"
        reason = f"checkpoint cadence is due ({checkpoint_age:.1f} minutes since last checkpoint)"
        return render_plan(project_dir, timestamp, action, reason, run, last_path, latest, next_iteration, command_plan(project_dir, action, run, next_iteration, reason))

    if heartbeat_age >= stale_after:
        action = "record_heartbeat"
        reason = f"heartbeat stale ({heartbeat_age:.1f} minutes old)"
        return render_plan(project_dir, timestamp, action, reason, run, last_path, latest, next_iteration, command_plan(project_dir, action, run, next_iteration, reason))

    if heartbeat_age >= heartbeat_interval:
        action = "record_heartbeat"
        reason = f"heartbeat cadence is due ({heartbeat_age:.1f} minutes old)"
        return render_plan(project_dir, timestamp, action, reason, run, last_path, latest, next_iteration, command_plan(project_dir, action, run, next_iteration, reason))

    action = "continue_build"
    reason = "cadence and failure controls are within policy"
    return render_plan(project_dir, timestamp, action, reason, run, last_path, latest, next_iteration, command_plan(project_dir, action, run, next_iteration, reason))


def next_resume_after(action: str, timestamp: str, run: dict[str, Any]) -> str | None:
    if action in {"stop", "closed", "not_configured"}:
        return None
    base = parse_iso(timestamp)
    if action in {"record_heartbeat", "run_checkpoint", "run_audit"}:
        return timestamp
    minutes = float(run.get("supervisor_poll_interval_minutes") or DEFAULT_POLICY["supervisor_poll_interval_minutes"])
    return iso(base + timedelta(minutes=minutes))


def render_plan(
    project_dir: Path,
    timestamp: str,
    action: str,
    reason: str,
    run: dict[str, Any],
    latest_path: Path | None,
    latest: dict[str, Any],
    next_iteration: int,
    commands: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": timestamp,
        "project_dir": str(project_dir),
        "decision": {
            "action": action,
            "reason": reason,
            "next_iteration": next_iteration,
            "next_resume_after": next_resume_after(action, timestamp, run),
            "requires_human": action in {"stop", "closed"} and action != "not_configured",
        },
        "run": {
            "run_id": run.get("run_id"),
            "active": bool(run.get("active")),
            "status": run.get("status"),
            "active_wo": run.get("active_wo"),
            "started_at": run.get("started_at"),
            "last_heartbeat_at": run.get("last_heartbeat_at"),
            "last_checkpoint_at": run.get("last_checkpoint_at"),
            "last_audit_at": run.get("last_audit_at"),
        },
        "latest_heartbeat": {
            "path": str(latest_path.relative_to(project_dir)) if latest_path else None,
            "timestamp": latest.get("timestamp"),
            "status": latest.get("status"),
            "loop_iteration": latest.get("loop_iteration"),
            "next_action": latest.get("next_action"),
        },
        "commands": commands,
    }


def write_outputs(project_dir: Path, plan: dict[str, Any]) -> None:
    autonomy_dir = project_dir / ".vibeos/autonomy"
    write_json(autonomy_dir / "resume-plan.json", plan)
    state = {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "last_decision_at": plan["generated_at"],
        "last_action": plan["decision"]["action"],
        "last_reason": plan["decision"]["reason"],
        "run_id": plan["run"].get("run_id"),
        "resume_plan": ".vibeos/autonomy/resume-plan.json",
    }
    write_json(autonomy_dir / "supervisor-state.json", state)
    log_path = project_dir / ".vibeos/build-log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"[{plan['generated_at']}] autonomy-supervisor "
            f"{plan['decision']['action']} reason={plan['decision']['reason']}\n"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan the next VibeOS long-run autonomy action.")
    parser.add_argument("--project-dir", default="", help="Project root. Defaults to PROJECT_ROOT or cwd.")
    parser.add_argument("--now", default="", help="Override current time for tests, ISO-8601.")
    parser.add_argument("--json", action="store_true", help="Print the supervisor plan as JSON.")
    parser.add_argument("--no-write", action="store_true", help="Do not write resume-plan.json or supervisor-state.json.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = project_root(args.project_dir)
    plan = plan_action(root, now_from_arg(args.now))
    if not args.no_write:
        write_outputs(root, plan)
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print(f"[autonomy-supervisor] {plan['decision']['action']}: {plan['decision']['reason']}")
        print("[autonomy-supervisor] Resume plan: .vibeos/autonomy/resume-plan.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
