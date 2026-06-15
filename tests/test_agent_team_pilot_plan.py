import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
DESIGN_DOC = REPO / "docs/planning/AGENT-TEAM-PILOT-DESIGN.md"
WO_DOC = REPO / "docs/planning/WO-125-agent-team-pilot-plan-evidence-model.md"
EVIDENCE_MODEL = REPO / "docs/evidence/vnext/wo-125-agent-team-pilot/evidence-model.json"
RUNTIME_PIN = REPO / "docs/evidence/vnext/wo-125-agent-team-pilot/runtime-pin.json"


class AgentTeamPilotPlanTests(unittest.TestCase):
    def test_design_doc_records_non_default_experimental_posture(self):
        text = DESIGN_DOC.read_text(encoding="utf-8")

        self.assertIn("experimental", text)
        self.assertIn("disabled by default", text)
        self.assertIn("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS", text)
        self.assertIn("2.1.32", text)
        self.assertIn("FALLBACK_TO_SUBAGENTS", text)
        self.assertIn("must not claim production readiness", text)

    def test_evidence_model_defines_required_go_no_go_criteria(self):
        model = json.loads(EVIDENCE_MODEL.read_text(encoding="utf-8"))
        criteria = {item["id"]: item for item in model["go_no_go_criteria"]}

        for key in [
            "stall_detection_latency",
            "pre_merge_defects_caught",
            "coordinator_labor_vs_sequential",
            "scope_safety",
            "cost_posture",
        ]:
            self.assertIn(key, criteria)
            self.assertTrue(criteria[key]["partial_unlock_target"])
            self.assertTrue(criteria[key]["no_go_condition"])
            self.assertTrue(criteria[key]["evidence"])

        self.assertIn("5 minutes p95", criteria["stall_detection_latency"]["partial_unlock_target"])
        self.assertIn("80 percent", criteria["coordinator_labor_vs_sequential"]["partial_unlock_target"])
        self.assertFalse(model["pilot_scope"]["default_adoption_allowed"])

    def test_evidence_model_requires_wo_126_artifacts_and_allowed_verdicts(self):
        model = json.loads(EVIDENCE_MODEL.read_text(encoding="utf-8"))
        required = set(model["required_evidence_bundle"])

        for artifact in [
            "runtime-pin.json",
            "task-list-start.json",
            "task-list-end.json",
            "team-governance-events.jsonl",
            "lane-packets/*.json",
            "cost-report.json",
            "defect-ledger.json",
            "coordinator-labor.json",
            "pilot-summary.json",
        ]:
            self.assertIn(artifact, required)

        self.assertEqual(
            set(model["allowed_verdicts"]),
            {"NO_GO", "FALLBACK_TO_SUBAGENTS", "PARTIAL_UNLOCK_CANDIDATE"},
        )
        self.assertIn("default agent-team adoption", model["blocked_claims"])

    def test_runtime_pin_records_local_capability_without_live_execution_claim(self):
        pin = json.loads(RUNTIME_PIN.read_text(encoding="utf-8"))

        self.assertEqual(pin["wo"], "WO-125")
        self.assertEqual(pin["claude_version"], "2.1.177")
        self.assertEqual(pin["agent_team_opt_in_env"], "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1")
        self.assertEqual(pin["agent_teams_status_with_opt_in"], "experimental_available")
        self.assertIn("not live agent-team execution proof", " ".join(pin["limitations"]))

    def test_wo_contract_marks_planning_only_scope(self):
        text = WO_DOC.read_text(encoding="utf-8")

        self.assertIn("status: Complete", text)
        self.assertIn("wo_class: planning", text)
        self.assertIn("Running an agent team", text)
        self.assertIn("Website changes", text)


if __name__ == "__main__":
    unittest.main()
