import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS_JSON = REPO_ROOT / "plugins/vibeos/hooks/hooks.json"
TEAM_GOVERNANCE = REPO_ROOT / "plugins/vibeos/hooks/scripts/team-governance.sh"
WORKTREE_SETUP = REPO_ROOT / "plugins/vibeos/hooks/scripts/worktree-scope-setup.sh"


class TeamGovernanceHookTests(unittest.TestCase):
    def run_hook(self, script: Path, payload: dict, project_dir: Path):
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project_dir), "VIBEOS_FORCE_HOOKS": "1"}
        return subprocess.run(
            ["bash", str(script)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
        )

    def test_hooks_json_registers_team_and_worktree_events(self):
        config = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
        hooks = config["hooks"]

        self.assertIn("WorktreeCreate", hooks)
        self.assertIn("TaskCreated", hooks)
        self.assertIn("TaskCompleted", hooks)
        self.assertIn("TeammateIdle", hooks)
        self.assertIn("worktree-scope-setup.sh", hooks["WorktreeCreate"][0]["hooks"][0]["command"])
        self.assertIn("team-governance.sh", hooks["TaskCreated"][0]["hooks"][0]["command"])
        self.assertIn("team-governance.sh", hooks["TaskCompleted"][0]["hooks"][0]["command"])
        self.assertIn("team-governance.sh", hooks["TeammateIdle"][0]["hooks"][0]["command"])

    def test_team_governance_allows_when_feature_flag_is_absent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_hook(
                TEAM_GOVERNANCE,
                {
                    "hook_event_name": "TaskCreated",
                    "task_subject": "Implement auth",
                    "team_name": "vnext",
                },
                root,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "allow")
            self.assertFalse(payload["enabled"])
            self.assertFalse((root / ".vibeos/team-governance/events.jsonl").exists())

    def test_team_governance_records_enabled_scoped_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".vibeos").mkdir()
            (root / ".vibeos/config.json").write_text(
                json.dumps({"features": {"agent_team_governance": True}}),
                encoding="utf-8",
            )
            result = self.run_hook(
                TEAM_GOVERNANCE,
                {
                    "hook_event_name": "TaskCreated",
                    "task_subject": "WO-117 implement team governance fixture",
                    "task_description": "Scope: tests only. Evidence: synthetic hook run.",
                    "team_name": "vnext",
                    "teammate_name": "tester",
                },
                root,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["enabled"])
            log = root / ".vibeos/team-governance/events.jsonl"
            self.assertTrue(log.is_file())
            entry = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(entry["event"], "TaskCreated")
            self.assertEqual(entry["team"], "vnext")

    def test_team_governance_blocks_enabled_task_without_wo_reference(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".vibeos").mkdir()
            (root / ".vibeos/config.json").write_text(
                json.dumps({"features": {"agent_team_governance": True}}),
                encoding="utf-8",
            )
            result = self.run_hook(
                TEAM_GOVERNANCE,
                {
                    "hook_event_name": "TaskCompleted",
                    "task_subject": "Finish auth cleanup",
                    "task_description": "No work order reference.",
                    "team_name": "vnext",
                },
                root,
            )

            self.assertEqual(result.returncode, 2)
            self.assertIn("governing WO", result.stderr)


class WorktreeScopeSetupTests(unittest.TestCase):
    def run_git(self, root: Path, *args: str):
        return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True)

    def run_hook(self, payload: dict, project_dir: Path):
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project_dir), "VIBEOS_FORCE_HOOKS": "1"}
        return subprocess.run(
            ["bash", str(WORKTREE_SETUP)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
        )

    def test_worktree_setup_creates_git_worktree_and_copies_scope_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.run_git(root, "init")
            (root / "README.md").write_text("# fixture\n", encoding="utf-8")
            (root / ".gitignore").write_text(".env.local\n", encoding="utf-8")
            self.run_git(root, "add", "README.md", ".gitignore")
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=VibeOS Test",
                    "-c",
                    "user.email=vibeos-test@example.com",
                    "commit",
                    "-m",
                    "init",
                ],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            )
            (root / ".vibeos").mkdir()
            (root / ".vibeos/worktree-scopes.json").write_text(
                json.dumps({"branches": {}, "shared_paths": []}) + "\n",
                encoding="utf-8",
            )
            (root / ".worktreeinclude").write_text(".env.local\n", encoding="utf-8")
            (root / ".env.local").write_text("LOCAL_ONLY=1\n", encoding="utf-8")

            result = self.run_hook({"hook_event_name": "WorktreeCreate", "name": "wo-117", "cwd": str(root)}, root)

            self.assertEqual(result.returncode, 0, result.stderr)
            target = Path(result.stdout.strip())
            self.assertTrue(target.is_absolute())
            self.assertTrue(target.is_dir())
            self.assertEqual(target.resolve(), (root / ".claude/worktrees/wo-117").resolve())
            self.assertTrue((target / ".vibeos/worktree-scopes.json").is_file())
            self.assertEqual((target / ".env.local").read_text(encoding="utf-8"), "LOCAL_ONLY=1\n")
            self.run_git(root, "worktree", "remove", "--force", str(target))


if __name__ == "__main__":
    unittest.main()
