from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "plugins/vibeos/scripts/claude-companion-audit.py"


def run(args, cwd, **kwargs):  # noqa: ANN001
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, **kwargs)


def write_json(path: Path, value) -> None:  # noqa: ANN001
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


class CompanionAuditTests(unittest.TestCase):
    def git(self, project: Path, *args: str) -> str:
        result = run(["git", *args], project)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.strip()

    def commit(self, project: Path, message: str) -> str:
        self.git(project, "add", ".")
        self.git(project, "commit", "-qm", message)
        return self.git(project, "rev-parse", "HEAD")

    def fake_claude(
        self, project: Path, structured, *, provider="firstParty",
        canonical_model="claude-fable-5-1", authenticated=True,
        reject_unknown_flags=False, version="2.1.277 (Claude Code fixture)",
        omit_help_flag=None,
    ) -> Path:  # noqa: ANN001
        fake = project.parent / "fake-claude"
        args_out = project.parent / "fake-claude-args.json"
        payload = {
            "is_error": False,
            "structured_output": structured,
            "modelUsage": {
                "claude-fable-5-1": {
                    "canonicalModel": canonical_model,
                    "provider": provider,
                    "inputTokens": 100,
                    "outputTokens": 50,
                    "costUSD": 0.2,
                }
            },
        }
        supported_flags = sorted([
            "--print", "--safe-mode", "--restricted", "--tools",
            "--disable-slash-commands", "--no-chrome", "--no-session-persistence",
            "--setting-sources", "--strict-mcp-config", "--mcp-config",
            "--permission-mode", "--permission-prompts", "--model", "--effort",
            "--max-budget-usd", "--max-turns", "--output-format", "--json-schema",
            "-p",
        ])
        help_flags = [flag for flag in supported_flags if flag != omit_help_flag]
        source = f"""#!/usr/bin/env python3
import json
import sys
if sys.argv[1:] == ["auth", "status"]:
    print(json.dumps({{"loggedIn": {authenticated!r}, "authMethod": "claude.ai", "apiProvider": "firstParty", "email": "fixture@example.test"}}))
elif sys.argv[1:] == ["--version"]:
    print({version!r})
elif sys.argv[1:] == ["--help"]:
    print("\\n".join({help_flags!r}))
else:
    known = {supported_flags!r}
    if {reject_unknown_flags!r} and any(arg.startswith("-") and arg not in known for arg in sys.argv[1:]):
        print("unknown flag", file=sys.stderr)
        raise SystemExit(2)
    open({str(args_out)!r}, "w", encoding="utf-8").write(json.dumps(sys.argv[1:]))
    open({str(project.parent / 'fake-claude-stdin.txt')!r}, "w", encoding="utf-8").write(sys.stdin.read())
    print(json.dumps({payload!r}))
"""
        fake.write_text(source, encoding="utf-8")
        fake.chmod(0o755)
        return fake

    def fixture(self, root: Path) -> tuple[Path, str, str]:
        project = root / "project"
        project.mkdir()
        self.git(project, "init", "-q")
        self.git(project, "config", "user.name", "Fixture")
        self.git(project, "config", "user.email", "fixture@example.invalid")
        (project / "README.md").write_text("# Fixture\n", encoding="utf-8")
        (project / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")
        base = self.commit(project, "base")
        self.git(project, "update-ref", "refs/remotes/origin/main", base)
        (project / "src").mkdir()
        (project / "tests").mkdir()
        (project / "docs/planning").mkdir(parents=True)
        (project / "src/app.py").write_text("def answer():\n    return 41\n", encoding="utf-8")
        (project / "tests/test_app.py").write_text(
            "from src.app import answer\n\ndef test_answer():\n    assert answer() == 42\n",
            encoding="utf-8",
        )
        wo = project / "docs/planning/WO-157-fixture.md"
        wo.write_text(
            "---\nwo: WO-157\nwrite_scope:\n"
            "  - src/**\n  - tests/**\n  - docs/planning/WO-157-fixture.md\n"
            "  - docs/evidence/WO-157/**\n---\n\n"
            "# WO-157\n\nAcceptance: answer returns 42.\n",
            encoding="utf-8",
        )
        contract = project / "docs/evidence/WO-157/acceptance-contract.md"
        contract.parent.mkdir(parents=True)
        contract.write_text("# Acceptance contract\n\nThe answer must return 42.\n", encoding="utf-8")
        evidence = project / "docs/evidence/WO-157/tests.txt"
        evidence.write_text("1 failed: expected 42, received 41\n", encoding="utf-8")
        config = {
            "enabled": True,
            "model": "claude-fable-5-1",
            "provider": "firstParty",
            "max_budget_usd": 5.0,
            "max_turns": 5,
            "timeout_seconds": 60,
            "max_prompt_bytes": 100000,
            "default_branch_ref": "origin/main",
        }
        write_json(project / "docs/evidence/WO-157/claude-config.json", config)
        scope = {
            "schema_version": 1,
            "work_order": "WO-157",
            "acceptance_contract": ["docs/evidence/WO-157/acceptance-contract.md"],
            "review_paths": ["src/app.py", "tests/test_app.py"],
            "evidence_paths": ["docs/evidence/WO-157/tests.txt"],
            "finding_ids": [],
        }
        write_json(project / "docs/evidence/WO-157/full-scope.json", scope)
        candidate = self.commit(project, "candidate")
        return project, base, candidate

    def full_result(self):
        return {
            "verdict": "changes_required",
            "summary": "The implementation contradicts the acceptance contract.",
            "findings": [
                {
                    "id": "F-001",
                    "severity": "high",
                    "title": "Wrong returned value",
                    "location": "src/app.py:2",
                    "evidence": "answer returns 41 while the contract and test require 42",
                    "recommendation": "Return 42 and rerun the focused test.",
                }
            ],
            "coverage": ["implementation and focused test"],
            "limitations": ["static review of supplied evidence"],
        }

    def verification_result(self):
        return {
            "verdict": "pass",
            "summary": "The named finding is closed by the correction and test evidence.",
            "finding_checks": [
                {
                    "id": "F-001",
                    "status": "closed",
                    "evidence": "src/app.py now returns 42 and the focused test passed",
                    "note": "No regression in the supplied affected behavior.",
                }
            ],
            "new_blockers": [],
            "coverage": ["F-001, correction diff, focused test"],
            "limitations": ["no broad reaudit performed"],
        }

    def invoke_full(self, project: Path, _base: str, fake: Path):
        return run(
            [
                "python3", str(SCRIPT), "full", "--project-dir", str(project),
                "--work-order", "docs/planning/WO-157-fixture.md",
                "--scope-manifest", "docs/evidence/WO-157/full-scope.json",
                "--candidate-ref", "HEAD",
                "--config", "docs/evidence/WO-157/claude-config.json",
                "--allow-unprofiled-project",
                "--claude-bin", str(fake),
                "--out", ".vibeos/audit-reports/WO-157-full.json",
            ],
            project,
        )

    def apply_fix(self, project: Path) -> str:
        (project / "src/app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
        (project / "docs/evidence/WO-157/tests-fixed.txt").write_text(
            "1 passed\n", encoding="utf-8"
        )
        scope = {
            "schema_version": 1,
            "work_order": "WO-157",
            "acceptance_contract": ["docs/evidence/WO-157/acceptance-contract.md"],
            "review_paths": ["src/app.py", "tests/test_app.py"],
            "evidence_paths": ["docs/evidence/WO-157/tests-fixed.txt"],
            "finding_ids": ["F-001"],
        }
        write_json(project / "docs/evidence/WO-157/verify-scope.json", scope)
        return self.commit(project, "fix F-001")

    def invoke_verification(
        self, project: Path, fake: Path, *,
        scope="docs/evidence/WO-157/verify-scope.json",
        out=".vibeos/audit-reports/WO-157-verification.json",
    ):
        return run(
            [
                "python3", str(SCRIPT), "verification", "--project-dir", str(project),
                "--work-order", "docs/planning/WO-157-fixture.md",
                "--scope-manifest", scope,
                "--candidate-ref", "HEAD",
                "--parent-receipt", ".vibeos/audit-reports/WO-157-full.json",
                "--config", "docs/evidence/WO-157/claude-config.json",
                "--allow-unprofiled-project",
                "--claude-bin", str(fake),
                "--out", out,
            ],
            project,
        )

    def test_schema_is_closed(self):
        result = run(["python3", str(SCRIPT), "schema"], ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["full"]["additionalProperties"])
        self.assertFalse(payload["verification"]["additionalProperties"])

    def test_full_audit_then_targeted_verification_closes_without_broad_rerun(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, candidate = self.fixture(Path(temporary))
            fake = self.fake_claude(project, self.full_result())
            full = self.invoke_full(project, base, fake)
            self.assertEqual(full.returncode, 3, full.stdout + full.stderr)
            full_receipt = json.loads(
                (project / ".vibeos/audit-reports/WO-157-full.json").read_text()
            )
            self.assertEqual(full_receipt["binding"]["candidate_commit"], candidate)
            self.assertEqual(full_receipt["closure"]["next_required"], "targeted_verification")
            provider_args = json.loads(
                (project.parent / "fake-claude-args.json").read_text()
            )
            self.assertIn("--safe-mode", provider_args)
            self.assertIn("--restricted", provider_args)
            self.assertIn("--no-session-persistence", provider_args)
            self.assertEqual(provider_args[provider_args.index("--tools") + 1], "")
            self.assertEqual(
                provider_args[provider_args.index("--permission-prompts") + 1],
                "none",
            )
            self.assertEqual(
                provider_args[provider_args.index("--permission-mode") + 1],
                "default",
            )
            self.assertEqual(
                provider_args[provider_args.index("--model") + 1],
                "claude-fable-5-1",
            )
            self.assertEqual(provider_args[-1], "-p")
            provider_stdin = (project.parent / "fake-claude-stdin.txt").read_text()
            self.assertIn("The answer must return 42.", provider_stdin)
            self.assertIn('"default_branch_ref": "origin/main"', provider_stdin)
            self.assertNotIn("The answer must return 42.", json.dumps(provider_args))
            self.apply_fix(project)
            fake = self.fake_claude(project, self.verification_result())
            verified = self.invoke_verification(project, fake)
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
            receipt = json.loads(
                (project / ".vibeos/audit-reports/WO-157-verification.json").read_text()
            )
            self.assertEqual(receipt["mode"], "verification")
            self.assertEqual(receipt["binding"]["parent_audit_id"], full_receipt["audit_id"])
            self.assertEqual(receipt["closure"]["status"], "pass")
            self.assertEqual(receipt["auditor"]["observed_model"], "claude-fable-5-1")
            self.assertEqual(receipt["auditor"]["provider_usage"]["costUSD"], 0.2)
            self.assertIn("cli_entrypoint_sha256", receipt["auditor"])
            self.assertNotIn("account_identifier_sha256", receipt["auditor"])
            report = (
                project / ".vibeos/audit-reports/WO-157-verification.md"
            ).read_text()
            self.assertIn("audit_visibility_mode: committed-tree", report)
            self.assertNotIn("Auditors dispatched", report)
            validated = run(
                [
                    "python3", str(SCRIPT), "validate", "--project-dir", str(project),
                    "--receipt", ".vibeos/audit-reports/WO-157-verification.json",
                    "--work-order", "WO-157",
                ],
                project,
            )
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)
            installed_scripts = project / ".vibeos/scripts"
            installed_scripts.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SCRIPT, installed_scripts / SCRIPT.name)
            write_json(
                project / ".vibeos/project-profile.json",
                {
                    "active_modules": ["claude-companion-audit"],
                    "phase_audit_runtime": "claude",
                },
            )
            env = dict(os.environ, PROJECT_ROOT=str(project))
            gate = run(
                [
                    "bash",
                    str(ROOT / "plugins/vibeos/scripts/validate-independent-audit.sh"),
                    "docs/planning/WO-157-fixture.md",
                    ".vibeos/audit-reports/WO-157-verification.md",
                ],
                project,
                env=env,
            )
            self.assertEqual(gate.returncode, 0, gate.stdout + gate.stderr)
            self.assertIn('"mode": "verification"', gate.stdout)

    def test_changed_acceptance_contract_requires_new_full_audit(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            fake = self.fake_claude(project, self.full_result())
            self.assertEqual(self.invoke_full(project, base, fake).returncode, 3)
            self.apply_fix(project)
            contract = project / "docs/evidence/WO-157/acceptance-contract.md"
            contract.write_text(contract.read_text() + "Changed contract.\n")
            self.commit(project, "change acceptance")
            fake = self.fake_claude(project, self.verification_result())
            verified = self.invoke_verification(project, fake)
            self.assertEqual(verified.returncode, 2)
            self.assertIn("acceptance_contract_changed_full_audit_required", verified.stderr)

    def test_large_packet_uses_stdin_and_strict_known_flags(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            marker = "PRIVATE-SOURCE-MARKER-" + ("x" * 135000)
            (project / "docs/evidence/WO-157/tests.txt").write_text(marker)
            config_path = project / "docs/evidence/WO-157/claude-config.json"
            config = json.loads(config_path.read_text())
            config["max_prompt_bytes"] = 200000
            write_json(config_path, config)
            candidate = self.commit(project, "large evidence")
            fake = self.fake_claude(
                project, self.full_result(), reject_unknown_flags=True
            )
            result = self.invoke_full(project, base, fake)
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            args = json.loads((project.parent / "fake-claude-args.json").read_text())
            stdin = (project.parent / "fake-claude-stdin.txt").read_text()
            self.assertGreater(len(stdin.encode()), 131072)
            self.assertIn("PRIVATE-SOURCE-MARKER", stdin)
            self.assertNotIn("PRIVATE-SOURCE-MARKER", json.dumps(args))
            receipt = json.loads(
                (project / ".vibeos/audit-reports/WO-157-full.json").read_text()
            )
            self.assertEqual(receipt["binding"]["candidate_commit"], candidate)

    def test_large_and_unicode_review_files_are_bound_without_text_quoting(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            large_path = project / "src/large.bin"
            unicode_path = project / "src/café.py"
            large_path.write_bytes(b"\0" + (b"x" * 170_000))
            unicode_path.write_text("value = 'café'\n", encoding="utf-8")
            scope_path = project / "docs/evidence/WO-157/full-scope.json"
            scope = json.loads(scope_path.read_text())
            scope["review_paths"] = ["src", "tests/test_app.py"]
            write_json(scope_path, scope)
            self.commit(project, "large and unicode review files")
            clean_result = {**self.full_result(), "verdict": "pass", "findings": []}
            fake = self.fake_claude(project, clean_result)
            result = self.invoke_full(project, base, fake)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            receipt = json.loads(
                (project / ".vibeos/audit-reports/WO-157-full.json").read_text()
            )
            self.assertEqual(receipt["closure"]["status"], "pass")
            validated = run(
                [
                    "python3", str(SCRIPT), "validate", "--project-dir", str(project),
                    "--receipt", ".vibeos/audit-reports/WO-157-full.json",
                ],
                project,
            )
            self.assertEqual(
                validated.returncode, 0, validated.stdout + validated.stderr
            )

    def test_missing_required_claude_flag_fails_before_provider_call(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            fake = self.fake_claude(
                project, self.full_result(), omit_help_flag="--setting-sources"
            )
            result = self.invoke_full(project, base, fake)
            self.assertEqual(result.returncode, 2)
            self.assertIn("claude_required_flags_missing", result.stderr)
            self.assertFalse((project.parent / "fake-claude-args.json").exists())

    def test_full_cli_rejects_a_late_base_ref_override(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, _base, candidate = self.fixture(Path(temporary))
            fake = self.fake_claude(project, self.full_result())
            result = run(
                [
                    "python3", str(SCRIPT), "full", "--project-dir", str(project),
                    "--work-order", "docs/planning/WO-157-fixture.md",
                    "--scope-manifest", "docs/evidence/WO-157/full-scope.json",
                    "--base-ref", candidate, "--candidate-ref", "HEAD",
                    "--config", "docs/evidence/WO-157/claude-config.json",
                    "--allow-unprofiled-project", "--claude-bin", str(fake),
                    "--out", ".vibeos/audit-reports/WO-157-full.json",
                ],
                project,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("unrecognized arguments: --base-ref", result.stderr)
            self.assertFalse((project.parent / "fake-claude-args.json").exists())

    def test_default_branch_authority_rejects_local_ref_and_allows_safe_remote_advance(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            config_path = project / "docs/evidence/WO-157/claude-config.json"
            config = json.loads(config_path.read_text())
            config["default_branch_ref"] = "HEAD~1"
            write_json(config_path, config)
            self.commit(project, "invalid default branch authority")
            fake = self.fake_claude(project, self.full_result())
            result = self.invoke_full(project, base, fake)
            self.assertEqual(result.returncode, 2)
            self.assertIn("default_branch_ref_must_be_origin_remote_ref", result.stderr)

        with tempfile.TemporaryDirectory() as temporary:
            project, base, candidate = self.fixture(Path(temporary))
            clean_result = {
                **self.full_result(),
                "verdict": "pass",
                "findings": [],
            }
            fake = self.fake_claude(project, clean_result)
            self.assertEqual(self.invoke_full(project, base, fake).returncode, 0)
            self.git(project, "update-ref", "refs/remotes/origin/main", candidate)
            validated = run(
                [
                    "python3", str(SCRIPT), "validate", "--project-dir", str(project),
                    "--receipt", ".vibeos/audit-reports/WO-157-full.json",
                ],
                project,
            )
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)

            tree = self.git(project, "rev-parse", f"{base}^{{tree}}")
            unrelated = self.git(project, "commit-tree", tree, "-m", "unrelated root")
            self.git(project, "update-ref", "refs/remotes/origin/main", unrelated)
            rejected = run(
                [
                    "python3", str(SCRIPT), "validate", "--project-dir", str(project),
                    "--receipt", ".vibeos/audit-reports/WO-157-full.json",
                ],
                project,
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("default_branch_merge_base_unavailable", rejected.stderr)

    def test_full_audit_rejects_change_outside_work_order_write_scope(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            (project / "outside.py").write_text("value = 1\n")
            scope_path = project / "docs/evidence/WO-157/full-scope.json"
            scope = json.loads(scope_path.read_text())
            scope["review_paths"].append("outside.py")
            write_json(scope_path, scope)
            self.commit(project, "undeclared work")
            fake = self.fake_claude(project, self.full_result())
            result = self.invoke_full(project, base, fake)
            self.assertEqual(result.returncode, 2)
            self.assertIn("changed_paths_outside_work_order_write_scope", result.stderr)

    def test_explicit_config_requires_recorded_unprofiled_override(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            fake = self.fake_claude(project, self.full_result())
            result = run(
                [
                    "python3", str(SCRIPT), "full", "--project-dir", str(project),
                    "--work-order", "docs/planning/WO-157-fixture.md",
                    "--scope-manifest", "docs/evidence/WO-157/full-scope.json",
                    "--candidate-ref", "HEAD",
                    "--config", "docs/evidence/WO-157/claude-config.json",
                    "--claude-bin", str(fake),
                    "--out", ".vibeos/audit-reports/WO-157-full.json",
                ],
                project,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn(
                "explicit_config_requires_allow_unprofiled_project", result.stderr
            )

    def test_profile_authorizes_provider_call_without_explicit_config(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            profile = {
                "active_modules": ["claude-companion-audit"],
                "phase_audit_runtime": "claude",
                "claude_companion_audit": json.loads(
                    (project / "docs/evidence/WO-157/claude-config.json").read_text()
                ),
            }
            write_json(project / ".vibeos/project-profile.json", profile)
            work_order = project / "docs/planning/WO-157-fixture.md"
            work_order.write_text(
                work_order.read_text().replace(
                    "  - src/**\n", "  - src/**\n  - .vibeos/project-profile.json\n"
                )
            )
            scope_path = project / "docs/evidence/WO-157/full-scope.json"
            scope = json.loads(scope_path.read_text())
            scope["review_paths"].append(".vibeos/project-profile.json")
            scope["evidence_paths"].append(
                "docs/evidence/WO-157/claude-config.json"
            )
            write_json(scope_path, scope)
            self.commit(project, "profile-authorized candidate")
            fake = self.fake_claude(project, self.full_result())
            result = run(
                [
                    "python3", str(SCRIPT), "full", "--project-dir", str(project),
                    "--work-order", "docs/planning/WO-157-fixture.md",
                    "--scope-manifest", "docs/evidence/WO-157/full-scope.json",
                    "--candidate-ref", "HEAD",
                    "--claude-bin", str(fake),
                    "--out", ".vibeos/audit-reports/WO-157-full.json",
                ],
                project,
            )
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            receipt = json.loads(
                (project / ".vibeos/audit-reports/WO-157-full.json").read_text()
            )
            self.assertFalse(receipt["binding"]["unprofiled_project_override"])

    def test_verification_rejects_missing_finding_and_expanded_scope_before_provider(self):
        for mutation, expected in (
            ("finding", "verification_scope_must_cover_every_original_finding"),
            ("scope", "verification_scope_expands_beyond_original_review"),
        ):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as temporary:
                project, base, _candidate = self.fixture(Path(temporary))
                fake = self.fake_claude(project, self.full_result())
                self.assertEqual(self.invoke_full(project, base, fake).returncode, 3)
                self.apply_fix(project)
                scope_path = project / "docs/evidence/WO-157/verify-scope.json"
                scope = json.loads(scope_path.read_text())
                if mutation == "finding":
                    scope["finding_ids"] = ["F-999"]
                else:
                    scope["review_paths"].append("README.md")
                write_json(scope_path, scope)
                self.commit(project, f"invalid {mutation}")
                (project.parent / "fake-claude-args.json").unlink(missing_ok=True)
                fake = self.fake_claude(project, self.verification_result())
                result = self.invoke_verification(project, fake)
                self.assertEqual(result.returncode, 2)
                self.assertIn(expected, result.stderr)
                self.assertFalse((project.parent / "fake-claude-args.json").exists())

    def test_verification_rejects_correction_outside_original_scope(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            fake = self.fake_claude(project, self.full_result())
            self.assertEqual(self.invoke_full(project, base, fake).returncode, 3)
            self.apply_fix(project)
            (project / "docs/planning/unrelated.md").write_text("outside correction\n")
            self.commit(project, "outside correction")
            (project.parent / "fake-claude-args.json").unlink(missing_ok=True)
            fake = self.fake_claude(project, self.verification_result())
            result = self.invoke_verification(project, fake)
            self.assertEqual(result.returncode, 2)
            self.assertIn("correction_scope_expanded_full_audit_required", result.stderr)
            self.assertFalse((project.parent / "fake-claude-args.json").exists())

    def test_provider_result_invariants_fail_closed(self):
        cases = [
            (
                "pass_with_blocker",
                {**self.full_result(), "verdict": "pass"},
                {},
                "pass_verdict_with_blocking_findings",
            ),
            (
                "canonical_mismatch",
                self.full_result(),
                {"canonical_model": "claude-other"},
                "claude_canonical_model_mismatch",
            ),
            (
                "not_authenticated",
                self.full_result(),
                {"authenticated": False},
                "claude_not_authenticated",
            ),
            (
                "old_cli",
                self.full_result(),
                {"version": "2.1.100 (Claude Code fixture)"},
                "claude_cli_version_too_old",
            ),
        ]
        for name, structured, options, expected in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                project, base, _candidate = self.fixture(Path(temporary))
                fake = self.fake_claude(project, structured, **options)
                result = self.invoke_full(project, base, fake)
                self.assertEqual(result.returncode, 2)
                self.assertIn(expected, result.stderr)
                self.assertFalse(
                    (project / ".vibeos/audit-reports/WO-157-full.json").exists()
                )

    def test_nonpass_full_result_without_findings_requires_new_full_audit(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            result_payload = {
                **self.full_result(),
                "verdict": "blocked",
                "findings": [],
            }
            fake = self.fake_claude(project, result_payload)
            result = self.invoke_full(project, base, fake)
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            receipt = json.loads(
                (project / ".vibeos/audit-reports/WO-157-full.json").read_text()
            )
            self.assertEqual(receipt["closure"]["next_required"], "full_audit")

    def test_malformed_parent_receipt_returns_controlled_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            fake = self.fake_claude(project, self.full_result())
            self.assertEqual(self.invoke_full(project, base, fake).returncode, 3)
            self.apply_fix(project)
            parent_path = project / ".vibeos/audit-reports/WO-157-full.json"
            parent = json.loads(parent_path.read_text())
            parent["binding"].pop("candidate_commit")
            parent_path.write_text(json.dumps(parent, indent=2) + "\n")
            fake = self.fake_claude(project, self.verification_result())
            result = self.invoke_verification(project, fake)
            self.assertEqual(result.returncode, 2)
            self.assertIn("parent_receipt_binding_invalid", result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_empty_diff_and_inconsistent_verification_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, _base, candidate = self.fixture(Path(temporary))
            self.git(project, "update-ref", "refs/remotes/origin/main", candidate)
            fake = self.fake_claude(project, self.full_result())
            result = self.invoke_full(project, candidate, fake)
            self.assertEqual(result.returncode, 2)
            self.assertIn("audit_diff_is_empty", result.stderr)

        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            fake = self.fake_claude(project, self.full_result())
            self.assertEqual(self.invoke_full(project, base, fake).returncode, 3)
            self.apply_fix(project)
            inconsistent = {**self.verification_result(), "verdict": "changes_required"}
            fake = self.fake_claude(project, inconsistent)
            result = self.invoke_verification(project, fake)
            self.assertEqual(result.returncode, 2)
            self.assertIn("verification_verdict_inconsistent", result.stderr)

    def test_open_verification_returns_three_and_requires_targeted_followup(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            fake = self.fake_claude(project, self.full_result())
            self.assertEqual(self.invoke_full(project, base, fake).returncode, 3)
            self.apply_fix(project)
            open_result = self.verification_result()
            open_result["verdict"] = "changes_required"
            open_result["finding_checks"][0]["status"] = "open"
            fake = self.fake_claude(project, open_result)
            result = self.invoke_verification(project, fake)
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            receipt = json.loads(
                (project / ".vibeos/audit-reports/WO-157-verification.json").read_text()
            )
            self.assertEqual(receipt["closure"]["next_required"], "targeted_verification")

    def test_second_targeted_round_accepts_prior_scope_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            fake = self.fake_claude(project, self.full_result())
            self.assertEqual(self.invoke_full(project, base, fake).returncode, 3)
            self.apply_fix(project)
            open_result = self.verification_result()
            open_result["verdict"] = "changes_required"
            open_result["finding_checks"][0]["status"] = "open"
            fake = self.fake_claude(project, open_result)
            self.assertEqual(self.invoke_verification(project, fake).returncode, 3)

            (project / "src/app.py").write_text(
                "def answer():\n    return 42  # verified correction\n"
            )
            second_evidence = project / "docs/evidence/WO-157/tests-round-2.txt"
            second_evidence.write_text("1 passed after round 2\n")
            second_scope = {
                "schema_version": 1,
                "work_order": "WO-157",
                "acceptance_contract": [
                    "docs/evidence/WO-157/acceptance-contract.md"
                ],
                "review_paths": ["src/app.py", "tests/test_app.py"],
                "evidence_paths": [
                    "docs/evidence/WO-157/tests-fixed.txt",
                    "docs/evidence/WO-157/tests-round-2.txt",
                ],
                "finding_ids": ["F-001"],
            }
            write_json(
                project / "docs/evidence/WO-157/verify-scope-round-2.json",
                second_scope,
            )
            self.commit(project, "second targeted correction")
            fake = self.fake_claude(project, self.verification_result())
            result = self.invoke_verification(
                project,
                fake,
                scope="docs/evidence/WO-157/verify-scope-round-2.json",
                out=".vibeos/audit-reports/WO-157-verification-round-2.json",
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_receipt_result_must_match_stored_provider_payload(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            fake = self.fake_claude(project, self.full_result())
            self.assertEqual(self.invoke_full(project, base, fake).returncode, 3)
            self.apply_fix(project)
            fake = self.fake_claude(project, self.verification_result())
            self.assertEqual(self.invoke_verification(project, fake).returncode, 0)
            receipt_path = project / ".vibeos/audit-reports/WO-157-verification.json"
            receipt = json.loads(receipt_path.read_text())
            receipt["result"]["summary"] = "forged summary"
            receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
            result = run(
                [
                    "python3", str(SCRIPT), "validate", "--project-dir", str(project),
                    "--receipt", ".vibeos/audit-reports/WO-157-verification.json",
                ],
                project,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("receipt_result_does_not_match_provider_payload", result.stderr)

    def test_verification_rejects_pruned_parent_findings_before_provider_call(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            fake = self.fake_claude(project, self.full_result())
            self.assertEqual(self.invoke_full(project, base, fake).returncode, 3)
            self.apply_fix(project)
            parent_path = project / ".vibeos/audit-reports/WO-157-full.json"
            parent = json.loads(parent_path.read_text())
            parent["result"]["findings"] = []
            parent_path.write_text(json.dumps(parent, indent=2) + "\n")
            (project.parent / "fake-claude-args.json").unlink(missing_ok=True)
            fake = self.fake_claude(project, self.verification_result())
            result = self.invoke_verification(project, fake)
            self.assertEqual(result.returncode, 2)
            self.assertIn(
                "parent_receipt_result_does_not_match_provider_payload",
                result.stderr,
            )
            self.assertFalse((project.parent / "fake-claude-args.json").exists())

    def test_disabled_companion_gate_mention_does_not_activate_module(self):
        gate_script = ROOT / "plugins/vibeos/scripts/validate-independent-audit.sh"
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "docs/planning").mkdir(parents=True)
            work_order = project / "docs/planning/WO-157-fixture.md"
            work_order.write_text("# WO-157\n")
            report = project / ".vibeos/audit-reports/WO-157.md"
            report.parent.mkdir(parents=True)
            report.write_text(
                "## Auditor Summary\n\nSecurity and correctness reviewed for WO-157.\n"
            )
            manifest = project / ".claude/quality-gate-manifest.json"
            manifest.parent.mkdir(parents=True)
            write_json(
                manifest,
                {
                    "gates": [
                        {
                            "name": "claude-companion-audit-closure",
                            "enabled": False,
                        }
                    ]
                },
            )
            write_json(
                project / ".vibeos/project-profile.json",
                {
                    "active_modules": [],
                    "disabled_modules": ["claude-companion-audit"],
                    "phase_audit_runtime": "claude",
                },
            )
            env = dict(os.environ, PROJECT_ROOT=str(project))
            result = run(
                ["/bin/bash", str(gate_script), str(work_order), str(report)],
                project,
                env=env,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_enabled_companion_gate_requires_registered_receipt(self):
        gate_script = ROOT / "plugins/vibeos/scripts/validate-independent-audit.sh"
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "docs/planning").mkdir(parents=True)
            work_order = project / "docs/planning/WO-157-fixture.md"
            work_order.write_text("# WO-157\n")
            report = project / ".vibeos/audit-reports/WO-157.md"
            report.parent.mkdir(parents=True)
            report.write_text(
                "## Auditor Summary\n\nSecurity and correctness reviewed for WO-157.\n"
            )
            manifest = project / ".claude/quality-gate-manifest.json"
            manifest.parent.mkdir(parents=True)
            write_json(
                manifest,
                {"gates": [{"name": "claude-companion-audit-closure"}]},
            )
            write_json(
                project / ".vibeos/project-profile.json",
                {
                    "active_modules": ["claude-companion-audit"],
                    "phase_audit_runtime": "claude",
                },
            )
            env = dict(os.environ, PROJECT_ROOT=str(project))
            result = run(
                ["/bin/bash", str(gate_script), str(work_order), str(report)],
                project,
                env=env,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("no receipt is registered", result.stdout + result.stderr)

    def test_enabled_companion_gate_does_not_skip_a_missing_report(self):
        gate_script = ROOT / "plugins/vibeos/scripts/validate-independent-audit.sh"
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / "docs/planning").mkdir(parents=True)
            work_order = project / "docs/planning/WO-157-fixture.md"
            work_order.write_text("# WO-157\n")
            manifest = project / ".claude/quality-gate-manifest.json"
            manifest.parent.mkdir(parents=True)
            write_json(
                manifest,
                {"gates": [{"name": "claude-companion-audit-closure"}]},
            )
            write_json(
                project / ".vibeos/project-profile.json",
                {
                    "active_modules": ["claude-companion-audit"],
                    "phase_audit_runtime": "claude",
                },
            )
            env = dict(os.environ, PROJECT_ROOT=str(project))
            result = run(
                ["/bin/bash", str(gate_script), str(work_order)],
                project,
                env=env,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(
                "No independent audit report registered",
                result.stdout + result.stderr,
            )

    def test_enabled_companion_gate_rejects_an_open_receipt(self):
        gate_script = ROOT / "plugins/vibeos/scripts/validate-independent-audit.sh"
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            fake = self.fake_claude(project, self.full_result())
            self.assertEqual(self.invoke_full(project, base, fake).returncode, 3)
            installed_scripts = project / ".vibeos/scripts"
            installed_scripts.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SCRIPT, installed_scripts / SCRIPT.name)
            write_json(
                project / ".vibeos/project-profile.json",
                {
                    "active_modules": ["claude-companion-audit"],
                    "phase_audit_runtime": "claude",
                },
            )
            manifest = project / ".claude/quality-gate-manifest.json"
            manifest.parent.mkdir(parents=True)
            write_json(
                manifest,
                {"gates": [{"name": "claude-companion-audit-closure"}]},
            )
            env = dict(os.environ, PROJECT_ROOT=str(project))
            result = run(
                [
                    "/bin/bash", str(gate_script),
                    "docs/planning/WO-157-fixture.md",
                    ".vibeos/audit-reports/WO-157-full.md",
                ],
                project,
                env=env,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("receipt_not_closed", result.stdout + result.stderr)

    def test_close_gate_fails_closed_for_misconfigured_profile_or_missing_jq(self):
        gate_script = ROOT / "plugins/vibeos/scripts/validate-independent-audit.sh"
        for case in ("inactive", "missing_jq"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                project = Path(temporary)
                (project / "docs/planning").mkdir(parents=True)
                work_order = project / "docs/planning/WO-157-fixture.md"
                work_order.write_text("# WO-157\n")
                report = project / ".vibeos/audit-reports/WO-157.md"
                report.parent.mkdir(parents=True)
                report.write_text("## Auditor Summary\n\nSecurity and correctness reviewed.\n")
                manifest = project / ".claude/quality-gate-manifest.json"
                manifest.parent.mkdir(parents=True)
                write_json(
                    manifest,
                    {"gates": [{"name": "claude-companion-audit-closure"}]},
                )
                profile = {
                    "active_modules": [] if case == "inactive" else ["claude-companion-audit"],
                    "phase_audit_runtime": "claude",
                }
                write_json(project / ".vibeos/project-profile.json", profile)
                env = dict(os.environ, PROJECT_ROOT=str(project))
                if case == "missing_jq":
                    fake_bin = project / "fake-bin"
                    fake_bin.mkdir()
                    for command in (
                        "basename", "cat", "dirname", "find", "grep", "head",
                        "python3", "sed",
                    ):
                        source = shutil.which(command)
                        self.assertIsNotNone(source)
                        (fake_bin / command).symlink_to(source)
                    env["PATH"] = str(fake_bin)
                result = run(
                    ["/bin/bash", str(gate_script), str(work_order), str(report)],
                    project,
                    env=env,
                )
                self.assertNotEqual(result.returncode, 0)
                expected = "active module" if case == "inactive" else "jq is required"
                self.assertIn(expected, result.stdout + result.stderr)

    def test_claude_proof_hook_protects_companion_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / ".vibeos").mkdir()
            write_json(project / ".vibeos/session-state.json", {"active": True})
            (project / ".vibeos/current-agent.txt").write_text("backend\n")
            receipt = project / ".vibeos/audit-reports/WO-157.json"
            receipt.parent.mkdir()
            receipt.write_text("{}\n")
            payload = {
                "tool_name": "Edit",
                "tool_input": {
                    "file_path": str(receipt),
                    "old_string": "{}",
                    "new_string": '{"closure":"pass"}',
                },
            }
            env = dict(
                os.environ,
                CLAUDE_PROJECT_DIR=str(project),
                VIBEOS_FORCE_HOOKS="1",
            )
            result = run(
                ["bash", str(ROOT / "plugins/vibeos/hooks/scripts/proof-protection.sh")],
                project,
                env=env,
                input=json.dumps(payload),
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            response = json.loads(result.stdout)
            self.assertEqual(
                response["hookSpecificOutput"]["permissionDecision"], "deny"
            )

    def test_work_order_status_edit_does_not_invalidate_stable_acceptance_contract(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            fake = self.fake_claude(project, self.full_result())
            self.assertEqual(self.invoke_full(project, base, fake).returncode, 3)
            self.apply_fix(project)
            work_order = project / "docs/planning/WO-157-fixture.md"
            work_order.write_text(work_order.read_text() + "\nStatus: complete.\n")
            self.commit(project, "record completion status")
            fake = self.fake_claude(project, self.verification_result())
            verified = self.invoke_verification(project, fake)
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)

    def test_provider_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            fake = self.fake_claude(project, self.full_result(), provider="bedrock")
            result = self.invoke_full(project, base, fake)
            self.assertEqual(result.returncode, 2)
            self.assertIn("claude_provider_mismatch", result.stderr)
            self.assertFalse((project / ".vibeos/audit-reports/WO-157-full.json").exists())

    def test_audited_scope_drift_invalidates_closed_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            fake = self.fake_claude(project, self.full_result())
            self.assertEqual(self.invoke_full(project, base, fake).returncode, 3)
            self.apply_fix(project)
            fake = self.fake_claude(project, self.verification_result())
            self.assertEqual(self.invoke_verification(project, fake).returncode, 0)
            ignored = project / "src/__pycache__/app.cpython-314.pyc"
            ignored.parent.mkdir()
            ignored.write_bytes(b"ignored bytecode")
            ignored_result = run(
                [
                    "python3", str(SCRIPT), "validate", "--project-dir", str(project),
                    "--receipt", ".vibeos/audit-reports/WO-157-verification.json",
                ],
                project,
            )
            self.assertEqual(
                ignored_result.returncode, 0, ignored_result.stdout + ignored_result.stderr
            )
            (project / "src/app.py").write_text("def answer():\n    return 43\n")
            result = run(
                [
                    "python3", str(SCRIPT), "validate", "--project-dir", str(project),
                    "--receipt", ".vibeos/audit-reports/WO-157-verification.json",
                ],
                project,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("audited_review_scope_drift_after_audit", result.stderr)

    def test_post_audit_commit_outside_review_roots_invalidates_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = self.fixture(Path(temporary))
            fake = self.fake_claude(project, self.full_result())
            self.assertEqual(self.invoke_full(project, base, fake).returncode, 3)
            self.apply_fix(project)
            fake = self.fake_claude(project, self.verification_result())
            self.assertEqual(self.invoke_verification(project, fake).returncode, 0)
            (project / "src/new_module.py").write_text("value = 1\n")
            self.commit(project, "post-audit out-of-scope change")
            result = run(
                [
                    "python3", str(SCRIPT), "validate", "--project-dir", str(project),
                    "--receipt", ".vibeos/audit-reports/WO-157-verification.json",
                ],
                project,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("post_audit_changes_outside_review_scope", result.stderr)


if __name__ == "__main__":
    unittest.main()
