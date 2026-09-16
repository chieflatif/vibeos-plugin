#!/usr/bin/env python3
"""Prepare, evaluate, and publish a bounded controlled evaluation."""

import ast
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import uuid

sys.dont_write_bytecode = True
PACKAGE_SOURCE = Path(__file__).resolve().parent / "controlled_evaluation"
sys.path.insert(0, str(PACKAGE_SOURCE))
import checks  # noqa: E402 - isolated sibling package after path setup
import configuration  # noqa: E402 - isolated sibling package after path setup

PACKAGE_FILES = tuple(sorted(configuration.PACKAGE_FILES))
SPEC_KEYS = set(
    """schema owner_tests project_adapter required_owner_tests required_project_cases
    held_project_checks writable_files tools dependencies timeout_seconds max_lines
    max_complexity""".split()
)
TEST = re.compile(r"test_[A-Za-z0-9_]+")
CASE = re.compile(r"[^\x00-\x1f\x7f]+")
COMMIT = re.compile(r"[0-9a-f]{40,64}")
USAGE = "usage: controlled-evaluation.py prepare --owner PATH --candidate PATH --spec FILE\n       controlled-evaluation.py evaluate|publish --owner PATH --run run-N"


canonical = configuration.canonical
digest = configuration.digest
regular_bytes = configuration.regular_bytes
tree_inventory = checks.tree_inventory


def canonical_file(raw, label):
    if not isinstance(raw, str):
        raise ValueError(f"invalid {label} path")
    path = Path(raw)
    if not path.is_absolute():
        raise ValueError(f"{label} path must be absolute")
    target = path.resolve(strict=True)
    if target != path or not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError(f"{label} must be a canonical regular file")
    return path


def _packed_commit(data, ref):
    matches = []
    for line in data.decode("utf8").splitlines():
        if not line or line.startswith(("#", "^")):
            continue
        fields = line.split(" ")
        if len(fields) != 2:
            raise ValueError("malformed packed-refs")
        if fields[1] == ref:
            matches.append(fields[0])
    if len(matches) != 1:
        raise ValueError("Git ref is missing or duplicated in packed-refs")
    return matches[0]


def git_metadata(candidate):
    entry = candidate / ".git"
    mode = entry.lstat().st_mode
    if stat.S_ISREG(mode):
        pointer = regular_bytes(entry)
        if not pointer.startswith(b"gitdir: ") or pointer.count(b"\n") != 1:
            raise ValueError("invalid candidate .git pointer")
        named = Path(pointer[8:].strip().decode())
        gitdir = named.resolve(strict=True) if named.is_absolute() else (candidate / named).resolve(strict=True)
        kind, entry_hash = "pointer", digest(pointer)
    elif stat.S_ISDIR(mode):
        gitdir = entry.resolve(strict=True)
        kind, entry_hash = "directory", None
    else:
        raise ValueError("candidate .git must be a directory or worktree pointer")
    if not gitdir.is_dir() or gitdir.is_symlink():
        raise ValueError("Git metadata root is not a canonical directory")
    head_path = gitdir / "HEAD"
    head_data = regular_bytes(head_path)
    head = head_data.decode("utf8").strip()
    common_path = gitdir / "commondir"
    if common_path.exists():
        common_data = regular_bytes(common_path)
        common = (gitdir / common_data.decode("utf8").strip()).resolve(strict=True)
        common_name, common_hash = str(common_path.resolve(strict=True)), digest(common_data)
    else:
        common, common_name, common_hash = gitdir, None, None
    ref = head[5:] if head.startswith("ref: ") else None
    if ref is None:
        revision_path, revision_data, revision_kind = head_path, head_data, "detached"
        commit = head
    else:
        if not ref.startswith("refs/") or ".." in Path(ref).parts:
            raise ValueError("invalid Git HEAD reference")
        loose = common / ref
        if loose.exists():
            revision_path, revision_data, revision_kind = loose, regular_bytes(loose), "loose-ref"
            commit = revision_data.decode("utf8").strip()
        else:
            revision_path = common / "packed-refs"
            revision_data, revision_kind = regular_bytes(revision_path), "packed-refs"
            commit = _packed_commit(revision_data, ref)
    if not COMMIT.fullmatch(commit):
        raise ValueError("HEAD does not resolve to a commit identifier")
    return commit, {
        "kind": kind, "entry_path": str(entry), "entry_sha256": entry_hash,
        "gitdir": str(gitdir), "head_path": str(head_path.resolve(strict=True)),
        "head_sha256": digest(head_data), "head": head,
        "common_path": common_name, "common_sha256": common_hash, "ref": ref,
        "revision_path": str(revision_path.resolve(strict=True)),
        "revision_sha256": digest(revision_data), "revision_kind": revision_kind,
    }


