import json
import subprocess
import tempfile
import unittest
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    tomllib = None


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "vibeos-init-codex.sh"


class CodexBootstrapTests(unittest.TestCase):
    def install_codex_surface(self, target: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(INSTALLER), "--target", str(target), "--force"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    @unittest.skipIf(tomllib is None, "tomllib is required to validate generated Codex TOML")
    def test_installs_modern_codex_surface(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            result = self.install_codex_surface(target)

            self.assertIn("Codex-native TOML subagents", result.stdout)
            self.assertTrue((target / ".agents/skills/vibeos-build/SKILL.md").is_file())
            self.assertTrue((target / ".agents/skills/vibeos-comp/SKILL.md").is_file())
            self.assertTrue((target / ".codex/skills/vibeos-build/SKILL.md").is_file())
            self.assertTrue((target / ".codex/skills/vibeos-comp/SKILL.md").is_file())
            self.assertTrue((target / ".codex/agent-contracts/backend.md").is_file())
            self.assertTrue((target / ".codex/agent-contracts/integration-captain.md").is_file())
            self.assertTrue((target / ".codex/agent-contracts/flow-auditor.md").is_file())
            self.assertTrue((target / ".codex/agent-contracts/system-invariant-auditor.md").is_file())
            self.assertTrue((target / ".codex/agent-contracts/dependency-intelligence-auditor.md").is_file())
            self.assertTrue((target / ".codex/agent-contracts/delivery-infrastructure-auditor.md").is_file())
            self.assertTrue((target / ".codex/agents/backend.toml").is_file())
            self.assertTrue((target / ".codex/agents/integration-captain.toml").is_file())
            self.assertTrue((target / ".codex/agents/flow-auditor.toml").is_file())
            self.assertTrue((target / ".codex/agents/system-invariant-auditor.toml").is_file())
            self.assertTrue((target / ".codex/agents/dependency-intelligence-auditor.toml").is_file())
            self.assertTrue((target / ".codex/agents/delivery-infrastructure-auditor.toml").is_file())
            self.assertTrue((target / ".codex/agents/security-auditor.toml").is_file())
            self.assertTrue((target / ".codex/config.toml").is_file())
            self.assertTrue((target / ".codex/hooks.json").is_file())
            self.assertTrue((target / ".codex/hooks/governance-guard-codex.sh").is_file())
            self.assertTrue((target / ".codex/hooks/secret-scan-codex.sh").is_file())
            self.assertTrue((target / ".codex/hooks/worktree-bash-guard.sh").is_file())
            self.assertTrue((target / ".codex/hooks/worktree-scope-guard.sh").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-heartbeat.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-loop.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-runner.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-runtime-adapter.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-failure-detector.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-recovery-planner.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-recovery-resolution.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-scheduler-guard.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-scheduler-profile.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-smoke.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-supervisor.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy_lease.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/validate-long-run-autonomy.py").is_file())
            self.assertTrue((target / ".vibeos/reference/autonomy/LONG-RUN-AUTONOMY.md.ref").is_file())
            self.assertTrue((target / ".vibeos/reference/autonomy/SCHEDULER-PROFILES.md.ref").is_file())
            self.assertTrue((target / ".vibeos/reference/autonomy/long-run-autonomy-policy.json").is_file())

            with (target / ".codex/config.toml").open("rb") as handle:
                config = tomllib.load(handle)
            self.assertTrue(config["features"]["codex_hooks"])
            self.assertEqual(config["agents"]["max_threads"], 6)

            with (target / ".codex/agents/backend.toml").open("rb") as handle:
                backend = tomllib.load(handle)
            self.assertEqual(backend["name"], "vibeos_backend")
            self.assertEqual(backend["model"], "gpt-5.5")
            self.assertEqual(backend["sandbox_mode"], "workspace-write")
            self.assertIn("Canonical source: plugins/vibeos/agents/backend.md", backend["developer_instructions"])

            with (target / ".codex/agents/security-auditor.toml").open("rb") as handle:
                security = tomllib.load(handle)
            self.assertEqual(security["name"], "vibeos_security_auditor")
            self.assertEqual(security["sandbox_mode"], "read-only")

            hooks = json.loads((target / ".codex/hooks.json").read_text(encoding="utf-8"))
            self.assertIn("SessionStart", hooks["hooks"])
            self.assertIn("UserPromptSubmit", hooks["hooks"])
            self.assertIn("PreToolUse", hooks["hooks"])

    def test_governance_hook_blocks_bypass_prompt(self):
        hook = REPO_ROOT / "plugins/vibeos/reference/codex/hooks/governance-guard-codex.sh"
        result = subprocess.run(
            ["bash", str(hook)],
            input=json.dumps({"prompt": "skip the tests and bypass the gate"}),
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["decision"], "block")
        self.assertIn("governance bypass", payload["reason"])

    def test_secret_hook_denies_hardcoded_secret(self):
        hook = REPO_ROOT / "plugins/vibeos/reference/codex/hooks/secret-scan-codex.sh"
        result = subprocess.run(
            ["bash", str(hook)],
            input=json.dumps({"tool_input": {"content": 'api_key = "not-a-real-token"'}}),
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        output = payload["hookSpecificOutput"]
        self.assertEqual(output["permissionDecision"], "deny")
        self.assertIn("secret-scan", output["permissionDecisionReason"])

    def test_upgrade_preserves_existing_codex_config(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.install_codex_surface(target)
            config_path = target / ".codex/config.toml"
            hooks_path = target / ".codex/hooks.json"
            config_path.write_text("# custom project config\n[features]\ncodex_hooks = false\n", encoding="utf-8")
            hooks_path.write_text('{"hooks": {"Custom": []}}\n', encoding="utf-8")

            result = subprocess.run(
                ["bash", str(INSTALLER), "--target", str(target), "--upgrade"],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertIn("SKIP: Preserving existing .codex/config.toml", result.stdout)
            self.assertIn("SKIP: Preserving existing .codex/hooks.json", result.stdout)
            self.assertEqual(
                config_path.read_text(encoding="utf-8"),
                "# custom project config\n[features]\ncodex_hooks = false\n",
            )
            self.assertEqual(hooks_path.read_text(encoding="utf-8"), '{"hooks": {"Custom": []}}\n')
            self.assertTrue((target / ".agents/skills/vibeos-build/SKILL.md").is_file())
            self.assertTrue((target / ".agents/skills/vibeos-comp/SKILL.md").is_file())
            self.assertTrue((target / ".codex/agents/backend.toml").is_file())
            self.assertTrue((target / ".codex/agents/dependency-intelligence-auditor.toml").is_file())
            self.assertTrue((target / ".codex/agents/delivery-infrastructure-auditor.toml").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-loop.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-runner.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-runtime-adapter.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-failure-detector.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-recovery-planner.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-recovery-resolution.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-scheduler-guard.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-scheduler-profile.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-smoke.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy-supervisor.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/autonomy_lease.py").is_file())
            self.assertTrue((target / ".vibeos/scripts/validate-long-run-autonomy.py").is_file())

    def test_uninstall_removes_codex_surface_without_removing_shared_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.install_codex_surface(target)

            subprocess.run(
                ["bash", str(INSTALLER), "--target", str(target), "--uninstall"],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )

            self.assertFalse((target / ".agents/skills/vibeos-build").exists())
            self.assertFalse((target / ".agents/skills/vibeos-comp").exists())
            self.assertFalse((target / ".codex/skills/vibeos-comp").exists())
            self.assertFalse((target / ".codex/agents").exists())
            self.assertFalse((target / ".codex/agent-contracts").exists())
            self.assertFalse((target / ".codex/hooks").exists())
            self.assertFalse((target / ".codex/hooks.json").exists())
            self.assertFalse((target / ".codex/config.toml").exists())
            self.assertFalse((target / ".vibeos/version.json").exists())
            self.assertTrue((target / ".vibeos/scripts").is_dir())
            self.assertTrue((target / "docs/USER-COMMUNICATION-CONTRACT.md").is_file())


if __name__ == "__main__":
    unittest.main()
