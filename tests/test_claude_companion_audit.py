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

    def fake_claude(self, project: Path, structured, *, provider="firstParty") -> Path:  # noqa: ANN001
        fake = project.parent / "fake-claude"
        args_out = project.parent / "fake-claude-args.json"
        payload = {
            "is_error": False,
            "structured_output": structured,
            "modelUsage": {
                "claude-fable-5-1": {
                    "canonicalModel": "claude-fable-5-1",
                    "provider": provider,
                    "inputTokens": 100,
                    "outputTokens": 50,
                    "costUSD": 0.2,
                }
            },
        }
        source = f"""#!/usr/bin/env python3
import json
import sys
if sys.argv[1:] == ["auth", "status"]:
    print(json.dumps({{"loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty", "email": "fixture@example.test"}}))
elif sys.argv[1:] == ["--version"]:
    print("fixture-claude 1.0")
else:
    open({str(args_out)!r}, "w", encoding="utf-8").write(json.dumps(sys.argv[1:]))
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
        base = self.commit(project, "base")
        (project / "src").mkdir()
        (project / "tests").mkdir()
        (project / "docs/planning").mkdir(parents=True)
        (project / "src/app.py").write_text("def answer():\n    return 41\n", encoding="utf-8")
        (project / "tests/test_app.py").write_text(
            "from src.app import answer\n\ndef test_answer():\n    assert answer() == 42\n",
            encoding="utf-8",
        )
        wo = project / "docs/planning/WO-157-fixture.md"
        wo.write_text("# WO-157\n\nAcceptance: answer returns 42.\n", encoding="utf-8")
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

    def invoke_full(self, project: Path, base: str, fake: Path):
        return run(
            [
                "python3", str(SCRIPT), "full", "--project-dir", str(project),
                "--work-order", "docs/planning/WO-157-fixture.md",
                "--scope-manifest", "docs/evidence/WO-157/full-scope.json",
                "--base-ref", base, "--candidate-ref", "HEAD",
                "--config", "docs/evidence/WO-157/claude-config.json",
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

    def invoke_verification(self, project: Path, fake: Path):
        return run(
            [
                "python3", str(SCRIPT), "verification", "--project-dir", str(project),
                "--work-order", "docs/planning/WO-157-fixture.md",
                "--scope-manifest", "docs/evidence/WO-157/verify-scope.json",
                "--candidate-ref", "HEAD",
                "--parent-receipt", ".vibeos/audit-reports/WO-157-full.json",
                "--config", "docs/evidence/WO-157/claude-config.json",
                "--claude-bin", str(fake),
                "--out", ".vibeos/audit-reports/WO-157-verification.json",
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
                provider_args[provider_args.index("--model") + 1],
                "claude-fable-5-1",
            )
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


if __name__ == "__main__":
    unittest.main()
