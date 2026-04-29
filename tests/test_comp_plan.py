import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLANNER = REPO_ROOT / "plugins/vibeos/scripts/comp-plan.py"

MISSION = """# Mission: Secure Client Portal

## Mission Promise

Give enterprise customers a secure client portal with audit-ready operations.
"""


class CompPlanTests(unittest.TestCase):
    def test_planner_generates_parallel_plan_for_greenfield_mission(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(MISSION, encoding="utf-8")
            result = subprocess.run(
                ["python3", str(PLANNER), "--project-dir", tmp, "--json"],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "parallel")
            self.assertTrue((root / "COMP-PLAN.md").is_file())
            plan = (root / "COMP-PLAN.md").read_text(encoding="utf-8")
            self.assertIn("## Primary Flow Checkpoints", plan)
            self.assertIn("auth/session", plan.lower())
            self.assertIn("## Dependency Intelligence Checkpoints", plan)
            self.assertIn("Stack currency packs", plan)
            self.assertIn("## Delivery Infrastructure Checkpoints", plan)
            self.assertIn("CI/CD pipeline", plan)
            scopes = json.loads((root / ".vibeos/worktree-scopes.json").read_text(encoding="utf-8"))
            self.assertGreaterEqual(len(scopes["branches"]), 3)
            self.assertIn("COMP-PLAN.md", scopes["shared_paths"])
            for branch, scope in scopes["branches"].items():
                self.assertTrue(branch.startswith("feat/"))
                self.assertRegex(scope["wo_ids"][0], r"^WO-[0-9]+")
                self.assertTrue(scope["exclusive_paths"])
                self.assertTrue(scope["description"])

    def test_planner_downgrades_ambiguous_existing_source_to_sequential(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(MISSION, encoding="utf-8")
            (root / "src").mkdir()
            (root / "src/main.py").write_text("print('hello')\n", encoding="utf-8")

            result = subprocess.run(
                ["python3", str(PLANNER), "--project-dir", tmp, "--json"],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["mode"], "sequential")
            scopes = json.loads((root / ".vibeos/worktree-scopes.json").read_text(encoding="utf-8"))
            self.assertEqual(scopes["branches"], {})
            self.assertIn("safe ownership was unclear", (root / "COMP-PLAN.md").read_text(encoding="utf-8"))

    def test_planner_fails_without_mission(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["python3", str(PLANNER), "--project-dir", tmp],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("MISSION.md is required", result.stderr)


if __name__ == "__main__":
    unittest.main()
