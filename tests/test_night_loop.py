import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
NIGHT_LOOP = REPO_ROOT / "plugins/vibeos/scripts/night-loop.sh"
FRAMEWORK = REPO_ROOT / "plugins/vibeos"


class NightLoopTests(unittest.TestCase):
    def run_night_loop(self, root: Path, *extra: str, env: dict[str, str] | None = None):
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
            env={**os.environ, **(env or {})},
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
            self.assertEqual(payload["headless_auth_mode"], "subscription")
            self.assertEqual(payload["model"], "sonnet")
            self.assertEqual(payload["max_budget_usd"], "1.00")
            self.assertTrue(payload["safe_mode"])
            claude_step = next(step for step in payload["steps"] if step["name"] == "claude_headless")
            self.assertIn("--safe-mode", claude_step["command"])
            self.assertNotIn("--bare", claude_step["command"])
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

    def test_execute_creates_evidence_dir_before_saving_headless_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "missing-evidence-dir"
            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_claude = fake_bin / "claude"
            fake_claude.write_text(
                "#!/usr/bin/env bash\n"
                "if [[ \"$1\" == \"auth\" && \"$2\" == \"status\" ]]; then\n"
                "  printf '%s\\n' '{\"loggedIn\":true,\"authMethod\":\"claude.ai\",\"apiProvider\":\"firstParty\",\"subscriptionType\":\"max\"}'\n"
                "  exit 0\n"
                "fi\n"
                "printf '%s\\n' '{\"session_id\":\"live-fixture\",\"model\":\"sonnet\",\"total_cost_usd\":0.03}'\n",
                encoding="utf-8",
            )
            fake_claude.chmod(0o755)
            scripts = root / ".vibeos/scripts"
            scripts.mkdir(parents=True)
            fake_loop = scripts / "autonomy-loop.py"
            fake_loop.write_text(
                "import json\nprint(json.dumps({'summary': {'status': 'pass'}}))\n",
                encoding="utf-8",
            )

            result = self.run_night_loop(
                root,
                "--evidence-dir",
                str(evidence),
                "--execute",
                "--json",
                env={
                    "PATH": f"{fake_bin}:{os.environ['PATH']}",
                    "VIBEOS_AGENT_SDK_CREDIT_CONFIRMED": "1",
                },
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["summary"]["status"], "pass")
            self.assertTrue(payload["summary"]["live_headless_run"])
            auth_step = next(step for step in payload["steps"] if step["name"] == "claude_auth_status")
            self.assertEqual(auth_step["status"], "pass")
            self.assertEqual(auth_step["subscription_type"], "max")
            self.assertTrue((evidence / "headless-output.json").is_file())
            cost = json.loads((evidence / "cost-report.json").read_text(encoding="utf-8"))
            self.assertEqual(cost["cost"]["total_cost_usd"], 0.03)

    def test_execute_blocks_when_subscription_auth_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_claude = fake_bin / "claude"
            fake_claude.write_text(
                "#!/usr/bin/env bash\n"
                "if [[ \"$1\" == \"auth\" && \"$2\" == \"status\" ]]; then\n"
                "  printf '%s\\n' '{\"loggedIn\":false}'\n"
                "  exit 0\n"
                "fi\n"
                "printf '%s\\n' '{\"unexpected\":true}'\n",
                encoding="utf-8",
            )
            fake_claude.chmod(0o755)

            result = self.run_night_loop(
                root,
                "--execute",
                "--json",
                env={
                    "PATH": f"{fake_bin}:{os.environ['PATH']}",
                    "VIBEOS_AGENT_SDK_CREDIT_CONFIRMED": "1",
                },
            )

            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["summary"]["status"], "blocked_claude_subscription_auth_required")
            self.assertFalse(payload["summary"]["live_headless_run"])
            self.assertEqual(payload["steps"][-1]["name"], "claude_auth_status")
            self.assertEqual(payload["steps"][-1]["status"], "blocked")

    def test_api_key_bare_mode_requires_api_key_or_settings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_claude = fake_bin / "claude"
            fake_claude.write_text("#!/usr/bin/env bash\nprintf '%s\\n' '{\"unexpected\":true}'\n", encoding="utf-8")
            fake_claude.chmod(0o755)

            env = {
                "PATH": f"{fake_bin}:{os.environ['PATH']}",
                "VIBEOS_AGENT_SDK_CREDIT_CONFIRMED": "1",
                "ANTHROPIC_API_KEY": "",
            }
            result = self.run_night_loop(root, "--execute", "--json", "--headless-auth-mode", "api-key-bare", env=env)

            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["summary"]["status"], "blocked_bare_api_key_required")
            claude_step = next(step for step in payload["steps"] if step["name"] == "claude_headless")
            self.assertIn("--bare", claude_step["command"])

    def test_execute_captures_cost_report_from_failed_headless_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            evidence = root / "failed-headless-evidence"
            fake_bin = root / "bin"
            fake_bin.mkdir()
            fake_claude = fake_bin / "claude"
            fake_claude.write_text(
                "#!/usr/bin/env bash\n"
                "if [[ \"$1\" == \"auth\" && \"$2\" == \"status\" ]]; then\n"
                "  printf '%s\\n' '{\"loggedIn\":true,\"authMethod\":\"claude.ai\",\"apiProvider\":\"firstParty\",\"subscriptionType\":\"max\"}'\n"
                "  exit 0\n"
                "fi\n"
                "printf '%s\\n' '{\"type\":\"result\",\"is_error\":true,\"result\":\"Not logged in\",\"total_cost_usd\":0}'\n"
                "printf '%s\\n' 'login required' >&2\n"
                "exit 1\n",
                encoding="utf-8",
            )
            fake_claude.chmod(0o755)

            result = self.run_night_loop(
                root,
                "--evidence-dir",
                str(evidence),
                "--execute",
                "--json",
                env={
                    "PATH": f"{fake_bin}:{os.environ['PATH']}",
                    "VIBEOS_AGENT_SDK_CREDIT_CONFIRMED": "1",
                },
            )

            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["summary"]["status"], "failed_claude_headless")
            self.assertTrue((evidence / "headless-output.json").is_file())
            self.assertTrue((evidence / "headless-stderr.txt").is_file())
            cost = json.loads((evidence / "cost-report.json").read_text(encoding="utf-8"))
            self.assertEqual(cost["cost"]["total_cost_usd"], 0)
            self.assertEqual(payload["steps"][-1]["name"], "live_cost_capture")
            self.assertEqual(payload["steps"][-1]["status"], "pass")


if __name__ == "__main__":
    unittest.main()
