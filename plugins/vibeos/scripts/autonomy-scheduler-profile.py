#!/usr/bin/env python3
"""Generate dry-run-first scheduler profiles for VibeOS long-run autonomy."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.2.0"
SUPPORTED_PROFILES = {"shell", "cron", "launchd", "github-actions"}


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


def quote(value: Path | str) -> str:
    return shlex.quote(str(value))


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def tick_command(root: Path, provider: str, launch_runtime: bool) -> str:
    scripts = root / ".vibeos/scripts"
    adapter_args = [
        "python3",
        str(scripts / "autonomy-runtime-adapter.py"),
        "--project-dir",
        str(root),
        "--provider",
        provider,
    ]
    if launch_runtime:
        adapter_args.append("--execute")
    parts = [
        f"cd {quote(root)}",
        f"python3 {quote(scripts / 'autonomy-scheduler-guard.py')} --project-dir {quote(root)} --json",
        f"bash {quote(scripts / 'detect-runtime-capabilities.sh')} --project-dir {quote(root)} --quiet",
        f"python3 {quote(scripts / 'autonomy-loop.py')} --project-dir {quote(root)} --execute --json",
        " ".join(quote(part) for part in adapter_args) + " --json",
    ]
    return " && ".join(parts)


def shell_profile(root: Path, provider: str, launch_runtime: bool) -> str:
    command = tick_command(root, provider, launch_runtime)
    return "\n".join(
        [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "",
            "# VibeOS long-run autonomy scheduler tick.",
            "# Safe default: local VibeOS loop commands execute;",
            "# model runtime launches only when generated with --launch-runtime.",
            command,
            "",
        ]
    )


def cron_profile(root: Path, interval_minutes: int, provider: str, launch_runtime: bool) -> str:
    minute = f"*/{interval_minutes}" if interval_minutes > 1 else "*"
    log_path = root / ".vibeos/autonomy/scheduler/cron.log"
    command = tick_command(root, provider, launch_runtime)
    return "\n".join(
        [
            "# VibeOS long-run autonomy cron profile.",
            "# Install manually only after reviewing the command and runtime launch mode.",
            f"{minute} * * * * {command} >> {quote(log_path)} 2>&1",
            "",
        ]
    )


def launchd_profile(root: Path, interval_minutes: int, provider: str, launch_runtime: bool) -> str:
    script_path = root / ".vibeos/autonomy/scheduler/vibeos-autonomy-tick.sh"
    log_path = root / ".vibeos/autonomy/scheduler/launchd.log"
    return "\n".join(
        [
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
            "<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\"",
            "  \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">",
            "<plist version=\"1.0\">",
            "<dict>",
            "  <key>Label</key>",
            "  <string>com.vibeos.autonomy</string>",
            "  <key>ProgramArguments</key>",
            "  <array>",
            "    <string>/bin/bash</string>",
            f"    <string>{script_path}</string>",
            "  </array>",
            "  <key>WorkingDirectory</key>",
            f"  <string>{root}</string>",
            "  <key>StartInterval</key>",
            f"  <integer>{interval_minutes * 60}</integer>",
            "  <key>StandardOutPath</key>",
            f"  <string>{log_path}</string>",
            "  <key>StandardErrorPath</key>",
            f"  <string>{log_path}</string>",
            f"  <!-- provider={provider}; launch_runtime={str(launch_runtime).lower()} -->",
            "</dict>",
            "</plist>",
            "",
        ]
    )


def github_actions_profile(root: Path, interval_minutes: int, provider: str, launch_runtime: bool) -> str:
    adapter_execute = " --execute" if launch_runtime else ""
    schedule = f"*/{interval_minutes} * * * *"
    return "\n".join(
        [
            "name: VibeOS Autonomy Tick",
            "",
            "on:",
            "  workflow_dispatch:",
            "  schedule:",
            f"    - cron: '{schedule}'",
            "",
            "jobs:",
            "  autonomy:",
            "    runs-on: ubuntu-latest",
            "    timeout-minutes: 30",
            "    steps:",
            "      - uses: actions/checkout@v4",
            "      - uses: actions/setup-python@v5",
            "        with:",
            "          python-version: '3.x'",
            "      - name: Guard autonomy scheduler tick",
            "        run: python3 .vibeos/scripts/autonomy-scheduler-guard.py --project-dir . --json",
            "      - name: Detect runtime capabilities",
            "        run: bash .vibeos/scripts/detect-runtime-capabilities.sh --project-dir . --quiet",
            "      - name: Run autonomy loop tick",
            "        run: python3 .vibeos/scripts/autonomy-loop.py --project-dir . --execute --json",
            "      - name: Plan runtime handoff",
            "        run: >",
            "          python3 .vibeos/scripts/autonomy-runtime-adapter.py",
            f"          --project-dir . --provider {provider}{adapter_execute} --json",
            "      - name: Upload autonomy evidence",
            "        uses: actions/upload-artifact@v4",
            "        if: always()",
            "        with:",
            "          name: vibeos-autonomy",
            "          path: .vibeos/autonomy/",
            "",
            f"# Generated for project: {root}",
        ]
    )


def selected_profiles(value: str) -> list[str]:
    if value == "all":
        return ["shell", "cron", "launchd", "github-actions"]
    profiles = [item.strip() for item in value.split(",") if item.strip()]
    unknown = sorted(set(profiles) - SUPPORTED_PROFILES)
    if unknown:
        raise ValueError(f"unknown profile(s): {', '.join(unknown)}")
    return profiles


def profile_content(
    root: Path,
    profile: str,
    interval_minutes: int,
    provider: str,
    launch_runtime: bool,
) -> tuple[Path, str]:
    out_dir = root / ".vibeos/autonomy/scheduler"
    if profile == "shell":
        return out_dir / "vibeos-autonomy-tick.sh", shell_profile(root, provider, launch_runtime)
    if profile == "cron":
        return out_dir / "vibeos-autonomy.cron", cron_profile(root, interval_minutes, provider, launch_runtime)
    if profile == "launchd":
        return out_dir / "com.vibeos.autonomy.plist", launchd_profile(root, interval_minutes, provider, launch_runtime)
    return (
        out_dir / "vibeos-autonomy.github-actions.yml",
        github_actions_profile(root, interval_minutes, provider, launch_runtime),
    )


def build_report(root: Path, args: argparse.Namespace) -> dict[str, Any]:
    profiles = selected_profiles(args.profile)
    artifacts = []
    for profile in profiles:
        path, content = profile_content(root, profile, args.interval_minutes, args.provider, args.launch_runtime)
        artifact = {
            "profile": profile,
            "path": str(path),
            "launch_runtime": args.launch_runtime,
            "provider": args.provider,
        }
        if not args.no_write:
            write_text(path, content)
            if profile == "shell":
                path.chmod(0o755)
            artifact["written"] = True
        else:
            artifact["written"] = False
            artifact["content"] = content
        artifacts.append(artifact)

    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": iso_now(),
        "project_dir": str(root),
        "interval_minutes": args.interval_minutes,
        "provider": args.provider,
        "launch_runtime": args.launch_runtime,
        "artifacts": artifacts,
        "summary": {
            "status": "pass",
            "profiles": profiles,
            "profile_count": len(profiles),
            "state_file": ".vibeos/autonomy/scheduler-profile.json",
        },
    }


def print_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    summary = report["summary"]
    print(
        "[autonomy-scheduler-profile] "
        f"{summary['status']}: profiles={','.join(summary['profiles'])}"
    )
    print("[autonomy-scheduler-profile] State: .vibeos/autonomy/scheduler-profile.json")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate VibeOS autonomy scheduler profiles.")
    parser.add_argument("--project-dir", default="", help="Project root. Defaults to PROJECT_ROOT or cwd.")
    parser.add_argument("--profile", default="all", help="all, or comma-separated shell,cron,launchd,github-actions.")
    parser.add_argument("--interval-minutes", type=int, default=15, help="Scheduler cadence in minutes.")
    parser.add_argument(
        "--provider",
        default="auto",
        choices=["auto", "codex", "claude"],
        help="Runtime adapter provider.",
    )
    parser.add_argument(
        "--launch-runtime",
        action="store_true",
        help="Include runtime adapter --execute in generated profiles.",
    )
    parser.add_argument("--no-write", action="store_true", help="Print/report profiles without writing artifacts.")
    parser.add_argument("--json", action="store_true", help="Print JSON report.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.interval_minutes < 1:
        print("[autonomy-scheduler-profile] FAIL: --interval-minutes must be >= 1", file=sys.stderr)
        return 2
    root = project_root(args.project_dir)
    try:
        report = build_report(root, args)
    except ValueError as exc:
        print(f"[autonomy-scheduler-profile] FAIL: {exc}", file=sys.stderr)
        return 2
    if not args.no_write:
        write_json(root / ".vibeos/autonomy/scheduler-profile.json", report)
    print_report(report, args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
