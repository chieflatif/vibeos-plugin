#!/usr/bin/env python3
# FILE-SIZE-EXCEPTION: WO-145 — framework governance script (cohesive single-purpose validator/orchestrator); size accepted per operator decision, see docs/planning/WO-145-phase34-gate-floor-remediation.md
"""Detect local VibeOS runtime capabilities for Codex and Claude Code."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.4.0"
TIMEOUT_SECONDS = 10

# Claude Code capability version thresholds (dotted-int tuples).
SUBAGENTS_MIN_VERSION = (2, 0, 0)
AGENT_TEAMS_MIN_VERSION = (2, 1, 32)
DYNAMIC_WORKFLOWS_MIN_VERSION = (2, 1, 154)
# Operator opt-in / opt-out environment variables.
AGENT_TEAMS_ENV = "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS"
DYNAMIC_WORKFLOWS_DISABLE_ENV = "CLAUDE_CODE_DISABLE_WORKFLOWS"
LEGACY_DYNAMIC_WORKFLOWS_DISABLE_ENV = "CLAUDE_DISABLE_DYNAMIC_WORKFLOWS"
DYNAMIC_WORKFLOWS_DISABLE_ENVS = (
    DYNAMIC_WORKFLOWS_DISABLE_ENV,
    LEGACY_DYNAMIC_WORKFLOWS_DISABLE_ENV,
)


def version_tuple(version: str | None) -> tuple[int, ...]:
    if not version:
        return ()
    parts: list[int] = []
    for chunk in version.split("."):
        m = re.match(r"\d+", chunk)
        if not m:
            break
        parts.append(int(m.group(0)))  # tolerate suffixes, e.g. "170-beta" -> 170
    return tuple(parts)


def version_ge(version: str | None, threshold: tuple[int, ...]) -> bool:
    """True when a dotted-int version is >= threshold (numeric, not lexical)."""
    vt = version_tuple(version)
    if not vt:
        return False
    length = max(len(vt), len(threshold))
    vt_p = vt + (0,) * (length - len(vt))
    th_p = threshold + (0,) * (length - len(threshold))
    return vt_p >= th_p


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _truthy_envs(names: tuple[str, ...]) -> list[str]:
    return [name for name in names if _env_truthy(name)]


def _fmt_version(t: tuple[int, ...]) -> str:
    return ".".join(str(x) for x in t)


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


def parse_claude_agents_json(output: str) -> dict[str, Any]:
    """Tolerant parser for `claude agents --json` (non-TTY retry path)."""
    try:
        data = json.loads(output)
    except (ValueError, TypeError):
        return {"active_count": None, "agents": [], "vibeos_agents": []}
    if isinstance(data, dict):
        data = data.get("agents", data.get("active", []))
    names: list[str] = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                name = item.get("name") or item.get("agent") or ""
            else:
                name = str(item)
            name = name.strip()
            if name:
                names.append(name)
    return {
        "active_count": len(names) if names else None,
        "agents": names,
        "vibeos_agents": [n for n in names if n.startswith("vibeos:")],
    }


def compute_claude_capabilities(
    version: str | None,
    help_output: str,
    path: str | None,
    agents_evidence: str,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Derive Claude capabilities + evidence from version, help text, and binary presence.

    Subagent availability is version-gated (authoritative) rather than dependent on
    `claude agents` active-count, which is empty in non-TTY runs.
    """
    binary_present = bool(path)
    subagents = binary_present and version_ge(version, SUBAGENTS_MIN_VERSION)

    agent_teams_optin = _env_truthy(AGENT_TEAMS_ENV)
    agent_teams_version_ok = version_ge(version, AGENT_TEAMS_MIN_VERSION)
    agent_teams = (
        "experimental_available"
        if binary_present and agent_teams_optin and agent_teams_version_ok
        else "unavailable"
    )

    disabled_envs = _truthy_envs(DYNAMIC_WORKFLOWS_DISABLE_ENVS)
    dynamic_version_ok = version_ge(version, DYNAMIC_WORKFLOWS_MIN_VERSION)
    dynamic_workflows = status(binary_present and dynamic_version_ok and not disabled_envs)

    capabilities = {
        "subagents": status(subagents),
        "worktree_sessions": status("--worktree" in help_output),
        "custom_agents_cli": status("--agents" in help_output),
        "hooks": "available",
        "agent_teams": agent_teams,
        "dynamic_workflows": dynamic_workflows,
        "headless": status(binary_present),
    }
    ver = version or "unknown"
    evidence = {
        "subagents": (
            f"claude {ver} present at {path}; >= {_fmt_version(SUBAGENTS_MIN_VERSION)} "
            f"({agents_evidence or 'version-gated'})"
            if binary_present
            else "claude binary not found"
        ),
        "agent_teams": (
            f"env {AGENT_TEAMS_ENV}={'set' if agent_teams_optin else 'unset'}; "
            f"version {'>=' if agent_teams_version_ok else '<'} {_fmt_version(AGENT_TEAMS_MIN_VERSION)}"
        ),
        "dynamic_workflows": (
            f"version {'>=' if dynamic_version_ok else '<'} {_fmt_version(DYNAMIC_WORKFLOWS_MIN_VERSION)}"
            + (f"; disabled via {', '.join(disabled_envs)}" if disabled_envs else "")
        ),
        "headless": (
            f"claude binary present at {path}" if binary_present else "claude binary not found"
        ),
    }
    return capabilities, evidence


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
        capabilities, evidence = compute_claude_capabilities(None, "", None, "")
        result["capabilities"] = capabilities
        result["capability_evidence"] = evidence
        return result

    code, stdout, stderr = run_command(["claude", "--version"])
    if code == 0:
        result["version"] = parse_claude_version(stdout)
    else:
        result["errors"].append(f"claude --version failed: {stderr or code}")

    # `claude agents` is TTY-oriented; on non-TTY failure, retry with --json.
    agents_evidence = "claude agents"
    code, stdout, stderr = run_command(["claude", "agents"])
    if code == 0 and stdout:
        result["agents"] = parse_claude_agents(stdout)
    else:
        code_j, stdout_j, stderr_j = run_command(["claude", "agents", "--json"])
        if code_j == 0 and stdout_j:
            result["agents"] = parse_claude_agents_json(stdout_j)
            agents_evidence = "claude agents --json (non-TTY retry)"
        else:
            result["errors"].append(
                f"claude agents failed: {stderr or code}; --json retry: {stderr_j or code_j}"
            )
            agents_evidence = "version-gated (claude agents unavailable in this context)"

    code, stdout, stderr = run_command(["claude", "--help"])
    help_output = stdout if code == 0 else ""
    if code != 0:
        result["errors"].append(f"claude --help failed: {stderr or code}")

    capabilities, evidence = compute_claude_capabilities(
        result["version"], help_output, path, agents_evidence
    )
    result["capabilities"] = capabilities
    result["capability_evidence"] = evidence
    result["limitations"] = [
        "Subagents cannot spawn subagents; orchestration must stay in the main thread.",
        "Agent teams are experimental and gated behind an explicit opt-in env var and version.",
    ]
    return result


