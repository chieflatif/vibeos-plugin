"""Owner-side evaluator using the runtime-native Codex sandbox."""

import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import admission  # noqa: E402 - isolated sibling package after path setup
import configuration  # noqa: E402 - isolated sibling package after path setup

ACTIVE = None


def bindings(config):
    """Re-read every pinned owner, package, tool, candidate, and Git input."""
    import checks

    root = Path(config["owner_root"])
    config_path = root / "protected-owner/config.json"
    config_hash = configuration.digest(configuration.regular_bytes(config_path))
    if config_hash != config["config_sha256"]:
        raise ValueError("configuration bytes changed")
    actual_owner = {
        "protected-owner/" + name
        for name in checks.tree_inventory(root / "protected-owner")
    }
    expected_owner = set(config["owner_sources"]) | {
        "protected-owner/config.json", "protected-owner/config.sha256"
    }
    if actual_owner != expected_owner:
        raise ValueError("protected owner inventory differs from profile")
    if set(checks.tree_inventory(root / "harness-adaptation")) != configuration.PACKAGE_FILES:
        raise ValueError("harness package inventory differs from profile")
    tools = {
        name: configuration.digest(configuration.external_bytes(item["path"]))
        for name, item in config["tools"].items()
    }
    if any(tools[name] != config["tools"][name]["sha256"] for name in tools):
        raise ValueError("tool hash mismatch")
    return {
        "config": config_hash,
        "owner_sources": configuration.pinned_files(
            config["owner_sources"], "owner source", base=root
        ),
        "package": configuration.pinned_files(
            config["package_files"], "package", base=root / "harness-adaptation"
        ),
        "candidate": checks.candidate_binding(config),
        "tools": tools,
        "dependencies": configuration.pinned_files(config["dependencies"], "dependency"),
        "git": checks.git_binding(config),
        "source_commit": config["source_commit"],
        "source_tree": config["source_tree"],
    }


def evaluation_command(config, run):
    """Build the only supported evaluation command: native Codex sandbox."""
    root = Path(config["owner_root"])
    output = root / "results/checks" / run
    setting = (
        'permissions.evaluator={extends=":read-only",filesystem={'
        + json.dumps(str(output))
        + '="write"}}'
    )
    return [
        config["tools"]["codex"]["path"],
        "sandbox",
        "--sandbox-state-disable-network",
        "-P",
        "evaluator",
        "-c",
        setting,
        "-C",
        str(root),
        "--",
        config["tools"]["python"]["path"],
        "-I",
        "-B",
        str(root / "harness-adaptation/checks.py"),
        str(root / "protected-owner/config.json"),
        run,
    ]


class EvaluationInterrupted(Exception):
    """Raised after owner-directed interruption and process-group cleanup."""


def exclusive_json(path, value):
    with path.open("xb") as stream:
        stream.write(configuration.canonical(value))
        stream.flush()
        os.fsync(stream.fileno())


def replace_json(path, value):
    if path.is_symlink():
        raise ValueError(f"authority output is a symlink: {path}")
    temporary = path.with_name(".current-" + str(os.getpid()) + ".partial")
    try:
        with temporary.open("xb") as stream:
            stream.write(configuration.canonical(value))
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def terminate(process):
    if process is None:
        return b"", b""
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    try:
        return process.communicate(timeout=3)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        return process.communicate()


def interrupted(signum, frame):
    del signum, frame
    terminate(ACTIVE)
    raise EvaluationInterrupted("controller interrupted")


