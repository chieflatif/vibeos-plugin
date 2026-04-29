#!/usr/bin/env python3
"""Plan or launch a Codex/Claude runtime handoff from VibeOS autonomy state."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from autonomy_lease import AutonomyLease, LeaseConflict, conflict_path, conflict_report


FRAMEWORK_VERSION = "2.2.0"
OUTPUT_LIMIT = 12000


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


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True) + "\n")


def history_entry(report: dict[str, Any]) -> dict[str, Any]:
    execution = report.get("execution") or {}
    summary = report.get("summary", {})
    return {
        "generated_at": report.get("generated_at"),
        "status": summary.get("status"),
        "provider": summary.get("provider"),
        "handoff": summary.get("handoff"),
        "exit_code": execution.get("exit_code"),
        "stderr": execution.get("stderr", ""),
        "stdout": execution.get("stdout", ""),
    }


def truncate(value: str) -> str:
    if len(value) <= OUTPUT_LIMIT:
        return value
    return value[:OUTPUT_LIMIT] + "\n[truncated]"


def has_handoff(loop_state: dict[str, Any], runner_report: dict[str, Any]) -> bool:
    if loop_state.get("summary", {}).get("status") == "handoff_required":
        return True
    return bool(runner_report.get("summary", {}).get("handoff_required", 0))


def runtime_available(matrix: dict[str, Any], provider: str) -> bool:
    runtime = matrix.get("runtimes", {}).get(provider, {})
    if runtime.get("available") is True:
        return True
    return bool(shutil.which(provider))


def select_provider(matrix: dict[str, Any], requested: str) -> str:
    if requested != "auto":
        return requested
    recommended = matrix.get("strategy", {}).get("recommended_primary")
    if recommended in {"codex", "claude"} and runtime_available(matrix, recommended):
        return recommended
    for provider in ("codex", "claude"):
        if runtime_available(matrix, provider):
            return provider
    return "unavailable"


def build_prompt(root: Path, role: str) -> str:
    if role == "audit":
        action = "run the VibeOS session-audit flow and report unresolved risks"
    else:
        action = "continue with the next eligible Work Order using the VibeOS build flow"
    return "\n".join(
        [
            "You are resuming a VibeOS Comp long-run autonomous session.",
            f"Project root: {root}",
            "",
            "Read these files first if they exist:",
            "- AGENTS.md",
            "- .vibeos/autonomy/loop-state.json",
            "- .vibeos/autonomy/resume-plan.json",
            "- .vibeos/autonomy/runner-report.json",
            "- .vibeos/session-state.json",
            "- docs/planning/WO-INDEX.md",
            "",
            f"Task: {action}.",
            "Use heartbeats, checkpoints, gates, and truthful partial states.",
            "Do not claim completion without evidence. Stop for real blockers.",
        ]
    )


def provider_command(provider: str, root: Path) -> list[str]:
    if provider == "codex":
        return [
            "codex",
            "exec",
            "--cd",
            str(root),
            "--sandbox",
            "workspace-write",
            "--ask-for-approval",
            "never",
            "--json",
            "-",
        ]
    if provider == "claude":
        return [
            "claude",
            "--print",
            "--output-format",
            "stream-json",
            "--permission-mode",
            "auto",
            "--add-dir",
            str(root),
        ]
    return []


def execute_command(argv: list[str], prompt: str, root: Path, timeout_seconds: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            argv,
            input=prompt,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "exit_code": 124,
            "stdout": truncate(exc.stdout or ""),
            "stderr": truncate(exc.stderr or "runtime command timed out"),
        }
    return {
        "exit_code": completed.returncode,
        "stdout": truncate(completed.stdout),
        "stderr": truncate(completed.stderr),
    }


def append_build_log(root: Path, report: dict[str, Any]) -> None:
    log_path = root / ".vibeos/build-log.md"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    summary = report["summary"]
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"[{report['generated_at']}] autonomy-runtime-adapter "
            f"status={summary['status']} provider={summary.get('provider') or 'none'} "
            f"execute={str(report['execute']).lower()}\n"
        )


def build_report(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    matrix = load_json(root / ".vibeos/runtime-capabilities.json", {})
    loop_state = load_json(root / ".vibeos/autonomy/loop-state.json", {})
    runner_report = load_json(root / ".vibeos/autonomy/runner-report.json", {})
    handoff = has_handoff(loop_state, runner_report)
    provider = select_provider(matrix, args.provider)
    prompt = build_prompt(root, args.role)
    argv = provider_command(provider, root)
    status = "ready"
    reason = "handoff command planned"

    if not handoff and not args.force:
        status = "no_handoff"
        reason = "latest autonomy state does not require a runtime handoff"
    elif provider == "unavailable" or not argv:
        status = "runtime_unavailable"
        reason = "no supported local Codex or Claude runtime was detected"

    report: dict[str, Any] = {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": iso_now(),
        "project_dir": str(root),
        "execute": args.execute,
        "prompt": prompt,
        "command": {"provider": provider, "argv": argv, "stdin_prompt": True},
        "inputs": {
            "loop_state": ".vibeos/autonomy/loop-state.json",
            "runner_report": ".vibeos/autonomy/runner-report.json",
            "runtime_capabilities": ".vibeos/runtime-capabilities.json",
        },
        "summary": {"status": status, "reason": reason, "provider": provider, "handoff": handoff},
    }
    if args.execute and status == "ready":
        execution = execute_command(argv, prompt, root, args.timeout_seconds)
        report["execution"] = execution
        report["summary"]["status"] = "passed" if execution["exit_code"] == 0 else "failed"
    return report


def print_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    summary = report["summary"]
    print(
        "[autonomy-runtime-adapter] "
        f"{summary['status']}: provider={summary.get('provider') or 'none'} "
        f"reason={summary['reason']}"
    )
    print("[autonomy-runtime-adapter] Plan: .vibeos/autonomy/runtime-adapter-plan.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan or launch a VibeOS runtime handoff.")
    parser.add_argument("--project-dir", default="", help="Project root. Defaults to PROJECT_ROOT or cwd.")
    parser.add_argument("--provider", default="auto", choices=["auto", "codex", "claude"], help="Runtime provider.")
    parser.add_argument("--role", default="build", choices=["build", "audit"], help="Resume task role.")
    parser.add_argument("--force", action="store_true", help="Build a handoff plan even without handoff state.")
    parser.add_argument("--execute", action="store_true", help="Launch the selected runtime command.")
    parser.add_argument("--timeout-seconds", type=int, default=3600, help="Runtime execution timeout.")
    parser.add_argument("--lease-owner", default="", help="Optional owner label for the autonomy run lease.")
    parser.add_argument("--lease-ttl-seconds", type=int, default=21600, help="Lease TTL for runtime handoff.")
    parser.add_argument("--json", action="store_true", help="Print adapter plan JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = project_root(args.project_dir)
    try:
        with AutonomyLease(root, "autonomy-runtime-adapter", args.lease_ttl_seconds, args.lease_owner) as lease:
            report = build_report(root, args)
            report["lease"] = lease.report()
            write_json(root / ".vibeos/autonomy/runtime-adapter-plan.json", report)
            append_jsonl(root / ".vibeos/autonomy/runtime-adapter-history.jsonl", history_entry(report))
            append_build_log(root, report)
    except LeaseConflict as exc:
        report = conflict_report(root, "autonomy-runtime-adapter", exc)
        write_json(conflict_path(root), report)
        append_jsonl(root / ".vibeos/autonomy/runtime-adapter-history.jsonl", history_entry(report))
        print_report(report, args.json)
        return 2

    print_report(report, args.json)

    status = report["summary"]["status"]
    if status == "lease_conflict":
        return 2
    if status in {"runtime_unavailable", "failed"}:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
