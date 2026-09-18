#!/usr/bin/env python3
"""Prove that accepted work is recoverable from the remote default branch."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile


FRAMEWORK_VERSION = "2.3.2"


class CloseoutError(RuntimeError):
    """A user-correctable canonical closeout failure."""


def run(*args: str, cwd: Path, timeout: int = 60) -> str:
    result = subprocess.run(
        args, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "command failed"
        raise CloseoutError(f"{' '.join(args)}: {detail}")
    return result.stdout.strip()


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def safe_relative(raw: str, label: str) -> Path:
    value = Path(raw)
    if value.is_absolute() or not value.parts or ".." in value.parts:
        raise CloseoutError(f"{label} must be a repository-relative path")
    return value


def contained_file(root: Path, relative: Path, label: str) -> Path:
    candidate = root / relative
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exc:
        raise CloseoutError(f"{label} is missing: {relative}") from exc
    resolved_root = root.resolve()
    if resolved_root not in resolved.parents or not resolved.is_file():
        raise CloseoutError(f"{label} escapes the repository or is not a file: {relative}")
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise CloseoutError(f"{label} may not traverse a symlink: {relative}")
    return resolved


def load_manifest(path: Path) -> tuple[dict, bytes]:
    if not path.is_file() or path.is_symlink():
        raise CloseoutError(f"manifest is missing or unsafe: {path}")
    payload = path.read_bytes()
    try:
        manifest = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise CloseoutError(f"manifest is invalid JSON: {exc}") from exc
    if not isinstance(manifest, dict):
        raise CloseoutError("manifest must be a JSON object")
    return manifest, payload


def require_string(manifest: dict, key: str) -> str:
    value = manifest.get(key)
    if not isinstance(value, str) or not value.strip():
        raise CloseoutError(f"manifest {key} must be a non-empty string")
    return value


def validate_shape(manifest: dict) -> None:
    if manifest.get("schema_version") != 1:
        raise CloseoutError("manifest schema_version must be 1")
    classification = require_string(manifest, "classification")
    if classification not in {"product-source", "evidence-only"}:
        raise CloseoutError("classification must be product-source or evidence-only")
    require_string(manifest, "remote")
    require_string(manifest, "default_branch")
    paths = manifest.get("front_door_paths")
    if not isinstance(paths, list) or not paths or not all(
        isinstance(item, str) and item for item in paths
    ):
        raise CloseoutError("front_door_paths must be a non-empty string array")
    if classification == "product-source":
        for key in ("accepted_commit", "accepted_tree"):
            if not re.fullmatch(r"[0-9a-f]{40}", require_string(manifest, key)):
                raise CloseoutError(f"manifest {key} must be a full lowercase Git SHA")
    else:
        require_string(manifest, "accepted_identity")
        safe_relative(require_string(manifest, "evidence_path"), "evidence_path")
        if not re.fullmatch(
            r"[0-9a-f]{64}", require_string(manifest, "evidence_sha256")
        ):
            raise CloseoutError("evidence_sha256 must be a lowercase SHA-256 digest")


def require_front_doors(clone: Path, manifest: dict) -> None:
    for raw in manifest["front_door_paths"]:
        relative = safe_relative(raw, "front_door_paths entry")
        contained_file(clone, relative, "front-door file")


def verify_product(clone: Path, manifest: dict) -> None:
    accepted = manifest["accepted_commit"]
    run("git", "cat-file", "-e", f"{accepted}^{{commit}}", cwd=clone)
    result = subprocess.run(
        ["git", "merge-base", "--is-ancestor", accepted, "HEAD"], cwd=clone
    )
    if result.returncode != 0:
        raise CloseoutError("accepted product commit is not on the remote default branch")
    observed_tree = run("git", "rev-parse", f"{accepted}^{{tree}}", cwd=clone)
    if observed_tree != manifest["accepted_tree"]:
        raise CloseoutError("accepted_tree does not match accepted_commit")


def verify_evidence(clone: Path, manifest: dict) -> None:
    relative = safe_relative(manifest["evidence_path"], "evidence_path")
    artifact = contained_file(clone, relative, "accepted evidence")
    if digest(artifact.read_bytes()) != manifest["evidence_sha256"]:
        raise CloseoutError("accepted evidence digest does not match the remote artifact")


def verify(project: Path, manifest_relative: Path) -> dict:
    local_path = contained_file(project, manifest_relative, "manifest")
    manifest, local_payload = load_manifest(local_path)
    validate_shape(manifest)
    remote = manifest["remote"]
    branch = manifest["default_branch"]
    remote_url = run("git", "remote", "get-url", remote, cwd=project)
    with tempfile.TemporaryDirectory(prefix="vibeos-canonical-closeout-") as tmp:
        clone = Path(tmp) / "clone"
        run(
            "git", "clone", "--quiet", "--single-branch", "--branch", branch,
            remote_url, str(clone), cwd=project, timeout=120,
        )
        remote_path = contained_file(clone, manifest_relative, "remote manifest")
        remote_manifest, remote_payload = load_manifest(remote_path)
        if digest(local_payload) != digest(remote_payload):
            raise CloseoutError("local closeout manifest is not the remote default-branch copy")
        if remote_manifest != manifest:
            raise CloseoutError("remote closeout manifest content differs from local content")
        if run("git", "status", "--porcelain", cwd=clone):
            raise CloseoutError("fresh clone is unexpectedly dirty")
        require_front_doors(clone, manifest)
        if manifest["classification"] == "product-source":
            verify_product(clone, manifest)
        else:
            verify_evidence(clone, manifest)
        head = run("git", "rev-parse", "HEAD", cwd=clone)
    return {
        "result": "PASS",
        "classification": manifest["classification"],
        "remote": remote,
        "default_branch": branch,
        "remote_head": head,
        "manifest": manifest_relative.as_posix(),
        "manifest_sha256": digest(local_payload),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify accepted source or evidence from a fresh remote-default clone."
    )
    parser.add_argument("--project-dir", default=".")
    parser.add_argument(
        "--manifest", default=".vibeos/canonical-closeout.json",
        help="repository-relative acceptance manifest",
    )
    args = parser.parse_args()
    project = Path(args.project_dir).expanduser().resolve()
    manifest_relative = safe_relative(args.manifest, "manifest")
    try:
        payload = verify(project, manifest_relative)
    except (CloseoutError, subprocess.TimeoutExpired) as exc:
        print(f"[validate-canonical-closeout] FAIL: {exc}")
        return 1
    print("[validate-canonical-closeout] PASS")
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
