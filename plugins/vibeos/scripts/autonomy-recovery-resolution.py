#!/usr/bin/env python3
"""Record evidence-backed resolution for VibeOS autonomy recovery actions."""

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
RECOVERY_RESOLUTION_HISTORY = ".vibeos/autonomy/recovery-resolution-history.jsonl"


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


def summary(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("summary") if isinstance(payload, dict) else {}
    return value if isinstance(value, dict) else {}


def plan_generated_at(recovery_plan: dict[str, Any]) -> str:
    return str(recovery_plan.get("generated_at") or "")


def normalize_actions(recovery_plan: dict[str, Any]) -> list[dict[str, Any]]:
    actions = recovery_plan.get("actions", [])
    if not isinstance(actions, list):
        return []
    return [action for action in actions if isinstance(action, dict) and str(action.get("id") or "")]


def blocking_actions(recovery_plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [action for action in normalize_actions(recovery_plan) if action.get("requires_review", True)]


def normalized_evidence(values: list[str] | None) -> list[str]:
    return [value.strip() for value in values or [] if value.strip()]


def default_resolved_by() -> str:
    return os.environ.get("USER") or os.environ.get("LOGNAME") or "unknown"


def normalize_resolutions(state: dict[str, Any]) -> list[dict[str, Any]]:
    values = state.get("resolutions", []) if isinstance(state, dict) else []
    if not isinstance(values, list):
        return []
    return [value for value in values if isinstance(value, dict)]


def valid_resolution_ids(resolutions: list[dict[str, Any]], generated_at: str) -> set[str]:
    resolved: set[str] = set()
    for resolution in resolutions:
        action_id = str(resolution.get("action_id") or "")
        if not action_id:
            continue
        if str(resolution.get("recovery_plan_generated_at") or "") != generated_at:
            continue
        if not str(resolution.get("summary") or "").strip():
            continue
        evidence = resolution.get("evidence", [])
        if not isinstance(evidence, list) or not normalized_evidence([str(item) for item in evidence]):
            continue
        resolved.add(action_id)
    return resolved


def unresolved_actions(
    recovery_plan: dict[str, Any],
    resolutions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    generated_at = plan_generated_at(recovery_plan)
    resolved = valid_resolution_ids(resolutions, generated_at)
    return [action for action in blocking_actions(recovery_plan) if str(action.get("id") or "") not in resolved]


def find_action(recovery_plan: dict[str, Any], action_id: str) -> dict[str, Any] | None:
    for action in normalize_actions(recovery_plan):
        if str(action.get("id") or "") == action_id:
            return action
    return None


def merge_resolution(
    resolutions: list[dict[str, Any]],
    resolution: dict[str, Any],
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    replaced = False
    key = (
        str(resolution.get("action_id") or ""),
        str(resolution.get("recovery_plan_generated_at") or ""),
    )
    for existing in resolutions:
        existing_key = (
            str(existing.get("action_id") or ""),
            str(existing.get("recovery_plan_generated_at") or ""),
        )
        if existing_key == key:
            if not replaced:
                merged.append(resolution)
                replaced = True
            continue
        merged.append(existing)
    if not replaced:
        merged.append(resolution)
    return merged


def invalid_report(root: Path, message: str) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": iso_now(),
        "project_dir": str(root),
        "inputs": {
            "recovery_plan": RECOVERY_PLAN,
            "resolution_file": RECOVERY_RESOLUTION,
        },
        "resolutions": [],
        "unresolved_actions": [],
        "summary": {
            "status": "invalid",
            "resolved_count": 0,
            "unresolved_count": 0,
            "state_file": RECOVERY_RESOLUTION,
            "message": message,
        },
    }


def build_report(root: Path, resolutions: list[dict[str, Any]]) -> dict[str, Any]:
    recovery_plan = load_json(root / RECOVERY_PLAN, {})
    generated_at = plan_generated_at(recovery_plan)
    current_resolved = valid_resolution_ids(resolutions, generated_at)
    unresolved = unresolved_actions(recovery_plan, resolutions)
    blocking = blocking_actions(recovery_plan)
    recovery_summary = summary(recovery_plan)
    legacy_block_without_actions = bool(
        recovery_plan
        and not blocking
        and int(recovery_summary.get("blocking_action_count") or 0) > 0
    )

    if not recovery_plan or (not blocking and not legacy_block_without_actions):
        status = "no_recovery_required"
    elif legacy_block_without_actions:
        status = "invalid"
    elif unresolved:
        status = "unresolved"
    else:
        status = "resolved"

    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": iso_now(),
        "project_dir": str(root),
        "inputs": {
            "recovery_plan": RECOVERY_PLAN,
            "recovery_plan_present": bool(recovery_plan),
            "recovery_plan_generated_at": generated_at,
            "resolution_file": RECOVERY_RESOLUTION,
        },
        "resolutions": resolutions,
        "unresolved_actions": unresolved,
        "summary": {
            "status": status,
            "resolved_count": len(current_resolved),
            "unresolved_count": len(unresolved),
            "state_file": RECOVERY_RESOLUTION,
        },
    }


def build_resolution(root: Path, args: argparse.Namespace) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    action_id = args.action_id.strip()
    if not action_id:
        return None, None
    recovery_plan = load_json(root / RECOVERY_PLAN, {})
    if not recovery_plan:
        return None, invalid_report(root, "recovery plan is required before recording a resolution")
    action = find_action(recovery_plan, action_id)
    if action is None:
        return None, invalid_report(root, f"unknown recovery action id: {action_id}")
    summary_text = args.summary.strip()
    if not summary_text:
        return None, invalid_report(root, "--summary is required when recording a resolution")
    evidence = normalized_evidence(args.evidence)
    if not evidence:
        return None, invalid_report(root, "--evidence is required when recording a resolution")
    return (
        {
            "action_id": action_id,
            "recovery_plan_generated_at": plan_generated_at(recovery_plan),
            "resolved_at": iso_now(),
            "resolved_by": args.resolved_by.strip() or default_resolved_by(),
            "summary": summary_text,
            "evidence": evidence,
            "action_title": action.get("title"),
        },
        None,
    )


def print_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    summary_data = report["summary"]
    print(
        "[autonomy-recovery-resolution] "
        f"{summary_data['status']}: resolved={summary_data['resolved_count']} "
        f"unresolved={summary_data['unresolved_count']}"
    )
    print(f"[autonomy-recovery-resolution] State: {RECOVERY_RESOLUTION}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record resolution evidence for autonomy recovery actions.")
    parser.add_argument("--project-dir", default="", help="Project root. Defaults to PROJECT_ROOT or cwd.")
    parser.add_argument("--action-id", default="", help="Recovery action id to mark resolved.")
    parser.add_argument("--summary", default="", help="Resolution summary for the action.")
    parser.add_argument("--evidence", action="append", default=[], help="Resolution evidence note or path.")
    parser.add_argument("--resolved-by", default="", help="Optional resolver label.")
    parser.add_argument("--no-write", action="store_true", help="Do not write resolution state or history.")
    parser.add_argument("--json", action="store_true", help="Print resolution report JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = project_root(args.project_dir)
    existing = load_json(root / RECOVERY_RESOLUTION, {})
    resolutions = normalize_resolutions(existing)

    resolution, invalid = build_resolution(root, args)
    if invalid is not None:
        print_report(invalid, args.json)
        return 2
    if resolution is not None:
        resolutions = merge_resolution(resolutions, resolution)

    report = build_report(root, resolutions)
    if not args.no_write:
        write_json(root / RECOVERY_RESOLUTION, report)
        if resolution is not None:
            append_jsonl(root / RECOVERY_RESOLUTION_HISTORY, resolution)
    print_report(report, args.json)

    status = report["summary"]["status"]
    if status == "invalid":
        return 2
    return 1 if status == "unresolved" else 0


if __name__ == "__main__":
    sys.exit(main())
