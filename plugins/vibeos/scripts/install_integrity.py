#!/usr/bin/env python3
"""Product-neutral integrity primitives for profile install transactions."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


class IntegrityError(ValueError):
    """Raised when an install binding is malformed, unsafe, or stale."""


def compact_json(payload: Any) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode(
        "utf-8"
    )


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_json(payload: Any) -> str:
    return sha256_bytes(compact_json(payload))


def safe_relative(value: Any, label: str = "path") -> str:
    if not isinstance(value, str) or not value:
        raise IntegrityError(f"{label} must be a non-empty relative path")
    if "\\" in value:
        raise IntegrityError(f"{label} must use POSIX separators")
    pure = PurePosixPath(value)
    if pure.is_absolute() or pure.as_posix() != value:
        raise IntegrityError(f"{label} must be a normalized relative path")
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise IntegrityError(f"{label} contains traversal: {value}")
    return value


def contained_path(root: Path, rel: str, label: str = "path") -> Path:
    root = root.resolve()
    safe_relative(rel, label)
    current = root
    parts = PurePosixPath(rel).parts
    for index, part in enumerate(parts):
        current = current / part
        if current.is_symlink():
            raise IntegrityError(f"{label} may not traverse a symlink: {rel}")
        if current.exists() and index < len(parts) - 1 and not current.is_dir():
            raise IntegrityError(f"{label} parent is not a directory: {rel}")
    resolved_parent = current.parent.resolve()
    if resolved_parent != root and root not in resolved_parent.parents:
        raise IntegrityError(f"{label} escapes canonical root: {rel}")
    return current


def file_state(root: Path, rel: str) -> dict[str, Any]:
    path = contained_path(root, rel, "target path")
    if not path.exists():
        return {"path": rel, "kind": "absent"}
    if not path.is_file():
        raise IntegrityError(f"target path must be a regular file or absent: {rel}")
    return {
        "path": rel,
        "kind": "file",
        "sha256": sha256_file(path),
        "mode": stat.S_IMODE(path.stat().st_mode),
    }


def target_binding(root: Path, paths: Iterable[str]) -> list[dict[str, Any]]:
    path_list = list(paths)
    unique = sorted(set(path_list))
    if len(unique) != len(path_list):
        raise IntegrityError("target binding paths contain duplicates")
    return [file_state(root, rel) for rel in unique]


def verify_target_binding(root: Path, expected: list[dict[str, Any]]) -> None:
    if not isinstance(expected, list):
        raise IntegrityError("target baseline is invalid")
    paths = [row.get("path") for row in expected if isinstance(row, dict)]
    if len(paths) != len(expected) or len(set(paths)) != len(paths):
        raise IntegrityError("target baseline contains malformed or duplicate paths")
    actual = [file_state(root, rel) for rel in paths]
    if actual != expected:
        mismatch = next(
            (row["path"] for row, wanted in zip(actual, expected) if row != wanted),
            "unknown",
        )
        raise IntegrityError(f"target baseline drift after analyze: {mismatch}")


def analysis_input_state(root: Path, rel: str) -> dict[str, Any]:
    path = contained_path(root, rel, "target analysis input")
    if not path.exists():
        return {"path": rel, "kind": "absent"}
    if path.is_file():
        return {"path": rel, "kind": "file", "sha256": sha256_file(path)}
    if path.is_dir():
        return {"path": rel, "kind": "directory"}
    raise IntegrityError(f"target analysis input has unsupported type: {rel}")


def analysis_input_binding(root: Path, paths: Iterable[str]) -> list[dict[str, Any]]:
    unique = sorted(set(paths))
    return [analysis_input_state(root, rel) for rel in unique]


def verify_analysis_input_binding(root: Path, expected: Any) -> None:
    if not isinstance(expected, list):
        raise IntegrityError("target analysis binding is invalid")
    paths = [row.get("path") for row in expected if isinstance(row, dict)]
    if len(paths) != len(expected) or len(set(paths)) != len(paths):
        raise IntegrityError("target analysis binding is malformed or duplicated")
    actual = [analysis_input_state(root, rel) for rel in paths]
    if actual != expected:
        mismatch = next(
            (row["path"] for row, wanted in zip(actual, expected) if row != wanted),
            "unknown",
        )
        raise IntegrityError(f"target analysis input drift after analyze: {mismatch}")


def output_inventory(outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    fields = (
        "path",
        "template_id",
        "source_hash",
        "content_hash",
        "instruction_surface",
        "executable",
    )
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in sorted(outputs, key=lambda row: row["path"]):
        rel = safe_relative(item.get("path"), "output path")
        if rel in seen:
            raise IntegrityError(f"duplicate output path: {rel}")
        seen.add(rel)
        rows.append({field: item.get(field) for field in fields})
    return rows


def _git(source: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(source), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "git command failed"
        raise IntegrityError(f"source Git provenance unavailable: {detail}")
    return result.stdout.strip()


def _source_worktree_dirty(repo: Path, source: Path) -> tuple[bool, list[str]]:
    try:
        source_scope = source.relative_to(repo).as_posix()
    except ValueError as exc:
        raise IntegrityError("plugin source is outside its Git repository") from exc
    scopes = [source_scope]
    guide = repo / "docs" / "CONTROLLED-EVALUATION.md"
    if guide.exists():
        scopes.append("docs/CONTROLLED-EVALUATION.md")
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            *scopes,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise IntegrityError("source Git worktree status is unavailable")
    return bool(result.stdout.strip()), scopes


def source_binding(source: Path, framework_version: str) -> dict[str, Any]:
    source = source.resolve()
    repo = Path(_git(source, "rev-parse", "--show-toplevel")).resolve()
    commit = _git(repo, "rev-parse", "HEAD")
    files: dict[str, str] = {}
    for rel in (
        "scripts/profile_install.py",
        "scripts/install_directories.py",
        "scripts/install_integrity.py",
        "scripts/install_recovery.py",
        ".claude-plugin/plugin.json",
    ):
        candidate = contained_path(source, rel, "source binding path")
        if candidate.is_file():
            files[rel] = sha256_file(candidate)
    dirty, status_scope = _source_worktree_dirty(repo, source)
    return {
        "repo": str(repo),
        "plugin_root": str(source),
        "commit": commit,
        "framework_version": framework_version,
        "source_worktree_dirty": dirty,
        "source_status_scope": status_scope,
        "files": files,
        "relevant_files_sha256": sha256_json(files),
    }


def verify_source_binding(source: Path, framework_version: str, expected: Any) -> None:
    if not isinstance(expected, dict):
        raise IntegrityError("source binding is missing")
    actual = source_binding(source, framework_version)
    if actual != expected:
        raise IntegrityError("source drift after analyze")


def profile_binding(profile_path: Path | None, normalized_hash: str) -> dict[str, Any]:
    binding: dict[str, Any] = {
        "kind": "generated",
        "normalized_sha256": normalized_hash,
    }
    if profile_path is not None:
        if profile_path.is_symlink() or not profile_path.is_file():
            raise IntegrityError(
                f"profile must be a regular non-symlink file: {profile_path}"
            )
        binding.update(
            {
                "kind": "file",
                "path": str(profile_path.resolve()),
                "sha256": sha256_file(profile_path),
            }
        )
    return binding


def verify_profile_binding(binding: Any, normalized_hash: str) -> None:
    if (
        not isinstance(binding, dict)
        or binding.get("normalized_sha256") != normalized_hash
    ):
        raise IntegrityError("normalized profile drift after analyze")
    if binding.get("kind") == "generated":
        return
    if binding.get("kind") != "file" or not isinstance(binding.get("path"), str):
        raise IntegrityError("profile binding is invalid")
    path = Path(binding["path"])
    if (
        path.is_symlink()
        or not path.is_file()
        or sha256_file(path) != binding.get("sha256")
    ):
        raise IntegrityError("profile file drift after analyze")


def plan_payload_hash(plan: dict[str, Any]) -> str:
    return sha256_json(
        {key: value for key, value in plan.items() if key != "plan_payload_hash"}
    )


def atomic_write(path: Path, payload: bytes, mode: int | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    if mode is not None:
        temporary.chmod(mode)
    os.replace(temporary, path)
