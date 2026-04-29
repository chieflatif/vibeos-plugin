#!/usr/bin/env python3
"""Run one or more scheduler-safe VibeOS long-run autonomy loop ticks."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from autonomy_lease import AutonomyLease, LeaseConflict, conflict_path, conflict_report


FRAMEWORK_VERSION = "2.2.0"
OUTPUT_LIMIT = 4000
RECOVERY_PLAN = ".vibeos/autonomy/recovery-plan.json"
RECOVERY_RESOLUTION = ".vibeos/autonomy/recovery-resolution.json"


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


def project_root(value: str) -> Path:
    if value:
        return Path(value).resolve()
    return Path(os.environ.get("PROJECT_ROOT", ".")).resolve()


def truncate(value: str) -> str:
    if len(value) <= OUTPUT_LIMIT:
        return value
    return value[:OUTPUT_LIMIT] + "\n[truncated]"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True) + "\n")


def history_entry(state: dict[str, Any]) -> dict[str, Any]:
    latest = state.get("iterations", [{}])[-1] if state.get("iterations") else {}
    decision = latest.get("decision") or {}
    return {
        "generated_at": state.get("generated_at"),
        "status": state.get("summary", {}).get("status"),
        "next_resume_after": state.get("summary", {}).get("next_resume_after"),
        "decision_action": decision.get("action"),
        "decision_reason": decision.get("reason"),
        "runner_summary": latest.get("runner_summary", {}),
    }


def recovery_summary(root: Path) -> dict[str, Any]:
    plan = load_json(root / RECOVERY_PLAN, {})
    summary = plan.get("summary") if isinstance(plan, dict) else {}
    return summary if isinstance(summary, dict) else {}


def plan_generated_at(recovery_plan: dict[str, Any]) -> str:
    return str(recovery_plan.get("generated_at") or "")


def blocking_actions(recovery_plan: dict[str, Any]) -> list[dict[str, Any]]:
    actions = recovery_plan.get("actions", [])
    if not isinstance(actions, list):
        return []
    return [
        action
        for action in actions
        if isinstance(action, dict)
        and str(action.get("id") or "")
        and action.get("requires_review", True)
    ]


def normalize_resolutions(recovery_resolution: dict[str, Any]) -> list[dict[str, Any]]:
    values = recovery_resolution.get("resolutions", []) if isinstance(recovery_resolution, dict) else []
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, dict)]


def valid_resolution_ids(recovery_resolution: dict[str, Any], generated_at: str) -> set[str]:
    resolved: set[str] = set()
    for resolution in normalize_resolutions(recovery_resolution):
        action_id = str(resolution.get("action_id") or "")
        if not action_id:
            continue
        if str(resolution.get("recovery_plan_generated_at") or "") != generated_at:
            continue
        if not str(resolution.get("summary") or "").strip():
            continue
        evidence = resolution.get("evidence", [])
        if not isinstance(evidence, list) or not any(str(item).strip() for item in evidence):
            continue
        resolved.add(action_id)
    return resolved


def unresolved_actions(
    recovery_plan: dict[str, Any],
    recovery_resolution: dict[str, Any],
) -> list[dict[str, Any]]:
    resolved = valid_resolution_ids(recovery_resolution, plan_generated_at(recovery_plan))
    return [action for action in blocking_actions(recovery_plan) if str(action.get("id") or "") not in resolved]


def legacy_block_without_actions(recovery_plan: dict[str, Any]) -> bool:
    summary = recovery_plan.get("summary") if isinstance(recovery_plan, dict) else {}
    summary = summary if isinstance(summary, dict) else {}
    if blocking_actions(recovery_plan):
        return False
    if summary.get("status") == "recovery_required":
        return True
    if summary.get("stop_scheduler_until_resolved"):
        return True
    return int(summary.get("blocking_action_count") or 0) > 0


def recovery_blocks_scheduler(root: Path) -> bool:
    recovery_plan = load_json(root / RECOVERY_PLAN, {})
    recovery_resolution = load_json(root / RECOVERY_RESOLUTION, {})
    return bool(unresolved_actions(recovery_plan, recovery_resolution)) or legacy_block_without_actions(
        recovery_plan
    )


def scheduler_guard_state(root: Path) -> dict[str, Any]:
    recovery_plan = load_json(root / RECOVERY_PLAN, {})
    recovery_resolution = load_json(root / RECOVERY_RESOLUTION, {})
    summary = recovery_summary(root)
    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": iso_now(),
        "project_dir": str(root),
        "execute": False,
        "iterations": [],
        "summary": {
            "status": "scheduler_guard_blocked",
            "iterations": 0,
            "next_resume_after": None,
            "state_file": ".vibeos/autonomy/loop-state.json",
            "reason": "recovery plan has unresolved blocking actions",
        },
        "guard": {
            "recovery_plan": RECOVERY_PLAN,
            "recovery_resolution": RECOVERY_RESOLUTION,
            "recovery_summary": summary,
            "recovery_plan_generated_at": plan_generated_at(recovery_plan),
            "unresolved_actions": unresolved_actions(recovery_plan, recovery_resolution),
            "resolved_action_ids": sorted(
                valid_resolution_ids(recovery_resolution, plan_generated_at(recovery_plan))
            ),
        },
    }


def append_build_log(root: Path, state: dict[str, Any]) -> None:
    log_path = root / ".vibeos/build-log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    summary = state["summary"]
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"[{state['generated_at']}] autonomy-loop status={summary['status']} "
            f"iterations={summary['iterations']} execute={str(state['execute']).lower()} "
            f"next_resume_after={summary.get('next_resume_after') or 'none'}\n"
        )


def run_command(argv: list[str], root: Path, timeout_seconds: int) -> dict[str, Any]:
    record: dict[str, Any] = {"argv": argv}
    try:
        completed = subprocess.run(
            argv,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        record.update(
            {
                "exit_code": 124,
                "stdout": truncate(exc.stdout or ""),
                "stderr": truncate(exc.stderr or "command timed out"),
            }
        )
        return record
    record.update(
        {
            "exit_code": completed.returncode,
            "stdout": truncate(completed.stdout),
            "stderr": truncate(completed.stderr),
        }
    )
    return record


def parse_stdout_json(record: dict[str, Any]) -> dict[str, Any] | None:
    try:
        data = json.loads(record.get("stdout") or "{}")
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def supervisor_args(root: Path, now: str) -> list[str]:
    args = [
        "python3",
        str(root / ".vibeos/scripts/autonomy-supervisor.py"),
        "--project-dir",
        str(root),
        "--json",
    ]
    if now:
        args.extend(["--now", now])
    return args


def runner_args(root: Path, execute: bool) -> list[str]:
    args = [
        "python3",
        str(root / ".vibeos/scripts/autonomy-runner.py"),
        "--project-dir",
        str(root),
        "--json",
    ]
    if execute:
        args.append("--execute")
    return args


def future_resume(next_resume_after: str | None, now: datetime) -> bool:
    if not next_resume_after:
        return False
    try:
        return parse_iso(next_resume_after) > now
    except ValueError:
        return False


def sleep_until(next_resume_after: str | None, max_sleep_seconds: int) -> None:
    if not next_resume_after:
        return
    delay = max(0.0, (parse_iso(next_resume_after) - datetime.now(timezone.utc)).total_seconds())
    time.sleep(min(delay, float(max_sleep_seconds)))


def loop_once(root: Path, args: argparse.Namespace, iteration: int) -> dict[str, Any]:
    supervisor = run_command(supervisor_args(root, args.now), root, args.timeout_seconds)
    supervisor_payload = parse_stdout_json(supervisor)
    record: dict[str, Any] = {"iteration": iteration, "supervisor": supervisor}
    if supervisor["exit_code"] != 0 or supervisor_payload is None:
        record["status"] = "failed"
        record["reason"] = "supervisor failed or did not emit JSON"
        return record

    runner = run_command(runner_args(root, args.execute), root, args.timeout_seconds)
    runner_payload = parse_stdout_json(runner)
    record.update({"runner": runner, "decision": supervisor_payload.get("decision", {})})
    if runner_payload is not None:
        record["runner_summary"] = runner_payload.get("summary", {})
    if runner["exit_code"] == 2:
        record["status"] = "blocked"
        record["reason"] = "runner blocked unsafe resume-plan command"
        return record
    if runner["exit_code"] != 0 or runner_payload is None:
        record["status"] = "failed"
        record["reason"] = "runner failed or did not emit JSON"
        return record

    action = (supervisor_payload.get("decision") or {}).get("action")
    runner_summary = runner_payload.get("summary", {})
    if action in {"stop", "closed", "not_configured"}:
        record["status"] = str(action)
    elif runner_summary.get("handoff_required", 0):
        record["status"] = "handoff_required"
    else:
        record["status"] = "ready"
    record["next_resume_after"] = (supervisor_payload.get("decision") or {}).get("next_resume_after")
    return record


def build_state(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    iterations: list[dict[str, Any]] = []
    status = "iteration_limit"
    next_resume_after = None
    for iteration in range(1, args.max_iterations + 1):
        record = loop_once(root, args, iteration)
        iterations.append(record)
        status = record["status"]
        next_resume_after = record.get("next_resume_after")
        if status != "ready":
            break
        now = parse_iso(args.now) if args.now else datetime.now(timezone.utc)
        if future_resume(next_resume_after, now):
            if not args.sleep:
                status = "scheduled"
                break
            sleep_until(next_resume_after, args.max_sleep_seconds)
    if status == "ready":
        status = "iteration_limit"

    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": iso_now(),
        "project_dir": str(root),
        "execute": args.execute,
        "iterations": iterations,
        "summary": {
            "status": status,
            "iterations": len(iterations),
            "next_resume_after": next_resume_after,
            "state_file": ".vibeos/autonomy/loop-state.json",
        },
    }


def print_state(state: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(state, indent=2, sort_keys=True))
        return
    summary = state["summary"]
    print(
        "[autonomy-loop] "
        f"{summary['status']}: iterations={summary.get('iterations', 0)} "
        f"next_resume_after={summary.get('next_resume_after') or 'none'}"
    )
    print("[autonomy-loop] State: .vibeos/autonomy/loop-state.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run VibeOS long-run autonomy loop ticks.")
    parser.add_argument("--project-dir", default="", help="Project root. Defaults to PROJECT_ROOT or cwd.")
    parser.add_argument("--execute", action="store_true", help="Let autonomy-runner execute allowlisted commands.")
    parser.add_argument("--max-iterations", type=int, default=1, help="Maximum loop ticks to run before returning.")
    parser.add_argument("--sleep", action="store_true", help="Sleep until next_resume_after between loop ticks.")
    parser.add_argument("--max-sleep-seconds", type=int, default=900, help="Maximum sleep between loop ticks.")
    parser.add_argument("--timeout-seconds", type=int, default=240, help="Per supervisor/runner command timeout.")
    parser.add_argument("--lease-owner", default="", help="Optional owner label for the autonomy run lease.")
    parser.add_argument("--lease-ttl-seconds", type=int, default=1800, help="Lease TTL for this loop driver.")
    parser.add_argument("--ignore-scheduler-guard", action="store_true", help="Bypass recovery-plan guard.")
    parser.add_argument("--now", default="", help="Override supervisor time for deterministic tests.")
    parser.add_argument("--json", action="store_true", help="Print loop state JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = project_root(args.project_dir)
    if not args.ignore_scheduler_guard and recovery_blocks_scheduler(root):
        state = scheduler_guard_state(root)
        write_json(root / ".vibeos/autonomy/loop-state.json", state)
        append_jsonl(root / ".vibeos/autonomy/loop-history.jsonl", history_entry(state))
        append_build_log(root, state)
        print_state(state, args.json)
        return 2
    try:
        with AutonomyLease(root, "autonomy-loop", args.lease_ttl_seconds, args.lease_owner) as lease:
            state = build_state(root, args)
            state["lease"] = lease.report()
            write_json(root / ".vibeos/autonomy/loop-state.json", state)
            append_jsonl(root / ".vibeos/autonomy/loop-history.jsonl", history_entry(state))
            append_build_log(root, state)
    except LeaseConflict as exc:
        state = conflict_report(root, "autonomy-loop", exc)
        write_json(conflict_path(root), state)
        append_jsonl(root / ".vibeos/autonomy/loop-history.jsonl", history_entry(state))
        print_state(state, args.json)
        return 2

    print_state(state, args.json)

    status = state["summary"]["status"]
    if status in {"blocked", "lease_conflict"}:
        return 2
    if status == "failed":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