def launch(command, root, timeout):
    global ACTIVE
    environment = dict(os.environ)
    environment.update(PYTHONDONTWRITEBYTECODE="1", PYTEST_DISABLE_PLUGIN_AUTOLOAD="1")
    environment.pop("PYTEST_ADDOPTS", None)
    environment.pop("PYTEST_PLUGINS", None)
    result = {
        "exit": None, "timed_out": False, "interrupted": False,
        "stdout": "", "stderr": "", "error": None, "reaped": False,
        "pid": None, "process_group": None,
    }
    previous = {
        item: signal.signal(item, interrupted) for item in (signal.SIGTERM, signal.SIGINT)
    }
    try:
        ACTIVE = subprocess.Popen(
            command, cwd=root, env=environment, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, start_new_session=True,
        )
        result.update(pid=ACTIVE.pid, process_group=os.getpgid(ACTIVE.pid))
        try:
            stdout, stderr = ACTIVE.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            result["timed_out"] = True
            stdout, stderr = terminate(ACTIVE)
        else:
            try:
                os.killpg(ACTIVE.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        result.update(
            exit=ACTIVE.returncode, stdout=stdout.decode(errors="replace"),
            stderr=stderr.decode(errors="replace"), reaped=ACTIVE.poll() is not None,
        )
        if ACTIVE.returncode != 0 and "sandbox" in result["stderr"].lower():
            result["error"] = "native Codex sandbox unavailable or refused this profile"
    except EvaluationInterrupted as exc:
        result.update(interrupted=True, error=str(exc), reaped=ACTIVE is None or ACTIVE.poll() is not None)
    except OSError as exc:
        result["error"] = f"native Codex sandbox launch failed: {type(exc).__name__}: {exc}"
    finally:
        ACTIVE = None
        for item, handler in previous.items():
            signal.signal(item, handler)
    return result


def _seal(root, run, result_name, sealed_name):
    result = root / "results/checks" / run / result_name
    if not result.exists() or result.is_symlink():
        return None
    data = configuration.regular_bytes(result)
    sealed = root / "results/runs" / run / sealed_name
    with sealed.open("xb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return hashlib.sha256(data).hexdigest()


def evaluate(config, run):
    root = Path(config["owner_root"])
    run_dir = configuration.descendant(root, root / "results/runs" / run, must_exist=False)
    result_dir = configuration.descendant(root, root / "results/checks" / run, must_exist=False)
    if run_dir.exists() or result_dir.exists():
        raise ValueError("run identity already exists")
    replace_json(root / "results/current.json", {"run": run, "eligible": False, "state": "evaluating"})
    run_dir.mkdir()
    result_dir.mkdir()
    before = configuration.bindings(config)
    command = configuration.evaluation_command(config, run)
    started = time.monotonic()
    launched = launch(command, root, config["timeout_seconds"] + 1)
    launched["duration_seconds"] = time.monotonic() - started
    report_hash = checks_hash = project_hash = result_files = None
    try:
        report_hash = _seal(root, run, "owner-report.xml", "sealed-owner-report.xml")
        checks_hash = _seal(root, run, "checks.json", "sealed-checks.json")
        project_hash = _seal(root, run, "project.json", "sealed-project.json")
        import checks

        result_files = checks.tree_inventory(result_dir, keep_directories=True)
        output_error = None
    except (OSError, ValueError) as exc:
        output_error = str(exc)
    try:
        after, after_error = configuration.bindings(config), None
    except (OSError, ValueError) as exc:
        after, after_error = None, str(exc)
    record = {
        "schema": "vibeos.controlled-evaluation.run.v1", "run": run,
        "command": command, "before": before, "after": after,
        "after_error": after_error, "launch": launched,
        "report_sha256": report_hash, "checks_sha256": checks_hash,
        "project_sha256": project_hash, "result_files": result_files,
        "output_error": output_error,
    }
    exclusive_json(run_dir / "record.json", record)
    eligible, reason = admission.assess_record(config, run)
    record_hash = hashlib.sha256((run_dir / "record.json").read_bytes()).hexdigest()
    replace_json(root / "results/current.json", {
        "run": run, "eligible": eligible, "record_sha256": record_hash, "reason": reason,
    })
    return {"status": "EVALUATED", "run": run, "eligible": eligible, "reason": reason}
