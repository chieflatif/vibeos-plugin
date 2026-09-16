import json
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINT = REPO_ROOT / "plugins/vibeos/scripts/controlled-evaluation.py"


def write_executable(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def git(candidate: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=candidate, check=True, capture_output=True, text=True
    )


class ControlledEvaluationCase(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory(prefix="controlled evaluation ")
        self.root = Path(self._temporary.name).resolve()
        self.inputs = self.root / "owner inputs"
        self.inputs.mkdir()
        self.owner = self.root / "protected owner"
        self.candidate = self.root / "candidate project one"
        self.behavior = self.inputs / "behavior.json"
        self.owner_test = self.inputs / "test_owner.py"
        self.adapter = self.inputs / "project_checks.py"
        self.fake_codex = self.inputs / "fake_codex.py"
        self.fake_ruff = self.inputs / "fake_ruff"
        self.spec = self.inputs / "evaluation spec.json"
        self._write_inputs()
        self.make_candidate(self.candidate, "project-one")

    def tearDown(self):
        self._temporary.cleanup()

    def _write_inputs(self):
        self.behavior.write_text(json.dumps({"mode": "pass"}), encoding="utf-8")
        self.owner_test.write_text(
            """from pathlib import Path


def test_candidate_file():
    assert Path.cwd().is_dir()


def test_candidate_identity():
    assert True
""",
            encoding="utf-8",
        )
        self.adapter.write_text(
            """import json
import sys
from pathlib import Path


candidate = Path(sys.argv[1]).resolve()
result_dir = Path(sys.argv[2]).resolve()
assert candidate.is_dir()
result_dir.mkdir(parents=True, exist_ok=True)
(result_dir / "project-evidence").mkdir(exist_ok=True)
(result_dir / "project-evidence" / "identity.txt").write_text(
    (candidate / "PROJECT-ID.txt").read_text(encoding="utf-8"), encoding="utf-8"
)
(result_dir / "project.json").write_text(json.dumps({
    "schema": "vibeos.project-checks.v1",
    "cases": [
        {"id": "project-build", "status": "PASS"},
        {"id": "project-test", "status": "PASS"}
    ],
    "held": ["manual-provider-check"],
    "project_qualified": False,
    "runtime_qualified": False
}, sort_keys=True), encoding="utf-8")
""",
            encoding="utf-8",
        )
        write_executable(
            self.fake_ruff,
            "#!/bin/sh\nexit 0\n",
        )
        write_executable(self.fake_codex, self._fake_codex_source())
        self.write_spec()

    def _fake_codex_source(self) -> str:
        return """#!/usr/bin/env python3
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
import xml.etree.ElementTree as ET


def strings(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if isinstance(key, str):
                yield key
            yield from strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from strings(child)
    elif isinstance(value, str):
        yield value


separator = sys.argv.index("--")
command = sys.argv[separator + 1:]
config = json.loads(Path(command[-2]).read_text(encoding="utf-8"))
paths = [Path(item) for item in strings(config) if item.endswith("behavior.json")]
behavior = json.loads(next(path for path in paths if path.is_file()).read_text(encoding="utf-8"))
mode = behavior.get("mode", "pass")
if mode in {"timeout", "hold"}:
    time.sleep(float(behavior.get("seconds", 30)))
if mode == "sigterm":
    os.kill(os.getpid(), signal.SIGTERM)
completed = subprocess.run(command)
owner = Path(command[-2]).resolve().parents[1]
check_dir = owner / "results" / "checks" / command[-1]
xml_path = check_dir / "owner-report.xml"
project_path = check_dir / "project.json"
checks_path = check_dir / "checks.json"
if mode in {"failed", "skipped", "duplicate", "missing", "empty"} and xml_path.exists():
    tree = ET.parse(xml_path)
    suite = tree.getroot()
    cases = list(suite.iter("testcase"))
    if mode == "failed" and cases:
        ET.SubElement(cases[0], "failure", message="synthetic failure")
    elif mode == "skipped" and cases:
        ET.SubElement(cases[0], "skipped", message="synthetic skip")
    elif mode == "duplicate" and cases:
        suite.append(ET.fromstring(ET.tostring(cases[0], encoding="unicode")))
    elif mode == "missing" and cases:
        parent = next(node for node in suite.iter() if cases[0] in list(node))
        parent.remove(cases[0])
    elif mode == "empty":
        for parent in suite.iter():
            for case in list(parent.findall("testcase")):
                parent.remove(case)
    tree.write(xml_path, encoding="unicode")
if mode == "malformed_xml" and xml_path.exists():
    xml_path.write_text("<testsuite>", encoding="utf-8")
if mode == "malformed_project" and project_path.exists():
    project_path.write_text("{", encoding="utf-8")
if mode == "duplicate_project" and project_path.exists():
    value = json.loads(project_path.read_text(encoding="utf-8"))
    value["cases"].append(dict(value["cases"][0]))
    project_path.write_text(json.dumps(value), encoding="utf-8")
if mode == "missing_project" and project_path.exists():
    value = json.loads(project_path.read_text(encoding="utf-8"))
    value["cases"] = value["cases"][:1]
    project_path.write_text(json.dumps(value), encoding="utf-8")
if mode == "malformed_checks" and checks_path.exists():
    checks_path.write_text("[] trailing", encoding="utf-8")
forced = behavior.get("exit_code")
raise SystemExit(int(forced) if forced is not None else completed.returncode)
"""

    def make_candidate(self, path: Path, identity: str):
        path.mkdir(parents=True)
        (path / "PROJECT-ID.txt").write_text(identity + "\n", encoding="utf-8")
        (path / "artifact.txt").write_text("candidate bytes\n", encoding="utf-8")
        git(path, "init", "-q")
        git(path, "add", ".")
        git(
            path,
            "-c",
            "user.name=Test Owner",
            "-c",
            "user.email=test-owner@example.invalid",
            "commit",
            "-qm",
            "synthetic baseline",
        )

    def write_behavior(self, mode="pass", **extra):
        self.behavior.write_text(
            json.dumps({"mode": mode, **extra}, sort_keys=True), encoding="utf-8"
        )

    def spec_value(self):
        return {
            "schema": "vibeos.controlled-evaluation.spec.v1",
            "owner_tests": [str(self.owner_test.resolve())],
            "project_adapter": str(self.adapter.resolve()),
            "required_owner_tests": [
                "test_candidate_file",
                "test_candidate_identity",
            ],
            "required_project_cases": ["project-build", "project-test"],
            "held_project_checks": ["manual-provider-check"],
            "writable_files": ["artifact.txt"],
            "tools": {
                "python": str(Path(sys.executable).resolve()),
                "ruff": str(self.fake_ruff.resolve()),
                "codex": str(self.fake_codex.resolve()),
            },
            "dependencies": [str(self.behavior.resolve())],
            "timeout_seconds": 2,
            "max_lines": 300,
            "max_complexity": 10,
        }

    def write_spec(self, value=None):
        self.spec.write_text(
            json.dumps(self.spec_value() if value is None else value, sort_keys=True),
            encoding="utf-8",
        )

    def cli(self, *args: str, timeout=15):
        return subprocess.run(
            [sys.executable, str(ENTRYPOINT), *map(str, args)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def prepare(self):
        return self.cli(
            "prepare",
            "--owner",
            self.owner,
            "--candidate",
            self.candidate,
            "--spec",
            self.spec,
        )

    def evaluate(self, run="run-1", timeout=15):
        return self.cli("evaluate", "--owner", self.owner, "--run", run, timeout=timeout)

    def publish(self, run="run-1"):
        return self.cli("publish", "--owner", self.owner, "--run", run)

    def assert_failed(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def assert_ok(self, result):
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def find_one(self, relative_glob: str) -> Path:
        matches = list(self.owner.glob(relative_glob))
        self.assertEqual(matches, matches[:1], f"expected one match: {matches}")
        self.assertTrue(matches, f"no artifact matched {relative_glob}")
        return matches[0]
