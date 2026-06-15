import json
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
BUNDLE = REPO / "docs/evidence/vnext/wo-126-agent-team-pilot"
LANES = BUNDLE / "lane-packets"
KIT = BUNDLE / "team-arm-kit"
WO_DOC = REPO / "docs/planning/WO-126-agent-team-pilot-execution.md"
WO125_EVIDENCE_MODEL = REPO / "docs/evidence/vnext/wo-125-agent-team-pilot/evidence-model.json"

ALLOWED_VERDICTS = {"NO_GO", "FALLBACK_TO_SUBAGENTS", "PARTIAL_UNLOCK_CANDIDATE"}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class WO126EvidenceBundleTests(unittest.TestCase):
    def test_required_bundle_artifacts_present(self):
        # The WO-125 evidence model defines the required WO-126 bundle. Every
        # required artifact (resolving the lane-packets/*.json glob) must exist.
        required = load(WO125_EVIDENCE_MODEL)["required_evidence_bundle"]
        for artifact in required:
            if artifact.endswith("/*.json"):
                subdir = BUNDLE / artifact.split("/*.json")[0]
                self.assertTrue(subdir.is_dir(), f"missing dir for {artifact}")
                self.assertTrue(list(subdir.glob("*.json")), f"no json under {artifact}")
            else:
                self.assertTrue((BUNDLE / artifact).exists(), f"missing artifact {artifact}")

    def test_pilot_summary_verdict_and_no_overclaim(self):
        summary = load(BUNDLE / "pilot-summary.json")
        self.assertEqual(summary["wo"], "WO-126")
        self.assertIn(summary["verdict"], ALLOWED_VERDICTS)
        self.assertEqual(summary["verdict"], "FALLBACK_TO_SUBAGENTS")
        self.assertFalse(summary["agent_teams_actually_ran"])
        self.assertTrue(summary["fallback_reason_recorded_before_completion"])
        # The four blocked claims must be explicitly honored.
        honored = " ".join(summary["blocked_claims_honored"]).lower()
        for phrase in ["production", "default", "parity", "autonomy"]:
            self.assertIn(phrase, honored)
        # All five go/no-go criteria are scored for the subagent arm.
        crit = summary["subagent_arm_results"]["criteria"]
        for key in [
            "stall_detection_latency",
            "pre_merge_defects_caught",
            "coordinator_labor_vs_sequential",
            "scope_safety",
            "cost_posture",
        ]:
            self.assertIn(key, crit)

    def test_runtime_pin_records_desktop_surface_without_teams(self):
        pin = load(BUNDLE / "runtime-pin.json")
        self.assertEqual(pin["wo"], "WO-126")
        self.assertEqual(pin["executing_session"]["surface"], "claude-desktop")
        self.assertFalse(pin["executing_session"]["agent_teams_available_here"])
        self.assertEqual(pin["executing_session"]["agent_teams_env_value"], "UNSET")
        self.assertFalse(pin["pilot_flag"]["git_tracked"])

    def test_comparison_model_marks_stall_detection_team_only(self):
        model = load(BUNDLE / "comparison-model.json")
        crit = {c["id"]: c for c in model["criteria"]}
        self.assertEqual(set(crit), {
            "stall_detection_latency",
            "pre_merge_defects_caught",
            "coordinator_labor_vs_sequential",
            "scope_safety",
            "cost_posture",
        })
        # Stall detection is structurally unmeasurable in the subagent arm.
        self.assertFalse(crit["stall_detection_latency"]["subagents_measurable"])
        self.assertTrue(crit["stall_detection_latency"]["teams_measurable"])
        self.assertEqual(model["decision_logic"]["this_session_verdict"], "FALLBACK_TO_SUBAGENTS")

    def test_input_lane_packets_disjoint_and_wo_cited(self):
        a = load(LANES / "lane-a-wo127.json")
        b = load(LANES / "lane-b-wo128.json")
        self.assertEqual(a["governing_wo"], "WO-126")
        self.assertEqual(b["governing_wo"], "WO-126")
        self.assertEqual(a["lane_target_wo"], "WO-127")
        self.assertEqual(b["lane_target_wo"], "WO-128")
        # Disjoint write scope — no same-file contention between lanes.
        self.assertEqual(
            set(a["allowed_write_paths"]).intersection(b["allowed_write_paths"]),
            set(),
        )

    def test_return_packets_complete_and_in_scope(self):
        for packet_name, target, allowed in [
            ("lane-a-wo127-return.json", "WO-127", "lane-a-wo127.json"),
            ("lane-b-wo128-return.json", "WO-128", "lane-b-wo128.json"),
        ]:
            ret = load(LANES / packet_name)
            inp = load(LANES / allowed)
            self.assertEqual(ret["status"], "COMPLETE", packet_name)
            self.assertEqual(ret["lane_target_wo"], target)
            sc = ret["scope_compliance"]
            self.assertFalse(sc["prohibited_touched"], packet_name)
            self.assertEqual(
                set(sc["paths_written"]),
                set(inp["allowed_write_paths"]),
                f"{packet_name} wrote outside its allowed path",
            )

    def test_defect_ledger_records_pre_merge_catch(self):
        ledger = load(BUNDLE / "defect-ledger.json")
        arm = ledger["subagent_arm"]
        self.assertTrue(arm["caught_before_merge"])
        self.assertGreaterEqual(arm["total_defects"], 1)
        self.assertEqual(arm["total_defects"], len(arm["defects"]))
        # At least one material (major) defect was caught pre-merge.
        self.assertTrue(any(d["severity"] == "major" for d in arm["defects"]))

    def test_team_arm_kit_is_self_contained(self):
        self.assertTrue((KIT / "README.md").exists())
        self.assertTrue((KIT / "WO-126-TEAM-PILOT-BRIEF.md").exists())
        self.assertTrue((KIT / "lane-packets" / "lane-a-wo127.json").exists())
        self.assertTrue((KIT / "lane-packets" / "lane-b-wo128.json").exists())
        tmpl = load(KIT / "evidence-template" / "pilot-summary.json")
        self.assertEqual(set(tmpl["allowed_verdicts"]), ALLOWED_VERDICTS)

    def test_wo_doc_frontmatter_and_fallback_recorded(self):
        text = WO_DOC.read_text(encoding="utf-8")
        self.assertIn("wo_class: planning", text)
        self.assertIn("status: In Progress", text)
        self.assertIn("FALLBACK_TO_SUBAGENTS", text)
        self.assertIn("Lane Scope Reduction", text)
        # Disjoint lanes and exactly-two-teammate constraint are documented.
        self.assertIn("exactly 2", text)


if __name__ == "__main__":
    unittest.main()
