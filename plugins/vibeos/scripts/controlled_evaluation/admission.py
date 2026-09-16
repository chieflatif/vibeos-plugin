"""Pure evidence reduction for one owner-controlled evaluation."""

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

import configuration  # noqa: E402 - isolated sibling package after path setup

RECORD_KEYS = set(
    """schema run command before after after_error launch report_sha256 checks_sha256
    project_sha256 result_files output_error""".split()
)
LAUNCH_KEYS = set(
    """exit timed_out interrupted stdout stderr error reaped duration_seconds pid
    process_group""".split()
)
EXECUTION_KEYS = {"command", "exit", "timed_out", "stdout", "stderr"}
PROJECT_KEYS = {"schema", "cases", "held", "project_qualified", "runtime_qualified"}


def load_object(path, keys):
    value = json.loads(configuration.regular_bytes(path), object_pairs_hook=configuration.pairs)
    if not isinstance(value, dict) or set(value) != keys:
        raise ValueError(f"invalid evidence schema: {Path(path).name}")
    return value


def junit_cases(data):
    root = ET.fromstring(data)
    if root.tag != "testsuites":
        raise ValueError("JUnit root is not testsuites")
    suites = list(root)
    if len(suites) != 1 or suites[0].tag != "testsuite":
        raise ValueError("invalid JUnit suite hierarchy")
    cases, totals = [], Counter()
    for suite in suites:
        for key in ("tests", "failures", "errors", "skipped"):
            raw = suite.get(key)
            if raw is None or not raw.isdecimal():
                raise ValueError("invalid JUnit counters")
            totals[key] += int(raw)
        children = list(suite)
        if any(child.tag != "testcase" for child in children):
            raise ValueError("unexpected JUnit child")
        if int(suite.get("tests")) != len(children):
            raise ValueError("JUnit suite count differs from contained cases")
        cases.extend(children)
    if totals["tests"] != len(cases) or any(totals[key] for key in ("failures", "errors", "skipped")):
        raise ValueError("JUnit does not record complete success")
    if any(list(case) for case in cases):
        raise ValueError("required test contains a failure or skip")
    return cases


def exact_coverage(config, report):
    expected = Counter(config["required_owner_tests"])
    observed = Counter()
    for case in junit_cases(report):
        if not case.get("classname") or not case.get("name"):
            raise ValueError("unexpected test case identity")
        observed[case.get("name")] += 1
    if observed != expected:
        raise ValueError("executed tests differ from required inventory")


def _successful_execution(value, command, label):
    if not isinstance(value, dict) or set(value) != EXECUTION_KEYS:
        raise ValueError(f"invalid {label} evidence")
    if value["command"] != command:
        raise ValueError(f"{label} command mismatch")
    if type(value["exit"]) is not int or value["exit"] != 0 or value["timed_out"] is not False:
        raise ValueError(f"{label} did not complete successfully")
    if not isinstance(value["stdout"], str) or not isinstance(value["stderr"], str):
        raise ValueError(f"invalid {label} streams")


def _check_summary(config, result_dir):
    import checks

    summary = load_object(result_dir / "checks.json", {"lint", "pytest", "project"})
    paths = checks.sources(config)
    lint = summary["lint"]
    if not isinstance(lint, dict) or set(lint) != EXECUTION_KEYS | {"sources"}:
        raise ValueError("invalid lint evidence")
    _successful_execution(
        {key: lint[key] for key in EXECUTION_KEYS},
        checks.lint_command(config, paths), "lint",
    )
    expected_paths = [str(path) for path in paths]
    sources = lint["sources"]
    if not isinstance(sources, list) or [item.get("path") if isinstance(item, dict) else None for item in sources] != expected_paths:
        raise ValueError("lint source inventory mismatch")
    if any(
        set(item) != {"path", "lines", "ok"}
        or type(item["lines"]) is not int
        or item["lines"] < 1
        or item["lines"] > config["max_lines"]
        or item["ok"] is not True
        for item in sources
    ):
        raise ValueError("lint source size evidence is invalid")
    _successful_execution(
        summary["pytest"], checks.pytest_command(config, result_dir / "owner-report.xml"), "pytest"
    )
    _successful_execution(
        summary["project"], checks.project_command(config, result_dir), "project checks"
    )


