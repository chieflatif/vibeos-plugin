from __future__ import annotations

import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from tests.test_claude_companion_audit import SCRIPT, run, write_json


def canonical(value) -> bytes:  # noqa: ANN001
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


class CompanionFallbackIntegrationTests(unittest.TestCase):
    def fixtures(self):  # noqa: ANN201
        from tests import test_claude_companion_audit as module

        return module.CompanionAuditTests(methodName="runTest")

    def command(self, project: Path, *, extra=None, out="WO-157-full.json"):
        return [
            "python3", str(SCRIPT), "full", "--project-dir", str(project),
            "--work-order", "docs/planning/WO-157-fixture.md",
            "--scope-manifest", "docs/evidence/WO-157/full-scope.json",
            "--candidate-ref", "HEAD",
            "--config", "docs/evidence/WO-157/claude-config.json",
            "--allow-unprofiled-project",
            "--out", f".vibeos/audit-reports/{out}",
            *(extra or []),
        ]

    def fake_codex(self, directory: Path, result: dict):
        binary = directory / "fake-codex"
        args_path = directory / "fake-codex-args.json"
        final = json.dumps(result, sort_keys=True, separators=(",", ":"))
        source = f'''#!/usr/bin/env python3
import json
import pathlib
import sys
if sys.argv[1:] == ["--version"]:
    print("codex-cli 0.147.0 fixture")
    raise SystemExit(0)
pathlib.Path({str(args_path)!r}).write_text(json.dumps(sys.argv[1:]))
args = sys.argv[1:]
pathlib.Path(args[args.index("--output-last-message") + 1]).write_text({final!r})
events = [
    {{"type": "thread.started", "thread_id": "fresh-fallback-thread"}},
    {{"type": "turn.started"}},
    {{"type": "item.completed", "item": {{"id": "message-1", "type": "agent_message", "text": {final!r}}}}},
    {{"type": "turn.completed", "usage": {{"input_tokens": 20, "output_tokens": 10}}}},
]
for event in events:
    print(json.dumps(event, separators=(",", ":")))
'''
        binary.write_text(source)
        binary.chmod(0o755)
        return binary, args_path

    def approval(self, failure: dict) -> dict:
        return {
            "schema_version": 1,
            "receipt_type": "vibeos.approved-same-model-codex-review",
            "approval_id": "approval-fixture",
            "recorded_at": "2026-09-20T21:00:00Z",
            "recorded_approver": "Latif",
            "source_ref": "test-fixture:explicit-approval",
            "authenticity": "operator_record_not_cryptographically_verified",
            "decision": "approve_same_model_fallback",
            "binding": copy.deepcopy(failure["binding"]),
            "claude_failure_id": failure["failure_id"],
            "claude_failure_sha256": hashlib.sha256(canonical(failure)).hexdigest(),
        }

    def produce_failure(self, project: Path, helper):  # noqa: ANN001, ANN201
        unavailable = helper.fake_claude(
            project, helper.full_result(), authenticated=False
        )
        result = run(
            self.command(
                project,
                extra=[
                    "--claude-bin", str(unavailable),
                    "--implementer-model", "gpt-5.6-sol",
                ],
            ),
            project,
        )
        self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
        choice = json.loads(result.stdout)
        self.assertEqual(choice["status"], "operator_choice_required")
        self.assertFalse(choice["automatic_fallback"])
        failure_path = project / choice["claude_failure"]
        return failure_path, json.loads(failure_path.read_text())

    def test_operational_failure_requires_choice_then_approved_fallback_closes(self):
        helper = self.fixtures()
        with tempfile.TemporaryDirectory() as temporary:
            project, _base, candidate = helper.fixture(Path(temporary))
            failure_path, failure = self.produce_failure(project, helper)
            self.assertFalse(
                (project / ".vibeos/audit-reports/WO-157-full.json").exists()
            )
            approval_path = project / ".vibeos/audit-reports/approval.json"
            write_json(approval_path, self.approval(failure))
            clean = {**helper.full_result(), "verdict": "pass", "findings": []}
            codex, args_path = self.fake_codex(Path(temporary), clean)
            completed = run(
                self.command(
                    project,
                    extra=[
                        "--implementer-model", "gpt-5.6-sol",
                        "--approved-fallback", str(approval_path.relative_to(project)),
                        "--claude-failure", str(failure_path.relative_to(project)),
                        "--codex-bin", str(codex),
                    ],
                ),
                project,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            receipt_path = project / ".vibeos/audit-reports/WO-157-full.json"
            receipt = json.loads(receipt_path.read_text())
            self.assertEqual(receipt["receipt_type"], "vibeos.independent-companion-audit")
            self.assertEqual(
                receipt["auditor"]["route"],
                "approved_same_model_codex_fallback",
            )
            self.assertEqual(receipt["auditor"]["requested_model"], "gpt-5.6-sol")
            self.assertIsNone(receipt["auditor"]["observed_model"])
            self.assertIsNone(receipt["auditor"]["observed_provider"])
            args = json.loads(args_path.read_text())
            self.assertIn("--ephemeral", args)
            self.assertNotIn("resume", args)
            helper.git(project, "tag", "fallback-candidate", candidate)
            valid = run(
                [
                    "python3", str(SCRIPT), "validate", "--project-dir", str(project),
                    "--receipt", str(receipt_path.relative_to(project)),
                    "--release-ref", "fallback-candidate",
                ],
                project,
            )
            self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)

    def test_fallback_full_receipt_can_parent_claude_verification(self):
        helper = self.fixtures()
        with tempfile.TemporaryDirectory() as temporary:
            project, _base, _candidate = helper.fixture(Path(temporary))
            failure_path, failure = self.produce_failure(project, helper)
            approval_path = project / ".vibeos/audit-reports/approval.json"
            write_json(approval_path, self.approval(failure))
            codex, _args_path = self.fake_codex(Path(temporary), helper.full_result())
            full = run(
                self.command(
                    project,
                    extra=[
                        "--implementer-model", "gpt-5.6-sol",
                        "--approved-fallback", str(approval_path.relative_to(project)),
                        "--claude-failure", str(failure_path.relative_to(project)),
                        "--codex-bin", str(codex),
                    ],
                ),
                project,
            )
            self.assertEqual(full.returncode, 3, full.stdout + full.stderr)
            helper.apply_fix(project)
            claude = helper.fake_claude(project, helper.verification_result())
            verified = helper.invoke_verification(project, claude)
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)

    def test_tampered_approval_is_rejected_before_codex(self):
        helper = self.fixtures()
        with tempfile.TemporaryDirectory() as temporary:
            project, _base, _candidate = helper.fixture(Path(temporary))
            failure_path, failure = self.produce_failure(project, helper)
            approval = self.approval(failure)
            approval["binding"]["candidate_commit"] = "9" * 40
            approval_path = project / ".vibeos/audit-reports/approval.json"
            write_json(approval_path, approval)
            codex, args_path = self.fake_codex(Path(temporary), helper.full_result())
            rejected = run(
                self.command(
                    project,
                    extra=[
                        "--implementer-model", "gpt-5.6-sol",
                        "--approved-fallback", str(approval_path.relative_to(project)),
                        "--claude-failure", str(failure_path.relative_to(project)),
                        "--codex-bin", str(codex),
                    ],
                ),
                project,
            )
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("approval_binding_mismatch", rejected.stderr)
            self.assertFalse(args_path.exists())


if __name__ == "__main__":
    unittest.main()
