import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_claude_companion_audit import SCRIPT, run, write_json


SPEC = importlib.util.spec_from_file_location("companion_audit_core", SCRIPT)
assert SPEC and SPEC.loader
CORE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CORE
SPEC.loader.exec_module(CORE)


class CompanionSimplificationTests(unittest.TestCase):
    def helper(self):  # noqa: ANN201
        from tests import test_claude_companion_audit as fixtures

        return fixtures.CompanionAuditTests(methodName="runTest")

    def medium_finding(self, *, acceptance=False, disposition="accepted"):
        return {
            "id": "F-001",
            "severity": "medium",
            "title": "Bounded concern",
            "location": "src/app.py:2",
            "evidence": "The supplied behavior has a bounded concern.",
            "recommendation": "Record the chosen treatment.",
            "acceptance_requirement": acceptance,
            "disposition": disposition,
        }

    def test_medium_requires_disposition_and_unmet_acceptance_still_blocks(self):
        accepted = self.medium_finding()
        result = {
            "verdict": "pass",
            "summary": "The medium concern is explicitly accepted.",
            "findings": [accepted],
            "coverage": ["implementation and acceptance contract"],
            "limitations": [],
        }
        CORE.validate_result("full", result, [])
        self.assertEqual(CORE.receipt_closure("full", result)["status"], "pass")

        missing = dict(accepted)
        missing.pop("disposition")
        with self.assertRaisesRegex(CORE.AuditError, "finding_keys_invalid"):
            CORE.validate_result("full", {**result, "findings": [missing]}, [])

        unmet = self.medium_finding(acceptance=True, disposition="accepted")
        with self.assertRaisesRegex(
            CORE.AuditError, "unmet_acceptance_requirement_must_be_fixed"
        ):
            CORE.validate_result("full", {**result, "findings": [unmet]}, [])

    def test_v1_medium_closure_keeps_legacy_blocking_semantics(self):
        legacy = self.medium_finding()
        legacy.pop("acceptance_requirement")
        legacy.pop("disposition")
        result = {
            "verdict": "changes_required",
            "summary": "Legacy medium remains blocking.",
            "findings": [legacy],
            "coverage": [],
            "limitations": [],
        }
        CORE.validate_result("full", result, [], policy_version=1)
        self.assertEqual(
            CORE.receipt_closure("full", result, 1)["blocking_finding_ids"],
            ["F-001"],
        )

    def test_nonmaterial_verification_can_disposition_but_material_must_close(self):
        context = {"F-001": self.medium_finding(disposition="fix")}
        verification = {
            "verdict": "pass",
            "summary": "The concern is explicitly deferred.",
            "finding_checks": [
                {
                    "id": "F-001",
                    "status": "deferred",
                    "evidence": "No acceptance requirement depends on this item.",
                    "note": "Deferred with a recorded rationale.",
                }
            ],
            "new_blockers": [],
            "coverage": ["F-001"],
            "limitations": [],
        }
        CORE.validate_result(
            "verification", verification, ["F-001"], finding_context=context
        )

        context["F-001"]["acceptance_requirement"] = True
        with self.assertRaisesRegex(CORE.AuditError, "material_finding_must_close"):
            CORE.validate_result(
                "verification", verification, ["F-001"], finding_context=context
            )

    def test_new_blocker_continues_as_targeted_verification_with_history(self):
        helper = self.helper()
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = helper.fixture(Path(temporary))
            fake = helper.fake_claude(project, helper.full_result())
            self.assertEqual(helper.invoke_full(project, base, fake).returncode, 3)
            helper.apply_fix(project)

            first = helper.verification_result()
            first["verdict"] = "changes_required"
            first["new_blockers"] = [
                {
                    "id": "F-002",
                    "severity": "high",
                    "title": "Correction regression",
                    "location": "src/app.py:2",
                    "evidence": "The correction exposes a material regression.",
                    "recommendation": "Correct and rerun the focused behavior.",
                    "acceptance_requirement": True,
                    "disposition": "fix",
                }
            ]
            fake = helper.fake_claude(project, first)
            result = helper.invoke_verification(project, fake)
            self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
            first_receipt_path = project / ".vibeos/audit-reports/WO-157-verification.json"
            first_receipt = json.loads(first_receipt_path.read_text())
            self.assertEqual(
                first_receipt["closure"]["next_required"], "targeted_verification"
            )

            (project / "src/app.py").write_text(
                "def answer():\n    return 42  # F-002 corrected\n",
                encoding="utf-8",
            )
            tested = helper.commit(project, "correct F-002")
            tested_tree = helper.git(project, "rev-parse", f"{tested}^{{tree}}")
            evidence = project / "docs/evidence/WO-157/tests-f002.md"
            evidence.write_text(
                "# F-002 tests\n\n"
                f"- Tested implementation commit: `{tested}`\n"
                f"- Tested tree: `{tested_tree}`\n\n1 passed\n",
                encoding="utf-8",
            )
            write_json(
                project / "docs/evidence/WO-157/verify-f002.json",
                {
                    "schema_version": 1,
                    "work_order": "WO-157",
                    "acceptance_contract": [
                        "docs/evidence/WO-157/acceptance-contract.md"
                    ],
                    "review_paths": ["src/app.py", "tests/test_app.py"],
                    "evidence_paths": ["docs/evidence/WO-157/tests-f002.md"],
                    "finding_ids": ["F-002"],
                },
            )
            helper.commit(project, "bind F-002 verification")
            final = {
                **helper.verification_result(),
                "summary": "F-002 is closed.",
                "finding_checks": [
                    {
                        "id": "F-002",
                        "status": "closed",
                        "evidence": "Focused test passes.",
                        "note": "The regression is corrected.",
                    }
                ],
            }
            fake = helper.fake_claude(project, final)
            result = run(
                [
                    "python3", str(SCRIPT), "verification",
                    "--project-dir", str(project),
                    "--work-order", "docs/planning/WO-157-fixture.md",
                    "--scope-manifest", "docs/evidence/WO-157/verify-f002.json",
                    "--candidate-ref", "HEAD",
                    "--parent-receipt", str(first_receipt_path.relative_to(project)),
                    "--config", "docs/evidence/WO-157/claude-config.json",
                    "--allow-unprofiled-project", "--claude-bin", str(fake),
                    "--out", ".vibeos/audit-reports/WO-157-verification-f002.json",
                ],
                project,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            final_receipt = json.loads(
                (project / ".vibeos/audit-reports/WO-157-verification-f002.json").read_text()
            )
            self.assertEqual(len(final_receipt["binding"]["finding_history"]), 2)

    def test_unrelated_worktree_changes_do_not_block_but_reviewed_bytes_do(self):
        helper = self.helper()
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = helper.fixture(Path(temporary))
            (project / "unrelated-notes.md").write_text("parallel notes\n")
            clean = {**helper.full_result(), "verdict": "pass", "findings": []}
            fake = helper.fake_claude(project, clean)
            result = helper.invoke_full(project, base, fake)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            validated = run(
                [
                    "python3", str(SCRIPT), "validate", "--project-dir", str(project),
                    "--receipt", ".vibeos/audit-reports/WO-157-full.json",
                ],
                project,
            )
            self.assertEqual(validated.returncode, 0, validated.stdout + validated.stderr)

            (project / "src/app.py").write_text("def answer():\n    return 99\n")
            invalid = run(
                [
                    "python3", str(SCRIPT), "validate", "--project-dir", str(project),
                    "--receipt", ".vibeos/audit-reports/WO-157-full.json",
                ],
                project,
            )
            self.assertEqual(invalid.returncode, 2)
            self.assertIn("audited_review_scope_drift_after_audit", invalid.stderr)

    def test_v1_receipt_validation_remains_strict_about_config_bytes(self):
        helper = self.helper()
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = helper.fixture(Path(temporary))
            clean = {**helper.full_result(), "verdict": "pass", "findings": []}
            fake = helper.fake_claude(project, clean)
            self.assertEqual(helper.invoke_full(project, base, fake).returncode, 0)
            receipt_path = project / ".vibeos/audit-reports/WO-157-full.json"
            receipt = json.loads(receipt_path.read_text())
            receipt["schema_version"] = 1
            receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")

            config_path = project / "docs/evidence/WO-157/claude-config.json"
            config = json.loads(config_path.read_text())
            config["max_turns"] = 6
            write_json(config_path, config)
            helper.commit(project, "prospective config change")
            validated = run(
                [
                    "python3", str(SCRIPT), "validate", "--project-dir", str(project),
                    "--receipt", str(receipt_path.relative_to(project)),
                ],
                project,
            )
            self.assertEqual(validated.returncode, 2)
            self.assertIn("audit_config_drift_after_audit", validated.stderr)

    def test_v2_profile_allows_prospective_limits_but_not_module_disable(self):
        helper = self.helper()
        with tempfile.TemporaryDirectory() as temporary:
            project, base, _candidate = helper.fixture(Path(temporary))
            config = json.loads(
                (project / "docs/evidence/WO-157/claude-config.json").read_text()
            )
            write_json(
                project / ".vibeos/project-profile.json",
                {
                    "active_modules": ["claude-companion-audit"],
                    "phase_audit_runtime": "claude",
                    "claude_companion_audit": config,
                },
            )
            work_order = project / "docs/planning/WO-157-fixture.md"
            work_order.write_text(
                work_order.read_text().replace(
                    "  - src/**\n", "  - src/**\n  - .vibeos/**\n"
                )
            )
            scope_path = project / "docs/evidence/WO-157/full-scope.json"
            scope = json.loads(scope_path.read_text())
            scope["evidence_paths"].append(
                "docs/evidence/WO-157/claude-config.json"
            )
            write_json(scope_path, scope)
            helper.bind_current_implementation(project, "bind profile candidate")
            clean = {**helper.full_result(), "verdict": "pass", "findings": []}
            fake = helper.fake_claude(project, clean)
            result = run(
                [
                    "python3", str(SCRIPT), "full", "--project-dir", str(project),
                    "--work-order", "docs/planning/WO-157-fixture.md",
                    "--scope-manifest", "docs/evidence/WO-157/full-scope.json",
                    "--candidate-ref", "HEAD", "--claude-bin", str(fake),
                    "--out", ".vibeos/audit-reports/WO-157-full.json",
                ],
                project,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

            profile_path = project / ".vibeos/project-profile.json"
            profile = json.loads(profile_path.read_text())
            profile["claude_companion_audit"]["max_turns"] = 6
            profile["operator_note"] = "prospective setting"
            write_json(profile_path, profile)
            helper.commit(project, "adjust prospective audit limits")
            valid = run(
                [
                    "python3", str(SCRIPT), "validate", "--project-dir", str(project),
                    "--receipt", ".vibeos/audit-reports/WO-157-full.json",
                ],
                project,
            )
            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)

            profile["active_modules"] = []
            write_json(profile_path, profile)
            helper.commit(project, "disable companion module")
            disabled = run(
                [
                    "python3", str(SCRIPT), "validate", "--project-dir", str(project),
                    "--receipt", ".vibeos/audit-reports/WO-157-full.json",
                ],
                project,
            )
            self.assertEqual(disabled.returncode, 2)
            self.assertIn("module_not_active_in_project_profile", disabled.stderr)


if __name__ == "__main__":
    unittest.main()
