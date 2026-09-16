"""Strict profile validation for generic controlled evaluation."""

import hashlib
import json
from pathlib import Path, PurePosixPath
import re

PACKAGE_FILES = frozenset(
    "configuration.py controller.py checks.py admission.py publication.py cleanup.py".split()
)
CONFIG_KEYS = set(
    """schema owner_root candidate_root source_commit source_tree baseline_files
    writable_files required_owner_tests owner_test_map required_project_cases
    held_project_checks tools dependencies owner_sources package_files git_metadata
    timeout_seconds max_lines max_complexity""".split()
)
SHA256 = re.compile(r"[0-9a-f]{64}")
COMMIT = re.compile(r"[0-9a-f]{40,64}")
RUN = re.compile(r"run-[1-9][0-9]*")
CASE = re.compile(r"[^\x00-\x1f\x7f]+")
TEST = re.compile(r"test_[A-Za-z0-9_]+")


def pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def regular_bytes(path):
    import cleanup

    return cleanup.regular_bytes(path)


def external_bytes(path):
    import cleanup

    return cleanup.external_bytes(path)


def descendant(root, path, *, must_exist=True):
    import cleanup

    return cleanup.descendant(root, path, must_exist=must_exist)


def _hash(value, label):
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise ValueError(f"invalid SHA256 for {label}")
    return value


def _relative(value, label):
    if not isinstance(value, str) or not value:
        raise ValueError(f"invalid relative path for {label}")
    path = PurePosixPath(value)
    if (
        str(path) != value
        or path.is_absolute()
        or ".." in path.parts
        or path.parts[0] == ".git"
    ):
        raise ValueError(f"invalid relative path for {label}: {value}")
    return value


def _string_list(value, pattern, label, *, allow_empty=False):
    if not isinstance(value, list) or (not value and not allow_empty):
        raise ValueError(f"invalid {label}")
    if any(not isinstance(item, str) or not pattern.fullmatch(item) for item in value):
        raise ValueError(f"invalid {label}")
    if value != sorted(set(value)):
        raise ValueError(f"{label} must be unique and sorted")
    return tuple(value)


def _path_hashes(value, label, *, required=None, allow_empty=False):
    if not isinstance(value, dict) or (not value and not allow_empty):
        raise ValueError(f"invalid {label}")
    result = {_relative(name, label): _hash(item, name) for name, item in value.items()}
    if required is not None and set(result) != set(required):
        raise ValueError(f"{label} has the wrong inventory")
    return result


def _absolute_hashes(value, label):
    if not isinstance(value, dict):
        raise ValueError(f"invalid {label}")
    result = {}
    for raw, expected in value.items():
        path = Path(raw) if isinstance(raw, str) else Path()
        if not path.is_absolute() or path.resolve(strict=True) != path:
            raise ValueError(f"{label} path must be canonical and absolute")
        result[str(path)] = _hash(expected, raw)
    return result


def _tools(value):
    if not isinstance(value, dict) or set(value) != {"codex", "python", "ruff"}:
        raise ValueError("invalid tool inventory")
    result = {}
    for name, item in value.items():
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise ValueError(f"invalid tool record: {name}")
        path = Path(item["path"]) if isinstance(item["path"], str) else Path()
        if not path.is_absolute() or path.resolve(strict=True) != path:
            raise ValueError(f"tool path must be canonical and absolute: {name}")
        result[name] = {"path": str(path), "sha256": _hash(item["sha256"], name)}
    return result


def _metadata_path(value, key):
    path = Path(value[key]) if isinstance(value[key], str) else Path()
    if not path.is_absolute() or path.resolve(strict=True) != path:
        raise ValueError(f"invalid git metadata path: {key}")


def _git_metadata(value):
    keys = {
        "kind", "entry_path", "entry_sha256", "gitdir", "head_path",
        "head_sha256", "head", "common_path", "common_sha256", "ref",
        "revision_path", "revision_sha256", "revision_kind",
    }
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError("invalid git metadata")
    if value["kind"] not in {"directory", "pointer"}:
        raise ValueError("invalid git metadata kind")
    nullable_hashes = {"entry_sha256", "common_sha256"}
    for key in ("gitdir", "head_path", "revision_path"):
        _metadata_path(value, key)
    if value["common_path"] is not None:
        _metadata_path(value, "common_path")
    for key in ("entry_sha256", "head_sha256", "common_sha256", "revision_sha256"):
        if value[key] is None and key in nullable_hashes:
            continue
        _hash(value[key], key)
    if value["revision_kind"] not in {"detached", "loose-ref", "packed-refs"}:
        raise ValueError("invalid Git revision kind")
    if not isinstance(value["head"], str) or not isinstance(value["ref"], (str, type(None))):
        raise ValueError("invalid Git HEAD metadata")
    return value


