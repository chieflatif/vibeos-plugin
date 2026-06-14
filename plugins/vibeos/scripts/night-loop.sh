#!/usr/bin/env bash
# VibeOS Plugin — Night Loop Wrapper
# Dry-run-first wrapper for scheduled headless Claude ticks.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export VIBEOS_SCRIPT_DIR="$SCRIPT_DIR"

python3 - "$@" <<'PY'
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


FRAMEWORK_VERSION = "2.2.0"
DEFAULT_ALLOWED_TOOLS = ["Bash", "Read", "Grep", "Glob"]
COST_LABEL = "estimate; reconcile against billing"


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def run_command(argv: list[str], cwd: Path, timeout_seconds: int) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "argv": argv,
            "exit_code": 124,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "command timed out",
        }
    return {
        "argv": argv,
        "exit_code": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def parse_stdout_json(record: dict[str, Any]) -> dict[str, Any] | None:
    try:
        payload = json.loads(record.get("stdout") or "{}")
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def script_path(root: Path, framework_dir: Path | None, name: str) -> Path:
    script_dir = Path(os.environ["VIBEOS_SCRIPT_DIR"]).resolve()
    candidates = [
        root / ".vibeos/scripts" / name,
        script_dir / name,
    ]
    if framework_dir:
        candidates.append(framework_dir / "scripts" / name)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]


def sdk_credit_confirmed(root: Path) -> bool:
    if os.environ.get("VIBEOS_AGENT_SDK_CREDIT_CONFIRMED") == "1":
        return True
    config = load_json(root / ".vibeos/config.json", {})
    if not isinstance(config, dict):
        return False
    return bool(
        ((config.get("decisions") or {}).get("agent_sdk_credit_confirmed"))
        or ((config.get("autonomy") or {}).get("agent_sdk_credit_confirmed"))
        or config.get("agent_sdk_credit_confirmed")
    )


def claude_command(prompt: str, allowed_tools: list[str]) -> list[str]:
    return [
        "claude",
        "-p",
        prompt,
        "--bare",
        "--output-format",
        "json",
        "--allowedTools",
        ",".join(allowed_tools),
    ]


def base_report(root: Path, evidence_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": iso_now(),
        "project_dir": str(root),
        "evidence_dir": str(evidence_dir),
        "execute": args.execute,
        "timeout_seconds": args.timeout_seconds,
        "allowed_tools": args.allow_tool or DEFAULT_ALLOWED_TOOLS,
        "d3_agent_sdk_credit_confirmed": sdk_credit_confirmed(root),
        "steps": [],
        "summary": {
            "status": "initializing",
            "live_headless_run": False,
            "cost_label": COST_LABEL,
        },
    }


def add_step(report: dict[str, Any], name: str, status: str, **extra: Any) -> None:
    step = {"name": name, "status": status}
    step.update(extra)
    report["steps"].append(step)


