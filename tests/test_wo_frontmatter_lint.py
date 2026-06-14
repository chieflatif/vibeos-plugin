import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "plugins/vibeos/scripts/wo-frontmatter-lint.py"
MANIFEST = REPO_ROOT / "plugins/vibeos/quality-gate-manifest.json"

MASTER_PLAN = """# Master

## 7. Detailed Development Plan (Phases 34-45)

### Phase 34 — Foundation Repair

| WO | Title | Scope | Acceptance criteria |
|---|---|---|---|
| **WO-107** | Gate Fix | script | tests |

### Phase 36 — Lane Readiness

| WO | Title | Scope | Acceptance criteria |
|---|---|---|---|
| **WO-114** | Lane Return-Packet Schema | schema | tests |

## 8. Upgrade Path Architecture
"""


def wo_doc(wo, title, status, phase, scope_path, body_token=None):
    token = body_token or Path(scope_path).name
    return f"""---
wo: {wo}
title: {title}
status: {status}
phase: {phase}
phase_name: Test Phase
wo_class: harness
write_scope:
  - docs/planning/{wo}-{title.lower().replace(" ", "-")}.md
  - {scope_path}
no_touch: []
required_auditors:
  - evidence-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# {wo}: {title}

## Status

`{status}`

## Scope

### In Scope
- Update {token}
"""


class WoFrontmatterLintTests(unittest.TestCase):
    def make_project(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        planning = root / "docs/planning"
        planning.mkdir(parents=True)
        (planning / "VNEXT-UPGRADE-AUDIT-AND-MASTER-PLAN-2026-06-10.md").write_text(MASTER_PLAN, encoding="utf-8")
        (planning / "WO-INDEX.md").write_text("# Work Order Index\n\n## Backlog\n\nLegacy rows stay here.\n", encoding="utf-8")
        (planning / "WO-106-historical-fixture.md").write_text(
            wo_doc("WO-106", "Historical Fixture", "Implemented Locally", 33, "plugins/vibeos/scripts/generate-inventory.py"),
            encoding="utf-8",
        )
        (planning / "WO-107-gate-fix.md").write_text(
            wo_doc("WO-107", "Gate Fix", "Complete", 34, "plugins/vibeos/scripts/gate-runner.sh"),
            encoding="utf-8",
        )
        return temp, root

    def run_script(self, root: Path, *args):
        return subprocess.run(
            ["python3", str(SCRIPT), *args, "--project-dir", str(root)],
            capture_output=True,
            text=True,
        )

    def test_lint_accepts_required_frontmatter_set(self):
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)

        result = self.run_script(root, "lint")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_lint_rejects_missing_wo_107_plus_frontmatter(self):
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        (root / "docs/planning/WO-108-missing.md").write_text("# WO-108\n", encoding="utf-8")

        result = self.run_script(root, "lint")

        self.assertEqual(result.returncode, 1)
        self.assertIn("missing required frontmatter", result.stderr)

    def test_lint_rejects_scope_not_reflected_in_prose(self):
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        (root / "docs/planning/WO-107-gate-fix.md").write_text(
            wo_doc("WO-107", "Gate Fix", "Complete", 34, "src/missing.py", body_token="different.py"),
            encoding="utf-8",
        )

        result = self.run_script(root, "lint")

        self.assertEqual(result.returncode, 1)
        self.assertIn("write_scope is not reflected", result.stderr)

    def test_generate_index_is_idempotent_and_points_to_next_planned_wo(self):
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        index = root / "docs/planning/WO-INDEX.md"

        first = self.run_script(root, "generate-index", "--out", str(index))
        first_text = index.read_text(encoding="utf-8")
        second = self.run_script(root, "generate-index", "--out", str(index))

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(index.read_text(encoding="utf-8"), first_text)
        self.assertIn("VIBEOS-GENERATED-START", first_text)
        self.assertIn("| WO-114 | Lane Return-Packet Schema | 36 | Planned | master-plan |", first_text)
        self.assertIn("Legacy rows stay here.", first_text)

    def test_validate_index_rejects_hand_edit_to_generated_block(self):
        temp, root = self.make_project()
        self.addCleanup(temp.cleanup)
        index = root / "docs/planning/WO-INDEX.md"
        self.run_script(root, "generate-index", "--out", str(index))
        index.write_text(index.read_text(encoding="utf-8").replace("WO-114", "WO-999", 1), encoding="utf-8")

        result = self.run_script(root, "validate-index")

        self.assertEqual(result.returncode, 1)
        self.assertIn("generated block is stale", result.stderr)

    def test_manifest_registers_frontmatter_lint_as_advisory_wo_entry_gate(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        gate = next(gate for gate in manifest["gates"] if gate["script"] == "scripts/validate-wo-frontmatter.sh")

        self.assertEqual(gate["phase"], "wo_entry")
        self.assertEqual(gate["tier"], 2)
        self.assertFalse(gate["blocking"])


if __name__ == "__main__":
    unittest.main()
