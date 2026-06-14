#!/usr/bin/env python3
"""Generate VibeOS contract artifacts from Work Order frontmatter."""

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_FIELDS = [
    "wo",
    "title",
    "status",
    "phase",
    "phase_name",
    "wo_class",
    "write_scope",
    "no_touch",
    "required_auditors",
    "model_policy",
    "budget_posture",
]

BRANCH_PATTERN = re.compile(r"^feat/.+$")
WO_PATTERN = re.compile(r"^WO-[0-9]{3}[a-z]?$")


class ContractError(ValueError):
    """Raised for invalid WO contract input."""


def schema_path() -> Path:
    return Path(__file__).resolve().parents[1] / "reference/wo-frontmatter.schema.json"


def parse_scalar(value: str):
    value = value.strip()
    if value == "":
        return ""
    if value == "null":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    if value == "[]":
        return []
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [parse_scalar(item.strip()) for item in inner.split(",")]
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    if re.match(r"^-?[0-9]+$", value):
        return int(value)
    if re.match(r"^-?[0-9]+(?:\.[0-9]+)?$", value):
        return float(value)
    return value


def parse_frontmatter_block(text: str) -> list[str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ContractError("WO file must start with YAML frontmatter delimited by ---")
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index]
    raise ContractError("WO frontmatter closing delimiter --- is missing")


def parse_frontmatter(text: str) -> dict:
    block = parse_frontmatter_block(text)
    result = {}
    index = 0
    while index < len(block):
        line = block[index]
        if not line.strip() or line.lstrip().startswith("#"):
            index += 1
            continue
        if line.startswith(" "):
            raise ContractError(f"unexpected indented line at top level: {line}")
        if ":" not in line:
            raise ContractError(f"expected key/value line: {line}")
        key, raw_value = line.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value:
            result[key] = parse_scalar(raw_value)
            index += 1
            continue

        children = []
        index += 1
        while index < len(block) and block[index].startswith("  "):
            children.append(block[index])
            index += 1
        result[key] = parse_children(key, children)
    return result


def parse_children(key: str, children: list[str]):
    if not children:
        return {}
    stripped = [line.strip() for line in children if line.strip()]
    if not stripped:
        return {}
    if all(line.startswith("- ") for line in stripped):
        return [parse_scalar(line[2:].strip()) for line in stripped]
    mapping = {}
    for line in stripped:
        if line.startswith("- "):
            raise ContractError(f"{key} cannot mix list and mapping values")
        if ":" not in line:
            raise ContractError(f"expected nested key/value under {key}: {line}")
        nested_key, nested_value = line.split(":", 1)
        mapping[nested_key.strip()] = parse_scalar(nested_value.strip())
    return mapping


def load_contract(wo_file: Path) -> dict:
    contract = parse_frontmatter(wo_file.read_text(encoding="utf-8"))
    validate_contract(contract)
    return contract


def validate_contract(contract: dict) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in contract]
    if missing:
        raise ContractError(f"missing required frontmatter field(s): {', '.join(missing)}")
    if not isinstance(contract["wo"], str) or not WO_PATTERN.match(contract["wo"]):
        raise ContractError("wo must match WO-NNN")
    for field in ["write_scope", "no_touch", "required_auditors"]:
        if not isinstance(contract[field], list):
            raise ContractError(f"{field} must be a list")
    if not contract["write_scope"]:
        raise ContractError("write_scope must contain at least one path")
    if not contract["required_auditors"]:
        raise ContractError("required_auditors must contain at least one auditor")
    budget = contract["budget_posture"]
    if not isinstance(budget, dict):
        raise ContractError("budget_posture must be a mapping")
    for key in ["token_ceiling", "turn_ceiling", "cost_ceiling_usd"]:
        if key not in budget:
            raise ContractError(f"budget_posture.{key} is required")


def load_schema_defaults(path: Path | None = None) -> dict:
    chosen = path or schema_path()
    schema = json.loads(chosen.read_text(encoding="utf-8"))
    return schema.get("x-vibeos-class-defaults", {})


def worktree_scope(contract: dict, branch: str) -> dict:
    if not BRANCH_PATTERN.match(branch):
        raise ContractError("worktree scope branch must match existing schema pattern feat/*")
    manifest = {
        "branches": {
            branch: {
                "wo_ids": [contract["wo"]],
                "exclusive_paths": contract["write_scope"],
                "description": f"{contract['wo']} {contract['title']}",
            }
        },
        "shared_paths": [],
    }
    validate_worktree_scope_manifest(manifest)
    return manifest


