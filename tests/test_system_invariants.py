import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "plugins/vibeos/scripts/validate-system-invariants.py"
CHECKLIST = REPO_ROOT / "plugins/vibeos/reference/comp/system-invariant-checklist.json"

PASSING_MISSION = """# Mission: Secure Client Portal

## Mission Promise

Give enterprise users a secure workflow with durable state and evidence.

## Core Workflow

1. The user authenticates and creates a record.
2. The backend persists data and returns success or error feedback.

## System Invariants

- Auth and ownership context must always protect user data.
- Record state transitions must never skip validation.
- Errors must preserve recoverable state and produce evidence for debugging.

## Acceptance Criteria

- Negative tests prove invalid state and unauthorized data access are rejected.
- Recovery evidence exists for failed writes.
"""


class SystemInvariantTests(unittest.TestCase):
    def test_invariant_checklist_is_valid(self):
        data = json.loads(CHECKLIST.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], "1.0")
        self.assertIn("implementation", data["lifecycle_integration"])
        ids = {dimension["id"] for dimension in data["dimensions"]}
        self.assertIn("invariants.identity_ownership", ids)
        self.assertIn("invariants.state_transitions", ids)
        self.assertIn("invariants.idempotency_retry", ids)
        self.assertIn("invariants.failure_recovery", ids)

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
        self.assertEqual(payload["findings"][0]["id"], "INV-MISSION-MISSING")

    def test_validator_fails_when_invariant_section_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(
                "# Mission: Thin Demo\n\n## Mission Promise\n\nDemo.\n\n## Core Workflow\n\n1. Start\n2. Finish\n\n## Acceptance Criteria\n\n- Works.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "fail")
        self.assertIn("INV-MISSION-SECTION", {finding["id"] for finding in payload["findings"]})

    def test_validator_passes_with_explicit_invariants(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(PASSING_MISSION, encoding="utf-8")
            (root / "SCORECARD.md").write_text("# Scorecard\n\n## System Invariants\n\nPass.\n", encoding="utf-8")
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["findings"], [])

    def test_validator_warns_without_blocking_for_advisory_terms(self):
        mission = """# Mission: Minimal Tool

## Mission Promise

Let a user complete work.

## Core Workflow

1. Start.
2. Finish.

## System Invariants

- Work must always belong to the right account.
- Invalid changes must never persist.
- Duplicate actions must not duplicate effects.

## Acceptance Criteria

- Invalid changes are rejected.
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
        self.assertEqual(payload["findings"][0]["id"], "INV-CONTEXT-TERMS")


if __name__ == "__main__":
    unittest.main()
