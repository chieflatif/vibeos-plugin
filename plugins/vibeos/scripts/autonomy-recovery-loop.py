#!/usr/bin/env python3
# FILE-SIZE-EXCEPTION: WO-122 — cohesive bounded recovery retry wrapper with state, history, and resolution-gate checks.
"""Run one bounded recovery retry for a VibeOS recovery plan."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.3.0"
RECOVERY_PLAN = ".vibeos/autonomy/recovery-plan.json"
RECOVERY_RESOLUTION = ".vibeos/autonomy/recovery-resolution.json"
RESUME_PLAN = ".vibeos/autonomy/resume-plan.json"
RECOVERY_LOOP_STATE = ".vibeos/autonomy/recovery-loop-state.json"
RECOVERY_LOOP_HISTORY = ".vibeos/autonomy/recovery-loop-history.jsonl"
OUTPUT_LIMIT = 4000


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def project_root(value: str) -> Path:
    if value:
        return Path(value).resolve()
    return Path(os.environ.get("PROJECT_ROOT", ".")).resolve()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def truncate(value: str) -> str:
    if len(value) <= OUTPUT_LIMIT:
        return value
    return value[:OUTPUT_LIMIT] + "\n[truncated]"


def runtime_script(root: Path, name: str) -> Path:
    installed = root / ".vibeos/scripts" / name
    if installed.exists():
        return installed
    return Path(__file__).resolve().parent / name


def parse_stdout_json(record: dict[str, Any]) -> dict[str, Any] | None:
    try:
        payload = json.loads(record.get("stdout") or "{}")
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def normalize_actions(recovery_plan: dict[str, Any]) -> list[dict[str, Any]]:
    actions = recovery_plan.get("actions", []) if isinstance(recovery_plan, dict) else []
    if not isinstance(actions, list):
        return []
    return [action for action in actions if isinstance(action, dict) and str(action.get("id") or "")]


def blocking_actions(recovery_plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [action for action in normalize_actions(recovery_plan) if action.get("requires_review", True)]


def normalize_resolutions(recovery_resolution: dict[str, Any]) -> list[dict[str, Any]]:
    values = recovery_resolution.get("resolutions", []) if isinstance(recovery_resolution, dict) else []
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, dict)]


def plan_generated_at(recovery_plan: dict[str, Any]) -> str:
    return str(recovery_plan.get("generated_at") or "")


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


def unresolved_actions(recovery_plan: dict[str, Any], recovery_resolution: dict[str, Any]) -> list[dict[str, Any]]:
    resolved = valid_resolution_ids(recovery_resolution, plan_generated_at(recovery_plan))
    return [action for action in blocking_actions(recovery_plan) if str(action.get("id") or "") not in resolved]


def action_ids(actions: list[dict[str, Any]]) -> list[str]:
    return sorted(str(action.get("id") or "") for action in actions if str(action.get("id") or ""))


def recovery_plan_key(recovery_plan: dict[str, Any]) -> str:
    generated_at = plan_generated_at(recovery_plan)
    ids = ",".join(action_ids(blocking_actions(recovery_plan)))
    return f"{generated_at}|{ids}"


def attempts_for_plan(state: dict[str, Any], plan_key: str) -> list[dict[str, Any]]:
    attempts = state.get("attempts", []) if isinstance(state, dict) else []
    if not isinstance(attempts, list):
        return []
    return [attempt for attempt in attempts if isinstance(attempt, dict) and attempt.get("recovery_plan_key") == plan_key]


def run_command(argv: list[str], root: Path, timeout_seconds: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(argv, cwd=root, capture_output=True, text=True, timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "exit_code": 124,
            "stdout": truncate(exc.stdout or ""),
            "stderr": truncate(exc.stderr or "command timed out"),
        }
    record = {
        "argv": argv,
        "exit_code": completed.returncode,
        "stdout": truncate(completed.stdout),
        "stderr": truncate(completed.stderr),
    }
    try:
        payload = json.loads(completed.stdout or "{}")
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict) and isinstance(payload.get("summary"), dict):
        record["stdout_summary"] = payload["summary"]
    return record


def runner_status(record: dict[str, Any]) -> str:
    summary = record.get("stdout_summary")
    if isinstance(summary, dict):
        return str(summary.get("status") or "failed")
    payload = parse_stdout_json(record)
    if not payload:
        return "failed"
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        return "failed"
    return str(summary.get("status") or "failed")


def build_report(root: Path, args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    recovery_plan = load_json(root / RECOVERY_PLAN, {})
    recovery_resolution = load_json(root / RECOVERY_RESOLUTION, {})
    state = load_json(root / RECOVERY_LOOP_STATE, {})
    generated_at = iso_now()
    resume_plan = Path(args.resume_plan) if args.resume_plan else root / RESUME_PLAN
    if not resume_plan.is_absolute():
        resume_plan = (root / resume_plan).resolve()

    unresolved = unresolved_actions(recovery_plan, recovery_resolution)
    plan_key = recovery_plan_key(recovery_plan) if recovery_plan else ""
    previous_attempts = attempts_for_plan(state, plan_key) if plan_key else []
    summary_status = "planned"
    exit_code = 0
    runner: dict[str, Any] | None = None
    attempt: dict[str, Any] | None = None

    if not recovery_plan:
        summary_status = "no_recovery_plan"
    elif not unresolved:
        summary_status = "resolved_no_retry_needed"
    elif previous_attempts:
        summary_status = "escalated_retry_already_attempted"
        exit_code = 2
    elif not resume_plan.exists():
        summary_status = "blocked_missing_resume_plan"
        exit_code = 2
    elif not args.execute:
        summary_status = "planned"
    else:
        runner_script = runtime_script(root, "autonomy-runner.py")
        runner = run_command(
            [
                "python3",
                str(runner_script),
                "--project-dir",
                str(root),
                "--resume-plan",
                str(resume_plan),
                "--execute",
                "--json",
                "--timeout-seconds",
                str(args.timeout_seconds),
            ],
            root,
            args.timeout_seconds,
        )
        status = runner_status(runner)
        failed = runner["exit_code"] != 0 or status in {"blocked", "failed"}
        summary_status = "retry_failed" if failed else "retry_completed"
        exit_code = 1 if failed else 0
        attempt = {
            "attempted_at": generated_at,
            "recovery_plan_key": plan_key,
            "recovery_plan_generated_at": plan_generated_at(recovery_plan),
            "action_ids": action_ids(unresolved),
            "resume_plan": str(resume_plan),
            "status": summary_status,
            "runner_exit_code": runner["exit_code"],
            "runner_summary_status": status,
        }

    attempts = state.get("attempts", []) if isinstance(state, dict) and isinstance(state.get("attempts"), list) else []
    if attempt is not None:
        attempts = [*attempts, attempt]

    report = {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": generated_at,
        "project_dir": str(root),
        "execute": args.execute,
        "inputs": {
            "recovery_plan": RECOVERY_PLAN,
            "recovery_plan_present": bool(recovery_plan),
            "recovery_plan_generated_at": plan_generated_at(recovery_plan),
            "recovery_plan_key": plan_key,
            "recovery_resolution": RECOVERY_RESOLUTION,
            "resume_plan": str(resume_plan),
            "state_file": RECOVERY_LOOP_STATE,
        },
        "unresolved_actions": unresolved,
        "previous_attempts": previous_attempts,
        "runner": runner,
        "attempts": attempts,
        "summary": {
            "status": summary_status,
            "attempt_count_for_plan": len(previous_attempts) + (1 if attempt else 0),
            "unresolved_count": len(unresolved),
            "resolution_required_to_unblock": bool(unresolved),
            "state_file": RECOVERY_LOOP_STATE,
        },
    }
    return report, exit_code


def print_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    summary = report["summary"]
    print(
        "[autonomy-recovery-loop] "
        f"{summary['status']}: unresolved={summary['unresolved_count']} "
        f"attempts={summary['attempt_count_for_plan']}"
    )
    print(f"[autonomy-recovery-loop] State: {RECOVERY_LOOP_STATE}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one bounded VibeOS recovery retry.")
    parser.add_argument("--project-dir", default="", help="Project root. Defaults to PROJECT_ROOT or cwd.")
    parser.add_argument("--resume-plan", default="", help="Resume plan path. Defaults to .vibeos/autonomy/resume-plan.json.")
    parser.add_argument("--execute", action="store_true", help="Execute the one allowed retry.")
    parser.add_argument("--timeout-seconds", type=int, default=180, help="Runner timeout.")
    parser.add_argument("--json", action="store_true", help="Print recovery-loop report JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = project_root(args.project_dir)
    report, exit_code = build_report(root, args)
    write_json(root / RECOVERY_LOOP_STATE, report)
    append_jsonl(root / RECOVERY_LOOP_HISTORY, {
        "generated_at": report["generated_at"],
        "status": report["summary"]["status"],
        "recovery_plan_key": report["inputs"]["recovery_plan_key"],
        "attempt_count_for_plan": report["summary"]["attempt_count_for_plan"],
    })
    print_report(report, args.json)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