def validate_worktree_scope_manifest(manifest: dict) -> None:
    if sorted(manifest.keys()) != ["branches", "shared_paths"]:
        raise ContractError("worktree scope manifest must contain only branches and shared_paths")
    if not isinstance(manifest["branches"], dict):
        raise ContractError("branches must be a mapping")
    if not isinstance(manifest["shared_paths"], list):
        raise ContractError("shared_paths must be a list")
    for branch, scope in manifest["branches"].items():
        if not BRANCH_PATTERN.match(branch):
            raise ContractError("branch key must match feat/*")
        if sorted(scope.keys()) != ["description", "exclusive_paths", "wo_ids"]:
            raise ContractError("branch scope must contain only wo_ids, exclusive_paths, and description")
        if not scope["wo_ids"] or not all(isinstance(wo_id, str) and wo_id.startswith("WO-") for wo_id in scope["wo_ids"]):
            raise ContractError("branch scope wo_ids must contain WO ids")
        if not isinstance(scope["exclusive_paths"], list) or not all(isinstance(path, str) for path in scope["exclusive_paths"]):
            raise ContractError("branch scope exclusive_paths must be a list of strings")
        if not isinstance(scope["description"], str) or not scope["description"]:
            raise ContractError("branch scope description must be a non-empty string")


def agent_policy(contract: dict) -> dict:
    payload = {
        "material_type": "agent_scope_policy",
        "wo": contract["wo"],
        "title": contract["title"],
        "wo_class": contract["wo_class"],
        "allowed_paths": contract["write_scope"],
        "denied_paths": contract["no_touch"],
        "model_policy": contract["model_policy"],
        "budget_posture": contract["budget_posture"],
    }
    loop = {
        "goal": contract.get("loop_goal"),
        "ceiling_turns": contract.get("loop_ceiling_turns"),
        "ceiling_cost_usd": contract.get("loop_ceiling_cost_usd"),
    }
    if any(value is not None for value in loop.values()):
        payload["loop"] = loop
    return payload


def auditor_requirements(contract: dict, defaults: dict | None = None) -> dict:
    class_defaults = (defaults or load_schema_defaults()).get(contract["wo_class"])
    payload = {
        "material_type": "auditor_requirements",
        "auditor_requirement_key": auditor_requirement_key(contract),
        "wo": contract["wo"],
        "wo_class": contract["wo_class"],
        "required_auditors": contract["required_auditors"],
    }
    if class_defaults:
        payload["governance"] = class_defaults
    else:
        payload["governance"] = {"custom_class": True}
    return payload


def auditor_requirement_key(contract: dict) -> str:
    auditors = ",".join(sorted(contract["required_auditors"]))
    return f"{contract['wo']}:{contract['wo_class']}:{auditors}"


def write_json(payload: dict, out: Path | None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common(subparser):
        subparser.add_argument("--wo-file", required=True, type=Path)
        subparser.add_argument("--out", type=Path)

    parse_cmd = subparsers.add_parser("parse", help="Emit parsed WO frontmatter.")
    add_common(parse_cmd)

    scope_cmd = subparsers.add_parser("emit-worktree-scope", help="Emit a worktree scope manifest entry.")
    add_common(scope_cmd)
    scope_cmd.add_argument("--branch", required=True)

    policy_cmd = subparsers.add_parser("emit-agent-policy", help="Emit agent allow/deny policy material.")
    add_common(policy_cmd)

    auditors_cmd = subparsers.add_parser("emit-auditor-requirements", help="Emit auditor requirements.")
    add_common(auditors_cmd)
    auditors_cmd.add_argument("--schema", type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        contract = load_contract(args.wo_file)
        if args.command == "parse":
            payload = contract
        elif args.command == "emit-worktree-scope":
            payload = worktree_scope(contract, args.branch)
        elif args.command == "emit-agent-policy":
            payload = agent_policy(contract)
        elif args.command == "emit-auditor-requirements":
            payload = auditor_requirements(contract, load_schema_defaults(args.schema))
        else:
            parser.error(f"unknown command: {args.command}")
        write_json(payload, args.out)
        return 0
    except (ContractError, OSError, json.JSONDecodeError) as exc:
        print(f"[wo-contracts] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