def _layout(value, config_path, package_dir):
    owner = Path(value["owner_root"]) if isinstance(value["owner_root"], str) else Path()
    candidate = (
        Path(value["candidate_root"])
        if isinstance(value["candidate_root"], str)
        else Path()
    )
    if not owner.is_absolute() or not candidate.is_absolute() or owner == candidate:
        raise ValueError("owner and candidate must be distinct absolute paths")
    if owner.resolve(strict=True) != owner or candidate.resolve(strict=True) != candidate:
        raise ValueError("roots must be existing canonical directories")
    if owner in candidate.parents or candidate in owner.parents:
        raise ValueError("owner and candidate must not be nested")
    if descendant(owner, config_path) != owner / "protected-owner/config.json":
        raise ValueError("configuration has the wrong authority path")
    if descendant(owner, package_dir) != owner / "harness-adaptation":
        raise ValueError("executing package is outside harness-adaptation")
    return owner, candidate


def _source_data(value):
    baseline = _path_hashes(value["baseline_files"], "baseline files")
    writable = tuple(
        _relative(item, "writable files")
        for item in _string_list(value["writable_files"], re.compile(r".+"), "writable files", allow_empty=True)
    )
    source_tree = value["source_tree"]
    if not isinstance(source_tree, dict) or set(source_tree) != {"tracked_files", "inventory_sha256"}:
        raise ValueError("invalid source tree record")
    if source_tree["tracked_files"] != sorted(baseline) or _hash(source_tree["inventory_sha256"], "source tree") != digest(canonical(baseline)):
        raise ValueError("source tree differs from baseline inventory")
    return baseline, writable


def _test_data(value, owner_sources):
    tests = _string_list(value["required_owner_tests"], TEST, "owner tests")
    test_map = value["owner_test_map"]
    if not isinstance(test_map, dict) or set(test_map) != set(tests):
        raise ValueError("owner test map differs from required tests")
    test_map = {name: _relative(path, "owner test map") for name, path in test_map.items()}
    if any(path not in owner_sources or not path.startswith("protected-owner/owner-tests/") for path in test_map.values()):
        raise ValueError("owner test map names an unpinned test source")
    cases = _string_list(value["required_project_cases"], CASE, "project cases")
    held = _string_list(value["held_project_checks"], CASE, "held project checks", allow_empty=True)
    return tests, test_map, cases, held


def _limits(value):
    for key, ceiling in (("timeout_seconds", 300), ("max_lines", 300), ("max_complexity", 10)):
        if type(value[key]) is not int or not 1 <= value[key] <= ceiling:
            raise ValueError(f"invalid {key}")


def load(config_path, package_dir):
    config_path, package_dir = Path(config_path), Path(package_dir)
    raw = regular_bytes(config_path)
    pinned = regular_bytes(config_path.with_name("config.sha256")).decode("ascii")
    if pinned != digest(raw) + "\n":
        raise ValueError("configuration bytes changed after preparation")
    value = json.loads(raw, object_pairs_hook=pairs)
    if not isinstance(value, dict) or set(value) != CONFIG_KEYS:
        raise ValueError("unknown or missing configuration fields")
    if value["schema"] != "vibeos.controlled-evaluation.profile.v1":
        raise ValueError("unsupported configuration schema")
    owner, candidate = _layout(value, config_path, package_dir)
    if not isinstance(value["source_commit"], str) or not COMMIT.fullmatch(value["source_commit"]):
        raise ValueError("invalid source commit")
    baseline, writable = _source_data(value)
    owner_sources = _path_hashes(value["owner_sources"], "owner sources")
    package_files = _path_hashes(value["package_files"], "package files", required=PACKAGE_FILES)
    tests, test_map, cases, held = _test_data(value, owner_sources)
    _limits(value)
    return dict(value, owner_root=str(owner), candidate_root=str(candidate), baseline_files=baseline,
                writable_files=writable, required_owner_tests=tests, owner_test_map=test_map,
                required_project_cases=cases, held_project_checks=held, tools=_tools(value["tools"]),
                dependencies=_absolute_hashes(value["dependencies"], "dependencies"),
                owner_sources=owner_sources, package_files=package_files,
                git_metadata=_git_metadata(value["git_metadata"]), config_sha256=digest(raw))


def pinned_files(items, label, *, base=None):
    result = {}
    for name, expected in items.items():
        target = Path(name) if base is None else descendant(base, Path(base) / name)
        actual = digest(external_bytes(target) if base is None else regular_bytes(target))
        if actual != expected:
            raise ValueError(f"{label} hash mismatch: {name}")
        result[name] = actual
    return result


def bindings(config):
    import controller

    return controller.bindings(config)


def evaluation_command(config, run):
    import controller

    return controller.evaluation_command(config, run)
