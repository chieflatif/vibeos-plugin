"""Single-writer evaluation and immutable PRE_REVIEW publication."""

import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import uuid

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import admission  # noqa: E402 - isolated sibling package after path setup
import cleanup  # noqa: E402 - isolated sibling package after path setup
import configuration  # noqa: E402 - isolated sibling package after path setup
import controller  # noqa: E402 - isolated sibling package after path setup


def acquire(root):
    path = configuration.descendant(root, root / "results/writer.lock")
    descriptor = os.open(path, os.O_RDWR | getattr(os, "O_NOFOLLOW", 0))
    stream = os.fdopen(descriptor, "r+")
    opened, current = os.fstat(stream.fileno()), path.lstat()
    if not stat.S_ISREG(opened.st_mode) or (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino):
        stream.close()
        raise ValueError("writer lock identity changed")
    try:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        stream.close()
        return None
    return stream


def exclusive(path, data):
    if path.is_symlink():
        raise ValueError(f"output is a symlink: {path}")
    try:
        with path.open("xb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if configuration.regular_bytes(path) != data:
            raise ValueError(f"existing immutable output differs: {path.name}")
    cleanup.sync_directory(path.parent)


def admitted_payload(config, run, record):
    root = Path(config["owner_root"])
    record_path = root / "results/runs" / run / "record.json"
    return configuration.canonical({
        "schema": "vibeos.controlled-evaluation.admitted.v1",
        "run": run,
        "record_sha256": hashlib.sha256(configuration.regular_bytes(record_path)).hexdigest(),
        "source_commit": config["source_commit"],
        "source_tree": config["source_tree"],
        "candidate_tree_sha256": record["after"]["candidate"]["tree_sha256"],
        "project_sha256": record["project_sha256"],
        "bindings": record["after"],
    })


def publication_packet(config, run, admitted, record):
    root = Path(config["owner_root"])
    record_path = root / "results/runs" / run / "record.json"
    return configuration.canonical({
        "schema": "vibeos.controlled-evaluation.publication.v1",
        "status": "PRE_REVIEW",
        "run": run,
        "admitted_sha256": hashlib.sha256(admitted).hexdigest(),
        "record_sha256": hashlib.sha256(configuration.regular_bytes(record_path)).hexdigest(),
        "bindings_sha256": hashlib.sha256(configuration.canonical(record["after"])).hexdigest(),
        "source_commit": config["source_commit"],
        "source_tree_sha256": config["source_tree"]["inventory_sha256"],
        "package_files": config["package_files"],
        "project_qualified": False,
        "runtime_qualified": False,
        "held_project_checks": list(config["held_project_checks"]),
    })


def publish(config, run, lock):
    root = Path(config["owner_root"])
    record = admission.verify_current(config, run)
    admitted = admitted_payload(config, run, record)
    exclusive(root / "results/runs" / run / "admitted.json", admitted)
    packet = publication_packet(config, run, admitted, record)
    final = configuration.descendant(root, root / "results/published" / f"{run}.json", must_exist=False)
    if final.is_symlink():
        raise ValueError("publication must not be a symlink")
    if final.exists():
        if configuration.regular_bytes(final) != packet:
            raise ValueError("existing publication differs; never overwrite")
        removed = cleanup.remove_aliases(final, run, lock)
        return {"status": "ALREADY_PUBLISHED", "run": run, "removed_aliases": removed}
    temporary = final.parent / f".{run}-{uuid.uuid4().hex}.partial"
    with temporary.open("xb") as stream:
        stream.write(packet)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, final)
    except FileExistsError:
        if configuration.regular_bytes(final) != packet:
            raise ValueError("publication conflict; never overwrite")
    cleanup.sync_directory(final.parent)
    removed = cleanup.remove_aliases(final, run, lock)
    return {"status": "PUBLISHED", "run": run, "removed_aliases": removed}


def perform(config_path, action, run):
    if action not in {"evaluate", "publish"}:
        raise ValueError("action must be evaluate or publish")
    if not configuration.RUN.fullmatch(run):
        raise ValueError("invalid run identity")
    package = Path(__file__).resolve().parent
    config = configuration.load(config_path, package)
    root = Path(config["owner_root"])
    lock = acquire(root)
    if lock is None:
        return {"status": "BUSY", "run": run}
    try:
        if action == "evaluate":
            return controller.evaluate(config, run)
        return publish(config, run, lock)
    finally:
        lock.close()


def main(argv):
    try:
        if len(argv) != 3:
            raise ValueError("expected CONFIG ACTION RUN only")
        result = perform(*argv)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, json.JSONDecodeError) as exc:
        result = {"status": "REFUSED", "reason": str(exc)}
    print(json.dumps(result, sort_keys=True))
    successful = result["status"] in {"PUBLISHED", "ALREADY_PUBLISHED"}
    successful = successful or (result["status"] == "EVALUATED" and result.get("eligible") is True)
    return 0 if successful else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
