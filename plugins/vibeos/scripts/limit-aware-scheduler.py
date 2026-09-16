#!/usr/bin/env python3
# FILE-SIZE-EXCEPTION: WO-139 — cohesive local provider/session-limit scheduler with parsing, state, and reviewed one-shot profiles.
"""Generate one-shot resume artifacts after provider/session limit signals."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.3.0"
STATE_DIR = ".vibeos/autonomy/limit-aware"
STATE_FILE = "limit-aware-scheduler.json"
EVENTS_FILE = "limit-events.jsonl"
DISPATCH_POLICY_FILE = "dispatch-policy.json"
LOOP_STATE = ".vibeos/autonomy/loop-state.json"
FAILURE_REPORT = ".vibeos/autonomy/failure-report.json"
LIMIT_PATTERNS = (
    "5-hour limit",
    "5 hour limit",
    "session limit",
    "usage limit",
    "rate limit",
    "quota",
    "too many requests",
    "429",
    "limit reached",
    "weekly limit",
    "monthly limit",
)
RESET_FIELD_NAMES = {
    "reset_at",
    "resetAt",
    "resets_at",
    "resetsAt",
    "window_reset_at",
    "windowResetAt",
    "retry_at",
    "retryAt",
    "next_resume_after",
    "reset_time",
    "resetTime",
}
RETRY_FIELD_NAMES = {
    "retry_after",
    "retryAfter",
    "retry_after_seconds",
    "retryAfterSeconds",
    "Retry-After",
}
ISO_PATTERN = re.compile(
    r"\b\d{4}-\d{2}-\d{2}[T ][0-9]{2}:[0-9]{2}(?::[0-9]{2})?"
    r"(?:\.[0-9]+)?(?:Z|[+-][0-9]{2}:?[0-9]{2})?\b"
)
RETRY_AFTER_PATTERN = re.compile(
    r"\bretry\s+after\s+([0-9]+)\s*(?:seconds?|secs?|s)?\b",
    re.IGNORECASE,
)
CLOCK_RESET_PATTERN = re.compile(
    r"\b(?:reset|resets|retry|available|window)\s*(?:at|after|until)?\s*"
    r"([0-9]{1,2})(?::([0-9]{2}))?\s*(am|pm)?\b",
    re.IGNORECASE,
)


def iso_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def parse_now(value: str) -> datetime:
    if not value:
        return datetime.now(timezone.utc).replace(microsecond=0)
    parsed = parse_datetime(value)
    if parsed is None:
        raise ValueError(f"invalid --now value: {value}")
    return parsed


def iso_z(value: datetime) -> str:
    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def project_root(value: str) -> Path:
    if value:
        return Path(value).resolve()
    return Path(os.environ.get("PROJECT_ROOT", ".")).resolve()


def quote(value: Path | str) -> str:
    return shlex.quote(str(value))


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(data, sort_keys=True) + "\n")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def read_input(root: Path, args: argparse.Namespace) -> tuple[str, str]:
    if args.input:
        if args.input == "-":
            return sys.stdin.read(), "stdin"
        path = Path(args.input)
        if not path.is_absolute():
            path = root / path
        return path.read_text(encoding="utf-8"), str(path)
    if args.source == "failure-report":
        path = root / FAILURE_REPORT
        return path.read_text(encoding="utf-8") if path.exists() else "", str(path)
    return sys.stdin.read(), "stdin"


def parse_payload(text: str) -> Any:
    if not text.strip():
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"text": text}


def iter_scalars(value: Any) -> list[str]:
    scalars: list[str] = []
    if isinstance(value, dict):
        for item in value.values():
            scalars.extend(iter_scalars(item))
    elif isinstance(value, list):
        for item in value:
            scalars.extend(iter_scalars(item))
    elif value is not None:
        scalars.append(str(value))
    return scalars


def collect_text(value: Any) -> str:
    return "\n".join(item for item in iter_scalars(value) if item.strip())


def parse_datetime(value: str) -> datetime | None:
    raw = value.strip()
    if not raw:
        return None
    normalized = raw.replace(" ", "T", 1)
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    match = re.match(r"^(.*[T ][0-9]{2}:[0-9]{2})([+-][0-9]{2})([0-9]{2})$", normalized)
    if match:
        normalized = f"{match.group(1)}{match.group(2)}:{match.group(3)}"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_numeric_seconds(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return max(0, int(value))
    if isinstance(value, str) and value.strip().isdigit():
        return max(0, int(value.strip()))
    return None


def find_field_reset(value: Any, now: datetime) -> tuple[datetime, str] | None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in RESET_FIELD_NAMES:
                if isinstance(item, str):
                    parsed = parse_first_datetime(item, now)
                    if parsed:
                        return parsed[0], f"field:{key}:{parsed[1]}"
                seconds = parse_numeric_seconds(item)
                if seconds is not None:
                    return now + timedelta(seconds=seconds), f"field:{key}:seconds"
            if key in RETRY_FIELD_NAMES:
                seconds = parse_numeric_seconds(item)
                if seconds is not None:
                    return now + timedelta(seconds=seconds), f"field:{key}:seconds"
                if isinstance(item, str):
                    retry = parse_retry_after(item, now)
                    if retry:
                        return retry[0], f"field:{key}:{retry[1]}"
            nested = find_field_reset(item, now)
            if nested:
                return nested
    elif isinstance(value, list):
        for item in value:
            nested = find_field_reset(item, now)
            if nested:
                return nested
    return None


def parse_retry_after(text: str, now: datetime) -> tuple[datetime, str] | None:
    match = RETRY_AFTER_PATTERN.search(text)
    if not match:
        return None
    return now + timedelta(seconds=int(match.group(1))), "retry-after-text"


def parse_clock_reset(text: str, now: datetime) -> tuple[datetime, str] | None:
    for match in CLOCK_RESET_PATTERN.finditer(text):
        hour = int(match.group(1))
        minute = int(match.group(2) or "0")
        suffix = (match.group(3) or "").lower()
        if hour > 23 or minute > 59:
            continue
        if suffix == "pm" and hour < 12:
            hour += 12
        if suffix == "am" and hour == 12:
            hour = 0
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate, "clock-text"
    return None


def parse_first_datetime(text: str, now: datetime) -> tuple[datetime, str] | None:
    for match in ISO_PATTERN.finditer(text):
        parsed = parse_datetime(match.group(0))
        if parsed:
            return parsed, "iso-text"
    retry = parse_retry_after(text, now)
    if retry:
        return retry
    return parse_clock_reset(text, now)


def contains_limit_signal(text: str) -> tuple[bool, str]:
    lowered = text.lower()
    for pattern in LIMIT_PATTERNS:
        if pattern in lowered:
            return True, pattern
    if "approaching" in lowered and "limit" in lowered:
        return True, "approaching+limit"
    if "limit" in lowered and "reset" in lowered:
        return True, "limit+reset"
    return False, ""


def failure_report_signal(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    findings = payload.get("findings")
    if not isinstance(findings, list):
        return None
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        if finding.get("id") != "AUTONOMY-PROVIDER-LIMIT":
            continue
        evidence = finding.get("evidence") if isinstance(finding.get("evidence"), dict) else {}
        return {
            "detected": True,
            "pattern": evidence.get("pattern") or "AUTONOMY-PROVIDER-LIMIT",
            "finding_id": "AUTONOMY-PROVIDER-LIMIT",
            "source": FAILURE_REPORT,
            "excerpt": evidence.get("excerpt") or finding.get("message") or "",
        }
    return None


def detect_signal(source: str, payload: Any) -> dict[str, Any]:
    if source == "failure-report":
        from_report = failure_report_signal(payload)
        if from_report:
            return from_report
    text = collect_text(payload)
    detected, pattern = contains_limit_signal(text)
    return {
        "detected": detected,
        "pattern": pattern,
        "finding_id": "",
        "source": source,
        "excerpt": text[:500],
    }


def resolve_reset(payload: Any, signal: dict[str, Any], now: datetime, fallback_minutes: int) -> dict[str, Any]:
    field_reset = find_field_reset(payload, now)
    if field_reset:
        reset_at, reset_source = field_reset
    else:
        text_reset = parse_first_datetime(collect_text(payload), now)
        if not text_reset and signal.get("excerpt"):
            text_reset = parse_first_datetime(str(signal["excerpt"]), now)
        if text_reset:
            reset_at, reset_source = text_reset
        else:
            reset_at = now + timedelta(minutes=fallback_minutes)
            reset_source = "fallback"
    return {
        "reset_at": iso_z(reset_at),
        "reset_epoch": int(reset_at.timestamp()),
        "reset_source": reset_source,
        "fallback_minutes": fallback_minutes,
        "fallback_used": reset_source == "fallback",
    }


def resume_shell(root: Path, reset_at: str, reset_epoch: int) -> str:
    marker = root / ".vibeos/autonomy/limit-aware/resume-once.done"
    evidence_dir = root / ".vibeos/evidence/limit-resume"
    return "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "",
            "# VibeOS provider/session-limit one-shot resume profile.",
            "# This script is pure local control-plane logic until it reaches night-loop.sh.",
            f"ROOT={quote(root)}",
            'SCRIPTS_DIR="${VIBEOS_SCRIPTS_DIR:-$ROOT/.vibeos/scripts}"',
            f"MARKER={quote(marker)}",
            f"RESET_AT={quote(reset_at)}",
            f"RESET_EPOCH={reset_epoch}",
            'NOW_EPOCH="$(date -u +%s)"',
            'if [ "$NOW_EPOCH" -lt "$RESET_EPOCH" ]; then',
            '  echo "[limit-aware-resume] waiting until $RESET_AT"',
            "  exit 0",
            "fi",
            'if [ -f "$MARKER" ]; then',
            '  echo "[limit-aware-resume] one-shot marker exists: $MARKER"',
            "  exit 0",
            "fi",
            'mkdir -p "$(dirname "$MARKER")"',
            'printf \'{"resumed_at":"%s","reset_at":"%s"}\\n\' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$RESET_AT" > "$MARKER"',
            'python3 "$SCRIPTS_DIR/autonomy-scheduler-guard.py" --project-dir "$ROOT" --json',
            f'bash "$SCRIPTS_DIR/night-loop.sh" --project-dir "$ROOT" --evidence-dir {quote(evidence_dir)} --execute --json',
            "",
        ]
    )


def cron_profile(root: Path, reset_dt: datetime) -> str:
    script = root / ".vibeos/autonomy/limit-aware/resume-once.sh"
    log = root / ".vibeos/autonomy/limit-aware/resume-once.log"
    return "\n".join(
        [
            "# VibeOS one-shot provider/session-limit resume profile.",
            "# Review before installing. The shell script has its own reset-time and one-shot guards.",
            "CRON_TZ=UTC",
            f"{reset_dt.minute} {reset_dt.hour} {reset_dt.day} {reset_dt.month} * bash {quote(script)} >> {quote(log)} 2>&1",
            "",
        ]
    )


def launchd_profile(root: Path, reset_dt: datetime) -> str:
    script = root / ".vibeos/autonomy/limit-aware/resume-once.sh"
    log = root / ".vibeos/autonomy/limit-aware/resume-once.log"
    return "\n".join(
        [
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\"",
            "  \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">",
            "<plist version=\"1.0\">",
            "<dict>",
            "  <key>Label</key>",
            "  <string>com.vibeos.limit-resume</string>",
            "  <key>ProgramArguments</key>",
            "  <array>",
            "    <string>/bin/bash</string>",
            f"    <string>{script}</string>",
            "  </array>",
            "  <key>WorkingDirectory</key>",
            f"  <string>{root}</string>",
            "  <key>StartCalendarInterval</key>",
            "  <dict>",
            f"    <key>Month</key><integer>{reset_dt.month}</integer>",
            f"    <key>Day</key><integer>{reset_dt.day}</integer>",
            f"    <key>Hour</key><integer>{reset_dt.hour}</integer>",
            f"    <key>Minute</key><integer>{reset_dt.minute}</integer>",
            "  </dict>",
            "  <key>StandardOutPath</key>",
            f"  <string>{log}</string>",
            "  <key>StandardErrorPath</key>",
            f"  <string>{log}</string>",
            "  <!-- Review timezone behavior before loading. resume-once.sh prevents pre-reset execution. -->",
            "</dict>",
            "</plist>",
            "",
        ]
    )


def write_artifacts(root: Path, schedule: dict[str, Any], no_write: bool) -> list[dict[str, Any]]:
    out_dir = root / STATE_DIR
    reset_dt = datetime.fromtimestamp(int(schedule["reset_epoch"]), timezone.utc)
    artifacts = [
        ("shell", out_dir / "resume-once.sh", resume_shell(root, schedule["reset_at"], int(schedule["reset_epoch"]))),
        ("cron", out_dir / "resume-once.cron", cron_profile(root, reset_dt)),
        ("launchd", out_dir / "com.vibeos.limit-resume.plist", launchd_profile(root, reset_dt)),
    ]
    report: list[dict[str, Any]] = []
    for kind, path, content in artifacts:
        item = {"kind": kind, "path": str(path), "written": not no_write}
        if no_write:
            item["content"] = content
        else:
            write_text(path, content)
            if kind == "shell":
                path.chmod(0o755)
        report.append(item)
    return report


def status_for_source(source: str) -> str:
    if source == "notification":
        return "LIMIT_WARNING_SCHEDULED"
    return "PAUSED_FOR_LIMIT"


def dispatch_policy(root: Path, report: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": report["generated_at"],
        "project_dir": str(root),
        "large_dispatch_allowed": False,
        "reason": "provider/session limit warning detected",
        "large_dispatch_definition": "multi-agent audit sweeps, parallel lanes, and high-tier workflows keyed by wo_class/governance tier",
        "reset_at": report["schedule"]["reset_at"],
    }


def update_loop_state(root: Path, report: dict[str, Any]) -> None:
    state_path = root / LOOP_STATE
    existing = load_json(state_path, {})
    if not isinstance(existing, dict):
        existing = {}
    summary = existing.get("summary")
    if not isinstance(summary, dict):
        summary = {}
    summary.update(
        {
            "status": "PAUSED_FOR_LIMIT",
            "next_resume_after": report["schedule"]["reset_at"],
            "limit_pause_source": report["source"],
        }
    )
    existing["summary"] = summary
    existing["limit_pause"] = {
        "generated_at": report["generated_at"],
        "reset_at": report["schedule"]["reset_at"],
        "reset_source": report["schedule"]["reset_source"],
        "signal": report["signal"],
    }
    write_json(state_path, existing)


def build_report(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    now = parse_now(args.now)
    input_text, input_path = read_input(root, args)
    payload = parse_payload(input_text)
    signal = detect_signal(args.source, payload)
    generated_at = iso_z(now) if args.now else iso_now()

    if not signal["detected"]:
        return {
            "schema_version": "1.0",
            "framework_version": FRAMEWORK_VERSION,
            "generated_at": generated_at,
            "project_dir": str(root),
            "source": args.source,
            "input_path": input_path,
            "signal": signal,
            "artifacts": [],
            "summary": {
                "status": "no_limit_signal",
                "scheduled": False,
                "state_file": str(Path(STATE_DIR) / STATE_FILE),
            },
        }

    schedule = resolve_reset(payload, signal, now, args.fallback_minutes)
    status = status_for_source(args.source)
    report = {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": generated_at,
        "project_dir": str(root),
        "source": args.source,
        "input_path": input_path,
        "signal": signal,
        "schedule": schedule,
        "artifacts": write_artifacts(root, schedule, args.no_write),
        "dispatch_policy": {},
        "summary": {
            "status": status,
            "scheduled": True,
            "state_file": str(Path(STATE_DIR) / STATE_FILE),
            "event_log": str(Path(STATE_DIR) / EVENTS_FILE),
        },
    }
    report["dispatch_policy"] = dispatch_policy(root, report)
    return report


def persist_report(root: Path, report: dict[str, Any], no_write: bool) -> None:
    if no_write or not report["summary"].get("scheduled"):
        return
    out_dir = root / STATE_DIR
    write_json(out_dir / STATE_FILE, report)
    write_json(out_dir / DISPATCH_POLICY_FILE, report["dispatch_policy"])
    append_jsonl(
        out_dir / EVENTS_FILE,
        {
            "generated_at": report["generated_at"],
            "source": report["source"],
            "status": report["summary"]["status"],
            "reset_at": report["schedule"]["reset_at"],
            "reset_source": report["schedule"]["reset_source"],
            "pattern": report["signal"].get("pattern", ""),
        },
    )
    if report["summary"]["status"] == "PAUSED_FOR_LIMIT":
        update_loop_state(root, report)


def print_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    summary = report["summary"]
    print(
        "[limit-aware-scheduler] "
        f"{summary['status']}: scheduled={str(summary['scheduled']).lower()}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate limit-aware VibeOS resume artifacts.")
    parser.add_argument("--project-dir", default="", help="Project root. Defaults to PROJECT_ROOT or cwd.")
    parser.add_argument(
        "--source",
        default="notification",
        choices=["notification", "headless-json", "failure-report", "text"],
        help="Local source payload type.",
    )
    parser.add_argument("--input", default="", help="Input file path or '-' for stdin.")
    parser.add_argument("--now", default="", help="Deterministic current time for tests.")
    parser.add_argument("--fallback-minutes", type=int, default=60, help="Fallback reset delay when no reset is parsed.")
    parser.add_argument("--no-write", action="store_true", help="Do not write state or profile artifacts.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.fallback_minutes < 1:
        print("[limit-aware-scheduler] FAIL: --fallback-minutes must be >= 1", file=sys.stderr)
        return 2
    root = project_root(args.project_dir)
    try:
        report = build_report(root, args)
    except (OSError, ValueError) as exc:
        print(f"[limit-aware-scheduler] FAIL: {exc}", file=sys.stderr)
        return 2
    persist_report(root, report, args.no_write)
    print_report(report, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
