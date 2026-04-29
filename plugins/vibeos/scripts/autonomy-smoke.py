#!/usr/bin/env python3
"""Run a disposable VibeOS long-run autonomy smoke test."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.2.0"
REQUIRED_SCRIPTS = [
    "autonomy-heartbeat.py",
    "autonomy-supervisor.py",
    "autonomy-runner.py",
    "autonomy-loop.py",
    "autonomy-runtime-adapter.py",
    "autonomy-failure-detector.py",
    "autonomy-recovery-planner.py",
    "autonomy-recovery-resolution.py",
    "autonomy-scheduler-guard.py",
    "autonomy_lease.py",
    "validate-long-run-autonomy.py",
    "detect-runtime-capabilities.sh",
    "runtime-capabilities.py",
]
OUTPUT_LIMIT = 4000


def iso_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def truncate(value: str) -> str:
    if len(value) <= OUTPUT_LIMIT:
        return value
    return value[:OUTPUT_LIMIT] + "\n[truncated]"


def project_root(value: str) -> Path:
    if value:
        return Path(value).resolve()
    return Path(os.environ.get("PROJECT_ROOT", ".")).resolve()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def source_scripts_dir(value: str) -> Path:
    if value:
        return Path(value).resolve()
    return Path(__file__).resolve().parent


def copy_scripts(source_dir: Path, target: Path) -> list[str]:
    copied = []
    scripts_dir = target / ".vibeos/scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)
    for name in REQUIRED_SCRIPTS:
        source = source_dir / name
        if not source.exists():
            raise FileNotFoundError(f"required script missing: {source}")
        destination = scripts_dir / name
        shutil.copy2(source, destination)
        destination.chmod(0o755)
        copied.append(str(destination.relative_to(target)))
    return copied


def run_step(name: str, argv: list[str], cwd: Path) -> dict[str, Any]:
    record: dict[str, Any] = {"name": name, "argv": argv}
    try:
        completed = subprocess.run(
            argv,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired as exc:
        record.update(
            {
                "exit_code": 124,
                "stdout": truncate(exc.stdout or ""),
                "stderr": truncate(exc.stderr or "command timed out"),
            }
        )
        return record
    record.update(
        {
            "exit_code": completed.returncode,
            "stdout": truncate(completed.stdout),
            "stderr": truncate(completed.stderr),
        }
    )
    return record


def synthetic_capability_matrix(target: Path, provider: str) -> dict[str, Any]:
    codex_available = provider == "codex"
    claude_available = provider == "claude"
    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": iso_now(),
        "project_dir": str(target),
        "runtimes": {
            "codex": {
                "available": codex_available,
                "capabilities": {"subagents": "available" if codex_available else "unavailable"},
            },
            "claude": {
                "available": claude_available,
                "capabilities": {"subagents": "available" if claude_available else "unavailable"},
            },
        },
        "strategy": {
            "recommended_primary": provider if provider in {"codex", "claude"} else "sequential",
            "orchestration_mode": f"{provider}-smoke" if provider in {"codex", "claude"} else "single-context",
        },
    }


def prepare_runtime_capabilities(target: Path, provider: str, steps: list[dict[str, Any]]) -> None:
    if provider == "auto":
        steps.append(
            run_step(
                "detect-runtime-capabilities",
                [
                    "bash",
                    str(target / ".vibeos/scripts/detect-runtime-capabilities.sh"),
                    "--project-dir",
                    str(target),
                    "--quiet",
                ],
                target,
            )
        )
        return
    write_json(target / ".vibeos/runtime-capabilities.json", synthetic_capability_matrix(target, provider))


def run_smoke(target: Path, source_dir: Path, provider: str, execute_runtime: bool) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    copied = copy_scripts(source_dir, target)
    prepare_runtime_capabilities(target, provider, steps)
    steps.append(
        run_step(
            "heartbeat",
            [
                "python3",
                str(target / ".vibeos/scripts/autonomy-heartbeat.py"),
                "--project-dir",
                str(target),
                "--now",
                "2026-04-29T00:00:00Z",
                "--status",
                "running",
                "--iteration",
                "1",
                "--wo",
                "WO-SMOKE",
                "--summary",
                "disposable autonomy smoke run",
                "--next-action",
                "run loop tick",
            ],
            target,
        )
    )
    steps.append(
        run_step(
            "loop",
            [
                "python3",
                str(target / ".vibeos/scripts/autonomy-loop.py"),
                "--project-dir",
                str(target),
                "--now",
                "2026-04-29T00:05:00Z",
                "--json",
            ],
            target,
        )
    )
    adapter_args = [
        "python3",
        str(target / ".vibeos/scripts/autonomy-runtime-adapter.py"),
        "--project-dir",
        str(target),
        "--provider",
        provider if provider in {"codex", "claude"} else "auto",
        "--json",
    ]
    if execute_runtime:
        adapter_args.append("--execute")
    steps.append(run_step("runtime-adapter", adapter_args, target))
    steps.append(
        run_step(
            "validate-long-run-autonomy",
            [
                "python3",
                str(target / ".vibeos/scripts/validate-long-run-autonomy.py"),
                "--project-dir",
                str(target),
                "--now",
                "2026-04-29T00:06:00Z",
                "--json",
            ],
            target,
        )
    )
    steps.append(
        run_step(
            "failure-detector",
            [
                "python3",
                str(target / ".vibeos/scripts/autonomy-failure-detector.py"),
                "--project-dir",
                str(target),
                "--json",
            ],
            target,
        )
    )
    steps.append(
        run_step(
            "recovery-planner",
            [
                "python3",
                str(target / ".vibeos/scripts/autonomy-recovery-planner.py"),
                "--project-dir",
                str(target),
                "--json",
            ],
            target,
        )
    )
    steps.append(
        run_step(
            "recovery-resolution",
            [
                "python3",
                str(target / ".vibeos/scripts/autonomy-recovery-resolution.py"),
                "--project-dir",
                str(target),
                "--json",
            ],
            target,
        )
    )
    steps.append(
        run_step(
            "scheduler-guard",
            [
                "python3",
                str(target / ".vibeos/scripts/autonomy-scheduler-guard.py"),
                "--project-dir",
                str(target),
                "--json",
            ],
            target,
        )
    )
    failures = [step for step in steps if step["exit_code"] != 0]
    status = "pass" if not failures else "fail"
    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": iso_now(),
        "target_dir": str(target),
        "source_scripts_dir": str(source_dir),
        "runtime_provider": provider,
        "execute_runtime": execute_runtime,
        "copied_scripts": copied,
        "steps": steps,
        "summary": {
            "status": status,
            "step_count": len(steps),
            "failed_steps": [step["name"] for step in failures],
            "state_file": ".vibeos/autonomy/smoke-report.json",
        },
    }


def print_report(report: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    summary = report["summary"]
    print(
        "[autonomy-smoke] "
        f"{summary['status']}: target={report['target_dir']} failed={','.join(summary['failed_steps']) or 'none'}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a disposable VibeOS autonomy smoke test.")
    parser.add_argument("--project-dir", default="", help="Existing target dir. Defaults to a disposable temp dir.")
    parser.add_argument("--source-scripts", default="", help="Source scripts dir. Defaults to this script's directory.")
    parser.add_argument(
        "--runtime-provider",
        default="codex",
        choices=["auto", "codex", "claude", "none"],
        help="Runtime capability source for adapter planning.",
    )
    parser.add_argument("--execute-runtime", action="store_true", help="Allow adapter to launch Codex/Claude.")
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the disposable temp dir when --project-dir is omitted.",
    )
    parser.add_argument("--json", action="store_true", help="Print smoke report JSON.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_dir = source_scripts_dir(args.source_scripts)
    temp_dir: tempfile.TemporaryDirectory[str] | None = None
    if args.project_dir:
        target = project_root(args.project_dir)
        target.mkdir(parents=True, exist_ok=True)
    else:
        temp_dir = tempfile.TemporaryDirectory(prefix="vibeos-autonomy-smoke-")
        target = Path(temp_dir.name).resolve()

    try:
        report = run_smoke(target, source_dir, args.runtime_provider, args.execute_runtime)
        write_json(target / ".vibeos/autonomy/smoke-report.json", report)
        print_report(report, args.json)
        return 0 if report["summary"]["status"] == "pass" else 1
    finally:
        if temp_dir is not None and not args.keep:
            temp_dir.cleanup()


if __name__ == "__main__":
    sys.exit(main())