def write_and_print(report: dict[str, Any], out_path: Path, as_json: bool) -> None:
    write_json(out_path, report)
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"[night-loop] {report['summary']['status']}: report={out_path}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run or plan a VibeOS night-loop tick.")
    parser.add_argument("--project-dir", default=".", help="Target project root.")
    parser.add_argument("--framework-dir", default="", help="VibeOS framework root containing scripts/.")
    parser.add_argument("--evidence-dir", default="", help="Evidence output directory.")
    parser.add_argument("--execute", action="store_true", help="Run live headless Claude and tick commands.")
    parser.add_argument("--prompt", default="Run one VibeOS night-loop tick and return JSON evidence.", help="Headless Claude prompt.")
    parser.add_argument("--timeout-seconds", type=int, default=900, help="Runtime ceiling per command.")
    parser.add_argument("--allow-tool", action="append", default=[], help="Allowed Claude tool name. Repeatable.")
    parser.add_argument("--headless-json", default="", help="Existing headless JSON to capture cost from.")
    parser.add_argument("--json", action="store_true", help="Print report JSON.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.project_dir).resolve()
    framework_dir = Path(args.framework_dir).resolve() if args.framework_dir else None
    evidence_dir = Path(args.evidence_dir).resolve() if args.evidence_dir else root / ".vibeos/evidence/night-loop"
    report_path = evidence_dir / "night-loop-report.json"
    report = base_report(root, evidence_dir, args)

    guard_script = script_path(root, framework_dir, "autonomy-scheduler-guard.py")
    guard = run_command(["python3", str(guard_script), "--project-dir", str(root), "--json"], root, args.timeout_seconds)
    add_step(report, "scheduler_guard", "pass" if guard["exit_code"] == 0 else "blocked", command=guard["argv"], exit_code=guard["exit_code"])
    if guard["exit_code"] != 0:
        report["summary"].update({"status": "scheduler_guard_blocked", "blocking_step": "scheduler_guard"})
        write_and_print(report, report_path, args.json)
        return 2

    if args.execute and not sdk_credit_confirmed(root):
        add_step(
            report,
            "agent_sdk_credit",
            "blocked",
            reason="Decision D-3 is open; set VIBEOS_AGENT_SDK_CREDIT_CONFIRMED=1 or .vibeos/config.json decisions.agent_sdk_credit_confirmed=true before live scheduled headless runs.",
        )
        report["summary"].update({"status": "blocked_agent_sdk_credit_required", "live_headless_run": False})
        write_and_print(report, report_path, args.json)
        return 2

    allowed_tools = args.allow_tool or DEFAULT_ALLOWED_TOOLS
    planned_claude = claude_command(args.prompt, allowed_tools)
    add_step(report, "claude_headless", "planned" if not args.execute else "pending", command=planned_claude)
    add_step(
        report,
        "autonomy_loop",
        "planned" if not args.execute else "pending",
        command=["python3", str(script_path(root, framework_dir, "autonomy-loop.py")), "--project-dir", str(root), "--max-iterations", "1", "--json"],
    )
    add_step(
        report,
        "full_audit_gate",
        "planned" if not args.execute else "pending",
        command=["bash", str(script_path(root, framework_dir, "gate-runner.sh")), "full_audit", "--continue-on-failure", "--project-dir", str(root)],
    )
    add_step(report, "drift_sweep", "planned", command=["python3", str(script_path(root, framework_dir, "wo-frontmatter-lint.py")), "validate-index", "--project-dir", str(root)])
    add_step(report, "waiver_check", "deferred_until_WO-127", reason="Waiver-expiry scan is planned in WO-127.")

    if args.headless_json:
        cost_script = script_path(root, framework_dir, "capture-headless-cost.py")
        cost = run_command(
            ["python3", str(cost_script), "--input", str(Path(args.headless_json).resolve()), "--evidence-dir", str(evidence_dir)],
            root,
            args.timeout_seconds,
        )
        add_step(report, "cost_capture", "pass" if cost["exit_code"] == 0 else "failed", command=cost["argv"], exit_code=cost["exit_code"])
        if cost["exit_code"] != 0:
            report["summary"].update({"status": "cost_capture_failed"})
            write_and_print(report, report_path, args.json)
            return 1
    else:
        add_step(report, "cost_capture", "not_run", reason="No headless JSON was supplied or produced.")

    if not args.execute:
        report["summary"].update({"status": "dry_run", "live_headless_run": False})
        write_and_print(report, report_path, args.json)
        return 0

    if shutil.which("claude") is None:
        report["summary"].update({"status": "failed_claude_not_found", "live_headless_run": False})
        write_and_print(report, report_path, args.json)
        return 1

    # Live execution is intentionally after guard + D-3 confirmation.
    headless_output = evidence_dir / "headless-output.json"
    claude = run_command(planned_claude, root, args.timeout_seconds)
    headless_output.write_text(claude["stdout"], encoding="utf-8")
    report["steps"] = [step if step["name"] != "claude_headless" else {**step, "status": "pass" if claude["exit_code"] == 0 else "failed", "exit_code": claude["exit_code"], "output": str(headless_output)} for step in report["steps"]]
    if claude["exit_code"] != 0:
        report["summary"].update({"status": "failed_claude_headless", "live_headless_run": True})
        write_and_print(report, report_path, args.json)
        return 1

    cost_script = script_path(root, framework_dir, "capture-headless-cost.py")
    cost = run_command(["python3", str(cost_script), "--input", str(headless_output), "--evidence-dir", str(evidence_dir)], root, args.timeout_seconds)
    add_step(report, "live_cost_capture", "pass" if cost["exit_code"] == 0 else "failed", command=cost["argv"], exit_code=cost["exit_code"])
    if cost["exit_code"] != 0:
        report["summary"].update({"status": "cost_capture_failed", "live_headless_run": True})
        write_and_print(report, report_path, args.json)
        return 1

    loop_script = script_path(root, framework_dir, "autonomy-loop.py")
    loop = run_command(["python3", str(loop_script), "--project-dir", str(root), "--max-iterations", "1", "--json"], root, args.timeout_seconds)
    add_step(report, "live_autonomy_loop", "pass" if loop["exit_code"] == 0 else "failed", command=loop["argv"], exit_code=loop["exit_code"])
    report["summary"].update({"status": "pass" if loop["exit_code"] == 0 else "failed_autonomy_loop", "live_headless_run": True})
    write_and_print(report, report_path, args.json)
    return 0 if loop["exit_code"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
PY
