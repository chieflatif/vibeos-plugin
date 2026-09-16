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
            self.assertEqual(blocking, "true")
            self.assertEqual(label, "critical")

            blocking2, label2 = self._print_tier(path, 2).split("|", 1)
            self.assertEqual(blocking2, "false")
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
            self.assertEqual(self._print_tier(path, 0).split("|", 1)[0], "true")
            self.assertEqual(self._print_tier(path, 1).split("|", 1)[0], "true")
            self.assertEqual(self._print_tier(path, 2).split("|", 1)[0], "false")
            self.assertEqual(self._print_tier(path, 3).split("|", 1)[0], "false")
            self.assertEqual(
                self._print_tier(path, 0).split("|", 1)[1],
                "Always run — security basics",
            )

    def test_missing_tier_falls_back_to_safe_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_manifest(tmp, {"0": {"label": "critical", "blocking": True}})
            # tier 5 not defined: blocking = (5 <= 1) => False, label = tier-5
            blocking, label = self._print_tier(path, 5).split("|", 1)
            self.assertEqual(blocking, "false")
            self.assertEqual(label, "tier-5")

    def test_null_blocking_falls_back_to_severity_not_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_manifest(tmp, {"0": {"label": "critical", "blocking": None}})
            # blocking: null must NOT silently demote a tier-0 gate to advisory.
            blocking, _ = self._print_tier(path, 0).split("|", 1)
            self.assertEqual(blocking, "true")

    def test_nonstandard_blocking_values_normalize_and_fail_closed(self):
        # WO-152: "blocking": 1 / "yes" must not silently demote a blocking tier
        # (the shell comparison accepts only the canonical form).
        with tempfile.TemporaryDirectory() as tmp:
            path = _write_manifest(tmp, {
                "0": {"label": "critical", "blocking": 1},
                "1": {"label": "important", "blocking": "yes"},
                "2": {"label": "advisory", "blocking": "no"},
            })
            self.assertEqual(self._print_tier(path, 0).split("|", 1)[0], "true")
            self.assertEqual(self._print_tier(path, 1).split("|", 1)[0], "true")
            self.assertEqual(self._print_tier(path, 2).split("|", 1)[0], "false")

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


