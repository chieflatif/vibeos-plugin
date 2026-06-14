import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NIGHT_LOOP = REPO_ROOT / "plugins/vibeos/scripts/night-loop.sh"
FRAMEWORK = REPO_ROOT / "plugins/vibeos"


class NightLoopTests(unittest.TestCase):
    def run_night_loop(self, root: Path, *extra: str):
        return subprocess.run(
            [
                "bash",
                str(NIGHT_LOOP),
                "--project-dir",
                str(root),
                "--framework-dir",
                str(FRAMEWORK),
                *extra,
            ],
            capture_output=True,
            text=True,
        )

    def test_dry_run_writes_report_and_cost_fixture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "evidence"
            headless = root / "headless.json"
            headless.write_text(json.dumps({"session_id": "fixture", "total_cost_usd": 0.02}), encoding="utf-8")

            result = self.run_night_loop(root, "--evidence-dir", str(evidence), "--headless-json", str(headless), "--json")

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["summary"]["status"], "dry_run")
            self.assertFalse(payload["summary"]["live_headless_run"])
            self.assertTrue((evidence / "night-loop-report.json").is_file())
            cost = json.loads((evidence / "cost-report.json").read_text(encoding="utf-8"))
            self.assertEqual(cost["cost"]["label"], "estimate; reconcile against billing")
            self.assertEqual(cost["cost"]["total_cost_usd"], 0.02)

    def test_scheduler_guard_blocks_night_loop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = root / ".vibeos/autonomy/recovery-plan.json"
            plan.parent.mkdir(parents=True, exist_ok=True)
            plan.write_text(
                json.dumps(
                    {
                        "generated_at": "2026-06-14T00:00:00Z",
                        "actions": [{"id": "A1", "requires_review": True}],
                        "summary": {"status": "recovery_required"},
                    }
                ),
                encoding="utf-8",
            )

            result = self.run_night_loop(root, "--json")

            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["summary"]["status"], "scheduler_guard_blocked")
            self.assertEqual(payload["steps"][0]["name"], "scheduler_guard")
            self.assertEqual(payload["steps"][0]["status"], "blocked")

    def test_execute_requires_agent_sdk_credit_decision(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = self.run_night_loop(root, "--execute", "--json")

            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["summary"]["status"], "blocked_agent_sdk_credit_required")
            self.assertFalse(payload["summary"]["live_headless_run"])
            self.assertIn("D-3", payload["steps"][1]["reason"])


if __name__ == "__main__":
    unittest.main()
