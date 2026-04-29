#!/usr/bin/env python3
"""Validate VibeOS long-run autonomy policy and heartbeat evidence."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_POLICY = {
    "max_duration_hours": 48,
    "min_heartbeat_interval_minutes": 5,
    "max_heartbeat_interval_minutes": 60,
    "max_checkpoint_interval_minutes": 120,
    "max_audit_interval_minutes": 360,
    "stale_heartbeat_multiplier": 3,
    "checkpoint_grace_multiplier": 2,
    "audit_grace_multiplier": 2,
    "required_stop_conditions": [
        "security_or_secret_risk",
        "destructive_or_irreversible_action",
        "unclear_product_decision",
        "repeated_gate_failure",
        "provider_or_session_limit",
        "repeated_no_progress_loop",
        "plan_complete",
    ],
}


def parse_iso(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_now(value: str) -> datetime:
    if value:
        return parse_iso(value)
    return datetime.now(timezone.utc).replace(microsecond=0)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def project_root_from_args(value: str) -> Path:
    if value:
        return Path(value).resolve()
    return Path(os.environ.get("PROJECT_ROOT", ".")).resolve()


def policy(project_dir: Path) -> dict[str, Any]:
    data = load_json(project_dir / ".vibeos/reference/autonomy/long-run-autonomy-policy.json", {})
    merged = dict(DEFAULT_POLICY)
    if isinstance(data, dict):
        merged.update(data.get("policy", data))
    return merged


def active_long_run(config: dict[str, Any], session: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], bool]:
    config_long_run = config.get("autonomy", {}).get("long_run", {})
    session_long_run = session.get("long_run", {})
    active = bool(config_long_run.get("active") or session_long_run.get("active"))
    return config_long_run, session_long_run, active


def heartbeat_files(project_dir: Path, run_id: str) -> list[Path]:
    heartbeat_dir = project_dir / ".vibeos/autonomy/heartbeats"
    if not heartbeat_dir.exists():
        return []
    files = []
    for path in heartbeat_dir.glob("*.json"):
        data = load_json(path, {})
        if not run_id or data.get("run_id") == run_id:
            files.append(path)
    return sorted(files)


def latest_heartbeat(project_dir: Path, run_id: str) -> tuple[Path | None, dict[str, Any]]:
    latest_path = None
    latest_data: dict[str, Any] = {}
    latest_time: datetime | None = None
    for path in heartbeat_files(project_dir, run_id):
        data = load_json(path, {})
        timestamp = data.get("timestamp")
        if not timestamp:
            continue
        try:
            parsed = parse_iso(timestamp)
        except ValueError:
            continue
        if latest_time is None or parsed > latest_time:
            latest_time = parsed
            latest_path = path
            latest_data = data
    return latest_path, latest_data


def finding(findings: list[dict[str, Any]], item_id: str, severity: str, file_name: str, message: str) -> None:
    findings.append({"id": item_id, "severity": severity, "file": file_name, "message": message})


def minutes_between(start: str, now: datetime) -> float:
    return (now - parse_iso(start)).total_seconds() / 60


def validate(project_dir: Path, now: datetime, require_closed: bool) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    config = load_json(project_dir / ".vibeos/config.json", {})
    session = load_json(project_dir / ".vibeos/session-state.json", {})
    current_policy = policy(project_dir)
    config_long_run, session_long_run, active = active_long_run(config, session)

    if require_closed and active:
        finding(
            findings,
            "LONGRUN-NOT-CLOSED",
            "high",
            ".vibeos/session-state.json",
            "Session-end validation requires the long-run autonomy session to be complete, paused, or blocked.",
        )

    if not active:
        return findings

    source = dict(config_long_run)
    source.update({k: v for k, v in session_long_run.items() if v is not None})
    run_id = str(source.get("run_id") or "")
    target_hours = int(source.get("target_hours") or 0)
    max_hours = int(source.get("max_hours") or target_hours or 0)
    heartbeat_interval = int(source.get("heartbeat_interval_minutes") or 0)
    checkpoint_interval = int(source.get("checkpoint_interval_minutes") or 0)
    audit_interval = int(source.get("audit_interval_minutes") or 0)

    if target_hours < 1 or target_hours > int(current_policy["max_duration_hours"]):
        finding(
            findings,
            "LONGRUN-DURATION-POLICY",
            "high",
            ".vibeos/config.json",
            f"target_hours must be between 1 and {current_policy['max_duration_hours']}.",
        )
    if max_hours < target_hours or max_hours > int(current_policy["max_duration_hours"]):
        finding(
            findings,
            "LONGRUN-MAX-DURATION-POLICY",
            "high",
            ".vibeos/config.json",
            f"max_hours must be >= target_hours and <= {current_policy['max_duration_hours']}.",
        )
    if heartbeat_interval < int(current_policy["min_heartbeat_interval_minutes"]) or heartbeat_interval > int(current_policy["max_heartbeat_interval_minutes"]):
        finding(
            findings,
            "LONGRUN-HEARTBEAT-CADENCE",
            "high",
            ".vibeos/config.json",
            "Heartbeat cadence is outside the allowed long-run autonomy policy.",
        )
    if checkpoint_interval < heartbeat_interval or checkpoint_interval > int(current_policy["max_checkpoint_interval_minutes"]):
        finding(
            findings,
            "LONGRUN-CHECKPOINT-CADENCE",
            "high",
            ".vibeos/config.json",
            "Checkpoint cadence must be at least the heartbeat cadence and within policy.",
        )
    if audit_interval < checkpoint_interval or audit_interval > int(current_policy["max_audit_interval_minutes"]):
        finding(
            findings,
            "LONGRUN-AUDIT-CADENCE",
            "high",
            ".vibeos/config.json",
            "Audit cadence must be at least the checkpoint cadence and within policy.",
        )

    stop_conditions = set(config_long_run.get("stop_conditions") or [])
    missing_stop_conditions = [condition for condition in current_policy["required_stop_conditions"] if condition not in stop_conditions]
    if missing_stop_conditions:
        finding(
            findings,
            "LONGRUN-STOP-CONDITIONS",
            "high",
            ".vibeos/config.json",
            "Long-run autonomy policy is missing stop conditions: " + ", ".join(missing_stop_conditions),
        )

    latest_path, latest = latest_heartbeat(project_dir, run_id)
    if active and latest_path is None:
        finding(
            findings,
            "LONGRUN-HEARTBEAT-MISSING",
            "high",
            ".vibeos/autonomy/heartbeats",
            "Active long-run autonomy requires at least one heartbeat artifact.",
        )
    elif latest:
        heartbeat_age = minutes_between(str(latest["timestamp"]), now)
        stale_after = heartbeat_interval * float(current_policy["stale_heartbeat_multiplier"])
        if active and heartbeat_age > stale_after:
            finding(
                findings,
                "LONGRUN-HEARTBEAT-STALE",
                "high",
                str(latest_path.relative_to(project_dir)) if latest_path else ".vibeos/autonomy/heartbeats",
                f"Latest heartbeat is {heartbeat_age:.1f} minutes old; policy allows {stale_after:.1f}.",
            )

    started_at = source.get("started_at")
    if active and started_at:
        run_age_hours = minutes_between(str(started_at), now) / 60
        if max_hours and run_age_hours > max_hours:
            finding(
                findings,
                "LONGRUN-MAX-RUNTIME-EXCEEDED",
                "critical",
                ".vibeos/session-state.json",
                f"Long-run autonomy has exceeded max_hours ({max_hours}).",
            )

        if checkpoint_interval:
            last_checkpoint = source.get("last_checkpoint_at")
            checkpoint_due_after = checkpoint_interval * float(current_policy["checkpoint_grace_multiplier"])
            if run_age_hours * 60 > checkpoint_due_after and not last_checkpoint:
                finding(
                    findings,
                    "LONGRUN-CHECKPOINT-MISSING",
                    "high",
                    ".vibeos/session-state.json",
                    "Long-run autonomy has run past checkpoint grace without checkpoint evidence.",
                )
            elif last_checkpoint and minutes_between(str(last_checkpoint), now) > checkpoint_due_after:
                finding(
                    findings,
                    "LONGRUN-CHECKPOINT-STALE",
                    "high",
                    ".vibeos/session-state.json",
                    "Latest long-run checkpoint is stale.",
                )

        if audit_interval:
            last_audit = source.get("last_audit_at")
            audit_due_after = audit_interval * float(current_policy["audit_grace_multiplier"])
            if run_age_hours * 60 > audit_due_after and not last_audit:
                finding(
                    findings,
                    "LONGRUN-AUDIT-MISSING",
                    "high",
                    ".vibeos/session-state.json",
                    "Long-run autonomy has run past audit grace without audit evidence.",
                )
            elif last_audit and minutes_between(str(last_audit), now) > audit_due_after:
                finding(
                    findings,
                    "LONGRUN-AUDIT-STALE",
                    "high",
                    ".vibeos/session-state.json",
                    "Latest long-run audit checkpoint is stale.",
                )

    return findings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate VibeOS long-run autonomy state.")
    parser.add_argument("--project-dir", default="", help="Project root. Defaults to PROJECT_ROOT or cwd.")
    parser.add_argument("--now", default="", help="Override current time for tests, ISO-8601.")
    parser.add_argument("--require-closed", action="store_true", help="Fail if a long-run session is still active.")
    parser.add_argument("--json", action="store_true", help="Print validation payload as JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    require_closed = args.require_closed or os.environ.get("LONG_RUN_REQUIRE_CLOSED", "").lower() == "true"
    project_dir = project_root_from_args(args.project_dir)
    now = iso_now(args.now)
    findings = validate(project_dir, now, require_closed)
    blocking = any(item["severity"] in {"critical", "high"} for item in findings)
    status = "fail" if blocking else "pass"
    payload = {"status": status, "findings": findings}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    elif findings:
        print("[validate-long-run-autonomy] FAIL: long-run autonomy findings detected")
        for item in findings:
            print(f"- {item['id']} [{item['severity']}]: {item['file']} - {item['message']}")
    else:
        print("[validate-long-run-autonomy] PASS: long-run autonomy state is within policy")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
