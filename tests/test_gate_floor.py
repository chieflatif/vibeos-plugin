"""WO-145: Phase 34 gate-floor remediation regression guards.

These assert the three remediated pre_commit gates pass via the framework's
sanctioned mechanisms (file-size exception markers, detect-stubs exclusions,
tests-pass TEST_CMD), independent of working-tree state.
"""

import json
import subprocess
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PLUGIN = REPO / "plugins/vibeos"
GATE_MANIFEST = PLUGIN / "quality-gate-manifest.json"


class FileSizeGateTests(unittest.TestCase):
    def test_oversized_framework_scripts_have_valid_exception_markers(self):
        # Run the gate as gate-runner invokes it (cwd = plugin dir), where the
        # framework scripts classify as code. All breaches must be marker-exempt.
        result = subprocess.run(
            ["bash", "scripts/validate-file-size.sh"],
            capture_output=True, text=True, cwd=str(PLUGIN),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("0 hard breach", result.stdout)

    def test_marker_resolves_against_repo_root_not_just_cwd(self):
        # The exception marker references WO-145; the gate must find that WO file
        # at the repo root even though it runs from the plugin subdirectory.
        result = subprocess.run(
            ["bash", "scripts/validate-file-size.sh"],
            capture_output=True, text=True, cwd=str(PLUGIN),
        )
        self.assertIn("marker valid", result.stdout)


class DetectStubsGateTests(unittest.TestCase):
    def test_detect_stubs_passes_with_fixture_and_self_scan_excluded(self):
        result = subprocess.run(
            ["python3", "scripts/detect-stubs-placeholders.py"],
            capture_output=True, text=True, cwd=str(PLUGIN),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class TestsPassGateTests(unittest.TestCase):
    def test_pre_commit_tests_pass_gate_has_test_command(self):
        m = json.loads(GATE_MANIFEST.read_text())
        gate = next(
            g for g in m["gates"]
            if "validate-tests-pass.sh" in g["script"] and g["phase"] == "pre_commit"
        )
        self.assertIn("TEST_CMD", gate.get("env", {}))
        self.assertIn("pytest", gate["env"]["TEST_CMD"])


if __name__ == "__main__":
    unittest.main()
