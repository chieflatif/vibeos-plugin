#!/usr/bin/env python3
"""Journaled exact rollback for profile install file mutations."""

from __future__ import annotations

import json
import fcntl
import shutil
import stat
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from install_directories import absent_parent_directories, remove_created_empty_parents
from install_integrity import (
    IntegrityError,
    atomic_write,
    contained_path,
    file_state,
    sha256_file,
)


JOURNAL_REL = ".vibeos/install-recovery.json"
BACKUP_ROOT_REL = ".vibeos/install-recovery"
LOCK_REL = ".vibeos/install-transaction.lock"


class RecoveryError(IntegrityError):
    """Raised when a transaction cannot be safely started or rolled back."""


def _json(payload: Any) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")


def journal_path(target: Path) -> Path:
    return contained_path(target, JOURNAL_REL, "recovery journal")


def load_journal(target: Path) -> dict[str, Any] | None:
    path = journal_path(target)
    if not path.exists():
        return None
    if not path.is_file():
        raise RecoveryError("recovery journal is not a regular file")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RecoveryError(f"recovery journal is malformed: {exc}") from exc
    if not isinstance(payload, dict):
        raise RecoveryError("recovery journal must be an object")
    return payload


def require_no_active_transaction(target: Path) -> None:
    journal = load_journal(target)
    if journal is not None:
        raise RecoveryError(
            "an interrupted install requires `recover --plan ...` before verify or apply"
        )


