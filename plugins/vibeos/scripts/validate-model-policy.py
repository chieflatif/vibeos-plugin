#!/usr/bin/env python3
"""Validate VibeOS model policy tiers against agents and WO frontmatter."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.3.1"
CUSTOM_POLICY_RE = re.compile(r"^custom-[a-z0-9][a-z0-9-]*$")


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def first_existing(paths: list[Path]) -> Path:
    for path in paths:
        if path.exists():
            return path
    return paths[0]


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    frontmatter = text[4:end]
    data: dict[str, str] = {}
    for raw_line in frontmatter.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        value = value.strip().strip("'\"")
        if value and not value.startswith("["):
            data[key.strip()] = value
    return data


def schema_tiers(schema_path: Path) -> set[str]:
    schema = read_json(schema_path)
    branches = schema["properties"]["model_policy"]["oneOf"]
    for branch in branches:
        enum = branch.get("enum")
        if enum:
            return set(enum)
    return set()


def validate_policy(policy: dict[str, Any], expected_tiers: set[str]) -> list[str]:
    errors: list[str] = []
    tiers = policy.get("tiers", {})
    aliases = policy.get("agent_model_aliases", {})
    effort_levels = set(policy.get("effort_levels", []))

    if policy.get("schema_version") != "1.0":
        errors.append("policy schema_version must be 1.0")
    if not isinstance(tiers, dict) or not tiers:
        errors.append("policy tiers must be a non-empty object")
        return errors
    if not isinstance(aliases, dict) or not aliases:
        errors.append("policy agent_model_aliases must be a non-empty object")
    if not effort_levels:
        errors.append("policy effort_levels must be non-empty")

    policy_tiers = set(tiers)
    missing = sorted(expected_tiers - policy_tiers)
    extra = sorted(policy_tiers - expected_tiers)
    if missing:
        errors.append(f"policy missing schema model_policy tiers: {', '.join(missing)}")
    if extra:
        errors.append(f"policy contains tiers not in WO schema: {', '.join(extra)}")

    alias_names = set(aliases)
    for tier_name, tier in tiers.items():
        if not isinstance(tier.get("allow_downgrade"), bool):
            errors.append(f"{tier_name}: allow_downgrade must be boolean")
        if tier.get("default_effort") not in effort_levels:
            errors.append(f"{tier_name}: default_effort must be in effort_levels")
        allowed_aliases = tier.get("allowed_model_aliases", [])
        if not isinstance(allowed_aliases, list) or not allowed_aliases:
            errors.append(f"{tier_name}: allowed_model_aliases must be a non-empty list")
        for alias in allowed_aliases:
            if alias not in alias_names:
                errors.append(f"{tier_name}: unknown model alias {alias}")
        if not tier.get("resolution_strategy"):
            errors.append(f"{tier_name}: resolution_strategy is required")

    for alias, config in aliases.items():
        if config.get("tier") not in policy_tiers:
            errors.append(f"agent alias {alias}: tier must reference a policy tier")
        if not config.get("runtime_resolution"):
            errors.append(f"agent alias {alias}: runtime_resolution is required")

    return errors


def validate_agents(root: Path, policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    aliases = set(policy.get("agent_model_aliases", {}))
    effort_levels = set(policy.get("effort_levels", []))
    agent_dirs = [
        root / "plugins/vibeos/agents",
        root / ".claude/agents",
    ]
    agent_paths = []
    for agent_dir in agent_dirs:
        if agent_dir.is_dir():
            agent_paths.extend(agent_dir.glob("*.md"))
    for path in sorted(agent_paths):
        fm = parse_frontmatter(path)
        model = fm.get("model")
        if not model:
            errors.append(f"{rel(path, root)}: missing model frontmatter")
        elif model not in aliases:
            errors.append(f"{rel(path, root)}: model '{model}' is not in model-policy agent_model_aliases")
        effort = fm.get("effort")
        if effort and effort not in effort_levels:
            errors.append(f"{rel(path, root)}: effort '{effort}' is not in model-policy effort_levels")
    return errors


def validate_work_orders(root: Path, policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    tiers = set(policy.get("tiers", {}))
    for path in sorted((root / "docs/planning").glob("WO-*.md")):
        fm = parse_frontmatter(path)
        model_policy = fm.get("model_policy")
        if not model_policy:
            continue
        if model_policy in tiers or CUSTOM_POLICY_RE.match(model_policy):
            continue
        errors.append(f"{rel(path, root)}: model_policy '{model_policy}' is not in model-policy tiers")
    return errors


def validate(root: Path, policy_path: Path, schema_path: Path) -> list[str]:
    policy = read_json(policy_path)
    errors = validate_policy(policy, schema_tiers(schema_path))
    errors.extend(validate_agents(root, policy))
    errors.extend(validate_work_orders(root, policy))
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate VibeOS model policy.")
    parser.add_argument("--project-dir", default=os.environ.get("PROJECT_ROOT", "."), help="Project root.")
    parser.add_argument("--policy", default="", help="Policy JSON path.")
    parser.add_argument("--schema", default="", help="WO schema path.")
    parser.add_argument("--json", action="store_true", help="Emit JSON result.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.project_dir).resolve()
    framework_root = Path(__file__).resolve().parents[1]
    policy_path = (
        (root / args.policy).resolve()
        if args.policy
        else first_existing(
            [
                root / "plugins/vibeos/reference/model-policy.json",
                root / ".vibeos/reference/model-policy.json",
                framework_root / "reference/model-policy.json",
            ]
        ).resolve()
    )
    schema_path = (
        (root / args.schema).resolve()
        if args.schema
        else first_existing(
            [
                root / "plugins/vibeos/reference/wo-frontmatter.schema.json",
                root / ".vibeos/reference/wo-frontmatter.schema.json",
                framework_root / "reference/wo-frontmatter.schema.json",
            ]
        ).resolve()
    )
    errors = validate(root, policy_path, schema_path)
    result = {
        "ok": not errors,
        "framework_version": FRAMEWORK_VERSION,
        "policy_path": rel(policy_path, root),
        "errors": errors,
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif errors:
        print("[validate-model-policy] FAIL")
        for error in errors:
            print(f"  - {error}")
    else:
        print("[validate-model-policy] PASS: model policy, agent aliases, and WO tiers are consistent")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
