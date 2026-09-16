#!/usr/bin/env python3
"""Directory-baseline helpers for exact profile-install rollback."""

from __future__ import annotations

import errno
from pathlib import Path, PurePosixPath
from typing import Iterable

from install_integrity import IntegrityError, contained_path, safe_relative


def absent_parent_directories(target: Path, mutation_paths: Iterable[str]) -> list[str]:
    """Record parent directories absent before the first install mutation."""
    parents: set[str] = set()
    for rel in mutation_paths:
        safe_relative(rel, "transaction mutation")
        pure = PurePosixPath(rel)
        for parent in pure.parents:
            if parent == PurePosixPath("."):
                continue
            parent_rel = parent.as_posix()
            path = contained_path(target, parent_rel, "transaction parent")
            if path.exists():
                if not path.is_dir():
                    raise IntegrityError(
                        f"transaction parent is not a directory: {parent_rel}"
                    )
            else:
                parents.add(parent_rel)
    return sorted(parents, key=lambda item: (len(PurePosixPath(item).parts), item))


def remove_created_empty_parents(target: Path, parents: Iterable[str]) -> list[str]:
    """Remove only recorded absent parents that remain empty after file restore."""
    removed: list[str] = []
    ordered = sorted(
        set(parents),
        key=lambda item: (len(PurePosixPath(item).parts), item),
        reverse=True,
    )
    for rel in ordered:
        path = contained_path(target, rel, "rollback parent")
        if not path.exists():
            continue
        if not path.is_dir():
            raise IntegrityError(f"rollback parent has unsafe type: {rel}")
        try:
            path.rmdir()
        except OSError as exc:
            if exc.errno in {errno.ENOTEMPTY, errno.EEXIST}:
                continue
            raise
        removed.append(rel)
    return removed
