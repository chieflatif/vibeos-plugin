import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "plugins/vibeos/scripts/gate-runner.sh"
MANIFEST = REPO_ROOT / "plugins/vibeos/quality-gate-manifest.json"
FRAMEWORK = REPO_ROOT / "plugins/vibeos"


class GateRunnerTests(unittest.TestCase):
    def test_dry_run_reads_flat_gate_manifest_entries(self):
        result = subprocess.run(
            [
                "bash",
                str(RUNNER),
                "comp_gauntlet",
                "--framework-dir",
                str(FRAMEWORK),
                "--project-dir",
                str(REPO_ROOT),
                "--manifest",
                str(MANIFEST),
                "--dry-run",
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("validate-flow-integrity.py", result.stdout)
        self.assertIn("validate-system-invariants.py", result.stdout)
        self.assertIn("validate-dependency-intelligence.py", result.stdout)
        self.assertIn("validate-delivery-infrastructure.py", result.stdout)
        self.assertIn("gate(s) would execute", result.stdout)

    def test_session_gates_include_long_run_autonomy_validation(self):
        result = subprocess.run(
            [
                "bash",
                str(RUNNER),
                "session_start",
                "--framework-dir",
                str(FRAMEWORK),
                "--project-dir",
                str(REPO_ROOT),
                "--manifest",
                str(MANIFEST),
                "--dry-run",
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("validate-session-start.sh", result.stdout)
        self.assertIn("validate-long-run-autonomy.py", result.stdout)

    def test_session_end_requires_long_run_closeout_validation(self):
        result = subprocess.run(
            [
                "bash",
                str(RUNNER),
                "session_end",
                "--framework-dir",
                str(FRAMEWORK),
                "--project-dir",
                str(REPO_ROOT),
                "--manifest",
                str(MANIFEST),
                "--dry-run",
            ],
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("validate-long-run-autonomy.py", result.stdout)


if __name__ == "__main__":
    unittest.main()
