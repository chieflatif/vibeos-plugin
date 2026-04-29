#!/usr/bin/env python3
"""Safely classify and run VibeOS long-run autonomy resume plans."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.2.0"
ALLOWED_SCRIPTS = {
    "autonomy-heartbeat.py": {"python", "python3"},
    "autonomy-supervisor.py": {"python", "python3"},
    "validate-long-run-autonomy.py": {"python", "python3"},
    "detect-runtime-capabilities.sh": {"bash"},
    "gate-runner.sh": {"bash"},
}
HANDOFF_PREFIXES = (
    "continue with ",
    "ask ",
    "resume ",
    "delegate ",
    "run /",
    "invoke ",
)
UNSAFE_SHELL_TOKENS = {";", "&&", "||", "|", ">", ">>", "<", "<<"}
OUTPUT_LIMIT = 4000


def iso_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def project_root(value: str) -> Path:
    if value:
        return Path(value).resolve()
    return Path(os.environ.get("PROJECT_ROOT", ".")).resolve()


def read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    if not path.exists():
        return None, f"resume plan not found: {path}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"resume plan is invalid JSON: {exc}"
    if not isinstance(data, dict):
        return None, "resume plan root must be an object"
    return data, None


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def truncate(value: str) -> str:
    if len(value) <= OUTPUT_LIMIT:
        return value
    return value[:OUTPUT_LIMIT] + "\n[truncated]"


def looks_like_handoff(command: str) -> bool:
    normalized = " ".join(command.strip().lower().split())
    return any(normalized.startswith(prefix) for prefix in HANDOFF_PREFIXES)


def has_unsafe_shell_tokens(argv: list[str]) -> bool:
    return any(token in UNSAFE_SHELL_TOKENS or "$(" in token or "`" in token for token in argv)


def resolve_script(root: Path, token: str) -> Path:
    script_path = Path(token)
    if not script_path.is_absolute():
        script_path = root / script_path
    return script_path.resolve()


def classify_command(command: str, root: Path, index: int) -> dict[str, Any]:
    item: dict[str, Any] = {"index": index, "command": command}
    stripped = command.strip()
    if not stripped:
        item.update({"classification": "blocked", "reason": "empty command"})
        return item
    if looks_like_handoff(stripped):
        item.update(
            {
                "classification": "handoff_required",
                "reason": "model/runtime continuation instruction",
            }
        )
        return item

    try:
        argv = shlex.split(stripped)
    except ValueError as exc:
        item.update({"classification": "blocked", "reason": f"cannot parse command: {exc}"})
        return item

    if not argv:
        item.update({"classification": "blocked", "reason": "empty command"})
        return item
    if has_unsafe_shell_tokens(argv):
        item.update({"classification": "blocked", "reason": "shell control tokens are not allowed"})
        return item

    runner = Path(argv[0]).name
    if len(argv) < 2 or runner not in {"python", "python3", "bash"}:
        item.update(
            {
                "classification": "blocked",
                "reason": "command is not an allowlisted VibeOS script invocation",
            }
        )
        return item

    script = resolve_script(root, argv[1])
    scripts_dir = (root / ".vibeos/scripts").resolve()
    allowed_runners = ALLOWED_SCRIPTS.get(script.name)
    if not allowed_runners or runner not in allowed_runners:
        item.update({"classification": "blocked", "reason": f"script is not allowlisted for {runner}"})
        return item
    if scripts_dir != script.parent:
        item.update({"classification": "blocked", "reason": "script must be directly under .vibeos/scripts"})
        return item

    item.update(
        {
            "classification": "executable",
            "reason": "allowlisted local VibeOS command",
            "argv": argv,
            "script": str(script.relative_to(root)),
            "script_exists": script.exists(),
            "runner": runner,
        }
    )
    return item


def execute_item(item: dict[str, Any], root: Path, timeout_seconds: int) -> None:
    if item.get("classification") != "executable":
        item["status"] = "skipped"
        return
    if not item.get("script_exists"):
        item.update({"status": "failed", "exit_code": 127, "stderr": "allowlisted script is missing"})
        return
    try:
        completed = subprocess.run(
            item["argv"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        item.update(
            {
                "status": "failed",
                "exit_code": 124,
                "stdout": truncate(exc.stdout or ""),
                "stderr": truncate(exc.stderr or "command timed out"),
            }
        )
        return
    item.update(
        {
            "status": "passed" if completed.returncode == 0 else "failed",
            "exit_code": completed.returncode,
            "stdout": truncate(completed.stdout),
            "stderr": truncate(completed.stderr),
        }
    )


def summarize(items: list[dict[str, Any]], execute: bool) -> dict[str, Any]:
    counts = {
        "total": len(items),
        "executable": sum(1 for item in items if item["classification"] == "executable"),
        "handoff_required": sum(1 for item in items if item["classification"] == "handoff_required"),
        "blocked": sum(1 for item in items if item["classification"] == "blocked"),
        "executed": sum(1 for item in items if item.get("status") in {"passed", "failed"}),
        "failed": sum(1 for item in items if item.get("status") == "failed"),
    }
    status = "pass"
    if counts["blocked"]:
        status = "blocked"
    elif counts["failed"]:
        status = "failed"
    elif counts["handoff_required"]:
        status = "handoff_required"
    elif not execute and counts["executable"]:
        status = "dry_run"
    return {"status": status, **counts}


def append_build_log(root: Path, report: dict[str, Any]) -> None:
    log_path = root / ".vibeos/build-log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    summary = report["summary"]
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"[{report['generated_at']}] autonomy-runner status={summary['status']} "
            f"execute={str(report['execute']).lower()} blocked={summary['blocked']} "
            f"failed={summary['failed']} handoff={summary['handoff_required']}\n"
        )


def build_report(
    root: Path,
    resume_plan: Path,
    plan: dict[str, Any],
    execute: bool,
    timeout_seconds: int,
) -> dict[str, Any]:
    commands = plan.get("commands") or []
    if not isinstance(commands, list):
        commands = []
    items = [classify_command(str(command), root, index) for index, command in enumerate(commands)]
    if execute:
        for item in items:
            execute_item(item, root, timeout_seconds)
    else:
        for item in items:
            if item["classification"] == "executable":
                item["status"] = "dry_run"
            else:
                item["status"] = "skipped"
    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": iso_now(),
        "project_dir": str(root),
        "resume_plan": str(resume_plan),
        "execute": execute,
        "decision": plan.get("decision", {}),
        "next_resume_after": (plan.get("decision") or {}).get("next_resume_after"),
        "items": items,
        "summary": summarize(items, execute),
    }


def error_report(root: Path, resume_plan: Path, message: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": iso_now(),
        "project_dir": str(root),
        "resume_plan": str(resume_plan),
        "execute": False,
        "items": [],
        "summary": {
            "status": "blocked",
            "total": 0,
            "blocked": 1,
            "failed": 0,
            "handoff_required": 0,
        },
        "error": message,
    }


def print_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    summary = report["summary"]
    print(
        "[autonomy-runner] "
        f"{summary['status']}: executable={summary.get('executable', 0)} "
        f"blocked={summary.get('blocked', 0)} failed={summary.get('failed', 0)} "
        f"handoff={summary.get('handoff_required', 0)}"
    )
    print("[autonomy-runner] Report: .vibeos/autonomy/runner-report.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely classify and run VibeOS autonomy resume plans.")
    parser.add_argument("--project-dir", default="", help="Project root. Defaults to PROJECT_ROOT or cwd.")
    parser.add_argument(
        "--resume-plan",
        default="",
        help="Path to resume-plan.json. Defaults to .vibeos/autonomy/resume-plan.json.",
    )
    parser.add_argument("--execute", action="store_true", help="Execute only allowlisted local VibeOS commands.")
    parser.add_argument("--json", action="store_true", help="Print runner report JSON.")
    parser.add_argument("--timeout-seconds", type=int, default=180, help="Per-command execution timeout.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = project_root(args.project_dir)
    resume_plan = Path(args.resume_plan) if args.resume_plan else root / ".vibeos/autonomy/resume-plan.json"
    if not resume_plan.is_absolute():
        resume_plan = (root / resume_plan).resolve()

    plan, error = read_json(resume_plan)
    if error:
        report = error_report(root, resume_plan, error)
    else:
        report = build_report(root, resume_plan, plan or {}, args.execute, args.timeout_seconds)

    write_json(root / ".vibeos/autonomy/runner-report.json", report)
    append_build_log(root, report)
    print_report(report, args.json)

    summary = report["summary"]
    if summary["status"] == "blocked":
        return 2
    if args.execute and summary.get("failed", 0):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
