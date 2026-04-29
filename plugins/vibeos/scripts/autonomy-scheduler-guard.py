#!/usr/bin/env python3
"""Block autonomy scheduler ticks while recovery actions are unresolved."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.2.0"
RECOVERY_PLAN = ".vibeos/autonomy/recovery-plan.json"
RECOVERY_RESOLUTION = ".vibeos/autonomy/recovery-resolution.json"
FAILURE_REPORT = ".vibeos/autonomy/failure-report.json"
GUARD_REPORT = ".vibeos/autonomy/scheduler-guard-report.json"


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


def summary(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("summary") if isinstance(payload, dict) else {}
    return value if isinstance(value, dict) else {}


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
    recovery_summary = summary(recovery_plan)
    if blocking_actions(recovery_plan):
        return False
    if recovery_summary.get("status") == "recovery_required":
        return True
    if recovery_summary.get("stop_scheduler_until_resolved"):
        return True
    if int(recovery_summary.get("blocking_action_count") or 0) > 0:
        return True
    return False


def recovery_blocks(recovery_plan: dict[str, Any], recovery_resolution: dict[str, Any]) -> bool:
    return bool(unresolved_actions(recovery_plan, recovery_resolution)) or legacy_block_without_actions(
        recovery_plan
    )


def failure_blocks_without_recovery(failure_report: dict[str, Any], recovery_plan: dict[str, Any]) -> bool:
    if recovery_plan:
        return False
    failure_summary = summary(failure_report)
    return int(failure_summary.get("blocking_count") or 0) > 0


def build_report(root: Path) -> dict[str, Any]:
    recovery_plan = load_json(root / RECOVERY_PLAN, {})
    recovery_resolution = load_json(root / RECOVERY_RESOLUTION, {})
    failure_report = load_json(root / FAILURE_REPORT, {})
    reasons: list[dict[str, Any]] = []

    unresolved = unresolved_actions(recovery_plan, recovery_resolution)
    if recovery_blocks(recovery_plan, recovery_resolution):
        reasons.append(
            {
                "id": "SCHEDULER-GUARD-RECOVERY-REQUIRED",
                "message": "Recovery plan has unresolved blocking actions.",
                "evidence": {
                    "recovery_plan": RECOVERY_PLAN,
                    "recovery_resolution": RECOVERY_RESOLUTION,
                    "recovery_plan_generated_at": plan_generated_at(recovery_plan),
                    "summary": summary(recovery_plan),
                    "unresolved_actions": unresolved,
                    "resolved_action_ids": sorted(
                        valid_resolution_ids(recovery_resolution, plan_generated_at(recovery_plan))
                    ),
                },
                "recommended_action": (
                    "Run autonomy-recovery-resolution.py with evidence for each blocking action, "
                    "or explicitly supersede the recovery plan before another tick."
                ),
            }
        )
    elif failure_blocks_without_recovery(failure_report, recovery_plan):
        reasons.append(
            {
                "id": "SCHEDULER-GUARD-MISSING-RECOVERY-PLAN",
                "message": "Failure report has blocking findings but no recovery plan exists.",
                "evidence": {"failure_report": FAILURE_REPORT, "summary": summary(failure_report)},
                "recommended_action": "Run autonomy-recovery-planner.py before another scheduler tick.",
            }
        )

    status = "blocked" if reasons else "pass"
    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": iso_now(),
        "project_dir": str(root),
        "inputs": {
            "recovery_plan": RECOVERY_PLAN,
            "recovery_plan_present": bool(recovery_plan),
            "recovery_resolution": RECOVERY_RESOLUTION,
            "recovery_resolution_present": bool(recovery_resolution),
            "failure_report": FAILURE_REPORT,
            "failure_report_present": bool(failure_report),
        },
        "reasons": reasons,
        "summary": {
            "status": status,
            "blocking_reason_count": len(reasons),
            "state_file": GUARD_REPORT,
        },
    }


def print_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    summary_data = report["summary"]
    print(
        "[autonomy-scheduler-guard] "
        f"{summary_data['status']}: blocking_reasons={summary_data['blocking_reason_count']}"
    )
    print(f"[autonomy-scheduler-guard] Report: {GUARD_REPORT}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Guard VibeOS autonomy scheduler ticks.")
    parser.add_argument("--project-dir", default="", help="Project root. Defaults to PROJECT_ROOT or cwd.")
    parser.add_argument("--no-write", action="store_true", help="Do not write the guard report.")
    parser.add_argument("--json", action="store_true", help="Print guard report JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = project_root(args.project_dir)
    report = build_report(root)
    if not args.no_write:
        write_json(root / GUARD_REPORT, report)
    print_report(report, args.json)
    return 2 if report["summary"]["status"] == "blocked" else 0


if __name__ == "__main__":
    sys.exit(main())
