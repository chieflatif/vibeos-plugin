import importlib.util
import os
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "plugins/vibeos/scripts/runtime-capabilities.py"
SPEC = importlib.util.spec_from_file_location("runtime_capabilities", MODULE_PATH)
runtime_capabilities = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runtime_capabilities)


class RuntimeCapabilityTests(unittest.TestCase):
    def test_parse_codex_version(self):
        self.assertEqual(runtime_capabilities.parse_codex_version("codex-cli 0.125.0"), "0.125.0")

    def test_parse_codex_features_handles_multi_word_stage(self):
        output = """
multi_agent                         stable             true
multi_agent_v2                      under development  false
codex_hooks                         stable             true
plugins                             stable             true
"""
        features = runtime_capabilities.parse_codex_features(output)
        self.assertTrue(features["multi_agent"]["enabled"])
        self.assertEqual(features["multi_agent_v2"]["stage"], "under development")
        self.assertFalse(features["multi_agent_v2"]["enabled"])
        self.assertTrue(features["codex_hooks"]["enabled"])

    def test_parse_claude_agents(self):
        output = """
18 active agents

Plugin agents:
  vibeos:backend · sonnet
  vibeos:security-auditor · sonnet

Built-in agents:
  general-purpose · inherit
"""
        parsed = runtime_capabilities.parse_claude_agents(output)
        self.assertEqual(parsed["active_count"], 18)
        self.assertIn("vibeos:backend", parsed["vibeos_agents"])
        self.assertIn("general-purpose", parsed["agents"])

    def test_recommend_strategy_prefers_codex_multi_agent(self):
        codex = {"capabilities": {"subagents": "available", "hooks": "available"}}
        claude = {"capabilities": {"subagents": "available", "hooks": "available"}}
        strategy = runtime_capabilities.recommend_strategy(codex, claude)
        self.assertEqual(strategy["recommended_primary"], "codex")
        self.assertEqual(strategy["orchestration_mode"], "codex-multi-agent")
        self.assertTrue(strategy["requires_git_hooks"])

    def test_recommend_strategy_falls_back_to_claude(self):
        codex = {"capabilities": {"subagents": "unavailable", "hooks": "unavailable"}}
        claude = {"capabilities": {"subagents": "available", "hooks": "available"}}
        strategy = runtime_capabilities.recommend_strategy(codex, claude)
        self.assertEqual(strategy["recommended_primary"], "claude")
        self.assertEqual(strategy["orchestration_mode"], "claude-subagents")


class VersionGateTests(unittest.TestCase):
    def test_version_ge_compares_dotted_ints_numerically(self):
        self.assertTrue(runtime_capabilities.version_ge("2.1.170", (2, 1, 32)))
        self.assertTrue(runtime_capabilities.version_ge("2.1.154", (2, 1, 154)))
        self.assertFalse(runtime_capabilities.version_ge("2.1.30", (2, 1, 32)))
        self.assertFalse(runtime_capabilities.version_ge("2.1.153", (2, 1, 154)))

    def test_version_ge_handles_missing_version(self):
        self.assertFalse(runtime_capabilities.version_ge(None, (2, 0, 0)))
        self.assertFalse(runtime_capabilities.version_ge("", (2, 0, 0)))

    def test_version_ge_tolerates_suffixed_versions(self):
        self.assertTrue(runtime_capabilities.version_ge("2.1.170-beta", (2, 1, 154)))
        self.assertEqual(runtime_capabilities.version_tuple("2.1.170-beta"), (2, 1, 170))


