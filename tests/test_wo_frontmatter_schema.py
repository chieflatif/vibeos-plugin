import json
import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = REPO_ROOT / "plugins/vibeos/reference/wo-frontmatter.schema.json"
SCHEMA_DOC = REPO_ROOT / "docs/planning/WO-SCHEMA.md"
REPO_TEMPLATE = REPO_ROOT / "docs/planning/WO-TEMPLATE.md"
REFERENCE_TEMPLATE = REPO_ROOT / "plugins/vibeos/reference/governance/WO-TEMPLATE.md.ref"


GOOD_CONTRACT = {
    "wo": "WO-111",
    "title": "WO Frontmatter Schema + Template",
    "status": "In Progress",
    "phase": 35,
    "phase_name": "Machine-Readable WO Contracts",
    "wo_class": "harness",
    "write_scope": ["docs/planning/WO-SCHEMA.md"],
    "no_touch": ["/Users/latifhorst/latifhorstweb/**"],
    "required_auditors": ["correctness-auditor", "evidence-auditor"],
    "model_policy": "implementation",
    "budget_posture": {
        "token_ceiling": None,
        "turn_ceiling": 8,
        "cost_ceiling_usd": 2.5,
    },
}


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def one_of_string_allowed(schema_branch, value):
    if "enum" in schema_branch:
        return value in schema_branch["enum"]
    pattern = schema_branch.get("pattern")
    return bool(pattern and re.match(pattern, value))


def validate_contract(contract, schema):
    errors = []
    for field in schema["required"]:
        if field not in contract:
            errors.append(f"missing:{field}")

    if "wo" in contract and not re.match(schema["properties"]["wo"]["pattern"], contract["wo"]):
        errors.append("invalid:wo")

    if "status" in contract and contract["status"] not in schema["properties"]["status"]["enum"]:
        errors.append("invalid:status")

    if "wo_class" in contract:
        branches = schema["properties"]["wo_class"]["oneOf"]
        if not any(one_of_string_allowed(branch, contract["wo_class"]) for branch in branches):
            errors.append("invalid:wo_class")

    if "model_policy" in contract:
        branches = schema["properties"]["model_policy"]["oneOf"]
        if not any(one_of_string_allowed(branch, contract["model_policy"]) for branch in branches):
            errors.append("invalid:model_policy")

    if not contract.get("write_scope"):
        errors.append("invalid:write_scope")

    if not contract.get("required_auditors"):
        errors.append("invalid:required_auditors")

    budget = contract.get("budget_posture")
    if isinstance(budget, dict):
        for key in schema["properties"]["budget_posture"]["required"]:
            if key not in budget:
                errors.append(f"missing:budget_posture.{key}")
        for key in ("token_ceiling", "turn_ceiling"):
            value = budget.get(key)
            if value is not None and (not isinstance(value, int) or value < 1):
                errors.append(f"invalid:budget_posture.{key}")
        value = budget.get("cost_ceiling_usd")
        if value is not None and (not isinstance(value, (int, float)) or value < 0):
            errors.append("invalid:budget_posture.cost_ceiling_usd")
    elif "budget_posture" in contract:
        errors.append("invalid:budget_posture")

    return errors


class WoFrontmatterSchemaTests(unittest.TestCase):
    def test_schema_is_parseable_and_defines_required_contract_fields(self):
        schema = load_schema()

        self.assertEqual(schema["title"], "VibeOS Work Order Frontmatter")
        for field in [
            "wo",
            "title",
            "status",
            "phase",
            "phase_name",
            "wo_class",
            "write_scope",
            "no_touch",
            "required_auditors",
            "model_policy",
            "budget_posture",
        ]:
            self.assertIn(field, schema["required"])
            self.assertIn(field, schema["properties"])

    def test_good_contract_and_custom_extension_class_validate(self):
        schema = load_schema()
        self.assertEqual(validate_contract(GOOD_CONTRACT, schema), [])

        custom = dict(GOOD_CONTRACT, wo_class="custom-client-safe-migration", model_policy="custom-cheap-review")
        self.assertEqual(validate_contract(custom, schema), [])

    def test_known_bad_contracts_fail_validation(self):
        schema = load_schema()

        missing_scope = dict(GOOD_CONTRACT)
        missing_scope.pop("write_scope")
        self.assertIn("missing:write_scope", validate_contract(missing_scope, schema))

        invalid_class = dict(GOOD_CONTRACT, wo_class="client-safe-migration")
        self.assertIn("invalid:wo_class", validate_contract(invalid_class, schema))

        invalid_budget = {
            **GOOD_CONTRACT,
            "budget_posture": {
                "token_ceiling": 0,
                "turn_ceiling": 0,
                "cost_ceiling_usd": -1,
            },
        }
        errors = validate_contract(invalid_budget, schema)
        self.assertIn("invalid:budget_posture.token_ceiling", errors)
        self.assertIn("invalid:budget_posture.turn_ceiling", errors)
        self.assertIn("invalid:budget_posture.cost_ceiling_usd", errors)

    def test_class_defaults_capture_governance_depth(self):
        schema = load_schema()
        defaults = schema["x-vibeos-class-defaults"]

        self.assertTrue(defaults["docs-only"]["differential_audit_allowed"])
        self.assertFalse(defaults["mutation-path"]["differential_audit_allowed"])
        self.assertIn("security-auditor", defaults["auth-security"]["minimum_required_auditors"])
        self.assertIn("dependency-intelligence-auditor", defaults["dependency"]["minimum_required_auditors"])

    def test_templates_and_schema_doc_include_frontmatter_contract(self):
        for path in [SCHEMA_DOC, REPO_TEMPLATE, REFERENCE_TEMPLATE]:
            text = path.read_text(encoding="utf-8")
            self.assertIn("wo_class", text, path)
            self.assertIn("write_scope", text, path)
            self.assertIn("required_auditors", text, path)
            self.assertIn("model_policy", text, path)
            self.assertIn("budget_posture", text, path)


if __name__ == "__main__":
    unittest.main()
