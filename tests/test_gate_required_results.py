"""Release contract tests for non-vacuous quality-gate results.

These cases describe the manifest-level result contract.  They intentionally do
not depend on the repository's populated production manifest.
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "plugins/vibeos/scripts/gate-runner.sh"


def run_runner(phase, manifest, framework, project, *options, cwd=None, env=None):
    return subprocess.run(
        [
            "bash",
            str(RUNNER),
            phase,
            "--manifest",
            str(manifest),
            "--framework-dir",
            str(framework),
            "--project-dir",
            str(project),
            *options,
        ],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )


def write_manifest(directory, phase_config, gates=None):
    path = Path(directory) / "manifest.json"
    path.write_text(
        json.dumps(
            {
                "version": "required-results-test",
                "tiers": {
                    "0": {"label": "critical", "blocking": True},
                    "2": {"label": "advisory", "blocking": False},
                },
                "phases": {"pre_commit": phase_config},
                "gates": gates or [],
            }
        )
    )
    return path


class GateRequiredResultsTests(unittest.TestCase):
    def test_project_dir_is_exported_to_gate_from_an_unrelated_working_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "target-project"
            project.mkdir()
            framework = root / "framework"
            scripts = framework / "scripts"
            scripts.mkdir(parents=True)
            unrelated = root / "unrelated"
            unrelated.mkdir()
            captured_root = root / "captured-project-root.txt"
            (scripts / "assert-project-root.sh").write_text(
                "#!/usr/bin/env bash\n"
                "printf '%s' \"$PROJECT_ROOT\" > \"$CAPTURE_PATH\"\n"
                "test \"$PROJECT_ROOT\" = \"$EXPECTED_ROOT\"\n"
                "echo '[test] PASS: received target project root'\n"
            )
            manifest = write_manifest(
                root,
                {"enabled": True},
                [
                    {
                        "name": "project-root-propagation",
                        "script": "scripts/assert-project-root.sh",
                        "tier": 0,
                        "phase": "pre_commit",
                        "env": {
                            "EXPECTED_ROOT": str(project.resolve()),
                            "CAPTURE_PATH": str(captured_root),
                        },
                    }
                ],
            )

            clean_env = os.environ.copy()
            clean_env.pop("PROJECT_ROOT", None)
            clean_env.pop("CLAUDE_PROJECT_DIR", None)
            result = run_runner(
                "pre_commit", manifest, framework, project, cwd=unrelated, env=clean_env
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(Path(captured_root.read_text()).resolve(), project.resolve())

    def test_gate_specific_project_root_is_not_overridden(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "target-project"
            project.mkdir()
            framework = root / "framework"
            scripts = framework / "scripts"
            scripts.mkdir(parents=True)
            override = root / "gate-specific-project"
            override.mkdir()
            captured_root = root / "captured-project-root.txt"
            (scripts / "assert-project-root.sh").write_text(
                "#!/usr/bin/env bash\n"
                "printf '%s' \"$PROJECT_ROOT\" > \"$CAPTURE_PATH\"\n"
                "test \"$PROJECT_ROOT\" = \"$EXPECTED_ROOT\"\n"
                "echo '[test] PASS: retained gate-specific project root'\n"
            )
            manifest = write_manifest(
                root,
                {"enabled": True},
                [
                    {
                        "name": "project-root-override",
                        "script": "scripts/assert-project-root.sh",
                        "tier": 0,
                        "phase": "pre_commit",
                        "env": {
                            "EXPECTED_ROOT": str(override.resolve()),
                            "PROJECT_ROOT": str(override.resolve()),
                            "CAPTURE_PATH": str(captured_root),
                        },
                    }
                ],
            )

            result = run_runner("pre_commit", manifest, framework, project)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(Path(captured_root.read_text()).resolve(), override.resolve())

    def test_enabled_empty_phase_fails_instead_of_reporting_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            framework = root / "framework"
            framework.mkdir()
            manifest = write_manifest(root, {"enabled": True})

            result = run_runner("pre_commit", manifest, framework, root)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("FAIL", result.stdout)
            self.assertIn("no gates configured", result.stdout)
            self.assertNotIn("Result: PASS", result.stdout)

    def test_explicitly_disabled_empty_phase_reports_skip_not_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            framework = root / "framework"
            framework.mkdir()
            manifest = write_manifest(root, {"enabled": False})

            result = run_runner("pre_commit", manifest, framework, root)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SKIP", result.stdout)
            self.assertNotIn("PASS", result.stdout)

            json_result = run_runner("pre_commit", manifest, framework, root, "--json")
            self.assertEqual(json_result.returncode, 0, json_result.stdout + json_result.stderr)
            payload = json.loads(json_result.stdout)
            self.assertEqual(payload["summary"]["result"], "SKIP")

    def test_explicitly_disabled_phase_does_not_run_declared_gates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            framework = root / "framework"
            scripts = framework / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "must-not-run.sh").write_text(
                "#!/usr/bin/env bash\n"
                "echo '[test] FAIL: disabled phase executed'\n"
                "exit 1\n"
            )
            manifest = write_manifest(
                root,
                {"enabled": False},
                [
                    {
                        "name": "disabled-check",
                        "script": "scripts/must-not-run.sh",
                        "tier": 0,
                        "phase": "pre_commit",
                    }
                ],
            )

            result = run_runner("pre_commit", manifest, framework, root)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SKIP", result.stdout)
            self.assertNotIn("disabled phase executed", result.stdout)

    def test_skipped_blocking_gate_fails_the_phase(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            framework = root / "framework"
            scripts = framework / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "blocked.sh").write_text(
                "#!/usr/bin/env bash\n"
                "echo '[test] SKIP: prerequisite unavailable'\n"
                "exit 0\n"
            )
            manifest = write_manifest(
                root,
                {"enabled": True},
                [
                    {
                        "name": "blocking-prerequisite",
                        "script": "scripts/blocked.sh",
                        "tier": 0,
                        "phase": "pre_commit",
                    }
                ],
            )

            result = run_runner("pre_commit", manifest, framework, root)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("SKIP [BLOCKING]", result.stdout)
            self.assertIn("Result: FAIL", result.stdout)

            json_result = run_runner("pre_commit", manifest, framework, root, "--json")
            self.assertEqual(json_result.returncode, 1, json_result.stdout + json_result.stderr)
            payload = json.loads(json_result.stdout)
            self.assertEqual(payload["summary"]["skipped"], 1)
            self.assertEqual(payload["summary"]["blocking_failures"], 1)
            self.assertEqual(payload["summary"]["result"], "FAIL")

    def test_gate_level_blocking_override_is_not_silently_demoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            framework = root / "framework"
            scripts = framework / "scripts"
            scripts.mkdir(parents=True)
            (scripts / "blocked.sh").write_text(
                "#!/usr/bin/env bash\n"
                "echo '[test] SKIP: prerequisite unavailable'\n"
                "exit 0\n"
            )
            manifest = write_manifest(
                root,
                {"enabled": True},
                [
                    {
                        "name": "explicitly-blocking-prerequisite",
                        "script": "scripts/blocked.sh",
                        "tier": 2,
                        "blocking": True,
                        "phase": "pre_commit",
                    }
                ],
            )

            result = run_runner("pre_commit", manifest, framework, root)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("SKIP [BLOCKING]", result.stdout)


if __name__ == "__main__":
    unittest.main()