class ClaudeCapabilityTests(unittest.TestCase):
    def _caps(self, version="2.1.170", help_output="", path="/usr/local/bin/claude"):
        caps, _evidence = runtime_capabilities.compute_claude_capabilities(
            version, help_output, path, "claude agents"
        )
        return caps

    def test_subagents_available_on_2_1_170(self):
        self.assertEqual(self._caps(version="2.1.170")["subagents"], "available")

    def test_subagents_unavailable_when_binary_absent(self):
        caps, _ = runtime_capabilities.compute_claude_capabilities(
            "2.1.170", "", None, ""
        )
        self.assertEqual(caps["subagents"], "unavailable")

    def test_agent_teams_experimental_requires_env_and_version(self):
        with mock.patch.dict(os.environ, {runtime_capabilities.AGENT_TEAMS_ENV: "1"}):
            self.assertEqual(self._caps(version="2.1.32")["agent_teams"], "experimental_available")
            self.assertEqual(self._caps(version="2.1.31")["agent_teams"], "unavailable")
        env_clean = {k: v for k, v in os.environ.items() if k != runtime_capabilities.AGENT_TEAMS_ENV}
        with mock.patch.dict(os.environ, env_clean, clear=True):
            self.assertEqual(self._caps(version="2.1.170")["agent_teams"], "unavailable")

    def test_agent_teams_env_matches_current_claude_code_docs(self):
        self.assertEqual(runtime_capabilities.AGENT_TEAMS_ENV, "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS")

    def test_dynamic_workflows_version_gated_and_disable_respected(self):
        env_clean = {k: v for k, v in os.environ.items()
                     if k not in runtime_capabilities.DYNAMIC_WORKFLOWS_DISABLE_ENVS}
        with mock.patch.dict(os.environ, env_clean, clear=True):
            self.assertEqual(self._caps(version="2.1.154")["dynamic_workflows"], "available")
            self.assertEqual(self._caps(version="2.1.153")["dynamic_workflows"], "unavailable")
        with mock.patch.dict(os.environ, {runtime_capabilities.DYNAMIC_WORKFLOWS_DISABLE_ENV: "1"}):
            self.assertEqual(self._caps(version="2.1.170")["dynamic_workflows"], "unavailable")

    def test_dynamic_workflows_disable_env_matches_current_claude_code_docs(self):
        self.assertEqual(runtime_capabilities.DYNAMIC_WORKFLOWS_DISABLE_ENV, "CLAUDE_CODE_DISABLE_WORKFLOWS")

    def test_legacy_dynamic_workflows_disable_env_remains_conservative(self):
        with mock.patch.dict(os.environ, {runtime_capabilities.LEGACY_DYNAMIC_WORKFLOWS_DISABLE_ENV: "1"}):
            self.assertEqual(self._caps(version="2.1.170")["dynamic_workflows"], "unavailable")

    def test_workflow_governance_policy_records_required_controls(self):
        claude = {
            "capabilities": {"dynamic_workflows": "available"},
            "capability_evidence": {"dynamic_workflows": "version >= 2.1.154"},
        }
        policy = runtime_capabilities.workflow_governance_policy(claude)
        self.assertEqual(policy["status"], "available")
        self.assertEqual(policy["saved_project_workflow_dir"], ".claude/workflows")
        self.assertTrue(policy["slice_first_cost_probe_required"])
        self.assertFalse(policy["project_governance_writes_allowed"])
        self.assertIn("CLAUDE_CODE_DISABLE_WORKFLOWS=1", policy["disable_paths"])
        self.assertIn("saved+reviewed", policy["recurring_use_policy"])

    def test_build_matrix_includes_workflow_governance(self):
        with mock.patch.object(runtime_capabilities, "detect_codex", return_value={"capabilities": {}}), \
             mock.patch.object(
                 runtime_capabilities,
                 "detect_claude",
                 return_value={
                     "capabilities": {"dynamic_workflows": "available"},
                     "capability_evidence": {"dynamic_workflows": "version >= 2.1.154"},
                 },
             ):
            matrix = runtime_capabilities.build_matrix(Path("/tmp/project"))
        self.assertIn("workflow_governance", matrix)
        self.assertEqual(matrix["workflow_governance"]["status"], "available")

    def test_headless_available_when_binary_present(self):
        self.assertEqual(self._caps(path="/usr/local/bin/claude")["headless"], "available")
        caps, _ = runtime_capabilities.compute_claude_capabilities("2.1.170", "", None, "")
        self.assertEqual(caps["headless"], "unavailable")

    def test_evidence_strings_present_for_new_capabilities(self):
        _caps, evidence = runtime_capabilities.compute_claude_capabilities(
            "2.1.170", "", "/usr/local/bin/claude", "claude agents"
        )
        for key in ("subagents", "agent_teams", "dynamic_workflows", "headless"):
            self.assertIn(key, evidence)
            self.assertTrue(evidence[key].strip())


class ClaudeAgentsJsonTests(unittest.TestCase):
    def test_parse_claude_agents_json_list_of_objects(self):
        out = '[{"name": "vibeos:backend"}, {"name": "general-purpose"}]'
        parsed = runtime_capabilities.parse_claude_agents_json(out)
        self.assertEqual(parsed["active_count"], 2)
        self.assertIn("vibeos:backend", parsed["vibeos_agents"])
        self.assertIn("general-purpose", parsed["agents"])

    def test_parse_claude_agents_json_tolerates_garbage(self):
        parsed = runtime_capabilities.parse_claude_agents_json("not json")
        self.assertIsNone(parsed["active_count"])
        self.assertEqual(parsed["agents"], [])


if __name__ == "__main__":
    unittest.main()
