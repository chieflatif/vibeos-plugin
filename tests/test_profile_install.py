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
VIBEOS = REPO_ROOT / "vibeos"


class ProfileInstallTests(unittest.TestCase):
    def make_target(self, root: Path) -> None:
        (root / "PROJECT.md").write_text("# IIN Impact Report Factory\n", encoding="utf-8")
        (root / "RULES.md").write_text("# Rules\n", encoding="utf-8")
        (root / "WORKFLOW.md").write_text("# Workflow\n", encoding="utf-8")
        (root / "tools").mkdir()
        (root / "tools/validate_all.py").write_text("print('ok')\n", encoding="utf-8")
        (root / "harness").mkdir()
        (root / "harness/run.py").write_text("print('ok')\n", encoding="utf-8")

    def analyze(self, target: Path, mode: str = "product-engineering", profile: Path | None = None) -> dict:
        cmd = [
            str(VIBEOS),
            "analyze",
            "--target",
            str(target),
            "--source",
            str(REPO_ROOT),
            "--mode",
            mode,
        ]
        if profile is not None:
            cmd.extend(["--profile", str(profile)])
        subprocess.run(cmd, cwd=REPO_ROOT, check=True, capture_output=True, text=True)
        return json.loads((target / ".vibeos/install-plan.json").read_text(encoding="utf-8"))

    def apply(self, target: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            [str(VIBEOS), "apply", "--plan", str(target / ".vibeos/install-plan.json")],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_minimal_and_product_install_do_not_copy_dormant_reference_payload(self):
        for mode in ["minimal", "product-engineering"]:
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp)
                self.make_target(target)
                plan = self.analyze(target, mode=mode)

                for key in [
                    "detected_canon",
                    "protected_files",
                    "existing_validators",
                    "enabled_modules",
                    "skipped_modules",
                    "active_gates",
                    "dormant_payload",
                    "overwrite_plan",
                    "post_install_checks",
                ]:
                    self.assertIn(key, plan)

                self.assertIn(".vibeos/reference", plan["dormant_payload"])
                self.assertIn(".vibeos/decision-engine", plan["dormant_payload"])
                self.assertIn(".vibeos/convergence", plan["dormant_payload"])
                self.assertIn("dormant-reference-payload", plan["skipped_modules"])

                self.apply(target)

                self.assertFalse((target / ".vibeos/reference").exists())
                self.assertFalse((target / ".vibeos/decision-engine").exists())
                self.assertFalse((target / ".vibeos/convergence").exists())
                self.assertTrue((target / ".vibeos/scripts/gate-runner.sh").is_file())
                self.assertTrue((target / ".vibeos/scripts/vibeos-active-surface-audit.py").is_file())

    @unittest.skipIf(tomllib is None, "tomllib is required to validate generated Codex TOML")
    def test_codex_toml_agents_are_generated_from_project_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            plan = self.analyze(target)
            self.apply(target)

            backend_md = (target / ".codex/agent-contracts/backend.md").read_text(encoding="utf-8")
            backend_toml = tomllib.loads((target / ".codex/agents/backend.toml").read_text(encoding="utf-8"))

            self.assertIn("IIN Impact Report Factory", backend_md)
            self.assertIn("IIN Impact Report Factory", backend_toml["developer_instructions"])
            self.assertIn(plan["profile_hash"], backend_toml["developer_instructions"])
            self.assertEqual(backend_toml["name"], "vibeos_backend")
            self.assertEqual(backend_toml["sandbox_mode"], "workspace-write")

            test_auditor = tomllib.loads((target / ".codex/agents/test-auditor.toml").read_text(encoding="utf-8"))
            self.assertEqual(test_auditor["sandbox_mode"], "read-only")

    def test_active_surface_audit_fails_on_generic_active_instruction(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            self.analyze(target)
            self.apply(target)

            agents_md = target / "AGENTS.md"
            agents_md.write_text(
                agents_md.read_text(encoding="utf-8")
                + "\nAn autonomous, self-governing development engine.\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                ["python3", ".vibeos/scripts/vibeos-active-surface-audit.py"],
                cwd=target,
                capture_output=True,
                text=True,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("generic active-instruction phrase", result.stdout)

    def test_generic_prompt_routing_and_commit_msg_enforcement_are_opt_in(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            plan = self.analyze(target)
            self.apply(target)

            codex_hooks = json.loads((target / ".codex/hooks.json").read_text(encoding="utf-8"))
            claude_settings = json.loads((target / ".claude/settings.json").read_text(encoding="utf-8"))

            self.assertNotIn("UserPromptSubmit", codex_hooks["hooks"])
            self.assertNotIn("UserPromptSubmit", claude_settings["hooks"])
            self.assertIn("generic-prompt-routing", plan["skipped_modules"])
            self.assertIn("generic-governance-prompt-scan", plan["skipped_modules"])
            self.assertIn("commit-msg-enforcement", plan["skipped_modules"])
            self.assertFalse((target / ".git/hooks/commit-msg").exists())

        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            profile = target / "iin-profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "project_name": "IIN Impact Report Factory",
                        "mode": "product-engineering",
                        "enabled_modules": ["generic-governance-prompt-scan"],
                    }
                ),
                encoding="utf-8",
            )
            self.analyze(target, profile=profile)
            self.apply(target)
            codex_hooks = json.loads((target / ".codex/hooks.json").read_text(encoding="utf-8"))
            self.assertIn("UserPromptSubmit", codex_hooks["hooks"])

    def test_profile_apply_preserves_locally_customized_generated_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            self.analyze(target)
            self.apply(target)

            backend = target / ".codex/agents/backend.toml"
            original = backend.read_text(encoding="utf-8")
            backend.write_text(original + "\n# local project customization\n", encoding="utf-8")

            self.analyze(target)
            result = self.apply(target)

            self.assertIn("MERGE: preserved .codex/agents/backend.toml", result.stdout)
            self.assertIn("# local project customization", backend.read_text(encoding="utf-8"))
            self.assertTrue((target / ".vibeos/merge-conflicts/.codex__agents__backend.toml.generated").is_file())


if __name__ == "__main__":
    unittest.main()
