from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "plugins/vibeos/scripts/approved-codex-review.py"
SPEC = importlib.util.spec_from_file_location("approved_codex_review", MODULE_PATH)
approved_codex_review = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(approved_codex_review)


def canonical(value) -> bytes:  # noqa: ANN001
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class ApprovedCodexReviewTests(unittest.TestCase):
    def binding(self, prompt="frozen packet") -> dict[str, str]:
        return {
            "work_order": "WO-158",
            "mode": "full",
            "candidate_commit": "1" * 40,
            "candidate_tree": "2" * 40,
            "prompt_sha256": sha256(prompt.encode()),
            "implementer_model_requested": "gpt-5.6-sol",
        }

    def records(self, binding=None):  # noqa: ANN001
        binding = copy.deepcopy(binding or self.binding())
        failure = {
            "schema_version": 1,
            "receipt_type": "vibeos.claude-operational-failure",
            "failure_id": "claude-failure-fixture",
            "created_at": "2026-09-20T20:00:00Z",
            "stage": "claude_operational",
            "reason_code": "claude_not_authenticated",
            "binding": copy.deepcopy(binding),
        }
        approval = {
            "schema_version": 1,
            "receipt_type": "vibeos.approved-same-model-codex-review",
            "approval_id": "approval-fixture",
            "recorded_at": "2026-09-20T20:01:00Z",
            "recorded_approver": "Latif",
            "source_ref": "current-task:user-approval-turn",
            "authenticity": "operator_record_not_cryptographically_verified",
            "decision": "approve_same_model_fallback",
            "binding": copy.deepcopy(binding),
            "claude_failure_id": failure["failure_id"],
            "claude_failure_sha256": sha256(canonical(failure)),
        }
        return approval, failure

    def fake_codex(self, directory: Path, mode="valid") -> tuple[Path, Path]:
        fake = directory / "fake-codex"
        args_path = directory / "codex-args.json"
        result = {"verdict": "pass", "summary": "bounded review passed"}
        final = json.dumps(result, sort_keys=True, separators=(",", ":"))
        events = [
            {"type": "thread.started", "thread_id": "fresh-thread-fixture"},
            {"type": "turn.started"},
            {
                "type": "item.completed",
                "item": {"id": "item-1", "type": "agent_message", "text": final},
            },
            {
                "type": "turn.completed",
                "usage": {"input_tokens": 10, "output_tokens": 5},
            },
        ]
        if mode == "duplicate":
            events.insert(1, copy.deepcopy(events[0]))
        elif mode == "malformed":
            events = ["NOT-JSON"]
        elif mode == "tool":
            events.insert(
                2,
                {
                    "type": "item.completed",
                    "item": {"id": "tool-1", "type": "command_execution", "command": "pwd"},
                },
            )
        source = f'''#!/usr/bin/env python3
import json
import pathlib
import sys
if sys.argv[1:] == ["--version"]:
    print("codex-cli 0.147.0 fixture")
    raise SystemExit(0)
pathlib.Path({str(args_path)!r}).write_text(json.dumps(sys.argv[1:]))
args = sys.argv[1:]
final_path = pathlib.Path(args[args.index("--output-last-message") + 1])
final_path.write_text({final!r})
events = {events!r}
if {mode!r} == "malformed":
    print("NOT-JSON")
else:
    for event in events:
        print(json.dumps(event, separators=(",", ":")))
'''
        fake.write_text(source)
        fake.chmod(0o755)
        return fake, args_path

    def schema(self):
        return {
            "type": "object",
            "properties": {
                "verdict": {"type": "string"},
                "summary": {"type": "string"},
            },
            "required": ["verdict", "summary"],
            "additionalProperties": False,
        }

    def test_valid_review_returns_revalidatable_honest_bundle(self):
        prompt = "frozen packet"
        binding = self.binding(prompt)
        approval, failure = self.records(binding)
        authorization = approved_codex_review.validate_approval(
            approval, failure, binding
        )
        with tempfile.TemporaryDirectory() as temporary:
            fake, args_path = self.fake_codex(Path(temporary))
            bundle = approved_codex_review.run_review(
                prompt, self.schema(), authorization, binary=str(fake), timeout=30
            )
            args = json.loads(args_path.read_text())
        self.assertEqual(args[0:2], ["exec", "-"])
        self.assertIn("--ephemeral", args)
        self.assertIn("--ignore-user-config", args)
        self.assertNotIn("--ignore-rules", args)
        self.assertEqual(args[args.index("--sandbox") + 1], "read-only")
        self.assertEqual(args[args.index("--model") + 1], "gpt-5.6-sol")
        self.assertEqual(
            args[args.index("--config") + 1], 'model_reasoning_effort="high"'
        )
        self.assertNotIn("resume", args)
        self.assertIsNone(bundle["transport"]["observed_model"])
        self.assertIsNone(bundle["transport"]["observed_provider"])
        self.assertEqual(
            approved_codex_review.validate_evidence(bundle, binding),
            bundle["result"],
        )

    def test_missing_or_tampered_approval_is_rejected(self):
        binding = self.binding()
        approval, failure = self.records(binding)
        cases = []
        cases.append(("missing", {}, failure, binding))
        for name, field, value in (
            ("candidate", "candidate_commit", "3" * 40),
            ("model", "implementer_model_requested", "gpt-5.6-terra"),
            ("mode", "mode", "verification"),
        ):
            changed = copy.deepcopy(approval)
            changed["binding"][field] = value
            cases.append((name, changed, failure, binding))
        changed_failure = copy.deepcopy(failure)
        changed_failure["reason_code"] = "claude_audit_timed_out"
        cases.append(("failure", approval, changed_failure, binding))
        for name, candidate_approval, candidate_failure, candidate_binding in cases:
            with self.subTest(name=name), self.assertRaises(
                approved_codex_review.ReviewError
            ):
                approved_codex_review.validate_approval(
                    candidate_approval, candidate_failure, candidate_binding
                )

    def test_prompt_must_match_approved_binding_before_cli(self):
        binding = self.binding("frozen packet")
        approval, failure = self.records(binding)
        authorization = approved_codex_review.validate_approval(
            approval, failure, binding
        )
        with tempfile.TemporaryDirectory() as temporary:
            fake, args_path = self.fake_codex(Path(temporary))
            with self.assertRaisesRegex(
                approved_codex_review.ReviewError, "prompt_binding_mismatch"
            ):
                approved_codex_review.run_review(
                    "different packet", self.schema(), authorization,
                    binary=str(fake), timeout=30,
                )
            self.assertFalse(args_path.exists())

    def test_malformed_duplicate_or_tool_lifecycle_is_rejected(self):
        binding = self.binding()
        approval, failure = self.records(binding)
        authorization = approved_codex_review.validate_approval(
            approval, failure, binding
        )
        expected = {
            "malformed": "codex_output_not_json",
            "duplicate": "codex_lifecycle_count_invalid",
            "tool": "codex_tool_or_unknown_item_observed",
        }
        for mode, error in expected.items():
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                fake, _args_path = self.fake_codex(Path(temporary), mode)
                with self.assertRaisesRegex(
                    approved_codex_review.ReviewError, error
                ):
                    approved_codex_review.run_review(
                        "frozen packet", self.schema(), authorization,
                        binary=str(fake), timeout=30,
                    )

    def test_persisted_event_or_result_tampering_is_rejected(self):
        binding = self.binding()
        approval, failure = self.records(binding)
        authorization = approved_codex_review.validate_approval(
            approval, failure, binding
        )
        with tempfile.TemporaryDirectory() as temporary:
            fake, _args_path = self.fake_codex(Path(temporary))
            bundle = approved_codex_review.run_review(
                "frozen packet", self.schema(), authorization,
                binary=str(fake), timeout=30,
            )
        changed = copy.deepcopy(bundle)
        changed["result"]["summary"] = "edited"
        with self.assertRaisesRegex(
            approved_codex_review.ReviewError, "evidence_result_mismatch"
        ):
            approved_codex_review.validate_evidence(changed, binding)
        changed = copy.deepcopy(bundle)
        changed["raw_events"] += "\n"
        with self.assertRaisesRegex(
            approved_codex_review.ReviewError, "evidence_output_hash_mismatch"
        ):
            approved_codex_review.validate_evidence(changed, binding)


if __name__ == "__main__":
    unittest.main()
