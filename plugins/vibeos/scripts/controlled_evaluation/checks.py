"""Sandbox-side fixed lint, owner tests, and project adapter execution."""

import json
import os
from pathlib import Path, PurePosixPath
import signal
import stat
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import configuration  # noqa: E402 - isolated sibling package after path setup
import cleanup  # noqa: E402 - isolated sibling package after path setup

ACTIVE = None
TERMINATION_GRACE_SECONDS = 0.5


class CheckInterrupted(Exception):
    """Raised after a controlling signal cleans the active check group."""


def tree_inventory(root, *, skip_git=False, keep_directories=False):
    """Hash a complete regular-file tree and reject links and special entries."""
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError(f"tree root is not a regular directory: {root}")
    files, directories = {}, set()
    stack = [root]
    while stack:
        directory = stack.pop()
        for entry in os.scandir(directory):
            relative = Path(entry.path).relative_to(root).as_posix()
            mode = entry.stat(follow_symlinks=False).st_mode
            if skip_git and relative == ".git":
                if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                    raise ValueError("candidate .git entry has an invalid type")
                continue
            if stat.S_ISDIR(mode):
                directories.add(relative)
                stack.append(Path(entry.path))
            elif stat.S_ISREG(mode):
                files[relative] = configuration.digest(
                    configuration.regular_bytes(entry.path)
                )
            else:
                raise ValueError(f"unexpected tree entry: {relative}")
    if keep_directories:
        return {"files": files, "directories": sorted(directories)}
    expected = {
        str(parent)
        for name in files
        for parent in PurePosixPath(name).parents
        if str(parent) != "."
    }
    if directories != expected:
        raise ValueError("tree has unexpected or empty directory entries")
    return files


def candidate_binding(config):
    observed = tree_inventory(config["candidate_root"], skip_git=True)
    baseline = config["baseline_files"]
    if observed != baseline:
        raise ValueError("candidate differs from the complete prepared baseline")
    return {
        "files": observed,
        "tree_sha256": configuration.digest(configuration.canonical(observed)),
        "writable": {name: observed.get(name) for name in config["writable_files"]},
    }


def _pinned(path, expected, label):
    actual = configuration.digest(configuration.external_bytes(path))
    if actual != expected:
        raise ValueError(f"{label} hash mismatch")
    return configuration.external_bytes(path)


def _packed_revision(data, ref):
    matches = []
    for raw in data.decode("utf8").splitlines():
        if not raw or raw.startswith(("#", "^")):
            continue
        fields = raw.split(" ")
        if len(fields) != 2:
            raise ValueError("malformed packed-refs")
        if fields[1] == ref:
            matches.append(fields[0])
    if len(matches) != 1:
        raise ValueError("Git ref is missing or duplicated in packed-refs")
    return matches[0]


def _verify_git_entry(metadata, entry, mode):
    if metadata["kind"] != "pointer":
        if not stat.S_ISDIR(mode) or entry.resolve(strict=True) != Path(metadata["gitdir"]):
            raise ValueError("candidate .git directory changed identity")
        return
    if not stat.S_ISREG(mode):
        raise ValueError("candidate .git pointer changed type")
    pointer = _pinned(entry, metadata["entry_sha256"], ".git pointer")
    prefix = b"gitdir: "
    if not pointer.startswith(prefix) or pointer.count(b"\n") != 1:
        raise ValueError("invalid candidate .git pointer")
    target = Path(pointer[len(prefix) :].strip().decode())
    if not target.is_absolute():
        target = (entry.parent / target).resolve(strict=True)
    if target.resolve(strict=True) != Path(metadata["gitdir"]):
        raise ValueError("candidate .git points at different metadata")


def git_binding(config):
    metadata = config["git_metadata"]
    entry = Path(metadata["entry_path"])
    mode = entry.lstat().st_mode
    _verify_git_entry(metadata, entry, mode)
    head_data = _pinned(metadata["head_path"], metadata["head_sha256"], "Git HEAD")
    head = head_data.decode("utf8").strip()
    if head != metadata["head"]:
        raise ValueError("Git HEAD content changed")
    if metadata["common_path"] is not None:
        _pinned(metadata["common_path"], metadata["common_sha256"], "Git commondir")
    revision_data = _pinned(
        metadata["revision_path"], metadata["revision_sha256"], "Git revision"
    )
    if metadata["revision_kind"] == "packed-refs":
        commit = _packed_revision(revision_data, metadata["ref"])
    else:
        commit = revision_data.decode("utf8").strip()
    if commit != config["source_commit"]:
        raise ValueError("HEAD does not resolve to the pinned source commit")
    return {
        "kind": metadata["kind"],
        "gitdir": metadata["gitdir"],
        "head": head,
        "head_ref": metadata["ref"],
        "commit": commit,
    }


def line_count(data):
    text = data.decode("utf8")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized.count("\n") + int(bool(normalized) and not normalized.endswith("\n"))


