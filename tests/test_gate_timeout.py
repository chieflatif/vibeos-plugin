"""Process-group timeout behavior for VibeOS gate execution."""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HELPER = REPO_ROOT / "plugins/vibeos/scripts/gate_timeout.py"
RUNNER = REPO_ROOT / "plugins/vibeos/scripts/gate-runner.sh"
VIBEOS = REPO_ROOT / "vibeos"
TIMEOUT_MARKER = "__VIBEOS_GATE_TIMEOUT__"


def run_helper(seconds, *command):
    return subprocess.run(
        [sys.executable, str(HELPER), str(seconds), "--", *command],
        capture_output=True,
        text=True,
    )


class GateTimeoutHelperTests(unittest.TestCase):
    def test_normal_completion_preserves_output_and_exit_code(self):
        result = run_helper(
            5,
            sys.executable,
            "-c",
            "import sys; print('normal-output'); sys.exit(0)",
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "normal-output\n")

    def test_nonzero_completion_preserves_output_and_exit_code(self):
        result = run_helper(
            5,
            sys.executable,
            "-c",
            "import sys; print('failure-output'); sys.exit(23)",
        )

        self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "failure-output\n")

    def test_natural_exit_124_is_not_marked_as_a_deadline(self):
        result = run_helper(
            5,
            sys.executable,
            "-c",
            "import sys; print('natural-124'); sys.exit(124)",
        )

        self.assertEqual(result.returncode, 124, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "natural-124\n")
        self.assertNotIn(TIMEOUT_MARKER, result.stderr)

    def test_timeout_terminates_parent_and_child_process_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            child_pid_path = Path(tmp) / "child.pid"
            parent_code = (
                "import pathlib, subprocess, sys, time; "
                "child = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)']); "
                "pathlib.Path(sys.argv[1]).write_text(str(child.pid)); "
                "print('parent-ready', flush=True); time.sleep(60)"
            )
            started = time.monotonic()
            result = run_helper(
                1,
                sys.executable,
                "-c",
                parent_code,
                str(child_pid_path),
            )
            elapsed = time.monotonic() - started

            self.assertEqual(result.returncode, 124, result.stdout + result.stderr)
            self.assertIn("parent-ready", result.stdout)
            self.assertIn(TIMEOUT_MARKER, result.stderr)
            self.assertLess(elapsed, 5, f"timeout took {elapsed:.2f}s")
            child_pid = int(child_pid_path.read_text())
            time.sleep(0.1)
            with self.assertRaises(ProcessLookupError):
                os.kill(child_pid, 0)


class GateRunnerTimeoutTests(unittest.TestCase):
    def test_runner_treats_natural_exit_124_as_gate_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            framework = root / "framework"
            scripts = framework / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "natural-124.sh").write_text(
                "#!/usr/bin/env bash\n"
                "echo '[test] natural exit 124'\n"
                "exit 124\n"
            )
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "version": "test",
                        "tiers": {"0": {"label": "critical", "blocking": True}},
                        "phases": {"pre_commit": {"enabled": True}},
                        "gates": [
                            {
                                "name": "natural-124-gate",
                                "script": "scripts/natural-124.sh",
                                "tier": 0,
                                "phase": "pre_commit",
                            }
                        ],
                    }
                )
            )

            result = subprocess.run(
                [
                    "bash",
                    str(RUNNER),
                    "pre_commit",
                    "--manifest",
                    str(manifest),
                    "--framework-dir",
                    str(framework),
                    "--project-dir",
                    str(root),
                    "--timeout",
                    "5",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("FAIL [BLOCKING]", result.stdout)
            self.assertIn("natural exit 124", result.stdout)
            self.assertNotIn("TIMEOUT", result.stdout)

    def test_runner_marks_timed_out_blocking_gate_as_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            framework = root / "framework"
            scripts = framework / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "slow.sh").write_text(
                "#!/usr/bin/env bash\n"
                "echo '[test] gate started'\n"
                "sleep 60\n"
            )
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "version": "test",
                        "tiers": {"0": {"label": "critical", "blocking": True}},
                        "phases": {"pre_commit": {"enabled": True}},
                        "gates": [
                            {
                                "name": "slow-blocking-gate",
                                "script": "scripts/slow.sh",
                                "tier": 0,
                                "phase": "pre_commit",
                            }
                        ],
                    }
                )
            )

            result = subprocess.run(
                [
                    "bash",
                    str(RUNNER),
                    "pre_commit",
                    "--manifest",
                    str(manifest),
                    "--framework-dir",
                    str(framework),
                    "--project-dir",
                    str(root),
                    "--timeout",
                    "1",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("TIMEOUT (1s)", result.stdout)
            self.assertIn("Result: FAIL", result.stdout)


class ProfileInstallTimeoutPayloadTests(unittest.TestCase):
    def test_profile_install_carries_timeout_helper(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            (target / "README.md").write_text("# Timeout fixture\n")
            subprocess.run(
                [
                    str(VIBEOS),
                    "analyze",
                    "--target",
                    str(target),
                    "--source",
                    str(REPO_ROOT),
                    "--mode",
                    "minimal",
                ],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [str(VIBEOS), "apply", "--plan", str(target / ".vibeos/install-plan.json")],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            installed = target / ".vibeos/scripts/gate_timeout.py"
            self.assertEqual(installed.read_bytes(), HELPER.read_bytes())


if __name__ == "__main__":
    unittest.main()
