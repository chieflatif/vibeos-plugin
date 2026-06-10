#!/usr/bin/env python3
"""Generate VibeOS source inventory and public claim ledger.

This utility is intentionally deterministic except for the generated_at field.
It turns repo files and manifests into the count source used by public proof
packages, so website copy does not depend on manually copied numbers.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.2.0"
DEFAULT_OUT = Path("docs/evidence/vnext/generated-inventory.json")
WO_RE = re.compile(r"^WO-\d{3}[a-z]?(?:-|\.md$)", re.I)


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def files(root: Path, pattern: str) -> list[Path]:
    return sorted(path for path in root.glob(pattern) if path.is_file())


def rfiles(root: Path, pattern: str) -> list[Path]:
    return sorted(path for path in root.rglob(pattern) if path.is_file())


def hook_command_count(hooks: dict[str, Any]) -> int:
    total = 0
    for event_blocks in hooks.get("hooks", {}).values():
        for block in event_blocks:
            for hook in block.get("hooks", []):
                if hook.get("type") == "command":
                    total += 1
    return total


def gate_summary(root: Path) -> dict[str, Any]:
    manifest_path = root / "plugins/vibeos/quality-gate-manifest.json"
    manifest = read_json(manifest_path)
    gates = manifest.get("gates", [])
    scripts = [gate.get("script", "") for gate in gates if gate.get("script")]
    missing = []
    for script in sorted(set(scripts)):
        candidate = root / "plugins/vibeos" / script
        if not candidate.exists():
            missing.append(script)
    return {
        "manifest_path": rel(manifest_path, root),
        "manifest_version": manifest.get("version"),
        "gate_entries": len(gates),
        "unique_gate_scripts": len(set(scripts)),
        "phase_counts": dict(sorted(Counter(gate.get("phase", "unknown") for gate in gates).items())),
        "blocking_entries": sum(1 for gate in gates if gate.get("blocking") is True),
        "advisory_entries": sum(1 for gate in gates if gate.get("blocking") is False),
        "missing_gate_scripts": missing,
    }


def build_inventory(root: Path, generated_at: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    plugin_manifest_path = root / "plugins/vibeos/.claude-plugin/plugin.json"
    marketplace_path = root / ".claude-plugin/marketplace.json"
    hook_manifest_path = root / "plugins/vibeos/hook-manifest.json"
    hook_config_path = root / "plugins/vibeos/hooks/hooks.json"
    runtime_path = root / ".vibeos/runtime-capabilities.json"

    hook_manifest = read_json(hook_manifest_path)
    hook_config = read_json(hook_config_path)
    plugin_manifest = read_json(plugin_manifest_path)
    marketplace = read_json(marketplace_path)
    runtime = read_json(runtime_path)

    claude_skills = files(root, "plugins/vibeos/skills/*/SKILL.md")
    codex_skills = files(root, "plugins/vibeos/reference/codex/skills/*/SKILL.md")
    agents = files(root, "plugins/vibeos/agents/*.md")
    hook_scripts = files(root, "plugins/vibeos/hooks/scripts/*.sh")
    scripts = files(root, "plugins/vibeos/scripts/*")
    decision_files = files(root, "plugins/vibeos/decision-engine/*.md")
    reference_files = [p for p in rfiles(root / "plugins/vibeos/reference", "*") if p.is_file()]
    convergence_scripts = files(root, "plugins/vibeos/convergence/*.sh")
    tests = files(root, "tests/test_*.py")
    work_orders = [p for p in files(root, "docs/planning/WO-*.md") if WO_RE.match(p.name)]

    configured_events = sorted(hook_config.get("hooks", {}).keys())
    documented_hooks = hook_manifest.get("hooks", [])
    gate_data = gate_summary(root)

    categories = {
        "claude_skills": {
            "count": len(claude_skills),
            "paths": [rel(path, root) for path in claude_skills],
            "claim_label": "Claude/Cursor source skills",
        },
        "codex_skills": {
            "count": len(codex_skills),
            "paths": [rel(path, root) for path in codex_skills],
            "claim_label": "Codex source skills",
        },
        "agents": {
            "count": len(agents),
            "same_tree_count": sum(1 for path in agents if path.name.endswith("-same-tree.md")),
            "paths": [rel(path, root) for path in agents],
            "claim_label": "Claude/Cursor agent contracts",
        },
        "hook_scripts": {
            "count": len(hook_scripts),
            "paths": [rel(path, root) for path in hook_scripts],
            "claim_label": "Hook scripts",
        },
        "hooks": {
            "documented_count": len(documented_hooks),
            "configured_events": configured_events,
            "configured_command_count": hook_command_count(hook_config),
            "manifest_path": rel(hook_manifest_path, root),
            "config_path": rel(hook_config_path, root),
            "claim_label": "Configured and documented hooks",
        },
        "scripts": {
            "count": len(scripts),
            "shell_count": sum(1 for path in scripts if path.suffix == ".sh"),
            "python_count": sum(1 for path in scripts if path.suffix == ".py"),
            "paths": [rel(path, root) for path in scripts],
            "claim_label": "Shared runtime scripts",
        },
        "decision_engine": {
            "count": len(decision_files),
            "paths": [rel(path, root) for path in decision_files],
            "claim_label": "Decision engine files",
        },
        "reference": {
            "count": len(reference_files),
            "paths": [rel(path, root) for path in reference_files],
            "claim_label": "Reference files",
        },
        "convergence": {
            "count": len(convergence_scripts),
            "paths": [rel(path, root) for path in convergence_scripts],
            "claim_label": "Convergence scripts",
        },
        "tests": {
            "count": len(tests),
            "paths": [rel(path, root) for path in tests],
            "claim_label": "Python test modules",
        },
        "work_orders": {
            "count": len(work_orders),
            "paths": [rel(path, root) for path in work_orders],
            "claim_label": "Work order documents",
        },
        "gates": {
            **gate_data,
            "claim_label": "Quality gate manifest entries",
        },
    }

    claim_ledger = []
    for key, data in categories.items():
        if "count" in data:
            value = data["count"]
        elif key == "hooks":
            value = {
                "documented_count": data["documented_count"],
                "configured_command_count": data["configured_command_count"],
            }
        else:
            value = data.get("gate_entries")
        claim_ledger.append(
            {
                "claim_id": f"inventory.{key}",
                "claim": data["claim_label"],
                "value": value,
                "source": "generated_from_repo",
                "source_paths": data.get("paths")
                or [data.get("manifest_path"), data.get("config_path")]
                or [gate_data["manifest_path"]],
                "public_status": "allowed_with_this_artifact",
            }
        )

    claim_ledger.extend(
        [
            {
                "claim_id": "posture.codex_hook_parity",
                "claim": "Codex has Claude-equivalent hook parity",
                "value": False,
                "source": "AGENTS.md and runtime capability matrix",
                "source_paths": ["AGENTS.md", rel(runtime_path, root)],
                "public_status": "blocked_overclaim",
            },
            {
                "claim_id": "posture.automatic_write_time_enforcement",
                "claim": "VibeOS has full automatic write-time enforcement across all runtimes",
                "value": False,
                "source": "AGENTS.md",
                "source_paths": ["AGENTS.md"],
                "public_status": "blocked_overclaim",
            },
            {
                "claim_id": "posture.repo_link_readiness",
                "claim": "This repo is ready to be linked as the public vNext harness",
                "value": False,
                "source": "WO-106 proof gate",
                "source_paths": ["docs/planning/WO-106-vnext-generated-inventory-and-claim-ledger.md"],
                "public_status": "blocked_until_install_gate_sample_trace_limitations_and_tag_proof_exist",
            },
        ]
    )

    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": generated_at or iso_now(),
        "project_dir": str(root),
        "git": {
            "current_branch_expected": "main",
            "public_tag_status": "not_selected",
        },
        "manifests": {
            "plugin": {
                "path": rel(plugin_manifest_path, root),
                "name": plugin_manifest.get("name"),
                "version": plugin_manifest.get("version"),
            },
            "marketplace": {
                "path": rel(marketplace_path, root),
                "plugin_count": len(marketplace.get("plugins", [])) if marketplace else 0,
            },
            "runtime_capabilities": {
                "path": rel(runtime_path, root),
                "generated_at": runtime.get("generated_at"),
                "strategy": runtime.get("strategy", {}),
            },
        },
        "inventory": categories,
        "claim_ledger": claim_ledger,
        "public_limitations": [
            "Do not claim Codex hook parity with Claude Code.",
            "Do not claim full automatic write-time enforcement across runtimes.",
            "Do not claim 24-48 hour autonomy without durable heartbeat/checkpoint/sample-run proof.",
            "Do not reuse old VibeOS5 or website count claims as current facts.",
            "Do not link this repo publicly as vNext until a clean tag, install proof, gate proof, secret scan, real sample trace, and public-safe limitation statement exist.",
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate VibeOS source inventory and claim ledger.")
    parser.add_argument("--project-dir", default=".", help="Repository root to inspect.")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output JSON path, relative to project dir unless absolute.")
    parser.add_argument("--stdout", action="store_true", help="Print JSON to stdout instead of writing a file.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.project_dir).resolve()
    inventory = build_inventory(root)
    payload = json.dumps(inventory, indent=2, sort_keys=True) + "\n"

    if args.stdout:
        print(payload, end="")
        return 0

    out = Path(args.out)
    if not out.is_absolute():
        out = root / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(payload, encoding="utf-8")
    print(f"[generate-inventory] PASS: wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