def sources(config):
    owner, candidate = Path(config["owner_root"]), Path(config["candidate_root"])
    paths = [owner / name for name in sorted(config["owner_sources"]) if name.endswith(".py")]
    paths.extend(owner / "harness-adaptation" / name for name in sorted(configuration.PACKAGE_FILES))
    paths.extend(
        candidate / name
        for name in config["writable_files"]
        if name.endswith(".py") and (candidate / name).exists()
    )
    return paths


def lint_command(config, paths):
    return [
        config["tools"]["ruff"]["path"], "check", "--no-cache", "--isolated",
        "--ignore-noqa", "--select", "E9,F,C901", "--config",
        f"lint.mccabe.max-complexity={config['max_complexity']}",
        *[str(path) for path in paths],
    ]


def pytest_command(config, report):
    owner = Path(config["owner_root"])
    selectors = [str(owner / config["owner_test_map"][name]) + "::" + name for name in config["required_owner_tests"]]
    return [
        config["tools"]["python"]["path"], "-I", "-B", "-m", "pytest", "-s", "-q",
        "-c", "/dev/null", "--noconftest", f"--rootdir={owner / 'protected-owner/owner-tests'}",
        "-p", "no:cacheprovider", f"--junitxml={report}", *selectors,
    ]


def project_command(config, result_dir):
    owner = Path(config["owner_root"])
    return [
        config["tools"]["python"]["path"], "-I", "-B",
        str(owner / "protected-owner/project_adapter.py"),
        config["candidate_root"], str(result_dir),
    ]


def terminate(process):
    if process is None:
        return b"", b""
    return cleanup.terminate_process_group(process, TERMINATION_GRACE_SECONDS)


def interrupted(signum, frame):
    del signum, frame
    terminate(ACTIVE)
    raise CheckInterrupted("checks interrupted by controller")


def execution_result(command, process, timed_out, stdout, stderr):
    return {
        "command": command, "exit": None if process is None else process.returncode,
        "timed_out": timed_out, "stdout": stdout.decode(errors="replace"),
        "stderr": stderr.decode(errors="replace"),
    }


def execute(command, config, environment, deadline):
    global ACTIVE
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        return execution_result(command, None, True, b"", b"")
    previous = {
        item: signal.signal(item, interrupted) for item in (signal.SIGTERM, signal.SIGINT)
    }
    try:
        ACTIVE = subprocess.Popen(
            command, cwd=config["owner_root"], env=environment,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
        )
        try:
            stdout, stderr = ACTIVE.communicate(timeout=remaining)
            timed_out = False
            cleanup.cleanup_process_group(ACTIVE.pid, TERMINATION_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            timed_out = True
            stdout, stderr = terminate(ACTIVE)
        return execution_result(command, ACTIVE, timed_out, stdout, stderr)
    finally:
        ACTIVE = None
        for item, handler in previous.items():
            signal.signal(item, handler)


def save(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True)
        stream.write("\n")


def run(config_path, run_name):
    if not configuration.RUN.fullmatch(run_name):
        raise ValueError("invalid run identity")
    package = Path(__file__).resolve().parent
    config = configuration.load(config_path, package)
    deadline = time.monotonic() + config["timeout_seconds"]
    configuration.bindings(config)
    root = Path(config["owner_root"])
    result_dir = configuration.descendant(root, root / "results/checks" / run_name)
    paths = sources(config)
    sizes = []
    for path in paths:
        data = configuration.regular_bytes(path)
        lines = line_count(data)
        sizes.append({"path": str(path), "lines": lines, "ok": bool(data) and lines <= config["max_lines"]})
    environment = dict(os.environ)
    environment.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1")
    environment.pop("PYTEST_ADDOPTS", None)
    environment.pop("PYTEST_PLUGINS", None)
    empty = {"command": None, "exit": None, "timed_out": False, "stdout": "", "stderr": ""}
    if not all(item["ok"] for item in sizes):
        save(result_dir / "checks.json", {"lint": dict(empty, sources=sizes), "pytest": None, "project": None})
        return 1
    lint = execute(lint_command(config, paths), config, environment, deadline)
    lint["sources"] = sizes
    if lint["exit"] != 0 or lint["timed_out"]:
        save(result_dir / "checks.json", {"lint": lint, "pytest": None, "project": None})
        return 1
    pytest_result = execute(pytest_command(config, result_dir / "owner-report.xml"), config, environment, deadline)
    project_result = execute(project_command(config, result_dir), config, environment, deadline)
    save(result_dir / "checks.json", {"lint": lint, "pytest": pytest_result, "project": project_result})
    return 0 if pytest_result["exit"] == 0 and project_result["exit"] == 0 else 1


def main(argv):
    try:
        if len(argv) != 2:
            raise ValueError("checks require config and run only")
        return run(*argv)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, CheckInterrupted, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
