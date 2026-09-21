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

    def test_local_engineering_intake_is_default_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            plan = self.analyze(target)
            self.assertIn("local-engineering-intake", plan["skipped_modules"])
            self.assertNotIn("local-engineering-intake", plan["enabled_modules"])
            self.apply(target)
            self.assertFalse(
                (target / ".vibeos/scripts/local-engineering-intake.py").exists()
            )
            self.assertFalse(
                (target / ".agents/skills/vibeos-local-intake/SKILL.md").exists()
            )

    def test_claude_companion_audit_is_default_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            plan = self.analyze(target)
            self.assertIn("claude-companion-audit", plan["skipped_modules"])
            self.assertNotIn("claude-companion-audit", plan["enabled_modules"])
            self.apply(target)
            self.assertFalse(
                (target / ".vibeos/scripts/claude-companion-audit.py").exists()
            )
            self.assertFalse(
                (
                    target
                    / ".agents/skills/vibeos-claude-companion-audit/SKILL.md"
                ).exists()
            )

    def test_claude_companion_audit_opt_in_installs_enforced_surfaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            profile = target / "profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "project_name": "Companion Audit Fixture",
                        "mode": "product-engineering",
                        "phase_audit_runtime": "claude",
                        "enabled_modules": ["claude-companion-audit"],
                        "claude_companion_audit": {"enabled": True},
                    }
                ),
                encoding="utf-8",
            )
            plan = self.analyze(target, profile=profile)
            self.assertIn("claude-companion-audit", plan["enabled_modules"])
            self.assertEqual(
                plan["profile"]["claude_companion_audit"]["model"],
                "claude-fable-5-1",
            )
            self.assertTrue(
                any(
                    gate["name"] == "claude-companion-audit-closure"
                    and gate["blocking"]
                    for gate in plan["active_gates"]
                )
            )
            self.apply(target)
            installed_profile = json.loads(
                (target / ".vibeos/project-profile.json").read_text(encoding="utf-8")
            )
            self.assertIn(
                "claude-companion-audit", installed_profile["active_modules"]
            )
            self.assertEqual(installed_profile["phase_audit_runtime"], "claude")
            self.assertTrue(installed_profile["claude_companion_audit"]["enabled"])
            self.assertEqual(
                installed_profile["claude_companion_audit"]["model"],
                "claude-fable-5-1",
            )
            self.assertTrue(
                (target / ".vibeos/scripts/claude-companion-audit.py").is_file()
            )
            self.assertTrue(
                (target / ".vibeos/scripts/validate-independent-audit.sh").is_file()
            )
            for root in [".agents", ".codex", ".claude"]:
                skill = (
                    target
                    / root
                    / "skills/vibeos-claude-companion-audit/SKILL.md"
                )
                self.assertTrue(skill.is_file())
                self.assertIn(
                    "Do not run another broad audit",
                    skill.read_text(encoding="utf-8"),
                )
            manifest = json.loads(
                (target / ".claude/quality-gate-manifest.json").read_text()
            )
            closure = next(
                gate
                for gate in manifest["gates"]
                if gate["name"] == "claude-companion-audit-closure"
            )
            self.assertEqual(closure["phase"], "wo_exit")
            self.assertTrue(closure["blocking"])

    def test_local_engineering_intake_opt_in_installs_all_skill_surfaces(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            profile = target / "profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "project_name": "IIN Impact Report Factory",
                        "mode": "product-engineering",
                        "enabled_modules": ["local-engineering-intake"],
                        "local_engineering_intake": {"enabled": True},
                    }
                ),
                encoding="utf-8",
            )
            plan = self.analyze(target, profile=profile)
            self.assertIn("local-engineering-intake", plan["enabled_modules"])
            config = plan["profile"]["local_engineering_intake"]
            self.assertEqual(config["base_url"], "http://127.0.0.1:1234/v1")
            self.assertEqual(config["model"], "gpt-oss-120b")
            self.apply(target)
            self.assertTrue(
                (target / ".vibeos/scripts/local-engineering-intake.py").is_file()
            )
            for root in [".agents", ".codex", ".claude"]:
                skill = target / root / "skills/vibeos-local-intake/SKILL.md"
                self.assertTrue(skill.is_file())
                text = skill.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"))
                self.assertIn("advisory", text)
                self.assertIn("fallback_required", text)
            installed_profile = json.loads(
                (target / ".vibeos/project-profile.json").read_text(encoding="utf-8")
            )
            self.assertTrue(installed_profile["local_engineering_intake"]["enabled"])

    def test_local_engineering_intake_rejects_mismatched_or_remote_profile(self):
        cases = [
            {
                "enabled_modules": ["local-engineering-intake"],
                "local_engineering_intake": {"enabled": False},
            },
            {
                "enabled_modules": [],
                "local_engineering_intake": {"enabled": True},
            },
            {
                "enabled_modules": ["local-engineering-intake"],
                "local_engineering_intake": {
                    "enabled": True,
                    "base_url": "https://models.example.com/v1",
                },
            },
            {
                "enabled_modules": ["local-engineering-intake"],
                "disabled_modules": ["local-engineering-intake"],
                "local_engineering_intake": {"enabled": True},
            },
            {
                "enabled_modules": ["local-engineering-intake"],
                "local_engineering_intake": {
                    "enabled": True,
                    "base_url": "http://127.0.0.1:not-a-port/v1",
                },
            },
        ]
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                target = Path(tmp)
                self.make_target(target)
                profile = target / "profile.json"
                profile.write_text(json.dumps(case), encoding="utf-8")
                result = subprocess.run(
                    [
                        str(VIBEOS),
                        "analyze",
                        "--target",
                        str(target),
                        "--source",
                        str(REPO_ROOT),
                        "--profile",
                        str(profile),
                    ],
                    cwd=REPO_ROOT,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
                self.assertRegex(
                    result.stdout + result.stderr,
                    r"local[-_]engineering[-_]intake",
                )

    def test_analyze_ignores_generated_agents_md_for_name_and_canon(self):
        # WO-150 AC-1/AC-4: a repo whose only heading source is a prior install's
        # generated AGENTS.md must fall back to the directory-name default and
        # must not treat the generated file as canon.
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "sync-connector"
            target.mkdir()
            (target / "AGENTS.md").write_text(
                "<!-- VIBEOS-GENERATED: profile-driven-install -->\n"
                "<!-- template_id: codex.agents-md.v1 -->\n"
                "<!-- profile_hash: abc -->\n"
                "<!-- source_hash: def -->\n\n"
                "# Widget — VibeOS Project Surface\n",
                encoding="utf-8",
            )
            plan = self.analyze(target)
            self.assertEqual(plan["profile"]["project_name"], "Sync Connector")
            self.assertNotIn("AGENTS.md", plan["detected_canon"])

    def test_vibeos_surface_suffix_never_becomes_project_name(self):
        # WO-150 AC-2: even without the generated header, a heading ending in
        # the generated-surface suffix must not be adopted verbatim.
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "boardsync"
            target.mkdir()
            (target / "README.md").write_text(
                "# Widget — VibeOS Project Surface\n", encoding="utf-8"
            )
            plan = self.analyze(target)
            self.assertEqual(plan["profile"]["project_name"], "Widget")

    def test_heading_that_strips_to_empty_falls_back_to_directory_name(self):
        # WO-150 AC-2 edge: a heading that is nothing but the generated-surface
        # suffix must fall through to the directory-name default.
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "boardsync"
            target.mkdir()
            (target / "README.md").write_text(
                "# — VibeOS Project Surface\n", encoding="utf-8"
            )
            plan = self.analyze(target)
            self.assertEqual(plan["profile"]["project_name"], "Boardsync")

    def test_unpinned_reanalyze_is_idempotent_on_name_and_canon(self):
        # WO-150 AC-4: analyze → apply → analyze without a profile must not
        # drift the detected name, canon, or profile hash via generated files.
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            first = self.analyze(target)
            self.apply(target)
            second = self.analyze(target)
            self.assertEqual(second["profile"]["project_name"], first["profile"]["project_name"])
            self.assertEqual(second["detected_canon"], first["detected_canon"])
            self.assertEqual(second["profile_hash"], first["profile_hash"])

    def test_non_ascii_project_name_renders_literally_and_passes_audit(self):
        # WO-150 AC-3: an em-dash project name must appear literally in the
        # generated Codex TOMLs (no — escapes) and the apply-time
        # active-surface audit must pass.
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            profile = target / "profile.json"
            profile.write_text(
                json.dumps(
                    {
                        "project_name": "Team Board — Connector",
                        "mode": "product-engineering",
                    }
                ),
                encoding="utf-8",
            )
            self.analyze(target, profile=profile)
            self.apply(target)
            backend = (target / ".codex/agents/backend.toml").read_text(encoding="utf-8")
            self.assertIn("Team Board — Connector", backend)
            self.assertNotIn("\\u2014", backend)

    def test_quoted_project_name_passes_audit(self):
        # Quotes are string-escaped inside TOML, so the audit's mention check
        # must accept the escaped form, not just the literal name.
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            target_readme = target / "README.md"
            target_readme.write_text('# The "Quoted" Project\n', encoding="utf-8")
            self.analyze(target)
            self.apply(target)
            backend = (target / ".codex/agents/backend.toml").read_text(encoding="utf-8")
            self.assertIn('The \\"Quoted\\" Project', backend)

    def test_missing_profile_path_fails_with_clear_message(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            self.make_target(target)
            result = subprocess.run(
                [
                    str(VIBEOS), "analyze",
                    "--target", str(target),
                    "--source", str(REPO_ROOT),
                    "--profile", str(target / "nope.json"),
                ],
                cwd=REPO_ROOT, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("profile not found", result.stdout)

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
