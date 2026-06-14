import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS_JSON = REPO_ROOT / "plugins/vibeos/hooks/hooks.json"
HOOK_MANIFEST = REPO_ROOT / "plugins/vibeos/hook-manifest.json"
LANE_LOOP_STOP = REPO_ROOT / "plugins/vibeos/hooks/scripts/lane-loop-stop.sh"


class LaneLoopStopTests(unittest.TestCase):
    def run_hook(self, payload: dict, project_dir: Path):
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project_dir)}
        return subprocess.run(
            ["bash", str(LANE_LOOP_STOP)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
        )

    def write_active_wo(self, root: Path, body: str = "Assistant claims the goal is complete.") -> None:
        (root / ".vibeos").mkdir(parents=True, exist_ok=True)
        planning = root / "docs/planning"
        planning.mkdir(parents=True, exist_ok=True)
        (planning / "WO-998-loop-fixture.md").write_text(
            f"""---
wo: WO-998
title: Loop Fixture
status: In Progress
phase: 99
phase_name: Fixture
wo_class: harness
write_scope:
  - docs/planning/WO-998-loop-fixture.md
no_touch: []
required_auditors:
  - evidence-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
loop_goal: pre_commit gate passed
loop_ceiling_turns: 2
---

# WO-998: Loop Fixture

{body}
""",
            encoding="utf-8",
        )
        (root / ".vibeos/session-state.json").write_text(
            json.dumps({"active": True, "active_wo": "docs/planning/WO-998-loop-fixture.md"}),
            encoding="utf-8",
        )

    def test_hooks_json_and_manifest_register_lane_loop_stop(self):
        hooks = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"]
        stop_commands = [
            hook["command"].split("/")[-1]
            for entry in hooks["Stop"]
            for hook in entry.get("hooks", [])
            if hook.get("type") == "command"
        ]
        self.assertIn("lane-loop-stop.sh", stop_commands)

        manifest = json.loads(HOOK_MANIFEST.read_text(encoding="utf-8"))
        documented = {
            (hook.get("event_type"), hook.get("script", "").split("/")[-1])
            for hook in manifest.get("hooks", [])
        }
        self.assertIn(("Stop", "lane-loop-stop.sh"), documented)

    def test_noops_without_active_loop_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".vibeos").mkdir()
            (root / ".vibeos/session-state.json").write_text(json.dumps({"active": True}), encoding="utf-8")

            result = self.run_hook({"hook_event_name": "Stop"}, root)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def test_blocks_before_ceiling_and_ignores_assistant_claim_without_gate_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_active_wo(root)

            result = self.run_hook({"hook_event_name": "Stop"}, root)

            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")
            session = json.loads((root / ".vibeos/session-state.json").read_text(encoding="utf-8"))
            self.assertEqual(session["lane_loop"]["turn_count"], 1)
            self.assertEqual(session["lane_loop"]["status"], "RUNNING")
            self.assertFalse(session["lane_loop"]["goal_verified"])

    def test_records_stalled_at_ceiling_on_second_unverified_turn(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_active_wo(root)

            first = self.run_hook({"hook_event_name": "Stop"}, root)
            second = self.run_hook({"hook_event_name": "Stop"}, root)

            self.assertEqual(first.returncode, 2)
            self.assertEqual(second.returncode, 0, second.stderr)
            payload = json.loads(second.stdout)
            self.assertEqual(payload["decision"], "allow")
            self.assertEqual(payload["lane_loop"]["status"], "STALLED_AT_CEILING")
            session = json.loads((root / ".vibeos/session-state.json").read_text(encoding="utf-8"))
            self.assertEqual(session["lane_loop"]["turn_count"], 2)
            self.assertEqual(session["loop_status"], "STALLED_AT_CEILING")
            self.assertEqual(session["current_wo_status"], "STALLED_AT_CEILING")

    def test_allows_when_gate_evidence_verifies_goal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_active_wo(root)
            event_dir = root / ".vibeos/hook-events"
            event_dir.mkdir(parents=True, exist_ok=True)
            (event_dir / "gate-results.jsonl").write_text(
                json.dumps(
                    {
                        "event": "PostToolUse",
                        "command": "bash plugins/vibeos/scripts/gate-runner.sh pre_commit",
                        "status": "pass",
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = self.run_hook({"hook_event_name": "Stop"}, root)

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["lane_loop"]["status"], "GOAL_VERIFIED")
            self.assertTrue(payload["lane_loop"]["goal_verified"])
            session = json.loads((root / ".vibeos/session-state.json").read_text(encoding="utf-8"))
            self.assertEqual(session["lane_loop"]["turn_count"], 1)
            self.assertEqual(session["loop_status"], "GOAL_VERIFIED")


if __name__ == "__main__":
    unittest.main()
