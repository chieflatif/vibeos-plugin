import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLANNER = REPO_ROOT / "plugins/vibeos/scripts/comp-plan.py"
INTEGRATION = REPO_ROOT / "plugins/vibeos/scripts/comp-integration-check.py"
SCORECARD = REPO_ROOT / "plugins/vibeos/scripts/comp-scorecard.py"
DIMENSIONS = REPO_ROOT / "plugins/vibeos/reference/comp/scorecard-dimensions.json"

MISSION = """# Mission: Secure Client Portal

## Mission Promise

Give enterprise customers a secure client portal with audit-ready operations.

## Enterprise Foundation Baseline

Security, identity, access, observability, health, logs, performance, latency, dependency freshness, deployment, runbook, and evidence are required.
The user workflow preserves auth, backend handoff, data persistence, error feedback, mission promise, objective fidelity, and evidence across the primary flow.
System invariants preserve state, auth ownership, data integrity, recovery, and evidence for invalid transitions.

## Dependency Intelligence

Dependency versions are verified against current source evidence. Lockfile-backed installs preserve package manager compatibility. Security audit output and upgrade notes are required.

## Delivery Infrastructure

CI pipeline, deploy path, environment secrets, observability, health, smoke, rollback, and runbook evidence are required.
"""


class CompScorecardTests(unittest.TestCase):
    def test_scorecard_dimensions_are_valid(self):
        data = json.loads(DIMENSIONS.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], "1.0")
        self.assertIn("design_partner_mvp", data["thresholds"])
        self.assertGreaterEqual(len(data["dimensions"]), 8)
        self.assertIn("flow_integrity", {dimension["id"] for dimension in data["dimensions"]})
        self.assertIn("objective_fidelity", {dimension["id"] for dimension in data["dimensions"]})
        self.assertIn("system_invariants", {dimension["id"] for dimension in data["dimensions"]})
        self.assertIn("dependency_intelligence", {dimension["id"] for dimension in data["dimensions"]})
        self.assertIn("delivery_infrastructure", {dimension["id"] for dimension in data["dimensions"]})
        for dimension in data["dimensions"]:
            self.assertTrue(dimension["id"])
            self.assertTrue(dimension["label"])
            self.assertIn(".", dimension["scorecard_field"])
            self.assertTrue(dimension["blocking_at"])

    def test_scorecard_passes_with_required_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(MISSION, encoding="utf-8")
            subprocess.run(["python3", str(PLANNER), "--project-dir", str(root)], check=True, capture_output=True, text=True)
            scopes = json.loads((root / ".vibeos/worktree-scopes.json").read_text(encoding="utf-8"))
            evidence_dir = root / "docs/evidence"
            evidence_dir.mkdir(parents=True, exist_ok=True)
            (evidence_dir / "FLOW-INTEGRITY.md").write_text(
                "# Flow Integrity\n\nThe user workflow preserves auth, backend handoff, data persistence, and error feedback.\n",
                encoding="utf-8",
            )
            (evidence_dir / "SYSTEM-INVARIANTS.md").write_text(
                "# System Invariants\n\nState invariants preserve auth ownership, data integrity, retry safety, and recovery evidence.\n",
                encoding="utf-8",
            )
            (evidence_dir / "DEPENDENCY-INTELLIGENCE.md").write_text(
                "# Dependency Intelligence\n\nDependency source verified on 2026-04-29. Version compatibility, lockfile evidence, security audit output, and upgrade path are captured.\n",
                encoding="utf-8",
            )
            (evidence_dir / "DELIVERY-INFRASTRUCTURE.md").write_text(
                "# Delivery Infrastructure\n\nCI pipeline runs tests and gates. Deploy, environment, secret, observability, health, smoke, rollback, and runbook evidence are captured.\n",
                encoding="utf-8",
            )
            for scope in scopes["branches"].values():
                for wo_id in scope["wo_ids"]:
                    (evidence_dir / f"{wo_id}.md").write_text(f"# Evidence {wo_id}\n\nTests passed.\n", encoding="utf-8")
            subprocess.run(["python3", str(INTEGRATION), "--project-dir", str(root)], check=True, capture_output=True, text=True)

            result = subprocess.run(
                ["python3", str(SCORECARD), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "pass")
            self.assertTrue((root / "SCORECARD.md").is_file())
            self.assertIn("| Security | pass |", (root / "SCORECARD.md").read_text(encoding="utf-8"))
            self.assertIn("| Flow Integrity | pass |", (root / "SCORECARD.md").read_text(encoding="utf-8"))
            self.assertIn("| System Invariants | pass |", (root / "SCORECARD.md").read_text(encoding="utf-8"))
            self.assertIn("| Dependency Intelligence | pass |", (root / "SCORECARD.md").read_text(encoding="utf-8"))
            self.assertIn("| Delivery Infrastructure | pass |", (root / "SCORECARD.md").read_text(encoding="utf-8"))

    def test_scorecard_fails_when_required_artifacts_are_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = subprocess.run(
                ["python3", str(SCORECARD), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "fail")


if __name__ == "__main__":
    unittest.main()
