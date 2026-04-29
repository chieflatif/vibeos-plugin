import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RED_TEAM = REPO_ROOT / "plugins/vibeos/scripts/comp-red-team.py"

MISSION = """# Mission: Secure Client Portal

## Mission Promise

Give enterprise customers a secure client portal.
"""

PASSING_SCORECARD = """# VibOS Comp Scorecard

## Status

`pass`

## Dimension Results

| Dimension | Status | Evidence | Risks |
|---|---|---|---|
| Flow Integrity | pass | primary flow evidence present |  |
| System Invariants | pass | invariant evidence present |  |
| Dependency Intelligence | pass | dependency evidence present |  |
| Delivery Infrastructure | pass | delivery evidence present |  |
"""


class CompRedTeamTests(unittest.TestCase):
    def test_red_team_blocks_missing_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["python3", str(RED_TEAM), "--project-dir", tmp, "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "blocked")
        self.assertTrue(any(item["severity"] == "critical" for item in payload["findings"]))

    def test_red_team_blocks_high_risk_mission_terms(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(MISSION + "\nPayments and tenant admin workflows are in scope.\n", encoding="utf-8")
            (root / "SCORECARD.md").write_text(PASSING_SCORECARD, encoding="utf-8")
            result = subprocess.run(
                ["python3", str(RED_TEAM), "--project-dir", tmp, "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "blocked")
        self.assertTrue(any(item["category"] == "mission threat model" for item in payload["findings"]))

    def test_red_team_reviews_clean_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(MISSION, encoding="utf-8")
            (root / "SCORECARD.md").write_text(PASSING_SCORECARD, encoding="utf-8")
            result = subprocess.run(
                ["python3", str(RED_TEAM), "--project-dir", tmp, "--json"],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "reviewed")
            self.assertTrue((root / "docs/evidence/RED-TEAM-REPORT.md").is_file())


if __name__ == "__main__":
    unittest.main()
