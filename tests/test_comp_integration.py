import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLANNER = REPO_ROOT / "plugins/vibeos/scripts/comp-plan.py"
CHECKER = REPO_ROOT / "plugins/vibeos/scripts/comp-integration-check.py"

MISSION = """# Mission: Secure Client Portal

## Mission Promise

Give enterprise customers a secure client portal with audit-ready operations.
"""


class CompIntegrationTests(unittest.TestCase):
    def create_plan(self, root: Path):
        (root / "MISSION.md").write_text(MISSION, encoding="utf-8")
        subprocess.run(["python3", str(PLANNER), "--project-dir", str(root)], check=True, capture_output=True, text=True)

    def test_integration_check_blocks_missing_package_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_plan(root)
            result = subprocess.run(
                ["python3", str(CHECKER), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "blocked")
            self.assertTrue(payload["missing_evidence"])
            self.assertTrue((root / "docs/evidence/COMP-INTEGRATION-EVIDENCE.md").is_file())

    def test_integration_check_passes_when_package_evidence_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.create_plan(root)
            scopes = json.loads((root / ".vibeos/worktree-scopes.json").read_text(encoding="utf-8"))
            evidence_dir = root / "docs/evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)
            for scope in scopes["branches"].values():
                for wo_id in scope["wo_ids"]:
                    (evidence_dir / f"{wo_id}.md").write_text(f"# Evidence {wo_id}\n\nTests passed.\n", encoding="utf-8")

            result = subprocess.run(
                ["python3", str(CHECKER), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "ready_for_integrated_checks")
            self.assertEqual(payload["missing_evidence"], [])
            evidence = (root / "docs/evidence/COMP-INTEGRATION-EVIDENCE.md").read_text(encoding="utf-8")
            self.assertIn("Flow integrity and objective fidelity", evidence)
            self.assertIn("System invariants and state safety", evidence)
            self.assertIn("Dependency intelligence", evidence)
            self.assertIn("Delivery infrastructure", evidence)

    def test_integration_check_fails_without_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(MISSION, encoding="utf-8")
            result = subprocess.run(
                ["python3", str(CHECKER), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertIn("COMP-PLAN.md", payload["missing_inputs"])


if __name__ == "__main__":
    unittest.main()
