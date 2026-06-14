"""WO-110: hook-manifest sync + plan/index status reconciliation."""

import json
import os
import subprocess
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
HOOKS_JSON = REPO / "plugins/vibeos/hooks/hooks.json"
HOOK_MANIFEST = REPO / "plugins/vibeos/hook-manifest.json"
GATE_MANIFEST = REPO / "plugins/vibeos/quality-gate-manifest.json"
INVENTORY_GEN = REPO / "plugins/vibeos/scripts/generate-inventory.py"
PREREQ = REPO / "plugins/vibeos/hooks/scripts/prereq-check.sh"


def configured_command_hooks():
    h = json.loads(HOOKS_JSON.read_text())
    entries = []
    for event, arr in h.get("hooks", {}).items():
        for entry in arr:
            matcher = entry.get("matcher", "")
            for hk in entry.get("hooks", []):
                if hk.get("type") == "command":
                    entries.append((event, matcher, hk.get("command", "").split("/")[-1]))
    return entries


def documented_hook_scripts():
    m = json.loads(HOOK_MANIFEST.read_text())
    return [
        (h.get("event_type", ""), h.get("matcher", ""), h.get("script", "").split("/")[-1])
        for h in m.get("hooks", [])
    ]


class HookManifestSyncTests(unittest.TestCase):
    def test_manifest_documents_all_configured_command_hooks(self):
        configured = set(configured_command_hooks())
        documented = set(documented_hook_scripts())
        self.assertEqual(len(configured), 16)
        self.assertEqual(
            documented,
            configured,
            f"missing from manifest: {configured - documented}; extra: {documented - configured}",
        )

    def test_inventory_counts_match_twelve(self):
        subprocess.run(
            ["python3", str(INVENTORY_GEN), "--project-dir", str(REPO)],
            capture_output=True, text=True, check=True, cwd=str(REPO),
        )
        inv = json.loads((REPO / "docs/evidence/vnext/generated-inventory.json").read_text())
        hooks = inv["inventory"]["hooks"]
        self.assertEqual(hooks["configured_command_count"], 16)
        self.assertEqual(hooks["documented_count"], 16)


class StatusReconciliationTests(unittest.TestCase):
    def test_no_plan_index_mismatches(self):
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(REPO)}
        result = subprocess.run(
            ["bash", str(PREREQ)],
            input="{}", capture_output=True, text=True, cwd=str(REPO), env=env,
        )
        self.assertIn("plan/index mismatches: none", result.stdout + result.stderr)


class StatusIntegrityGateTests(unittest.TestCase):
    def test_status_integrity_gate_blocking_at_wo_exit(self):
        m = json.loads(GATE_MANIFEST.read_text())
        gate = next(g for g in m["gates"] if "validate-wo-status-integrity.sh" in g["script"])
        self.assertEqual(gate["phase"], "wo_exit")
        self.assertTrue(gate.get("blocking"))
        self.assertLessEqual(gate.get("tier", 99), 1)


if __name__ == "__main__":
    unittest.main()
