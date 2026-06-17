import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "plugins/vibeos/scripts/gate-runner.sh"
MANIFEST = REPO_ROOT / "plugins/vibeos/quality-gate-manifest.json"
FRAMEWORK = REPO_ROOT / "plugins/vibeos"


def _run(*args, **kwargs):
    return subprocess.run(
        ["bash", str(RUNNER), *args],
        capture_output=True,
        text=True,
        **kwargs,
    )


def _write_manifest(tmpdir, tiers):
    """Write a minimal manifest with the given tiers block and one pre_commit gate."""
    manifest = {
        "version": "test",
        "gates": [
            {
                "script": "scripts/validate-no-secrets.sh",
                "tier": 0,
                "blocking": True,
                "phase": "pre_commit",
                "env": {},
            }
        ],
        "phases": {"pre_commit": "Pre-commit gates"},
        "tiers": tiers,
    }
    path = Path(tmpdir) / "manifest.json"
    path.write_text(json.dumps(manifest))
    return path


class GateRunnerTests(unittest.TestCase):
    def test_dry_run_reads_flat_gate_manifest_entries(self):
        result = _run(
            "comp_gauntlet",
            "--framework-dir", str(FRAMEWORK),
            "--project-dir", str(REPO_ROOT),
            "--manifest", str(MANIFEST),
            "--dry-run",
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("validate-flow-integrity.py", result.stdout)
        self.assertIn("validate-system-invariants.py", result.stdout)
        self.assertIn("validate-dependency-intelligence.py", result.stdout)
        self.assertIn("validate-delivery-infrastructure.py", result.stdout)
        self.assertIn("gate(s) would execute", result.stdout)

    def test_session_gates_include_long_run_autonomy_validation(self):
        result = _run(
            "session_start",
            "--framework-dir", str(FRAMEWORK),
            "--project-dir", str(REPO_ROOT),
            "--manifest", str(MANIFEST),
            "--dry-run",
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("validate-session-start.sh", result.stdout)
        self.assertIn("validate-long-run-autonomy.py", result.stdout)

    def test_session_end_requires_long_run_closeout_validation(self):
        result = _run(
            "session_end",
            "--framework-dir", str(FRAMEWORK),
            "--project-dir", str(REPO_ROOT),
            "--manifest", str(MANIFEST),
            "--dry-run",
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("validate-long-run-autonomy.py", result.stdout)

    def test_optional_workstation_check_phase_is_registered(self):
        result = _run(
            "workstation_check",
            "--framework-dir", str(FRAMEWORK),
            "--project-dir", str(REPO_ROOT),
            "--manifest", str(MANIFEST),
            "--dry-run",
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("workstation-package.sh", result.stdout)


class TierResolutionTests(unittest.TestCase):
    """WO-107: get_tier_info must handle object, legacy-string, and missing tiers."""

    def _print_tier(self, manifest_path, tier):
        result = _run(
            "--print-tier", str(tier),
            "--framework-dir", str(FRAMEWORK),
            "--project-dir", str(REPO_ROOT),
            "--manifest", str(manifest_path),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.strip()

    def test_object_tier_uses_declared_blocking_and_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_manifest(tmp, {
                "0": {"label": "critical", "blocking": True},
                "2": {"label": "advisory", "blocking": False},
            })
            blocking, label = self._print_tier(path, 0).split("|", 1)
            self.assertEqual(blocking, "True")
            self.assertEqual(label, "critical")

            blocking2, label2 = self._print_tier(path, 2).split("|", 1)
            self.assertEqual(blocking2, "False")
            self.assertEqual(label2, "advisory")

    def test_legacy_string_tier_infers_blocking_from_severity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_manifest(tmp, {
                "0": "Always run — security basics",
                "1": "Blocking — code quality",
                "2": "Important — compliance",
                "3": "Advisory — docs",
            })
            # tier <= 1 => blocking True; otherwise False. String doubles as label.
            self.assertEqual(self._print_tier(path, 0).split("|", 1)[0], "True")
            self.assertEqual(self._print_tier(path, 1).split("|", 1)[0], "True")
            self.assertEqual(self._print_tier(path, 2).split("|", 1)[0], "False")
            self.assertEqual(self._print_tier(path, 3).split("|", 1)[0], "False")
            self.assertEqual(
                self._print_tier(path, 0).split("|", 1)[1],
                "Always run — security basics",
            )

    def test_missing_tier_falls_back_to_safe_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_manifest(tmp, {"0": {"label": "critical", "blocking": True}})
            # tier 5 not defined: blocking = (5 <= 1) => False, label = tier-5
            blocking, label = self._print_tier(path, 5).split("|", 1)
            self.assertEqual(blocking, "False")
            self.assertEqual(label, "tier-5")

    def test_null_blocking_falls_back_to_severity_not_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_manifest(tmp, {"0": {"label": "critical", "blocking": None}})
            # blocking: null must NOT silently demote a tier-0 gate to advisory.
            blocking, _ = self._print_tier(path, 0).split("|", 1)
            self.assertEqual(blocking, "True")

    def test_non_integer_tier_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_manifest(tmp, {"0": {"label": "critical", "blocking": True}})
            result = _run(
                "--print-tier", "abc",
                "--framework-dir", str(FRAMEWORK),
                "--project-dir", str(REPO_ROOT),
                "--manifest", str(path),
            )
            self.assertNotEqual(result.returncode, 0)


class PreCommitExecutionTests(unittest.TestCase):
    """WO-107: pre_commit must execute all gates end-to-end (no tier-resolution crash)."""

    @unittest.skipIf(
        os.environ.get("VIBEOS_TESTS_PASS_GATE") == "1",
        "pre_commit execution test is skipped inside validate-tests-pass to avoid recursive gate invocation",
    )
    def test_pre_commit_executes_all_ten_gates(self):
        result = _run(
            "pre_commit",
            "--continue-on-failure",
            "--framework-dir", str(FRAMEWORK),
            "--project-dir", str(REPO_ROOT),
            "--manifest", str(MANIFEST),
        )
        combined = result.stdout + result.stderr
        # The runner must NOT abort on tier resolution.
        self.assertNotIn("'str' object has no attribute 'get'", combined)
        self.assertNotIn("AttributeError", combined)
        # All 10 pre_commit gates must be attempted.
        self.assertIn("Running 10 gate(s)", combined)
        self.assertIn("Total: 10", combined)


if __name__ == "__main__":
    unittest.main()