def workflow_governance_policy(claude: dict[str, Any]) -> dict[str, Any]:
    caps = claude.get("capabilities", {})
    evidence = claude.get("capability_evidence", {})
    status_value = caps.get("dynamic_workflows", "unavailable")
    return {
        "schema_version": "1.0",
        "status": status_value,
        "capability": "claude.dynamic_workflows",
        "capability_evidence": evidence.get("dynamic_workflows", ""),
        "saved_project_workflow_dir": ".claude/workflows",
        "recurring_use_policy": "saved+reviewed scripts only after a bounded successful run",
        "slice_first_cost_probe_required": True,
        "project_governance_writes_allowed": False,
        "governance_write_no_touch": [
            "docs/planning/**",
            ".vibeos/**",
            ".claude/settings*.json",
            ".claude/workflows/**",
        ],
        "disable_paths": [
            "/config -> Dynamic workflows off",
            "~/.claude/settings.json: {\"disableWorkflows\": true}",
            "managed settings: {\"disableWorkflows\": true}",
            f"{DYNAMIC_WORKFLOWS_DISABLE_ENV}=1",
        ],
        "documented_limits": {
            "max_concurrent_agents": 16,
            "max_total_agents_per_run": 1000,
            "resume_scope": "same Claude Code session only",
        },
        "adoption_gate": "WO-124 must run a bounded slice and compare workflow evidence against the subagent baseline before default adoption.",
        "limitations": [
            "Dynamic workflow availability does not remove VibeOS gates, hooks, Work Orders, or evidence requirements.",
            "Workflow agents may edit implementation files according to the active tool allowlist, but recurring workflow scripts and governance files require separate review.",
            "Large workflow runs can consume materially more tokens; run a narrow cost probe first.",
        ],
    }


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
        "workflow_governance": workflow_governance_policy(claude),
        "sources": [
            "local: codex --version",
            "local: codex features list",
            "local: claude --version",
            "local: claude agents (--json retry on non-TTY failure)",
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
        f" worktrees={claude['capabilities'].get('worktree_sessions', 'unknown')}"
        f" workflows={claude['capabilities'].get('dynamic_workflows', 'unknown')}",
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