@contextmanager
def project_lock(target: Path, *, exclusive: bool = True):
    path = contained_path(target, LOCK_REL, "install transaction lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("a+b")
    operation = fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH
    try:
        try:
            fcntl.flock(handle.fileno(), operation | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RecoveryError(
                "another install transaction holds the project lock"
            ) from exc
        yield
    finally:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def begin_transaction(
    target: Path,
    plan_path: Path,
    plan_hash: str,
    mutations: list[dict[str, Any]],
) -> dict[str, Any]:
    require_no_active_transaction(target)
    transaction_id = uuid.uuid4().hex
    backup_root = contained_path(
        target, f"{BACKUP_ROOT_REL}/{transaction_id}", "recovery backup root"
    )
    if backup_root.exists():
        raise RecoveryError("recovery backup collision")
    backup_root.mkdir(parents=True)
    entries: list[dict[str, Any]] = []
    try:
        paths = [row.get("path") for row in mutations if isinstance(row, dict)]
        if len(paths) != len(mutations) or len(set(paths)) != len(paths):
            raise RecoveryError(
                "transaction mutation inventory is malformed or duplicated"
            )
        mutation_by_path = {row["path"]: row for row in mutations}
        for index, rel in enumerate(sorted(paths)):
            before = file_state(target, rel)
            after = mutation_by_path[rel].get("after")
            if after is not None and not isinstance(after, dict):
                raise RecoveryError(f"transaction expected state is invalid for {rel}")
            entry: dict[str, Any] = {
                "path": rel,
                "before": before,
                "after": after,
                "backup": None,
            }
            if before["kind"] == "file":
                backup = backup_root / f"{index:05d}.bin"
                source = contained_path(target, rel, "transaction mutation")
                shutil.copyfile(source, backup)
                backup.chmod(stat.S_IMODE(source.stat().st_mode))
                entry["backup"] = backup.name
            entries.append(entry)
        journal = {
            "schema_version": 1,
            "transaction_id": transaction_id,
            "state": "applying",
            "target": str(target.resolve()),
            "plan_path": str(plan_path.resolve()),
            "plan_hash": plan_hash,
            "backup_root": backup_root.relative_to(target).as_posix(),
            "created_parent_dirs": absent_parent_directories(target, paths),
            "entries": entries,
        }
        atomic_write(journal_path(target), _json(journal), 0o600)
        return journal
    except Exception:
        shutil.rmtree(backup_root, ignore_errors=True)
        raise


def record_expected_state(
    target: Path,
    rel: str,
    expected: dict[str, Any],
    *,
    allow_previous: bool = False,
) -> None:
    journal = load_journal(target)
    if journal is None:
        raise RecoveryError(
            "recovery journal disappeared while recording expected state"
        )
    matching = [
        entry for entry in journal.get("entries", []) if entry.get("path") == rel
    ]
    if len(matching) != 1:
        raise RecoveryError(f"recovery journal does not bind mutation path: {rel}")
    previous = matching[0].get("after")
    if allow_previous and previous is not None:
        allowed = previous if isinstance(previous, list) else [previous]
        if expected not in allowed:
            allowed.append(expected)
        matching[0]["after"] = allowed
    else:
        matching[0]["after"] = expected
    atomic_write(journal_path(target), _json(journal), 0o600)


def mark_recovery_required(target: Path, reason: str) -> None:
    journal = load_journal(target)
    if journal is None:
        return
    journal["state"] = "recovery-required"
    journal["reason"] = reason
    atomic_write(journal_path(target), _json(journal), 0o600)


def complete_transaction(target: Path) -> None:
    journal = load_journal(target)
    if journal is None:
        raise RecoveryError(
            "recovery journal disappeared before transaction completion"
        )
    backup_root = contained_path(target, journal["backup_root"], "recovery backup root")
    _preflight_backup_tree(backup_root, journal.get("entries"))
    journal_path(target).unlink()
    shutil.rmtree(backup_root)
    parent = backup_root.parent
    if parent.is_dir() and not any(parent.iterdir()):
        parent.rmdir()


def _preflight_backup_tree(backup_root: Path, entries: Any) -> None:
    if backup_root.is_symlink() or not backup_root.is_dir():
        raise RecoveryError("recovery backup root is missing or unsafe")
    if not isinstance(entries, list):
        raise RecoveryError("recovery journal entries are invalid")
    expected_names = {entry.get("backup") for entry in entries if entry.get("backup")}
    actual_names: set[str] = set()
    for child in backup_root.iterdir():
        if child.is_symlink() or not child.is_file():
            raise RecoveryError("recovery backup tree contains an unsafe entry")
        actual_names.add(child.name)
    if actual_names != expected_names:
        raise RecoveryError("recovery backup inventory mismatch")


def _state_matches(actual: dict[str, Any], expected: Any) -> bool:
    if isinstance(expected, list):
        return any(_state_matches(actual, candidate) for candidate in expected)
    return isinstance(expected, dict) and actual == expected


def recover_transaction(target: Path, plan_path: Path, plan_hash: str) -> list[str]:
    journal = load_journal(target)
    if journal is None:
        raise RecoveryError("no interrupted install transaction exists")
    if journal.get("target") != str(target.resolve()):
        raise RecoveryError("recovery journal target binding mismatch")
    if (
        journal.get("plan_path") != str(plan_path.resolve())
        or journal.get("plan_hash") != plan_hash
    ):
        raise RecoveryError("recovery journal plan binding mismatch")
    entries = journal.get("entries")
    if not isinstance(entries, list):
        raise RecoveryError("recovery journal entries are invalid")
    backup_root = contained_path(
        target, journal.get("backup_root"), "recovery backup root"
    )
    _preflight_backup_tree(backup_root, entries)
    for entry in entries:
        before = entry.get("before") if isinstance(entry, dict) else None
        if not isinstance(before, dict):
            raise RecoveryError("recovery journal entry is invalid")
        if before.get("kind") == "file":
            backup_name = entry.get("backup")
            if not isinstance(backup_name, str) or "/" in backup_name:
                raise RecoveryError(f"missing recovery backup for {entry.get('path')}")
            backup = backup_root / backup_name
            if (
                backup.is_symlink()
                or not backup.is_file()
                or sha256_file(backup) != before.get("sha256")
            ):
                raise RecoveryError(
                    f"recovery backup hash mismatch for {entry.get('path')}"
                )
    restore_entries: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("before"), dict):
            raise RecoveryError("recovery journal entry is invalid")
        rel = entry.get("path")
        current = file_state(target, rel)
        before = entry["before"]
        after = entry.get("after")
        if _state_matches(current, before):
            continue
        if not _state_matches(current, after):
            raise RecoveryError(
                f"recovery refused unexpected current bytes for {rel}; preserve the user edit and replan"
            )
        restore_entries.append(entry)
    restored: list[str] = []
    for entry in reversed(restore_entries):
        rel = entry.get("path")
        path = contained_path(target, rel, "recovery path")
        before = entry["before"]
        if before.get("kind") == "absent":
            if path.exists():
                if not path.is_file():
                    raise RecoveryError(f"cannot remove non-file recovery path: {rel}")
                path.unlink()
        elif before.get("kind") == "file":
            backup_name = entry.get("backup")
            if not isinstance(backup_name, str) or "/" in backup_name:
                raise RecoveryError(f"missing recovery backup for {rel}")
            backup = backup_root / backup_name
            if not backup.is_file() or sha256_file(backup) != before.get("sha256"):
                raise RecoveryError(f"recovery backup hash mismatch for {rel}")
            atomic_write(path, backup.read_bytes(), int(before["mode"]))
        else:
            raise RecoveryError(f"unknown pre-apply state for {rel}")
        if file_state(target, rel) != before:
            raise RecoveryError(f"rollback verification failed for {rel}")
        restored.append(rel)
    created_parents = journal.get("created_parent_dirs")
    if not isinstance(created_parents, list) or not all(
        isinstance(item, str) for item in created_parents
    ):
        raise RecoveryError("recovery journal parent-directory baseline is invalid")
    remove_created_empty_parents(target, created_parents)
    complete_transaction(target)
    return restored
