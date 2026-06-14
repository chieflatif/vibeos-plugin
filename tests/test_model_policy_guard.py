import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
HOOKS_JSON = REPO_ROOT / "plugins/vibeos/hooks/hooks.json"
HOOK_MANIFEST = REPO_ROOT / "plugins/vibeos/hook-manifest.json"
MODEL_POLICY_GUARD = REPO_ROOT / "plugins/vibeos/hooks/scripts/model-policy-guard.sh"
COST_CAPTURE = REPO_ROOT / "plugins/vibeos/scripts/capture-headless-cost.py"


class ModelPolicyGuardTests(unittest.TestCase):
    def run_guard(self, payload: dict, project_dir: Path):
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project_dir)}
        return subprocess.run(
            ["bash", str(MODEL_POLICY_GUARD)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            env=env,
        )

    def write_active_wo(self, root: Path, model_policy: str = "frontier-audit") -> Path:
        (root / ".vibeos").mkdir(parents=True, exist_ok=True)
        planning = root / "docs/planning"
        planning.mkdir(parents=True, exist_ok=True)
        wo = planning / "WO-999-audit-fixture.md"
        wo.write_text(
            f"""---
wo: WO-999
title: Audit Fixture
status: In Progress
phase: 99
phase_name: Fixture
wo_class: audit
write_scope:
  - docs/planning/WO-999-audit-fixture.md
no_touch: []
required_auditors:
  - evidence-auditor
model_policy: {model_policy}
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---

# WO-999: Audit Fixture

## Status

`In Progress`
""",
            encoding="utf-8",
        )
        (root / ".vibeos/session-state.json").write_text(
            json.dumps({"active": True, "active_wo": "docs/planning/WO-999-audit-fixture.md"}),
            encoding="utf-8",
        )
        return wo

    def test_hooks_json_and_manifest_register_config_change_guard(self):
        hooks = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))["hooks"]
        self.assertIn("ConfigChange", hooks)
        self.assertIn("model-policy-guard.sh", hooks["ConfigChange"][0]["hooks"][0]["command"])

        manifest = json.loads(HOOK_MANIFEST.read_text(encoding="utf-8"))
        documented = {
            (hook.get("event_type"), hook.get("script", "").split("/")[-1])
            for hook in manifest.get("hooks", [])
        }
        self.assertIn(("ConfigChange", "model-policy-guard.sh"), documented)

    def test_guard_allows_when_no_active_policy_exists(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self.run_guard(
                {"hook_event_name": "ConfigChange", "source": "project_settings", "model": "haiku"},
                root,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "allow")
            self.assertIn("No active model_policy", payload["reason"])

    def test_guard_blocks_frontier_audit_model_and_effort_downgrade(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_active_wo(root, "frontier-audit")
            settings = root / ".claude/settings.local.json"
            settings.parent.mkdir(parents=True, exist_ok=True)
            settings.write_text(json.dumps({"model": "sonnet", "effortLevel": "low"}), encoding="utf-8")

            result = self.run_guard(
                {"hook_event_name": "ConfigChange", "source": "project_settings", "file_path": str(settings)},
                root,
            )

            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "block")
            self.assertEqual(payload["active_model_policy"], "frontier-audit")
            self.assertIn("sonnet", payload["reason"])

    def test_guard_allows_frontier_audit_compliant_alias_and_effort(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_active_wo(root, "frontier-audit")

            result = self.run_guard(
                {
                    "hook_event_name": "ConfigChange",
                    "source": "project_settings",
                    "model": "claude-opus-4-fixture",
                    "effortLevel": "xhigh",
                },
                root,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "allow")
            self.assertEqual(payload["active_model_policy"], "frontier-audit")

    def test_guard_observes_policy_settings_without_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".vibeos").mkdir()
            (root / ".vibeos/session-state.json").write_text(
                json.dumps({"active_model_policy": "frontier-audit"}),
                encoding="utf-8",
            )

            result = self.run_guard(
                {
                    "hook_event_name": "ConfigChange",
                    "source": "policy_settings",
                    "model": "sonnet",
                    "effortLevel": "low",
                },
                root,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["decision"], "allow")
            self.assertIn("observed only", payload["reason"])


class HeadlessCostCaptureTests(unittest.TestCase):
    def run_capture(self, *args):
        return subprocess.run(
            ["python3", str(COST_CAPTURE), *args],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )

    def test_cost_capture_writes_estimate_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "headless.json"
            evidence = root / "evidence"
            source.write_text(
                json.dumps(
                    {
                        "session_id": "fixture-session",
                        "model": "opus",
                        "num_turns": 2,
                        "duration_ms": 1234,
                        "total_cost_usd": 0.1234,
                        "model_costs": {"opus": 0.1234},
                    }
                ),
                encoding="utf-8",
            )

            result = self.run_capture(
                "--input",
                str(source),
                "--evidence-dir",
                str(evidence),
                "--generated-at",
                "2026-06-14T00:00:00Z",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads((evidence / "cost-report.json").read_text(encoding="utf-8"))
            self.assertEqual(report["generated_at"], "2026-06-14T00:00:00Z")
            self.assertEqual(report["cost"]["label"], "estimate; reconcile against billing")
            self.assertEqual(report["cost"]["total_cost_usd"], 0.1234)
            self.assertEqual(report["run"]["session_id"], "fixture-session")

    def test_cost_capture_fails_without_total_cost(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "headless.json"
            source.write_text(json.dumps({"result": "ok"}), encoding="utf-8")

            result = self.run_capture("--input", str(source), "--evidence-dir", str(Path(tmp) / "evidence"))

            self.assertEqual(result.returncode, 1)
            self.assertIn("total_cost_usd", result.stderr)


if __name__ == "__main__":
    unittest.main()
