"""Filesystem custody helpers for controlled evaluation."""

import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import time


def regular_bytes(path):
    """Read one stable regular file without following a final symlink."""
    path = Path(path)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError(f"not a regular file: {path}")
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        opened = os.fstat(descriptor)
        chunks = []
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            chunks.append(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    current = path.lstat()
    identities = {
        (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns)
        for item in (before, opened, after, current)
    }
    if len(identities) != 1:
        raise ValueError(f"file changed while read: {path}")
    return b"".join(chunks)


def external_bytes(path):
    """Read the canonical target of a pinned external path."""
    target = Path(path).resolve(strict=True)
    if target != Path(path):
        raise ValueError(f"external path is not canonical: {path}")
    return regular_bytes(target)


def descendant(root, path, *, must_exist=True):
    """Return a canonical lexical descendant after rejecting parent links."""
    root, path = Path(root), Path(path)
    if not root.is_absolute() or not path.is_absolute():
        raise ValueError("paths must be absolute")
    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes configured root: {path}") from exc
    if not relative.parts or ".." in relative.parts:
        raise ValueError(f"path is not a root descendant: {path}")
    cursor = root
    for part in relative.parts:
        cursor /= part
        try:
            mode = cursor.lstat().st_mode
        except FileNotFoundError:
            if must_exist:
                raise
            break
        if stat.S_ISLNK(mode):
            raise ValueError(f"symlink rejected: {cursor}")
    if root.resolve(strict=True) != root:
        raise ValueError(f"non-canonical root: {root}")
    if must_exist and path.resolve(strict=True) != path:
        raise ValueError(f"non-canonical path: {path}")
    return path


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _group_alive(process_group):
    try:
        os.killpg(process_group, 0)
        return True
    except ProcessLookupError:
        return False


def _signal_group(process_group, signum):
    try:
        os.killpg(process_group, signum)
    except ProcessLookupError:
        return False
    return True


def cleanup_process_group(process_group, grace_seconds):
    """Terminate a process group even when its original leader has exited."""
    deadline = time.monotonic() + grace_seconds
    _signal_group(process_group, signal.SIGTERM)
    while _group_alive(process_group) and time.monotonic() < deadline:
        time.sleep(min(0.05, max(0, deadline - time.monotonic())))
    if _group_alive(process_group):
        _signal_group(process_group, signal.SIGKILL)


def terminate_process_group(process, grace_seconds):
    """Stop a launched group and return the leader's captured streams."""
    deadline = time.monotonic() + grace_seconds
    _signal_group(process.pid, signal.SIGTERM)
    try:
        output = process.communicate(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        output = None
    remaining = max(0, deadline - time.monotonic())
    if _group_alive(process.pid) and remaining:
        time.sleep(remaining)
    if _group_alive(process.pid):
        _signal_group(process.pid, signal.SIGKILL)
    return process.communicate() if output is None else output


def remove_aliases(final, run, lock):
    """Remove only same-inode temporary aliases while holding the writer lock."""
    final = Path(final)
    if not re.fullmatch(r"run-[1-9][0-9]*", run) or final.name != run + ".json":
        raise ValueError("invalid publication identity")
    lock_stat = os.fstat(lock.fileno())
    current_lock = (final.parents[1] / "writer.lock").lstat()
    if not stat.S_ISREG(current_lock.st_mode) or (
        lock_stat.st_dev,
        lock_stat.st_ino,
    ) != (current_lock.st_dev, current_lock.st_ino):
        raise ValueError("publication lock identity changed")
    identity = final.lstat()
    if not stat.S_ISREG(identity.st_mode):
        raise ValueError("publication must be a regular file")
    removed = []
    pattern = re.compile(r"\." + re.escape(run) + r"-[0-9a-f]{32}\.partial")
    for alias in sorted(final.parent.iterdir()):
        if not pattern.fullmatch(alias.name):
            continue
        entry = alias.lstat()
        if stat.S_ISREG(entry.st_mode) and (entry.st_dev, entry.st_ino) == (
            identity.st_dev,
            identity.st_ino,
        ):
            alias.unlink()
            removed.append(alias.name)
    sync_directory(final.parent)
    return removed
