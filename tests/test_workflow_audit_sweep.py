import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
WORKFLOW = REPO / ".claude/workflows/vibeos-audit-sweep"
MODULE_PATH = REPO / "plugins/vibeos/scripts/workflow-audit-sweep-evidence.py"
SPEC = importlib.util.spec_from_file_location("workflow_audit_sweep_evidence", MODULE_PATH)
workflow_evidence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(workflow_evidence)


class WorkflowAuditSweepTests(unittest.TestCase):
    def test_saved_workflow_expresses_bounded_twelve_auditor_sweep(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        markers = workflow_evidence.marker_map(text)
        auditors = workflow_evidence.csv_marker(markers["VIBEOS_WORKFLOW_AUDITORS"])

        self.assertTrue(text.startswith("const meta ="))
        self.assertEqual(markers["VIBEOS_WORKFLOW_ID"], "vibeos-audit-sweep")
        self.assertEqual(len(auditors), 12)
        self.assertIn("security-auditor", auditors)
        self.assertIn("contract-validator", auditors)
        self.assertEqual(
            markers["VIBEOS_WORKFLOW_DEFAULT_TARGET"],
            "plugins/vibeos/scripts/runtime-capabilities.py",
        )
        self.assertIn("bounded-live-run-required", markers["VIBEOS_WORKFLOW_STATUS"])
        self.assertIn("typeof args", text)
        self.assertNotIn("require(\"fs\")", text)
        self.assertNotIn("child_process", text)

    def test_static_report_defers_without_live_workflow_evidence(self):
        report = workflow_evidence.build_report(
            root=REPO,
            workflow_path=WORKFLOW,
            target="plugins/vibeos/scripts/runtime-capabilities.py",
            baseline_path=None,
            live_output=None,
            live_stderr=None,
            generated_at="2026-06-15T00:00:00Z",
        )

        self.assertEqual(report["summary"]["status"], "pass")
        self.assertTrue(report["static_workflow_checks"]["meta_first_statement_ok"])
        self.assertEqual(report["static_workflow_checks"]["auditor_count"], 12)
        self.assertEqual(report["subagent_path_baseline"]["execution_status"], "source_derived_not_live")
        self.assertEqual(report["live_workflow_run"]["status"], "not_run")
        self.assertEqual(report["adoption_verdict"], "DEFER_LIVE_WORKFLOW_NOT_RUN")
        self.assertEqual(
            report["comparison"]["token_or_cost_comparison_status"],
            "pending_baseline_or_workflow_token_evidence",
        )

    def test_live_output_cost_is_compared_when_present(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            output = root / "claude-output.json"
            stderr = root / "claude-stderr.txt"
            baseline = root / "baseline.json"
            output.write_text(
                json.dumps(
                    {
                        "type": "result",
                        "subtype": "success",
                        "num_turns": 1,
                        "total_cost_usd": 0.12,
                        "result": "bounded workflow returned",
                    }
                ),
                encoding="utf-8",
            )
            stderr.write_text("", encoding="utf-8")
            baseline.write_text(
                json.dumps(
                    {
                        "auditors": workflow_evidence.csv_marker(
                            workflow_evidence.marker_map(WORKFLOW.read_text(encoding="utf-8"))[
                                "VIBEOS_WORKFLOW_AUDITORS"
                            ]
                        ),
                        "findings": {"count": 0},
                        "cost": {"total_cost_usd": 0.08},
                    }
                ),
                encoding="utf-8",
            )

            report = workflow_evidence.build_report(
                root=REPO,
                workflow_path=WORKFLOW,
                target="plugins/vibeos/scripts/runtime-capabilities.py",
                baseline_path=baseline,
                live_output=output,
                live_stderr=stderr,
                generated_at="2026-06-15T00:00:00Z",
            )

        self.assertEqual(report["live_workflow_run"]["status"], "completed_or_returned")
        self.assertEqual(report["comparison"]["workflow_total_cost_usd"], 0.12)
        self.assertEqual(report["comparison"]["baseline_total_cost_usd"], 0.08)
        self.assertEqual(report["comparison"]["token_or_cost_comparison_status"], "available")

    def test_workflow_permission_denial_defers_review_gate(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            output = root / "claude-output.json"
            output.write_text(
                json.dumps(
                    {
                        "type": "result",
                        "subtype": "success",
                        "num_turns": 2,
                        "total_cost_usd": 0.05,
                        "result": "Review dynamic workflow before running. The workflow did not launch.",
                        "permission_denials": [{"tool_name": "Workflow"}],
                    }
                ),
                encoding="utf-8",
            )

            report = workflow_evidence.build_report(
                root=REPO,
                workflow_path=WORKFLOW,
                target="plugins/vibeos/scripts/runtime-capabilities.py",
                baseline_path=None,
                live_output=output,
                live_stderr=None,
                generated_at="2026-06-15T00:00:00Z",
            )

        self.assertEqual(report["live_workflow_run"]["status"], "blocked_review_gate")
        self.assertTrue(report["live_workflow_run"]["workflow_permission_denied"])
        self.assertEqual(report["adoption_verdict"], "DEFER_WORKFLOW_REVIEW_GATE_NOT_APPROVED")

    def test_budget_limited_run_defers_adoption(self):
        with tempfile.TemporaryDirectory() as tempdir:
            root = Path(tempdir)
            output = root / "claude-output.json"
            output.write_text(
                json.dumps(
                    {
                        "type": "result",
                        "subtype": "error_max_budget_usd",
                        "is_error": True,
                        "num_turns": 4,
                        "total_cost_usd": 0.18,
                        "permission_denials": [],
                        "errors": ["Reached maximum budget ($0.15)"],
                    }
                ),
                encoding="utf-8",
            )

            report = workflow_evidence.build_report(
                root=REPO,
                workflow_path=WORKFLOW,
                target="plugins/vibeos/scripts/runtime-capabilities.py",
                baseline_path=None,
                live_output=output,
                live_stderr=None,
                generated_at="2026-06-15T00:00:00Z",
            )

        self.assertEqual(report["live_workflow_run"]["status"], "budget_limited")
        self.assertEqual(report["adoption_verdict"], "DEFER_LIVE_WORKFLOW_BUDGET_LIMIT")


if __name__ == "__main__":
    unittest.main()
