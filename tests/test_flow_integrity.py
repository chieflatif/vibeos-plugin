import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "plugins/vibeos/scripts/validate-flow-integrity.py"
CHECKLIST = REPO_ROOT / "plugins/vibeos/reference/comp/flow-integrity-checklist.json"

PASSING_MISSION = """# Mission: Secure Client Portal

## Mission Promise

Give enterprise users a secure workflow for reviewing data and completing the objective with evidence.

## Core Workflow

1. The user signs in through auth and opens the dashboard.
2. The user submits the workflow form, the frontend calls the backend API, data is persisted, and an error state appears if validation fails.

## Acceptance Criteria

- The backend stores data only after auth succeeds.
- The UI shows success, validation error, and evidence links for the completed workflow.
"""


class FlowIntegrityTests(unittest.TestCase):
    def test_flow_checklist_is_valid(self):
        data = json.loads(CHECKLIST.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], "1.0")
        self.assertIn("testing", data["lifecycle_integration"])
        self.assertIn("auditing", data["lifecycle_integration"])
        ids = {dimension["id"] for dimension in data["dimensions"]}
        self.assertIn("flow.primary_user_outcome", ids)
        self.assertIn("flow.frontend_backend_handoff", ids)
        self.assertIn("flow.auth_session_continuity", ids)
        self.assertIn("flow.objective_fidelity", ids)

    def test_validator_fails_when_mission_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", tmp, "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["findings"][0]["id"], "FLOW-MISSION-MISSING")

    def test_validator_fails_when_required_sections_are_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text("# Mission: Thin Demo\n\nNo flow detail.\n", encoding="utf-8")
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "fail")
        self.assertIn("FLOW-MISSION-SECTION", {finding["id"] for finding in payload["findings"]})

    def test_validator_passes_with_explicit_flow_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(PASSING_MISSION, encoding="utf-8")
            (root / "SCORECARD.md").write_text("# Scorecard\n\n## Flow Integrity\n\nPass.\n", encoding="utf-8")
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["findings"], [])

    def test_validator_warns_without_blocking_for_advisory_flow_terms(self):
        mission = """# Mission: Minimal Tool

## Mission Promise

Let a user complete a workflow with evidence.

## Core Workflow

1. The user starts.
2. The user finishes.

## Acceptance Criteria

- The workflow is visible.
"""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(mission, encoding="utf-8")
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "warn")
        self.assertEqual(payload["findings"][0]["id"], "FLOW-HANDOFF-CONTEXT")


if __name__ == "__main__":
    unittest.main()
