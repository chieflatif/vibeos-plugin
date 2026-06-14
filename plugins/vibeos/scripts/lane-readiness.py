#!/usr/bin/env python3
"""Check parallel lane readiness in a scratch worktree."""

import argparse
import fnmatch
import importlib.util
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


def load_contracts_module():
    path = Path(__file__).with_name("wo-contracts.py")
    spec = importlib.util.spec_from_file_location("wo_contracts", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


contracts = load_contracts_module()


def run(cmd, cwd: Path, check: bool = False):
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "command failed")
    return result


def git(cwd: Path, *args, check: bool = False):
    return run(["git", *args], cwd, check=check)


def matches(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        clean = pattern.rstrip("/")
        if fnmatch.fnmatch(path, pattern) or path == clean or path.startswith(clean + "/"):
            return True
    return False


def schema_path() -> Path:
    return Path(__file__).resolve().parents[1] / "reference/lane-packet.schema.json"


def validate_packet(packet: dict) -> list[str]:
    schema = json.loads(schema_path().read_text(encoding="utf-8"))
    errors = []
    for field in schema["required"]:
        if field not in packet:
            errors.append(f"missing:{field}")
    if packet.get("lane_status") not in schema["properties"]["lane_status"]["enum"]:
        errors.append("invalid:lane_status")
    if not isinstance(packet.get("gate_results"), list) or not packet["gate_results"]:
        errors.append("invalid:gate_results")
    if not isinstance(packet.get("defects"), list):
        errors.append("invalid:defects")
    if not packet.get("evidence_bundle_path"):
        errors.append("invalid:evidence_bundle_path")
    for index, gate in enumerate(packet.get("gate_results", [])):
        for field in schema["properties"]["gate_results"]["items"]["required"]:
            if field not in gate:
                errors.append(f"missing:gate_results[{index}].{field}")
        if gate.get("status") not in ["PASS", "FAIL", "SKIP"]:
            errors.append(f"invalid:gate_results[{index}].status")
    for index, defect in enumerate(packet.get("defects", [])):
        for field in schema["properties"]["defects"]["items"]["required"]:
            if field not in defect:
                errors.append(f"missing:defects[{index}].{field}")
    return errors


def default_gate_command(project_dir: Path, framework_dir: Path, wo_number: str) -> str:
    return " ".join(shlex.quote(item) for item in default_gate_args(project_dir, framework_dir, wo_number))


def default_gate_args(project_dir: Path, framework_dir: Path, wo_number: str) -> list[str]:
    runner = framework_dir / "scripts/gate-runner.sh"
    manifest = framework_dir / "quality-gate-manifest.json"
    return [
        "bash",
        str(runner),
        "wo_exit",
        "--continue-on-failure",
        "--wo",
        wo_number,
        "--manifest",
        str(manifest),
        "--project-dir",
        str(project_dir),
        "--framework-dir",
        str(framework_dir),
    ]


def changed_paths(scratch: Path, base_ref: str) -> list[str]:
    result = git(scratch, "diff", "--name-only", f"{base_ref}...HEAD", check=True)
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def scope_defects(paths: list[str], contract: dict) -> list[dict]:
    defects = []
    for path in paths:
        if matches(path, contract.get("no_touch", [])):
            defects.append(
                {
                    "severity": "high",
                    "source": "no-touch",
                    "message": f"Lane changed no_touch path {path}.",
                    "path": path,
                }
            )
        elif not matches(path, contract["write_scope"]):
            defects.append(
                {
                    "severity": "high",
                    "source": "write-scope",
                    "message": f"Lane changed path outside write_scope: {path}.",
                    "path": path,
                }
            )
    return defects


def make_packet(contract: dict, args, gate_results: list[dict], defects: list[dict], commit: str | None = None):
    packet = {
        "wo_number": contract["wo"],
        "lane_status": "ACCEPT" if not defects and all(gate["status"] != "FAIL" for gate in gate_results) else "DEFER",
        "gate_results": gate_results,
        "defects": defects,
        "evidence_bundle_path": args.evidence_bundle_path or f"docs/evidence/{contract['wo']}/lane-packet.json",
        "lane_branch": args.lane_branch,
        "base_ref": args.base_ref,
    }
    if commit:
        packet["commit"] = commit
    return packet


def write_packet(project_dir: Path, packet: dict, packet_out: Path | None) -> None:
    out = packet_out or project_dir / packet["evidence_bundle_path"]
    if not out.is_absolute():
        out = project_dir / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def remove_scratch(project_dir: Path, scratch: Path) -> None:
    if scratch.exists():
        git(project_dir, "worktree", "remove", "--force", str(scratch))
    shutil.rmtree(scratch, ignore_errors=True)


def check_lane(args) -> dict:
    project_dir = args.project_dir.resolve()
    wo_file = args.wo_file if args.wo_file.is_absolute() else project_dir / args.wo_file
    contract = contracts.load_contract(wo_file)
    scratch = args.scratch_dir.resolve()
    if scratch.exists():
        remove_scratch(project_dir, scratch)

    defects = []
    gate_results = []
    commit = None
    try:
        add = git(project_dir, "worktree", "add", "--detach", str(scratch), args.lane_branch)
        if add.returncode != 0:
            raise RuntimeError(add.stderr.strip() or add.stdout.strip() or "worktree add failed")
        rebase = git(scratch, "rebase", args.base_ref)
        if rebase.returncode != 0:
            git(scratch, "rebase", "--abort")
            gate_results.append({"phase": "rebase", "status": "FAIL", "passed": 0, "failed": 1, "skipped": 0})
            defects.append({"severity": "high", "source": "rebase", "message": "Lane branch could not rebase onto base ref."})
            return make_packet(contract, args, gate_results, defects)

        commit = git(scratch, "rev-parse", "HEAD", check=True).stdout.strip()
        gate_args = shlex.split(args.gate_command) if args.gate_command else default_gate_args(project_dir, args.framework_dir.resolve(), contract["wo"])
        gate_command = " ".join(shlex.quote(item) for item in gate_args)
        gate = subprocess.run(gate_args, cwd=str(scratch), capture_output=True, text=True)
        gate_results.append(
            {
                "phase": "wo_exit",
                "status": "PASS" if gate.returncode == 0 else "FAIL",
                "passed": 1 if gate.returncode == 0 else 0,
                "failed": 0 if gate.returncode == 0 else 1,
                "skipped": 0,
                "command": gate_command,
            }
        )
        paths = changed_paths(scratch, args.base_ref)
        defects.extend(scope_defects(paths, contract))
        if gate.returncode != 0:
            defects.append({"severity": "high", "source": "gate-runner", "message": "wo_exit gate command failed."})
        return make_packet(contract, args, gate_results, defects, commit)
    finally:
        remove_scratch(project_dir, scratch)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--framework-dir", type=Path, default=Path("plugins/vibeos"))
    parser.add_argument("--lane-branch", required=True)
    parser.add_argument("--base-ref", required=True)
    parser.add_argument("--wo-file", type=Path, required=True)
    parser.add_argument("--scratch-dir", type=Path, required=True)
    parser.add_argument("--gate-command")
    parser.add_argument("--packet-out", type=Path)
    parser.add_argument("--evidence-bundle-path")
    args = parser.parse_args(argv)

    try:
        packet = check_lane(args)
        errors = validate_packet(packet)
        if errors:
            packet["lane_status"] = "DEFER"
            packet["defects"].append({"severity": "high", "source": "packet-schema", "message": "; ".join(errors)})
        write_packet(args.project_dir.resolve(), packet, args.packet_out)
        print(json.dumps(packet, indent=2, sort_keys=True))
        return 0 if packet["lane_status"] == "ACCEPT" else 1
    except Exception as exc:
        print(f"[lane-readiness] ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
