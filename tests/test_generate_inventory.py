import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "plugins/vibeos/scripts/generate-inventory.py"
SPEC = importlib.util.spec_from_file_location("generate_inventory", MODULE_PATH)
generate_inventory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generate_inventory)


class GenerateInventoryTests(unittest.TestCase):
    def make_repo(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        for path in [
            "plugins/vibeos/skills/build",
            "plugins/vibeos/reference/codex/skills/vibeos-build",
            "plugins/vibeos/agents",
            "plugins/vibeos/hooks/scripts",
            "plugins/vibeos/scripts",
            "plugins/vibeos/decision-engine",
            "plugins/vibeos/reference/governance",
            "plugins/vibeos/convergence",
            "plugins/vibeos/.claude-plugin",
            ".claude-plugin",
            ".vibeos",
            "docs/planning",
            "tests",
        ]:
            (root / path).mkdir(parents=True, exist_ok=True)
        (root / "plugins/vibeos/skills/build/SKILL.md").write_text("# Build\n", encoding="utf-8")
        (root / "plugins/vibeos/reference/codex/skills/vibeos-build/SKILL.md").write_text("# Build\n", encoding="utf-8")
        (root / "plugins/vibeos/agents/backend.md").write_text("# Backend\n", encoding="utf-8")
        (root / "plugins/vibeos/agents/test-auditor-same-tree.md").write_text("# Audit\n", encoding="utf-8")
        (root / "plugins/vibeos/hooks/scripts/secrets-scan.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        (root / "plugins/vibeos/scripts/gate-runner.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        (root / "plugins/vibeos/scripts/runtime-capabilities.py").write_text("#!/usr/bin/env python3\n", encoding="utf-8")
        (root / "plugins/vibeos/decision-engine/gate-selection.md").write_text("# Gate\n", encoding="utf-8")
        (root / "plugins/vibeos/reference/governance/WO-TEMPLATE.md.ref").write_text("# Template\n", encoding="utf-8")
        (root / "plugins/vibeos/convergence/state-hash.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        (root / "tests/test_alpha.py").write_text("def test_alpha():\n    assert True\n", encoding="utf-8")
        (root / "docs/planning/WO-106-example.md").write_text("# WO-106\n", encoding="utf-8")
        (root / "plugins/vibeos/.claude-plugin/plugin.json").write_text(
            json.dumps({"name": "vibeos", "version": "2.2.0"}),
            encoding="utf-8",
        )
        (root / ".claude-plugin/marketplace.json").write_text(json.dumps({"plugins": [{}]}), encoding="utf-8")
        (root / ".vibeos/runtime-capabilities.json").write_text(
            json.dumps({"generated_at": "2026-06-10T00:00:00Z", "strategy": {"orchestration_mode": "sequential"}}),
            encoding="utf-8",
        )
        (root / "plugins/vibeos/hooks/hooks.json").write_text(
            json.dumps({"hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": "x"}]}]}}),
            encoding="utf-8",
        )
        (root / "plugins/vibeos/hook-manifest.json").write_text(
            json.dumps({"version": "2.2.0", "hooks": [{"name": "secrets-scan"}]}),
            encoding="utf-8",
        )
        (root / "plugins/vibeos/quality-gate-manifest.json").write_text(
            json.dumps(
                {
                    "version": "2.2.0",
                    "gates": [
                        {"script": "scripts/gate-runner.sh", "phase": "pre_commit", "blocking": True},
                        {"script": "scripts/runtime-capabilities.py", "phase": "session_start", "blocking": False},
                    ],
                }
            ),
            encoding="utf-8",
        )
        return temp, root

    def test_inventory_counts_are_source_derived(self):
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        inventory = generate_inventory.build_inventory(root, generated_at="2026-06-10T00:00:00Z")

        self.assertEqual(inventory["inventory"]["claude_skills"]["count"], 1)
        self.assertEqual(inventory["inventory"]["codex_skills"]["count"], 1)
        self.assertEqual(inventory["inventory"]["agents"]["count"], 2)
        self.assertEqual(inventory["inventory"]["agents"]["same_tree_count"], 1)
        self.assertEqual(inventory["inventory"]["gates"]["gate_entries"], 2)
        self.assertEqual(inventory["inventory"]["gates"]["unique_gate_scripts"], 2)
        self.assertFalse(inventory["inventory"]["gates"]["missing_gate_scripts"])

    def test_claim_ledger_blocks_public_overclaims(self):
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        inventory = generate_inventory.build_inventory(root, generated_at="2026-06-10T00:00:00Z")

        claims = {claim["claim_id"]: claim for claim in inventory["claim_ledger"]}
        self.assertEqual(claims["inventory.claude_skills"]["value"], 1)
        self.assertFalse(claims["posture.codex_hook_parity"]["value"])
        self.assertEqual(claims["posture.codex_hook_parity"]["public_status"], "blocked_overclaim")
        self.assertFalse(claims["posture.repo_link_readiness"]["value"])

    def test_main_writes_default_artifact(self):
        temp, root = self.make_repo()
        self.addCleanup(temp.cleanup)
        code = generate_inventory.main(["--project-dir", str(root)])

        self.assertEqual(code, 0)
        out = root / "docs/evidence/vnext/generated-inventory.json"
        self.assertTrue(out.is_file())
        payload = json.loads(out.read_text(encoding="utf-8"))
        self.assertIn("claim_ledger", payload)


if __name__ == "__main__":
    unittest.main()
