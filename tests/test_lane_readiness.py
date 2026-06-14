import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
WRAPPER = REPO_ROOT / "plugins/vibeos/scripts/check-lane-readiness.sh"
MODULE_PATH = REPO_ROOT / "plugins/vibeos/scripts/lane-readiness.py"
SPEC = importlib.util.spec_from_file_location("lane_readiness", MODULE_PATH)
lane_readiness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lane_readiness)

WO_TEXT = """---
wo: WO-115
title: Lane Readiness Fixture
status: In Progress
phase: 36
phase_name: Lane-Readiness Automation
wo_class: harness
write_scope:
  - docs/planning/WO-115-fixture.md
  - src/allowed.txt
  - src/conflict.txt
no_touch: []
required_auditors:
  - evidence-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# WO-115: Lane Readiness Fixture

## Status

`In Progress`

## Scope

### In Scope
- Update src/allowed.txt
- Update src/conflict.txt
"""


def run(cmd, cwd: Path):
    return subprocess.run(cmd, cwd=str(cwd), check=True, capture_output=True, text=True)


class LaneReadinessTests(unittest.TestCase):
    def make_repo(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        run(["git", "init"], root)
        run(["git", "checkout", "-b", "main"], root)
        run(["git", "config", "user.email", "test@example.com"], root)
        run(["git", "config", "user.name", "Test User"], root)
        (root / "docs/planning").mkdir(parents=True)
        (root / "docs/planning/WO-115-fixture.md").write_text(WO_TEXT, encoding="utf-8")
        (root / "src").mkdir()
        (root / "src/allowed.txt").write_text("base\n", encoding="utf-8")
        run(["git", "add", "."], root)
        run(["git", "commit", "-m", "base"], root)
        return temp, root

    def create_branch_change(self, root: Path, branch: str, path: str, text: str):
        run(["git", "checkout", "-b", branch], root)
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        run(["git", "add", path], root)
        run(["git", "commit", "-m", branch], root)
        run(["git", "checkout", "main"], root)

    def run_check(self, root: Path, branch: str):
        packet = root / f"{branch.replace('/', '-')}-packet.json"
        scratch = root / f"{branch.replace('/', '-')}-scratch"
        result = subprocess.run(
            [
                "bash",
                str(WRAPPER),
                "--project-dir",
                str(root),
                "--framework-dir",
                str(REPO_ROOT / "plugins/vibeos"),
                "--lane-branch",
                branch,
                "--base-ref",
                "main",
                "--wo-file",
                "docs/planning/WO-115-fixture.md",
                "--scratch-dir",
                str(scratch),
                "--gate-command",
                "true",
                "--packet-out",
                str(packet),
            ],
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)
        return result, payload, packet, scratch

    def test_clean_lane_rebases_runs_gate_and_accepts(self):
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        self.create_branch_change(root, "feat/clean", "src/allowed.txt", "lane\n")

        result, payload, packet, scratch = self.run_check(root, "feat/clean")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(payload["lane_status"], "ACCEPT")
        self.assertEqual(payload["gate_results"][0]["phase"], "wo_exit")
        self.assertEqual(payload["gate_results"][0]["status"], "PASS")
        self.assertEqual(payload["defects"], [])
        self.assertTrue(packet.is_file())
        self.assertFalse(scratch.exists())

    def test_scope_violation_defers_with_scope_defect(self):
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        self.create_branch_change(root, "feat/scope", "src/outside.txt", "outside\n")

        result, payload, _packet, scratch = self.run_check(root, "feat/scope")

        self.assertEqual(result.returncode, 1)
        self.assertEqual(payload["lane_status"], "DEFER")
        self.assertEqual(payload["defects"][0]["source"], "write-scope")
        self.assertIn("src/outside.txt", payload["defects"][0]["path"])
        self.assertFalse(scratch.exists())

    def test_rebase_conflict_defers_and_cleans_scratch_worktree(self):
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        self.create_branch_change(root, "feat/conflict", "src/conflict.txt", "lane\n")
        (root / "src/conflict.txt").write_text("main\n", encoding="utf-8")
        run(["git", "add", "src/conflict.txt"], root)
        run(["git", "commit", "-m", "main conflict"], root)

        result, payload, _packet, scratch = self.run_check(root, "feat/conflict")

        self.assertEqual(result.returncode, 1)
        self.assertEqual(payload["lane_status"], "DEFER")
        self.assertEqual(payload["gate_results"][0]["phase"], "rebase")
        self.assertEqual(payload["gate_results"][0]["status"], "FAIL")
        self.assertEqual(payload["defects"][0]["source"], "rebase")
        self.assertFalse(scratch.exists())

    def test_default_gate_command_integrates_gate_runner_wo_exit(self):
        command = lane_readiness.default_gate_command(Path("/repo"), Path("/repo/plugins/vibeos"), "WO-115")

        self.assertIn("gate-runner.sh wo_exit", command)
        self.assertIn("--wo WO-115", command)
        self.assertIn("--continue-on-failure", command)


if __name__ == "__main__":
    unittest.main()
