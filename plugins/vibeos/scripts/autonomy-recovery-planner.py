#!/usr/bin/env python3
"""Plan safe recovery actions for VibeOS long-run autonomy failures."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.2.0"
FAILURE_REPORT = ".vibeos/autonomy/failure-report.json"
RECOVERY_PLAN = ".vibeos/autonomy/recovery-plan.json"


ACTION_TEMPLATES: dict[str, dict[str, Any]] = {
    "AUTONOMY-REPEATED-HANDOFF": {
        "id": "RECOVERY-RUNTIME-HANDOFF",
        "category": "handoff",
        "severity": "high",
        "title": "Resume the model handoff path",
        "reason": "Scheduler ticks are repeatedly reaching a model handoff boundary without runtime pickup.",
        "stop_scheduler_until_resolved": True,
        "commands": [
            'python3 ".vibeos/scripts/autonomy-runtime-adapter.py" --project-dir "." --json',
        ],
        "manual_checks": [
            "Confirm the adapter plan targets the intended provider before using --execute.",
            "Verify the next Work Order remains the correct objective before launching another runtime.",
        ],
    },
    "AUTONOMY-REPEATED-DECISION": {
        "id": "RECOVERY-INSPECT-NO-PROGRESS-DECISION",
        "category": "no_progress",
        "severity": "high",
        "title": "Inspect the repeated supervisor decision",
        "reason": "The supervisor is producing the same no-progress decision across repeated loop ticks.",
        "stop_scheduler_until_resolved": True,
        "commands": [
            'python3 ".vibeos/scripts/autonomy-supervisor.py" --project-dir "." --json',
            'python3 ".vibeos/scripts/autonomy-runner.py" --project-dir "." --json',
        ],
        "manual_checks": [
            "Read .vibeos/autonomy/resume-plan.json and confirm the active Work Order is still actionable.",
            "If the plan is stale, update the Work Order evidence before another scheduler tick.",
        ],
    },
    "AUTONOMY-CONSECUTIVE-FAILURES": {
        "id": "RECOVERY-PAUSE-FAILURE-LOOP",
        "category": "failure_loop",
        "severity": "critical",
        "title": "Pause the scheduler and audit the failure loop",
        "reason": "Multiple control-plane attempts failed consecutively.",
        "stop_scheduler_until_resolved": True,
        "commands": [
            'python3 ".vibeos/scripts/autonomy-heartbeat.py" --status blocked '
            '--summary "autonomy control-plane failure loop" --blocker "repeated_no_progress_loop" '
            '--next-action "session audit"',
            'bash ".vibeos/scripts/gate-runner.sh" session_end --continue-on-failure --project-dir "."',
        ],
        "manual_checks": [
            "Inspect loop-state, runner-report, runtime-adapter-plan, and failure-report together.",
            "Do not schedule another tick until the repeated failure source has changed.",
        ],
    },
    "AUTONOMY-LEASE-CONFLICTS": {
        "id": "RECOVERY-RESOLVE-LEASE-CONFLICT",
        "category": "concurrency",
        "severity": "high",
        "title": "Resolve the active autonomy lease conflict",
        "reason": "Another driver appears to own the long-run autonomy lease.",
        "stop_scheduler_until_resolved": True,
        "commands": [],
        "manual_checks": [
            "Inspect .vibeos/autonomy/run-lease.json and confirm whether the owning driver is still alive.",
            "Only clear a lease when it is expired or the owner is proven dead.",
        ],
    },
    "AUTONOMY-RUNNER-BLOCKED": {
        "id": "RECOVERY-REPAIR-RUNNER-PLAN",
        "category": "runner",
        "severity": "high",
        "title": "Repair the blocked or failed resume plan",
        "reason": "The runner blocked or failed the latest resume-plan command.",
        "stop_scheduler_until_resolved": True,
        "commands": [
            'python3 ".vibeos/scripts/autonomy-runner.py" --project-dir "." --json',
        ],
        "manual_checks": [
            "Review the blocked command and decide whether the Work Order, resume plan, or allowlist is wrong.",
            "Do not expand the runner allowlist without an evidence-backed Work Order.",
        ],
    },
    "AUTONOMY-RUNTIME-FAILED": {
        "id": "RECOVERY-REFRESH-RUNTIME-CAPABILITY",
        "category": "runtime",
        "severity": "high",
        "title": "Refresh runtime capability and rebuild the handoff plan",
        "reason": "The runtime adapter failed or no supported local runtime was available.",
        "stop_scheduler_until_resolved": True,
        "commands": [
            'bash ".vibeos/scripts/detect-runtime-capabilities.sh" --project-dir "."',
            'python3 ".vibeos/scripts/autonomy-runtime-adapter.py" --project-dir "." --provider auto --json',
        ],
        "manual_checks": [
            "Confirm Codex or Claude is installed, authenticated, and usable from this project root.",
            "If one provider is unavailable, use the capability matrix before switching providers.",
        ],
    },
    "AUTONOMY-PROVIDER-LIMIT": {
        "id": "RECOVERY-PROVIDER-SESSION-LIMIT",
        "category": "provider_limit",
        "severity": "critical",
        "title": "Pause and resume through a fresh provider/session",
        "reason": "Runtime output indicates a provider, context, usage, or session limit.",
        "stop_scheduler_until_resolved": True,
        "commands": [
            'python3 ".vibeos/scripts/autonomy-heartbeat.py" --status blocked '
            '--summary "provider/session limit" --blocker "provider_or_session_limit" '
            '--next-action "resume through fresh provider/session"',
        ],
        "manual_checks": [
            "Preserve the latest heartbeat, checkpoint, loop state, and failure report.",
            "Resume through a fresh provider/session only after the provider limit clears.",
        ],
    },
}


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


def status_of(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") if isinstance(payload, dict) else {}
    if isinstance(summary, dict):
        return str(summary.get("status") or "")
    return ""


def normalize_findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    findings = report.get("findings", [])
    if not isinstance(findings, list):
        return []
    return [finding for finding in findings if isinstance(finding, dict)]


def action_for_finding(finding: dict[str, Any]) -> dict[str, Any] | None:
    finding_id = str(finding.get("id") or "")
    template = ACTION_TEMPLATES.get(finding_id)
    if not template:
        return None
    action = dict(template)
    action["finding_ids"] = [finding_id]
    action["finding_messages"] = [finding.get("message")]
    action["evidence"] = [finding.get("evidence", {})]
    action["requires_review"] = True
    return action


def merge_action(actions: list[dict[str, Any]], action: dict[str, Any]) -> None:
    for existing in actions:
        if existing.get("id") != action.get("id"):
            continue
        existing["finding_ids"].extend(action["finding_ids"])
        existing["finding_messages"].extend(action["finding_messages"])
        existing["evidence"].extend(action["evidence"])
        return
    actions.append(action)


def severity_rank(action: dict[str, Any]) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(str(action.get("severity")), 4)


def build_actions(failure_report: dict[str, Any]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for finding in normalize_findings(failure_report):
        if not finding.get("blocking", True):
            continue
        action = action_for_finding(finding)
        if action is not None:
            merge_action(actions, action)
    actions.sort(key=severity_rank)
    return actions


def build_report(root: Path) -> dict[str, Any]:
    failure_report = load_json(root / FAILURE_REPORT, {})
    runtime_capabilities = load_json(root / ".vibeos/runtime-capabilities.json", {})
    lease = load_json(root / ".vibeos/autonomy/run-lease.json", {})
    actions = build_actions(failure_report)
    status = "recovery_required" if actions else "pass"
    next_action = actions[0]["id"] if actions else "continue_autonomy"
    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": iso_now(),
        "project_dir": str(root),
        "inputs": {
            "failure_report": FAILURE_REPORT,
            "failure_report_status": status_of(failure_report),
            "runtime_capabilities": ".vibeos/runtime-capabilities.json",
            "runtime_strategy": runtime_capabilities.get("strategy", {}),
            "active_lease": ".vibeos/autonomy/run-lease.json" if lease else None,
        },
        "actions": actions,
        "summary": {
            "status": status,
            "action_count": len(actions),
            "blocking_action_count": len(actions),
            "stop_scheduler_until_resolved": any(
                action.get("stop_scheduler_until_resolved") for action in actions
            ),
            "next_action": next_action,
            "state_file": RECOVERY_PLAN,
        },
    }


def print_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    summary = report["summary"]
    print(
        "[autonomy-recovery-planner] "
        f"{summary['status']}: actions={summary['action_count']} "
        f"next={summary['next_action']}"
    )
    print(f"[autonomy-recovery-planner] Plan: {RECOVERY_PLAN}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan recovery actions for VibeOS autonomy failures.")
    parser.add_argument("--project-dir", default="", help="Project root. Defaults to PROJECT_ROOT or cwd.")
    parser.add_argument("--no-write", action="store_true", help="Do not write the recovery plan.")
    parser.add_argument("--json", action="store_true", help="Print recovery plan JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = project_root(args.project_dir)
    report = build_report(root)
    if not args.no_write:
        write_json(root / RECOVERY_PLAN, report)
    print_report(report, args.json)
    return 1 if report["summary"]["blocking_action_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
