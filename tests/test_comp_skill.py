import json
import subprocess
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MISSION_TEMPLATE = REPO_ROOT / "plugins/vibeos/reference/product/MISSION.md.ref"
CLAUDE_SKILL = REPO_ROOT / "plugins/vibeos/skills/comp/SKILL.md"
CODEX_SKILL = REPO_ROOT / "plugins/vibeos/reference/codex/skills/vibeos-comp/SKILL.md"
INTENT_ROUTER = REPO_ROOT / "plugins/vibeos/hooks/scripts/intent-router.sh"


class CompSkillTests(unittest.TestCase):
    def test_mission_template_has_enterprise_mvp_sections(self):
        text = MISSION_TEMPLATE.read_text(encoding="utf-8")
        required_sections = [
            "## Mission Promise",
            "## Users And Buyers",
            "## Core Workflow",
            "## Flow Integrity",
            "## Objective Fidelity",
            "## System Invariants",
            "## Dependency Intelligence",
            "## Delivery Infrastructure",
            "## Product Scope",
            "## Enterprise Foundation Baseline",
            "## Threat Model",
            "## Observability And Operations",
            "## Performance Budgets",
            "## Acceptance Criteria",
            "## Downstream Handoff",
        ]

        for section in required_sections:
            self.assertIn(section, text)

        self.assertIn("reduce features before reducing security", text)
        self.assertIn("observability", text.lower())

    def test_comp_skills_preserve_scope_cutting_rule(self):
        claude_text = CLAUDE_SKILL.read_text(encoding="utf-8")
        codex_text = CODEX_SKILL.read_text(encoding="utf-8")

        for text in (claude_text, codex_text):
            self.assertIn("Cut product scope before cutting", text)
            self.assertIn("Ask at most three essential questions", text)
            self.assertIn("enterprise-mvp-foundation.json", text)
            self.assertIn("MISSION.md", text)
            self.assertIn("system invariants", text.lower())
            self.assertIn("dependency intelligence", text.lower())
            self.assertIn("delivery infrastructure", text.lower())
            self.assertIn("full VibeOS discovery/planning", text)

    def test_intent_router_routes_enterprise_mvp_to_comp(self):
        result = subprocess.run(
            ["bash", str(INTENT_ROUTER)],
            input=json.dumps(
                {
                    "prompt": "Build this as a competition-grade enterprise MVP for a design partner",
                    "cwd": str(REPO_ROOT),
                }
            ),
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Suggested skill: /vibeos:comp", result.stdout)
        self.assertIn("Confidence: high", result.stdout)


if __name__ == "__main__":
    unittest.main()