def test_map(paths, required):
    found = {}
    for path in paths:
        source = regular_bytes(path)
        module = ast.parse(source, filename=str(path))
        names = {
            node.name for node in module.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and TEST.fullmatch(node.name)
        }
        destination = "protected-owner/owner-tests/" + path.name
        for name in names:
            if name in found:
                raise ValueError(f"duplicate owner test function: {name}")
            found[name] = destination
    if set(required) != set(found).intersection(required):
        raise ValueError("a required owner test function is missing")
    return {name: found[name] for name in required}


def write_file(path, data):
    with path.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def pinned_tool(name, raw):
    path = canonical_file(raw, name)
    if not os.access(path, os.X_OK):
        raise ValueError(f"tool is not executable: {name}")
    return {"path": str(path), "sha256": digest(regular_bytes(path))}


def prepare_layout(owner_raw, candidate_raw):
    owner, candidate = Path(owner_raw), Path(candidate_raw)
    if not owner.is_absolute() or not candidate.is_absolute():
        raise ValueError("owner and candidate must be absolute paths")
    resolved_candidate = candidate.resolve(strict=True)
    if resolved_candidate != candidate or not stat.S_ISDIR(candidate.lstat().st_mode):
        raise ValueError("candidate must be a canonical directory")
    if owner.parent.resolve(strict=True) != owner.parent or owner.name in {"", ".", ".."}:
        raise ValueError("owner parent must be canonical and existing")
    try:
        owner.lstat()
    except FileNotFoundError:
        pass
    else:
        raise ValueError("owner path already exists")
    owner = owner.parent / owner.name
    if owner == candidate or owner in candidate.parents or candidate in owner.parents:
        raise ValueError("owner and candidate must be distinct and nonnested")
    return owner, candidate


def prepare_spec(spec_raw):
    spec_path = canonical_file(spec_raw, "spec")
    spec = json.loads(regular_bytes(spec_path), object_pairs_hook=configuration.pairs)
    if not isinstance(spec, dict) or set(spec) != SPEC_KEYS or spec["schema"] != "vibeos.controlled-evaluation.spec.v1":
        raise ValueError("unknown, missing, or unsupported spec fields")
    required = configuration._string_list(spec["required_owner_tests"], TEST, "required owner tests")
    cases = configuration._string_list(spec["required_project_cases"], CASE, "required project cases")
    held = configuration._string_list(spec["held_project_checks"], CASE, "held project checks", allow_empty=True)
    writable = tuple(
        configuration._relative(item, "writable files")
        for item in configuration._string_list(spec["writable_files"], re.compile(r".+"), "writable files", allow_empty=True)
    )
    if not isinstance(spec["owner_tests"], list) or not spec["owner_tests"]:
        raise ValueError("owner_tests must be a nonempty path list")
    owner_tests = [canonical_file(item, "owner test") for item in spec["owner_tests"]]
    if len({path.name for path in owner_tests}) != len(owner_tests):
        raise ValueError("owner test basenames must be unique")
    adapter = canonical_file(spec["project_adapter"], "project adapter")
    mapping = test_map(owner_tests, required)
    if not isinstance(spec["tools"], dict) or set(spec["tools"]) != {"python", "ruff", "codex"}:
        raise ValueError("tools must name python, ruff, and codex")
    tools = {name: pinned_tool(name, raw) for name, raw in spec["tools"].items()}
    if not isinstance(spec["dependencies"], list) or len(set(spec["dependencies"])) != len(spec["dependencies"]):
        raise ValueError("dependencies must be an absolute path list")
    paths = [canonical_file(raw, "dependency") for raw in spec["dependencies"]]
    dependencies = {str(path): digest(regular_bytes(path)) for path in paths}
    for key, ceiling in (("timeout_seconds", 300), ("max_lines", 300), ("max_complexity", 10)):
        if type(spec[key]) is not int or not 1 <= spec[key] <= ceiling:
            raise ValueError(f"invalid {key}")
    return spec, required, cases, held, writable, owner_tests, adapter, mapping, tools, dependencies


