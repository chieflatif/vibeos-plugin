import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS_JSON = REPO_ROOT / "plugins/vibeos/hooks/hooks.json"
GATE_CAPTURE = REPO_ROOT / "plugins/vibeos/hooks/scripts/gate-result-capture.sh"
AGENT_RETURN = REPO_ROOT / "plugins/vibeos/hooks/scripts/validate-agent-return.sh"
STATE_FLUSH = REPO_ROOT / "plugins/vibeos/hooks/scripts/state-flush.sh"
LIMIT_WARNING = REPO_ROOT / "plugins/vibeos/hooks/scripts/limit-warning-capture.sh"


class HookLifecycleTests(unittest.TestCase):
    def run_hook(self, script: Path, payload: dict, project_dir: Path):
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project_dir)}
        return subprocess.run(
            ["bash", str(script)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
        )

    def test_hooks_json_registers_current_lifecycle_events(self):
        config = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
        hooks = config["hooks"]

        self.assertIn("PostToolUse", hooks)
        self.assertIn("SubagentStop", hooks)
        self.assertIn("PreCompact", hooks)
        self.assertIn("SessionEnd", hooks)
        self.assertIn("Notification", hooks)
        self.assertEqual(hooks["PostToolUse"][0]["matcher"], "Bash")
        self.assertIn("gate-result-capture.sh", hooks["PostToolUse"][0]["hooks"][0]["command"])
        self.assertIn("validate-agent-return.sh", hooks["SubagentStop"][0]["hooks"][0]["command"])
        self.assertIn("state-flush.sh", hooks["PreCompact"][0]["hooks"][0]["command"])
        self.assertIn("state-flush.sh", hooks["SessionEnd"][0]["hooks"][0]["command"])
        self.assertIn("limit-warning-capture.sh", hooks["Notification"][0]["hooks"][0]["command"])

    def test_gate_result_capture_records_gate_bash_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_hook(
                GATE_CAPTURE,
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": "bash plugins/vibeos/scripts/gate-runner.sh pre_commit"},
                    "tool_response": {"exit_code": 0},
                },
                root,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["captured"])
            log = root / ".vibeos/hook-events/gate-results.jsonl"
            self.assertTrue(log.is_file())
            entry = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(entry["event"], "PostToolUse")
            self.assertEqual(entry["status"], "pass")

    def test_gate_result_capture_ignores_unrelated_bash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_hook(
                GATE_CAPTURE,
                {"tool_name": "Bash", "tool_input": {"command": "echo hello"}, "tool_response": {"exit_code": 0}},
                root,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["captured"])
            self.assertFalse((root / ".vibeos/hook-events/gate-results.jsonl").exists())

    def test_validate_agent_return_allows_passing_audit_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_hook(
                AGENT_RETURN,
                {
                    "agent_type": "evidence-auditor",
                    "result": {"type": "audit_result", "decision": "PASS", "findings": []},
                },
                Path(tmp),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["decision"], "allow")

    def test_validate_agent_return_blocks_failed_or_high_audit_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_hook(
                AGENT_RETURN,
                {
                    "agent_type": "security-auditor",
                    "result": {
                        "type": "audit_result",
                        "decision": "PASS",
                        "findings": [{"severity": "HIGH", "message": "unsafe path"}],
                    },
                },
                Path(tmp),
            )

            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")
            self.assertIn("high=1", payload["reason"])

    def test_state_flush_records_precompact_and_session_end_events(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            precompact = self.run_hook(STATE_FLUSH, {"hook_event_name": "PreCompact", "trigger": "auto"}, root)
            session_end = self.run_hook(STATE_FLUSH, {"hook_event_name": "SessionEnd", "trigger": "logout"}, root)

            self.assertEqual(precompact.returncode, 0, precompact.stderr)
            self.assertEqual(session_end.returncode, 0, session_end.stderr)
            payload = json.loads(session_end.stdout)
            self.assertEqual(payload["state"], "flushed")
            flush = json.loads((root / ".vibeos/hook-events/session-flush.json").read_text(encoding="utf-8"))
            self.assertEqual(flush["event"], "SessionEnd")
            history = (root / ".vibeos/hook-events/session-flush.jsonl").read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(history), 2)

    def test_limit_warning_capture_schedules_limit_notification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_hook(
                LIMIT_WARNING,
                {
                    "hook_event_name": "Notification",
                    "notification_type": "idle_prompt",
                    "message": "Approaching 5-hour session limit. Resets at 2026-04-29T05:00:00Z.",
                },
                root,
            )
            state_path = root / ".vibeos/autonomy/limit-aware/limit-aware-scheduler.json"
            state_exists = state_path.is_file()

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["captured"])
        self.assertEqual(payload["summary"]["status"], "LIMIT_WARNING_SCHEDULED")
        self.assertTrue(state_exists)

    def test_limit_warning_capture_ignores_non_limit_notification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_hook(
                LIMIT_WARNING,
                {
                    "hook_event_name": "Notification",
                    "notification_type": "permission_prompt",
                    "message": "Claude needs your permission",
                },
                root,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["captured"])


if __name__ == "__main__":
    unittest.main()
