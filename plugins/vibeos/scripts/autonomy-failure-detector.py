#!/usr/bin/env python3
"""Detect stuck loops and operational failures in VibeOS long-run autonomy state."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.2.0"
LOOP_HISTORY = ".vibeos/autonomy/loop-history.jsonl"
RUNTIME_HISTORY = ".vibeos/autonomy/runtime-adapter-history.jsonl"
FAILURE_REPORT = ".vibeos/autonomy/failure-report.json"
FAILURE_STATUSES = {"blocked", "failed", "lease_conflict", "runtime_unavailable"}
NO_PROGRESS_STATUSES = FAILURE_STATUSES | {"handoff_required"}
DEFAULT_MAX_REPEAT = 3
DEFAULT_MAX_FAILURES = 2
DEFAULT_PROVIDER_LIMIT_PATTERNS = (
    "rate limit",
    "quota",
    "context length",
    "maximum context",
    "context window",
    "session limit",
    "usage limit",
    "too many requests",
    "429",
    "limit reached",
    "token limit",
    "timed out",
)


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


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            parsed = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            rows.append(parsed)
    return rows


def load_policy(root: Path) -> dict[str, Any]:
    data = load_json(root / ".vibeos/reference/autonomy/long-run-autonomy-policy.json", {})
    if isinstance(data, dict):
        policy = data.get("policy", data)
        if isinstance(policy, dict):
            return policy
    return {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def status_of(payload: dict[str, Any]) -> str:
    summary = payload.get("summary") if isinstance(payload, dict) else {}
    if isinstance(summary, dict):
        return str(summary.get("status") or "")
    return ""


def add_finding(
    findings: list[dict[str, Any]],
    finding_id: str,
    severity: str,
    message: str,
    evidence: dict[str, Any],
    recommended_action: str,
    blocking: bool = True,
) -> None:
    findings.append(
        {
            "id": finding_id,
            "severity": severity,
            "blocking": blocking,
            "message": message,
            "evidence": evidence,
            "recommended_action": recommended_action,
        }
    )


def tail(rows: list[dict[str, Any]], count: int) -> list[dict[str, Any]]:
    if count <= 0:
        return []
    return rows[-count:]


def compact_entries(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "generated_at": row.get("generated_at"),
            "status": row.get("status"),
            "decision_action": row.get("decision_action"),
            "decision_reason": row.get("decision_reason"),
            "provider": row.get("provider"),
            "exit_code": row.get("exit_code"),
        }
        for row in rows
    ]


def detect_repeated_handoff(
    findings: list[dict[str, Any]],
    loop_history: list[dict[str, Any]],
    max_repeat: int,
) -> None:
    rows = tail(loop_history, max_repeat)
    if len(rows) < max_repeat:
        return
    if not all(row.get("status") == "handoff_required" for row in rows):
        return
    add_finding(
        findings,
        "AUTONOMY-REPEATED-HANDOFF",
        "high",
        f"Last {max_repeat} autonomy loop ticks stopped at the same model handoff boundary.",
        {"history": LOOP_HISTORY, "tail": compact_entries(rows)},
        "Resume the handoff in a model runtime or change the scheduler to launch a reviewed runtime adapter path.",
    )


def detect_repeated_decision(
    findings: list[dict[str, Any]],
    loop_history: list[dict[str, Any]],
    max_repeat: int,
) -> None:
    rows = tail(loop_history, max_repeat)
    if len(rows) < max_repeat:
        return
    fingerprints = [
        (row.get("decision_action"), row.get("decision_reason"), row.get("status"))
        for row in rows
    ]
    first = fingerprints[0]
    if not first[0] or first[2] not in NO_PROGRESS_STATUSES:
        return
    if not all(fingerprint == first for fingerprint in fingerprints):
        return
    add_finding(
        findings,
        "AUTONOMY-REPEATED-DECISION",
        "high",
        f"Last {max_repeat} loop ticks produced the same no-progress supervisor decision.",
        {"history": LOOP_HISTORY, "tail": compact_entries(rows)},
        "Inspect the active Work Order, latest runner report, and handoff path before scheduling another tick.",
    )


def detect_consecutive_failures(
    findings: list[dict[str, Any]],
    history: list[dict[str, Any]],
    history_name: str,
    max_failures: int,
) -> None:
    rows = tail(history, max_failures)
    if len(rows) < max_failures:
        return
    if not all(row.get("status") in FAILURE_STATUSES for row in rows):
        return
    add_finding(
        findings,
        "AUTONOMY-CONSECUTIVE-FAILURES",
        "high",
        f"Last {max_failures} autonomy control-plane attempts ended in failure states.",
        {"history": history_name, "tail": compact_entries(rows)},
        "Stop autonomous scheduling and resolve the repeated failure before continuing.",
    )


def detect_repeated_lease_conflicts(
    findings: list[dict[str, Any]],
    histories: list[tuple[str, list[dict[str, Any]]]],
    max_repeat: int,
) -> None:
    combined: list[dict[str, Any]] = []
    for history_name, rows in histories:
        for row in rows:
            enriched = dict(row)
            enriched["history"] = history_name
            combined.append(enriched)
    rows = tail(combined, max_repeat)
    if len(rows) < max_repeat:
        return
    if not all(row.get("status") == "lease_conflict" for row in rows):
        return
    add_finding(
        findings,
        "AUTONOMY-LEASE-CONFLICTS",
        "high",
        f"Last {max_repeat} autonomy driver attempts hit run-lease conflicts.",
        {"tail": compact_entries(rows)},
        "Confirm the active driver is healthy, then wait for or clear only an expired lease.",
    )


def detect_latest_runner(findings: list[dict[str, Any]], runner_report: dict[str, Any]) -> None:
    status = status_of(runner_report)
    if status not in {"blocked", "failed"}:
        return
    summary = runner_report.get("summary", {})
    items = runner_report.get("items", [])
    add_finding(
        findings,
        "AUTONOMY-RUNNER-BLOCKED",
        "high",
        f"Latest autonomy runner report is {status}.",
        {
            "report": ".vibeos/autonomy/runner-report.json",
            "summary": summary,
            "items": items[:5] if isinstance(items, list) else [],
        },
        "Review the blocked or failed command and update the Work Order or allowlist only with evidence.",
    )


def detect_latest_runtime(findings: list[dict[str, Any]], adapter_plan: dict[str, Any]) -> None:
    status = status_of(adapter_plan)
    if status not in {"failed", "runtime_unavailable"}:
        return
    add_finding(
        findings,
        "AUTONOMY-RUNTIME-FAILED",
        "high",
        f"Latest runtime adapter status is {status}.",
        {
            "report": ".vibeos/autonomy/runtime-adapter-plan.json",
            "summary": adapter_plan.get("summary", {}),
            "execution": adapter_plan.get("execution", {}),
        },
        "Fix the runtime launch issue or select an available provider before scheduling another handoff.",
    )


def runtime_text_records(
    adapter_plan: dict[str, Any],
    runtime_history: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    records: list[tuple[str, str]] = []
    execution = adapter_plan.get("execution")
    if isinstance(execution, dict):
        records.append((".vibeos/autonomy/runtime-adapter-plan.json:stdout", str(execution.get("stdout") or "")))
        records.append((".vibeos/autonomy/runtime-adapter-plan.json:stderr", str(execution.get("stderr") or "")))
    for index, row in enumerate(runtime_history[-5:], start=max(0, len(runtime_history) - 5)):
        records.append((f"{RUNTIME_HISTORY}:{index}:stdout", str(row.get("stdout") or "")))
        records.append((f"{RUNTIME_HISTORY}:{index}:stderr", str(row.get("stderr") or "")))
    return records


def detect_provider_limit(
    findings: list[dict[str, Any]],
    adapter_plan: dict[str, Any],
    runtime_history: list[dict[str, Any]],
    patterns: tuple[str, ...],
) -> None:
    for source, text in runtime_text_records(adapter_plan, runtime_history):
        lowered = text.lower()
        pattern = next((candidate for candidate in patterns if candidate in lowered), "")
        if not pattern:
            continue
        excerpt = text[:500]
        add_finding(
            findings,
            "AUTONOMY-PROVIDER-LIMIT",
            "high",
            f"Runtime output contains provider/session limit signal: {pattern}.",
            {"source": source, "pattern": pattern, "excerpt": excerpt},
            "Pause the autonomous run, preserve state, and resume through a fresh provider/session once limits clear.",
        )
        return


def active_lease_conflict(lease_conflict: dict[str, Any]) -> bool:
    if status_of(lease_conflict) != "lease_conflict":
        return False
    active = lease_conflict.get("active_lease")
    if not isinstance(active, dict):
        return True
    expires_at = active.get("expires_at")
    if not expires_at:
        return True
    try:
        parsed = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
    except ValueError:
        return True
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc) > datetime.now(timezone.utc)


def detect_latest_lease_conflict(
    findings: list[dict[str, Any]],
    lease_conflict: dict[str, Any],
) -> None:
    if not active_lease_conflict(lease_conflict):
        return
    if any(finding.get("id") == "AUTONOMY-LEASE-CONFLICTS" for finding in findings):
        return
    add_finding(
        findings,
        "AUTONOMY-LEASE-CONFLICTS",
        "high",
        "Latest autonomy driver attempt was blocked by an active run lease.",
        {
            "report": ".vibeos/autonomy/lease-conflict.json",
            "summary": lease_conflict.get("summary", {}),
            "active_lease": lease_conflict.get("active_lease", {}),
        },
        "Let the owning driver finish or verify the lease is stale before another driver mutates autonomy state.",
    )


def build_report(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    loop_history = load_jsonl(root / LOOP_HISTORY)
    runtime_history = load_jsonl(root / RUNTIME_HISTORY)
    loop_state = load_json(root / ".vibeos/autonomy/loop-state.json", {})
    runner_report = load_json(root / ".vibeos/autonomy/runner-report.json", {})
    adapter_plan = load_json(root / ".vibeos/autonomy/runtime-adapter-plan.json", {})
    lease_conflict = load_json(root / ".vibeos/autonomy/lease-conflict.json", {})
    findings: list[dict[str, Any]] = []

    detect_repeated_handoff(findings, loop_history, args.max_repeat)
    detect_repeated_decision(findings, loop_history, args.max_repeat)
    detect_consecutive_failures(findings, loop_history, LOOP_HISTORY, args.max_failures)
    detect_consecutive_failures(findings, runtime_history, RUNTIME_HISTORY, args.max_failures)
    detect_repeated_lease_conflicts(
        findings,
        [(LOOP_HISTORY, loop_history), (RUNTIME_HISTORY, runtime_history)],
        args.max_repeat,
    )
    detect_latest_runner(findings, runner_report)
    detect_latest_runtime(findings, adapter_plan)
    detect_provider_limit(findings, adapter_plan, runtime_history, args.provider_limit_patterns)
    detect_latest_lease_conflict(findings, lease_conflict)

    blocking_count = sum(1 for finding in findings if finding.get("blocking"))
    status = "fail" if blocking_count else "pass"
    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": iso_now(),
        "project_dir": str(root),
        "inputs": {
            "loop_history": LOOP_HISTORY,
            "runtime_history": RUNTIME_HISTORY,
            "loop_state_status": status_of(loop_state),
            "runner_status": status_of(runner_report),
            "runtime_adapter_status": status_of(adapter_plan),
            "lease_conflict_status": status_of(lease_conflict),
        },
        "thresholds": {
            "max_repeat": args.max_repeat,
            "max_failures": args.max_failures,
        },
        "findings": findings,
        "summary": {
            "status": status,
            "finding_count": len(findings),
            "blocking_count": blocking_count,
            "state_file": FAILURE_REPORT,
        },
    }


def print_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    summary = report["summary"]
    print(
        "[autonomy-failure-detector] "
        f"{summary['status']}: findings={summary['finding_count']} "
        f"blocking={summary['blocking_count']}"
    )
    print(f"[autonomy-failure-detector] Report: {FAILURE_REPORT}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect VibeOS autonomy loops and operational failures.")
    parser.add_argument("--project-dir", default="", help="Project root. Defaults to PROJECT_ROOT or cwd.")
    parser.add_argument("--max-repeat", type=int, default=None, help="Repeated no-progress loop threshold.")
    parser.add_argument("--max-failures", type=int, default=None, help="Consecutive failure threshold.")
    parser.add_argument("--no-write", action="store_true", help="Do not write the detector report.")
    parser.add_argument("--json", action="store_true", help="Print detector report JSON.")
    return parser.parse_args()


def resolve_options(root: Path, args: argparse.Namespace) -> None:
    policy = load_policy(root)
    args.max_repeat = int(
        args.max_repeat
        or policy.get("failure_detector_repeat_threshold")
        or DEFAULT_MAX_REPEAT
    )
    args.max_failures = int(
        args.max_failures
        or policy.get("failure_detector_consecutive_failure_threshold")
        or DEFAULT_MAX_FAILURES
    )
    patterns = policy.get("provider_limit_patterns") or DEFAULT_PROVIDER_LIMIT_PATTERNS
    if not isinstance(patterns, (list, tuple)):
        patterns = DEFAULT_PROVIDER_LIMIT_PATTERNS
    args.provider_limit_patterns = tuple(str(pattern).lower() for pattern in patterns)


def main() -> int:
    args = parse_args()
    root = project_root(args.project_dir)
    resolve_options(root, args)
    if args.max_repeat < 2:
        print("[autonomy-failure-detector] --max-repeat must be >= 2", file=sys.stderr)
        return 2
    if args.max_failures < 1:
        print("[autonomy-failure-detector] --max-failures must be >= 1", file=sys.stderr)
        return 2
    report = build_report(root, args)
    if not args.no_write:
        write_json(root / FAILURE_REPORT, report)
    print_report(report, args.json)
    return 1 if report["summary"]["blocking_count"] else 0


if __name__ == "__main__":
    sys.exit(main())
