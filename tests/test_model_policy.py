import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = REPO_ROOT / "plugins/vibeos/scripts/validate-model-policy.py"
SPEC = importlib.util.spec_from_file_location("validate_model_policy", MODULE_PATH)
validate_model_policy = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_model_policy)


class ModelPolicyTests(unittest.TestCase):
    def make_project(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        (root / "plugins/vibeos/reference").mkdir(parents=True)
        (root / "plugins/vibeos/agents").mkdir(parents=True)
        (root / "docs/planning").mkdir(parents=True)

        policy = json.loads((REPO_ROOT / "plugins/vibeos/reference/model-policy.json").read_text(encoding="utf-8"))
        (root / "plugins/vibeos/reference/model-policy.json").write_text(
            json.dumps(policy, indent=2) + "\n",
            encoding="utf-8",
        )
        (root / "plugins/vibeos/reference/wo-frontmatter.schema.json").write_text(
            json.dumps(
                {
                    "properties": {
                        "model_policy": {
                            "oneOf": [
                                {"enum": sorted(policy["tiers"].keys())},
                                {"pattern": "^custom-[a-z0-9][a-z0-9-]*$"},
                            ]
                        }
                    }
                }
            )
            + "\n",
            encoding="utf-8",
        )
        (root / "plugins/vibeos/agents/backend.md").write_text(
            "---\nname: backend\nmodel: sonnet\n---\n# Backend\n",
            encoding="utf-8",
        )
        (root / "docs/planning/WO-999-fixture.md").write_text(
            "---\nwo: WO-999\nmodel_policy: implementation\n---\n# Fixture\n",
            encoding="utf-8",
        )
        return temp, root

    def validate(self, root: Path):
        return validate_model_policy.validate(
            root,
            root / "plugins/vibeos/reference/model-policy.json",
            root / "plugins/vibeos/reference/wo-frontmatter.schema.json",
        )

    def test_current_repo_policy_passes(self):
        errors = validate_model_policy.validate(
            REPO_ROOT,
            REPO_ROOT / "plugins/vibeos/reference/model-policy.json",
            REPO_ROOT / "plugins/vibeos/reference/wo-frontmatter.schema.json",
        )

        self.assertEqual(errors, [])

    def test_rejects_unknown_agent_model_alias(self):
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        (root / "plugins/vibeos/agents/backend.md").write_text(
            "---\nname: backend\nmodel: banana\n---\n# Backend\n",
            encoding="utf-8",
        )

        errors = self.validate(root)

        self.assertTrue(any("banana" in error for error in errors))

    def test_rejects_schema_policy_tier_drift(self):
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        policy_path = root / "plugins/vibeos/reference/model-policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["tiers"].pop("dependency-research")
        policy_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")

        errors = self.validate(root)

        self.assertTrue(any("dependency-research" in error for error in errors))

    def test_accepts_custom_wo_model_policy_pattern(self):
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        (root / "docs/planning/WO-999-fixture.md").write_text(
            "---\nwo: WO-999\nmodel_policy: custom-client-review\n---\n# Fixture\n",
            encoding="utf-8",
        )

        errors = self.validate(root)

        self.assertEqual(errors, [])

    def test_installed_layout_uses_vibeos_reference_and_claude_agents(self):
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        (root / ".vibeos/reference").mkdir(parents=True)
        (root / ".claude/agents").mkdir(parents=True)
        (root / ".vibeos/reference/model-policy.json").write_text(
            (root / "plugins/vibeos/reference/model-policy.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (root / ".vibeos/reference/wo-frontmatter.schema.json").write_text(
            (root / "plugins/vibeos/reference/wo-frontmatter.schema.json").read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        (root / ".claude/agents/custom.md").write_text(
            "---\nname: custom\nmodel: sonnet\n---\n# Custom\n",
            encoding="utf-8",
        )
        for path in [root / "plugins/vibeos/reference", root / "plugins/vibeos/agents"]:
            for child in path.glob("*"):
                child.unlink()

        errors = validate_model_policy.validate(
            root,
            root / ".vibeos/reference/model-policy.json",
            root / ".vibeos/reference/wo-frontmatter.schema.json",
        )

        self.assertEqual(errors, [])

    def test_gate_manifest_registers_model_policy_lint(self):
        manifest = json.loads((REPO_ROOT / "plugins/vibeos/quality-gate-manifest.json").read_text(encoding="utf-8"))
        gate = next(gate for gate in manifest["gates"] if gate["script"] == "scripts/validate-model-policy.py")

        self.assertEqual(gate["phase"], "wo_entry")
        self.assertEqual(gate["tier"], 1)
        self.assertTrue(gate["blocking"])

        reference = json.loads(
            (REPO_ROOT / "plugins/vibeos/reference/manifests/quality-gate-manifest.json.ref").read_text(
                encoding="utf-8"
            )
        )
        ref_gate = next(gate for gate in reference["phases"]["wo_entry"]["gates"] if gate["script"] == "scripts/validate-model-policy.py")
        self.assertEqual(ref_gate["tier"], 1)


if __name__ == "__main__":
    unittest.main()