def _project_result(config, data):
    project = json.loads(data, object_pairs_hook=configuration.pairs)
    if not isinstance(project, dict) or set(project) != PROJECT_KEYS:
        raise ValueError("invalid project check schema")
    if project["schema"] != "vibeos.project-checks.v1":
        raise ValueError("unsupported project check schema")
    cases = project["cases"]
    if not isinstance(cases, list) or any(
        not isinstance(item, dict)
        or set(item) != {"id", "status"}
        or not isinstance(item["id"], str)
        or item["status"] not in {"PASS", "FAIL"}
        for item in cases
    ):
        raise ValueError("invalid project case inventory")
    expected = [{"id": item, "status": "PASS"} for item in config["required_project_cases"]]
    if cases != expected:
        raise ValueError("project cases differ from required exact PASS inventory")
    if project["held"] != list(config["held_project_checks"]):
        raise ValueError("held project checks differ from the profile")
    if project["project_qualified"] is not False or project["runtime_qualified"] is not False:
        raise ValueError("project adapter overstates qualification")


def _launch_evidence(record):
    launch = record["launch"]
    if not isinstance(launch, dict) or set(launch) != LAUNCH_KEYS:
        raise ValueError("invalid launch evidence")
    if (
        type(launch["exit"]) is not int
        or launch["exit"] != 0
        or launch["timed_out"] is not False
        or launch["interrupted"] is not False
        or launch["reaped"] is not True
        or launch["error"] is not None
        or launch["stdout"] != ""
        or launch["stderr"] != ""
    ):
        raise ValueError("evaluation did not exit cleanly and successfully")
    if record["output_error"] is not None:
        raise ValueError("evaluation output could not be sealed")


def _assess(config, run):
    import checks

    root = Path(config["owner_root"])
    run_dir = configuration.descendant(root, root / "results/runs" / run)
    result_dir = configuration.descendant(root, root / "results/checks" / run)
    record = load_object(run_dir / "record.json", RECORD_KEYS)
    if record["schema"] != "vibeos.controlled-evaluation.run.v1" or record["run"] != run:
        raise ValueError("run record identity mismatch")
    if record["command"] != configuration.evaluation_command(config, run):
        raise ValueError("evaluation command mismatch")
    _launch_evidence(record)
    live = configuration.bindings(config)
    if record["before"] != live or record["after"] != live or record["after_error"] is not None:
        raise ValueError("bound inputs changed during or after evaluation")
    top = {item.name: item.lstat().st_mode for item in result_dir.iterdir()}
    if set(top) != {"owner-report.xml", "checks.json", "project.json", "project-evidence"}:
        raise ValueError("project result top-level inventory is invalid")
    if (
        not all((result_dir / name).is_file() and not (result_dir / name).is_symlink() for name in ("owner-report.xml", "checks.json", "project.json"))
        or not (result_dir / "project-evidence").is_dir()
        or (result_dir / "project-evidence").is_symlink()
    ):
        raise ValueError("project result top-level entry type is invalid")
    result_files = checks.tree_inventory(result_dir, keep_directories=True)
    if record["result_files"] != result_files:
        raise ValueError("project result tree differs from run evidence")
    report = configuration.regular_bytes(result_dir / "owner-report.xml")
    sealed = configuration.regular_bytes(run_dir / "sealed-owner-report.xml")
    checks_data = configuration.regular_bytes(result_dir / "checks.json")
    sealed_checks = configuration.regular_bytes(run_dir / "sealed-checks.json")
    project_data = configuration.regular_bytes(result_dir / "project.json")
    sealed_project = configuration.regular_bytes(run_dir / "sealed-project.json")
    if report != sealed or hashlib.sha256(report).hexdigest() != record["report_sha256"]:
        raise ValueError("owner report differs from sealed evidence")
    if checks_data != sealed_checks or hashlib.sha256(checks_data).hexdigest() != record["checks_sha256"]:
        raise ValueError("check detail differs from run evidence")
    if project_data != sealed_project or hashlib.sha256(project_data).hexdigest() != record["project_sha256"]:
        raise ValueError("project result differs from run evidence")
    _check_summary(config, result_dir)
    exact_coverage(config, report)
    _project_result(config, project_data)
    return record


def assess_record(config, run):
    try:
        _assess(config, run)
        return True, None
    except (OSError, ValueError, TypeError, KeyError, UnicodeError, ET.ParseError, json.JSONDecodeError) as exc:
        return False, str(exc)


def verify_current(config, run):
    root = Path(config["owner_root"])
    current = load_object(root / "results/current.json", {"run", "eligible", "record_sha256", "reason"})
    if current["run"] != run or current["eligible"] is not True or current["reason"] is not None:
        raise ValueError("requested run is not currently eligible")
    record_path = root / "results/runs" / run / "record.json"
    if hashlib.sha256(configuration.regular_bytes(record_path)).hexdigest() != current["record_sha256"]:
        raise ValueError("current decision does not bind the run record")
    eligible, reason = assess_record(config, run)
    if not eligible:
        raise ValueError(reason)
    return _assess(config, run)
