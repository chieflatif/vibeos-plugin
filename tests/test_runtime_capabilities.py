import importlib.util
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
