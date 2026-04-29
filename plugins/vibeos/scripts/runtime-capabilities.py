#!/usr/bin/env python3
"""Detect local VibeOS runtime capabilities for Codex and Claude Code."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.2.0"
TIMEOUT_SECONDS = 10


def run_command(argv: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(
            argv,
            check=False,
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        return 127, "", "command not found"
    except subprocess.TimeoutExpired:
        return 124, "", "command timed out"
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def parse_codex_version(output: str) -> str | None:
    match = re.search(r"codex(?:-cli)?\s+([0-9]+(?:\.[0-9]+){1,3})", output)
    return match.group(1) if match else None


def parse_codex_features(output: str) -> dict[str, dict[str, Any]]:
    features: dict[str, dict[str, Any]] = {}
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("Inspect feature flags") or line.startswith("Usage:"):
            continue
        match = re.match(r"^([A-Za-z0-9_]+)\s+(.+?)\s+(true|false)$", line)
        if not match:
            continue
        name, stage, enabled = match.groups()
        features[name] = {"stage": stage.strip(), "enabled": enabled == "true"}
    return features


def parse_claude_version(output: str) -> str | None:
    match = re.search(r"([0-9]+(?:\.[0-9]+){1,3})", output)
    return match.group(1) if match else None


def parse_claude_agents(output: str) -> dict[str, Any]:
    active_count = None
    match = re.search(r"(\d+)\s+active agents", output)
    if match:
        active_count = int(match.group(1))

    agents = []
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if "·" in line:
            name = line.split("·", 1)[0].strip()
            if name:
                agents.append(name)

    return {
        "active_count": active_count,
        "agents": agents,
        "vibeos_agents": [name for name in agents if name.startswith("vibeos:")],
    }


def bool_feature(features: dict[str, dict[str, Any]], name: str) -> bool:
    return bool(features.get(name, {}).get("enabled"))


def status(value: bool) -> str:
    return "available" if value else "unavailable"


def detect_codex() -> dict[str, Any]:
    path = shutil.which("codex")
    result: dict[str, Any] = {
        "available": bool(path),
        "path": path,
        "version": None,
        "features": {},
        "capabilities": {},
        "limitations": [],
        "errors": [],
    }
    if not path:
        result["errors"].append("codex command not found")
        result["capabilities"] = {
            "subagents": "unavailable",
            "hooks": "unavailable",
            "app_worktrees": "unavailable",
            "automations": "unavailable",
            "repo_skills": "unknown",
        }
        return result

    code, stdout, stderr = run_command(["codex", "--version"])
    if code == 0:
        result["version"] = parse_codex_version(stdout)
    else:
        result["errors"].append(f"codex --version failed: {stderr or code}")

    code, stdout, stderr = run_command(["codex", "features", "list"])
    if code == 0:
        result["features"] = parse_codex_features(stdout)
    else:
        result["errors"].append(f"codex features list failed: {stderr or code}")

    features = result["features"]
    result["capabilities"] = {
        "subagents": status(bool_feature(features, "multi_agent")),
        "hooks": status(bool_feature(features, "codex_hooks")),
        "app_worktrees": status(bool_feature(features, "apps")),
        "automations": status(bool_feature(features, "apps")),
        "repo_skills": "available",
        "plugins": status(bool_feature(features, "plugins")),
        "browser_use": status(bool_feature(features, "browser_use")),
    }
    result["limitations"] = [
        "Codex hooks are not treated as Claude Code hook parity; use Git hooks and VibeOS gates for commit-boundary enforcement.",
        "Subagent use still requires explicit orchestration and bounded ownership.",
    ]
    return result


def detect_claude() -> dict[str, Any]:
    path = shutil.which("claude")
    result: dict[str, Any] = {
        "available": bool(path),
        "path": path,
        "version": None,
        "agents": {"active_count": None, "agents": [], "vibeos_agents": []},
        "capabilities": {},
        "limitations": [],
        "errors": [],
    }
    if not path:
        result["errors"].append("claude command not found")
        result["capabilities"] = {
            "subagents": "unavailable",
            "worktree_sessions": "unavailable",
            "hooks": "unknown",
            "agent_teams": "unknown",
        }
        return result

    code, stdout, stderr = run_command(["claude", "--version"])
    if code == 0:
        result["version"] = parse_claude_version(stdout)
    else:
        result["errors"].append(f"claude --version failed: {stderr or code}")

    code, stdout, stderr = run_command(["claude", "agents"])
    if code == 0:
        result["agents"] = parse_claude_agents(stdout)
    else:
        result["errors"].append(f"claude agents failed: {stderr or code}")

    code, stdout, stderr = run_command(["claude", "--help"])
    help_output = stdout if code == 0 else ""
    if code != 0:
        result["errors"].append(f"claude --help failed: {stderr or code}")

    result["capabilities"] = {
        "subagents": status(bool(result["agents"]["active_count"])),
        "worktree_sessions": status("--worktree" in help_output),
        "custom_agents_cli": status("--agents" in help_output),
        "hooks": "available",
        "agent_teams": "unknown",
    }
    result["limitations"] = [
        "Subagents cannot spawn subagents; orchestration must stay in the main thread.",
        "Agent teams are treated as optional/experimental until explicitly detected for the local version.",
    ]
    return result


def recommend_strategy(codex: dict[str, Any], claude: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    codex_caps = codex.get("capabilities", {})
    claude_caps = claude.get("capabilities", {})

    if codex_caps.get("subagents") == "available":
        primary = "codex"
        mode = "codex-multi-agent"
        reasons.append("Codex multi-agent capability is available locally.")
    elif claude_caps.get("subagents") == "available":
        primary = "claude"
        mode = "claude-subagents"
        reasons.append("Claude Code subagents are available locally.")
    else:
        primary = "sequential"
        mode = "single-context"
        reasons.append("No local multi-agent runtime was detected.")

    if codex_caps.get("hooks") == "available" or claude_caps.get("hooks") == "available":
        reasons.append("Runtime hooks are available on at least one surface, but Git hooks remain the cross-runtime enforcement fallback.")
    else:
        reasons.append("No runtime hook surface was detected; rely on explicit gates and Git hooks.")

    return {
        "recommended_primary": primary,
        "orchestration_mode": mode,
        "requires_git_hooks": True,
        "requires_explicit_gates": True,
        "reasons": reasons,
    }


def build_matrix(project_dir: Path) -> dict[str, Any]:
    codex = detect_codex()
    claude = detect_claude()
    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "project_dir": str(project_dir),
        "runtimes": {
            "codex": codex,
            "claude": claude,
        },
        "strategy": recommend_strategy(codex, claude),
        "sources": [
            "local: codex --version",
            "local: codex features list",
            "local: claude --version",
            "local: claude agents",
            "local: claude --help",
        ],
    }


def default_output(project_dir: Path) -> Path:
    return project_dir / ".vibeos" / "runtime-capabilities.json"


def write_matrix(matrix: dict[str, Any], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(matrix, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def summary(matrix: dict[str, Any], out_path: Path) -> str:
    codex = matrix["runtimes"]["codex"]
    claude = matrix["runtimes"]["claude"]
    strategy = matrix["strategy"]
    lines = [
        "[runtime-capabilities] Runtime Capability Matrix",
        f"[runtime-capabilities] Output: {out_path}",
        f"[runtime-capabilities] Codex: {'available' if codex['available'] else 'missing'}"
        f" version={codex.get('version') or 'unknown'}"
        f" subagents={codex['capabilities'].get('subagents', 'unknown')}"
        f" hooks={codex['capabilities'].get('hooks', 'unknown')}",
        f"[runtime-capabilities] Claude: {'available' if claude['available'] else 'missing'}"
        f" version={claude.get('version') or 'unknown'}"
        f" subagents={claude['capabilities'].get('subagents', 'unknown')}"
        f" worktrees={claude['capabilities'].get('worktree_sessions', 'unknown')}",
        f"[runtime-capabilities] Strategy: {strategy['recommended_primary']} / {strategy['orchestration_mode']}",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Detect VibeOS runtime capabilities.")
    parser.add_argument("--project-dir", default=".", help="Project directory to write runtime state into.")
    parser.add_argument("--out", default="", help="Output JSON path. Defaults to .vibeos/runtime-capabilities.json.")
    parser.add_argument("--json", action="store_true", help="Print the full JSON matrix to stdout.")
    parser.add_argument("--quiet", action="store_true", help="Do not print the human summary.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_dir = Path(args.project_dir).resolve()
    out_path = Path(args.out).resolve() if args.out else default_output(project_dir)
    matrix = build_matrix(project_dir)
    write_matrix(matrix, out_path)

    if args.json:
        print(json.dumps(matrix, indent=2, sort_keys=True))
    elif not args.quiet:
        print(summary(matrix, out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
