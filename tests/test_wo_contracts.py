import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "plugins/vibeos/scripts/wo-contracts.py"

GOOD_WO = """---
wo: WO-112
title: Frontmatter Generators
status: In Progress
phase: 35
phase_name: Machine-Readable WO Contracts
wo_class: harness
write_scope:
  - plugins/vibeos/scripts/wo-contracts.py
  - tests/test_wo_contracts.py
no_touch:
  - /Users/latifhorst/latifhorstweb/**
  - /Users/latifhorst/Joan4U/**
required_auditors:
  - correctness-auditor
  - evidence-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: 6
  cost_ceiling_usd: 2.5
---

# WO-112: Frontmatter Generators
"""


class WoContractsTests(unittest.TestCase):
    def write_wo(self, root: Path, text: str = GOOD_WO) -> Path:
        path = root / "WO-112-frontmatter-generators.md"
        path.write_text(text, encoding="utf-8")
        return path

    def run_script(self, *args, cwd=None):
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            cwd=cwd,
            capture_output=True,
            text=True,
        )

    def test_parse_emits_frontmatter_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            wo_file = self.write_wo(Path(tmp))

            result = self.run_script("parse", "--wo-file", str(wo_file))

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["wo"], "WO-112")
            self.assertEqual(payload["phase"], 35)
            self.assertEqual(payload["budget_posture"]["turn_ceiling"], 6)
            self.assertEqual(payload["write_scope"][0], "plugins/vibeos/scripts/wo-contracts.py")

    def test_worktree_scope_emits_schema_compatible_feat_branch_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            wo_file = self.write_wo(Path(tmp))

            result = self.run_script(
                "emit-worktree-scope",
                "--wo-file",
                str(wo_file),
                "--branch",
                "feat/wo-112-frontmatter-generators",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["shared_paths"], [])
            scope = payload["branches"]["feat/wo-112-frontmatter-generators"]
            self.assertEqual(scope["wo_ids"], ["WO-112"])
            self.assertEqual(
                scope["exclusive_paths"],
                ["plugins/vibeos/scripts/wo-contracts.py", "tests/test_wo_contracts.py"],
            )
            self.assertEqual(sorted(scope.keys()), ["description", "exclusive_paths", "wo_ids"])

    def test_agent_policy_is_deterministic_and_preserves_allow_deny_material(self):
        with tempfile.TemporaryDirectory() as tmp:
            wo_file = self.write_wo(Path(tmp))

            first = self.run_script("emit-agent-policy", "--wo-file", str(wo_file))
            second = self.run_script("emit-agent-policy", "--wo-file", str(wo_file))

            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(second.returncode, 0, second.stderr)
            self.assertEqual(first.stdout, second.stdout)
            payload = json.loads(first.stdout)
            self.assertEqual(payload["material_type"], "agent_scope_policy")
            self.assertEqual(payload["allowed_paths"], ["plugins/vibeos/scripts/wo-contracts.py", "tests/test_wo_contracts.py"])
            self.assertEqual(
                payload["denied_paths"],
                ["/Users/latifhorst/latifhorstweb/**", "/Users/latifhorst/Joan4U/**"],
            )
            self.assertEqual(payload["model_policy"], "implementation")

    def test_auditor_requirements_include_stable_key_and_schema_governance_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            wo_file = self.write_wo(Path(tmp))

            result = self.run_script("emit-auditor-requirements", "--wo-file", str(wo_file))

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["material_type"], "auditor_requirements")
            self.assertEqual(payload["auditor_requirement_key"], "WO-112:harness:correctness-auditor,evidence-auditor")
            self.assertEqual(payload["required_auditors"], ["correctness-auditor", "evidence-auditor"])
            self.assertEqual(payload["governance"]["governance_tier"], "standard")
            self.assertEqual(payload["governance"]["evidence_depth"], "tests-gates-and-proof")

    def test_worktree_scope_rejects_non_feat_branch(self):
        with tempfile.TemporaryDirectory() as tmp:
            wo_file = self.write_wo(Path(tmp))

            result = self.run_script(
                "emit-worktree-scope",
                "--wo-file",
                str(wo_file),
                "--branch",
                "codex/wo-112-frontmatter-generators",
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn("feat/*", result.stderr)

    def test_missing_frontmatter_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            wo_file = self.write_wo(Path(tmp), "# WO-112\n")

            result = self.run_script("parse", "--wo-file", str(wo_file))

            self.assertEqual(result.returncode, 1)
            self.assertIn("frontmatter", result.stderr)


if __name__ == "__main__":
    unittest.main()
