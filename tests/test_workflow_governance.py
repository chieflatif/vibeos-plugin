import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHITECTURE_REF = REPO_ROOT / "plugins/vibeos/reference/governance/ARCHITECTURE.md.ref"
RUNTIME_MANIFEST_REF = REPO_ROOT / "plugins/vibeos/reference/governance/RUNTIME-MANIFEST.md.ref"
BUILD_SKILL = REPO_ROOT / "plugins/vibeos/skills/build/SKILL.md"
AUDIT_SKILL = REPO_ROOT / "plugins/vibeos/skills/audit/SKILL.md"


class WorkflowGovernanceDocsTests(unittest.TestCase):
    def test_architecture_reference_documents_workflow_governance(self):
        text = ARCHITECTURE_REF.read_text(encoding="utf-8")
        self.assertIn("Runtime And Workflow Governance", text)
        self.assertIn("workflow_governance.status", text)
        self.assertIn("CLAUDE_CODE_DISABLE_WORKFLOWS=1", text)
        self.assertIn("slice-first cost probe", text)

    def test_runtime_manifest_reference_documents_required_controls(self):
        text = RUNTIME_MANIFEST_REF.read_text(encoding="utf-8")
        self.assertIn("Dynamic Workflow Governance", text)
        self.assertIn(".claude/workflows/", text)
        self.assertIn("Governance no-write rule", text)
        self.assertIn("CLAUDE_CODE_DISABLE_WORKFLOWS=1", text)

    def test_build_skill_consumes_workflow_governance(self):
        text = BUILD_SKILL.read_text(encoding="utf-8")
        self.assertIn("workflow_governance", text)
        self.assertIn("slice-first cost probe", text)
        self.assertIn("fall back to subagents", text)

    def test_audit_skill_consumes_workflow_governance(self):
        text = AUDIT_SKILL.read_text(encoding="utf-8")
        self.assertIn("workflow_governance", text)
        self.assertIn("WO-124", text)
        self.assertIn("existing subagent audit baseline", text)


if __name__ == "__main__":
    unittest.main()
