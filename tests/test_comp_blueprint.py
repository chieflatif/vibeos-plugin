import json
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BLUEPRINT = REPO_ROOT / "plugins/vibeos/reference/comp/enterprise-mvp-foundation.json"
STACK_CURRENCY = REPO_ROOT / "plugins/vibeos/reference/comp/stack-dependency-currency.json"
STACK_VARIANTS = [
    REPO_ROOT / "plugins/vibeos/reference/comp/stack-typescript-node.json",
    REPO_ROOT / "plugins/vibeos/reference/comp/stack-python-fastapi.json",
    REPO_ROOT / "plugins/vibeos/reference/comp/stack-frontend-app.json",
]
SCRIPTS_DIR = REPO_ROOT / "plugins/vibeos/scripts"


class CompBlueprintTests(unittest.TestCase):
    def test_blueprint_maps_requirements_to_evidence_gates_and_scorecard(self):
        data = json.loads(BLUEPRINT.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], "1.0")
        self.assertIn("local_proof", data["thresholds"])
        self.assertIn("design_partner_mvp", data["thresholds"])
        self.assertIn("production_ready", data["thresholds"])
        self.assertGreaterEqual(len(data["requirements"]), 10)

        domains = {item["domain"] for item in data["requirements"]}
        ids = {item["id"] for item in data["requirements"]}
        self.assertIn("DEP-002", ids)
        self.assertIn("OPS-002", ids)
        for domain in [
            "identity_access",
            "data_integrity",
            "flow_integrity",
            "system_invariants",
            "security",
            "testing",
            "observability_operations",
            "deployment_release",
            "frontend_experience",
            "performance_scalability",
            "dependencies_supply_chain",
            "documentation_evidence",
        ]:
            self.assertIn(domain, domains)

        for item in data["requirements"]:
            self.assertTrue(item["id"])
            self.assertTrue(item["evidence"], item["id"])
            self.assertTrue(item["gates"], item["id"])
            self.assertIn(".", item["scorecard_field"], item["id"])
            self.assertTrue(item["deferral_rule"], item["id"])
            for gate in item["gates"]:
                self.assertTrue((SCRIPTS_DIR / gate).is_file(), f"{item['id']} references missing gate {gate}")

    def test_stack_variants_are_parseable_and_actionable(self):
        for path in STACK_VARIANTS:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["schema_version"], "1.0")
            self.assertTrue(data["stack"])
            self.assertTrue(data["applies_to"])
            self.assertTrue(data["baseline"])
            self.assertTrue(data["evidence_commands"])
            self.assertIn("freshness_policy", data)
            self.assertIn("currency_pack", data)

    def test_stack_dependency_currency_packs_are_parseable_and_actionable(self):
        data = json.loads(STACK_CURRENCY.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], "1.0")
        ids = {pack["id"] for pack in data["packs"]}
        for expected in [
            "typescript_node",
            "frontend_app",
            "python_fastapi",
            "ai_sdk",
            "auth_security",
            "database_orm",
            "deployment_runtime",
        ]:
            self.assertIn(expected, ids)

        for pack in data["packs"]:
            self.assertTrue(pack["label"])
            self.assertTrue(pack["applies_when"])
            self.assertTrue(pack["required_evidence_terms"])
            self.assertTrue(pack["current_source_targets"])
            self.assertTrue(pack["evidence_commands"])
            self.assertNotRegex(json.dumps(pack), r"\b\d+\.\d+\.\d+\b")


if __name__ == "__main__":
    unittest.main()