class MissingScriptTests(unittest.TestCase):
    """WO-152: missing scripts for blocking gates must fail closed."""

    TIERS = {
        "0": {"label": "critical", "blocking": True},
        "1": {"label": "important", "blocking": True},
        "2": {"label": "advisory", "blocking": False},
        "3": {"label": "informational", "blocking": False},
    }

    def _manifest(self, tmpdir, gates):
        manifest = {
            "version": "test",
            "gates": gates,
            "phases": {"pre_commit": {"description": "Pre-commit gates"}},
            "tiers": self.TIERS,
        }
        path = Path(tmpdir) / "manifest.json"
        path.write_text(json.dumps(manifest))
        return path

    def _run_phase(self, tmpdir, manifest_path):
        return _run(
            "pre_commit",
            "--framework-dir", str(Path(tmpdir) / "framework"),
            "--project-dir", tmpdir,
            "--manifest", str(manifest_path),
            "--continue-on-failure",
        )

    def test_missing_blocking_gate_script_fails_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "framework/scripts").mkdir(parents=True)
            manifest = self._manifest(
                tmp,
                [{"script": "scripts/does-not-exist.sh", "tier": 0, "phase": "pre_commit", "env": {}}],
            )
            result = self._run_phase(tmp, manifest)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("script not found", result.stdout)
            self.assertIn("FAIL", result.stdout)

    def test_missing_nonblocking_gate_script_still_skips(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "framework/scripts").mkdir(parents=True)
            manifest = self._manifest(
                tmp,
                [{"script": "scripts/does-not-exist.sh", "tier": 2, "phase": "pre_commit", "env": {}}],
            )
            result = self._run_phase(tmp, manifest)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("SKIP", result.stdout)

    def test_marker_skip_fails_blocking_tiers_and_skips_advisory_tiers(self):
        for tier, blocking in ((0, True), (1, True), (2, False), (3, False)):
            with self.subTest(tier=tier), tempfile.TemporaryDirectory() as tmp:
                scripts = Path(tmp) / "framework/scripts"
                scripts.mkdir(parents=True)
                skip_gate = scripts / "skips.sh"
                skip_gate.write_text('#!/usr/bin/env bash\necho "[TEST] SKIP: nothing to do"\nexit 0\n')
                skip_gate.chmod(0o755)
                manifest = self._manifest(
                    tmp,
                    [{"script": "scripts/skips.sh", "tier": tier, "phase": "pre_commit", "env": {}}],
                )
                result = self._run_phase(tmp, manifest)
                self.assertIn("SKIP", result.stdout)
                if blocking:
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertIn("SKIP [BLOCKING]", result.stdout)
                    self.assertIn("Result: FAIL", result.stdout)
                else:
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertNotIn("FAIL", result.stdout)

    def test_marker_skip_with_large_output_fails_blocking_gate(self):
        # WO-152: the SKIP-marker match must not race SIGPIPE on large output
        # (misclassified marker-skips as PASS before the pure-bash match).
        with tempfile.TemporaryDirectory() as tmp:
            scripts = Path(tmp) / "framework/scripts"
            scripts.mkdir(parents=True)
            noisy_skip = scripts / "noisy-skip.sh"
            noisy_skip.write_text(
                "#!/usr/bin/env bash\n"
                'echo "[TEST] SKIP: nothing to do"\n'
                'for i in $(seq 1 4000); do echo "detail $i: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"; done\n'
                "exit 0\n"
            )
            noisy_skip.chmod(0o755)
            manifest = self._manifest(
                tmp,
                [{"script": "scripts/noisy-skip.sh", "tier": 0, "phase": "pre_commit", "env": {}}],
            )
            result = self._run_phase(tmp, manifest)
            self.assertEqual(result.returncode, 1, result.stdout[:2000] + result.stderr[:2000])
            self.assertIn("Skipped: 1", result.stdout)
            self.assertIn("Failed: 1", result.stdout)
            self.assertIn("Passed: 0", result.stdout)
            self.assertIn("Result: FAIL", result.stdout)

    def test_large_gate_output_does_not_abort_run(self):
        # WO-152 finding 5: header extraction must survive gate output larger
        # than the pipe buffer without aborting the phase mid-run.
        with tempfile.TemporaryDirectory() as tmp:
            scripts = Path(tmp) / "framework/scripts"
            scripts.mkdir(parents=True)
            noisy = scripts / "noisy.sh"
            noisy.write_text(
                "#!/usr/bin/env bash\n"
                'for i in $(seq 1 4000); do echo "line $i: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"; done\n'
                "exit 0\n"
            )
            noisy.chmod(0o755)
            quiet = scripts / "quiet.sh"
            quiet.write_text('#!/usr/bin/env bash\necho "[TEST] PASS: ok"\nexit 0\n')
            quiet.chmod(0o755)
            manifest = self._manifest(
                tmp,
                [
                    {"script": "scripts/noisy.sh", "tier": 0, "phase": "pre_commit", "env": {}},
                    {"script": "scripts/quiet.sh", "tier": 0, "phase": "pre_commit", "env": {}},
                ],
            )
            result = self._run_phase(tmp, manifest)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Total: 2 | Passed: 2", result.stdout)

    def test_missing_blocking_script_fails_in_json_mode_and_later_gates_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts = Path(tmp) / "framework/scripts"
            scripts.mkdir(parents=True)
            healthy = scripts / "ok.sh"
            healthy.write_text('#!/usr/bin/env bash\necho "[TEST] PASS: ok"\nexit 0\n')
            healthy.chmod(0o755)
            manifest = self._manifest(
                tmp,
                [
                    {"script": "scripts/does-not-exist.sh", "tier": 0, "phase": "pre_commit", "env": {}},
                    {"script": "scripts/ok.sh", "tier": 0, "phase": "pre_commit", "env": {}},
                ],
            )
            result = _run(
                "pre_commit",
                "--framework-dir", str(Path(tmp) / "framework"),
                "--project-dir", tmp,
                "--manifest", str(manifest),
                "--continue-on-failure",
                "--json",
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            payload = json.loads(result.stdout[result.stdout.index("{"):])
            self.assertEqual(payload["summary"]["blocking_failures"], 1)
            self.assertEqual(payload["summary"]["result"], "FAIL")
            self.assertEqual(payload["summary"]["total"], 2)
            self.assertEqual(payload["summary"]["passed"], 1)

    def test_missing_blocking_script_aborts_without_continue_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            scripts = Path(tmp) / "framework/scripts"
            scripts.mkdir(parents=True)
            healthy = scripts / "ok.sh"
            healthy.write_text('#!/usr/bin/env bash\necho "[TEST] PASS: ok"\nexit 0\n')
            healthy.chmod(0o755)
            manifest = self._manifest(
                tmp,
                [
                    {"script": "scripts/does-not-exist.sh", "tier": 0, "phase": "pre_commit", "env": {}},
                    {"script": "scripts/ok.sh", "tier": 0, "phase": "pre_commit", "env": {}},
                ],
            )
            result = _run(
                "pre_commit",
                "--framework-dir", str(Path(tmp) / "framework"),
                "--project-dir", tmp,
                "--manifest", str(manifest),
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("ABORT", result.stdout)
            self.assertIn("Total: 1", result.stdout)


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