def prepare(owner_raw, candidate_raw, spec_raw):
    owner, candidate = prepare_layout(owner_raw, candidate_raw)
    values = prepare_spec(spec_raw)
    spec, required, cases, held, writable = values[:5]
    owner_tests, adapter, mapping, tools, dependencies = values[5:]
    before = tree_inventory(candidate, skip_git=True)
    source_commit, git = git_metadata(candidate)
    git_tool = Path(shutil.which("git") or "").resolve(strict=True)
    revision = subprocess.run(
        [str(git_tool), "-C", str(candidate), "rev-parse", "--verify", "HEAD^{commit}"],
        capture_output=True,
        env={"PATH": os.environ.get("PATH", ""), "LC_ALL": "C"},
        timeout=30,
    )
    if revision.returncode != 0 or revision.stdout.decode().strip() != source_commit:
        raise ValueError("candidate HEAD is not the validated source commit")
    package_source = Path(__file__).resolve().parent / "controlled_evaluation"
    package_data = {name: regular_bytes(package_source / name) for name in PACKAGE_FILES}
    temporary = owner.parent / f".{owner.name}-{uuid.uuid4().hex}.partial"
    temporary.mkdir()
    try:
        (temporary / "protected-owner/owner-tests").mkdir(parents=True)
        (temporary / "harness-adaptation").mkdir()
        for directory in ("results/runs", "results/checks", "results/published"):
            (temporary / directory).mkdir(parents=True, exist_ok=True)
        for source in owner_tests:
            write_file(temporary / "protected-owner/owner-tests" / source.name, regular_bytes(source))
        write_file(temporary / "protected-owner/project_adapter.py", regular_bytes(adapter))
        for name, data in package_data.items():
            write_file(temporary / "harness-adaptation" / name, data)
        write_file(temporary / "results/writer.lock", b"")
        owner_sources = {
            "protected-owner/" + name: value
            for name, value in tree_inventory(temporary / "protected-owner").items()
        }
        package_files = tree_inventory(temporary / "harness-adaptation")
        config = {
            "schema": "vibeos.controlled-evaluation.profile.v1",
            "owner_root": str(owner), "candidate_root": str(candidate),
            "source_commit": source_commit,
            "source_tree": {"tracked_files": sorted(before), "inventory_sha256": digest(canonical(before))},
            "baseline_files": before, "writable_files": writable,
            "required_owner_tests": required, "owner_test_map": mapping,
            "required_project_cases": cases, "held_project_checks": held,
            "tools": tools, "dependencies": dependencies,
            "owner_sources": owner_sources, "package_files": package_files,
            "git_metadata": git, "timeout_seconds": spec["timeout_seconds"],
            "max_lines": spec["max_lines"], "max_complexity": spec["max_complexity"],
        }
        config_data = canonical(config)
        write_file(temporary / "protected-owner/config.json", config_data)
        write_file(temporary / "protected-owner/config.sha256", (digest(config_data) + "\n").encode())
        after = tree_inventory(candidate, skip_git=True)
        after_commit, after_git = git_metadata(candidate)
        if before != after or source_commit != after_commit or git != after_git:
            raise ValueError("candidate changed during preparation")
        os.rename(temporary, owner)
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return {"status": "PREPARED", "owner": str(owner), "candidate": str(candidate), "source_commit": source_commit}


def owner_action(action, owner_raw, run):
    owner = Path(owner_raw)
    if not owner.is_absolute() or owner.resolve(strict=True) != owner:
        raise ValueError("owner must be a canonical absolute directory")
    package = owner / "harness-adaptation"
    for name in ("publication", "controller", "admission", "checks", "configuration", "cleanup"):
        sys.modules.pop(name, None)
    sys.path.insert(0, str(package))
    import publication

    return publication.main([str(owner / "protected-owner/config.json"), action, run])


def main(argv):
    try:
        if argv in (["-h"], ["--help"]):
            print(USAGE)
            return 0
        if len(argv) == 7 and argv[0] == "prepare" and argv[1] == "--owner" and argv[3] == "--candidate" and argv[5] == "--spec":
            result = prepare(argv[2], argv[4], argv[6])
            print(json.dumps(result, sort_keys=True))
            return 0
        if len(argv) == 5 and argv[0] in {"evaluate", "publish"} and argv[1] == "--owner" and argv[3] == "--run":
            return owner_action(argv[0], argv[2], argv[4])
        raise ValueError(USAGE)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, json.JSONDecodeError, SyntaxError) as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc)}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
