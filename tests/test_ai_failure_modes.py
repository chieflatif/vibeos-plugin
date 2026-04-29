import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY = REPO_ROOT / "plugins/vibeos/reference/comp/ai-failure-modes.json"
VALIDATOR = REPO_ROOT / "plugins/vibeos/scripts/validate-comp-ai-failure-modes.py"
SCRIPTS_DIR = REPO_ROOT / "plugins/vibeos/scripts"


VALID_MISSION = """# Mission: Example

## Mission Promise

Deliver a narrow workflow with enterprise-grade foundations.

## Users And Buyers

- Primary user: operations analyst
- Enterprise buyer or sponsor: operations leader

## Core Workflow

1. Create a record
2. Review the record
3. Export the result

## Flow Integrity

The user starts in the UI, authenticates through auth, submits the workflow to the backend, persists data, receives success or error feedback, and leaves evidence.

## Objective Fidelity

The objective is to deliver the mission promise without drifting into analytics or billing.

## System Invariants

- Auth ownership must always protect user data.
- Record state transitions must never skip validation.
- Recovery evidence must exist when errors occur.

## Dependency Intelligence

- Dependency versions are verified against current source evidence.
- Lockfile policy and runtime compatibility are required.
- Security audit output and upgrade notes are attached.

## Delivery Infrastructure

- CI pipeline runs tests, gates, dependency checks, security checks, and build.
- Deploy path, environment, secret handling, health, smoke, rollback, and runbook evidence are required.

## Product Scope

Must ship the core workflow. Non-goals are advanced analytics and billing.

## Enterprise Foundation Baseline

Readiness threshold: design_partner_mvp.
Identity and access are defined. Security, testing, observability, deployment, evidence, flow, objective, invariant state rules, dependency versions, lockfile policy, compatibility, verified source evidence, pipeline health checks, and rollback are non-negotiable.

## Threat Model

Sensitive data is limited to business records. Abuse paths include unauthorized record access.

## Observability And Operations

Health, logs, request IDs, and actionable errors are required.

## Performance Budgets

Core workflow should complete within two seconds for normal pilot data volumes.

## Acceptance Criteria

- [ ] Core workflow works end to end.
- [ ] Tests and evidence are attached.

## Downstream Handoff

Next artifact: COMP-PLAN.md.
"""


class AiFailureModeTests(unittest.TestCase):
    def test_registry_maps_failure_modes_to_checks_and_scorecard(self):
        data = json.loads(REGISTRY.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], "1.0")
        self.assertGreaterEqual(len(data["failure_modes"]), 10)

        for mode in data["failure_modes"]:
            self.assertTrue(mode["id"])
            self.assertTrue(mode["severity"])
            self.assertTrue(mode["detection"])
            self.assertIn(".", mode["scorecard_field"])
            self.assertIn("design_partner_mvp", mode["threshold_behavior"])
            for detection in mode["detection"]:
                if detection.endswith((".sh", ".py")):
                    self.assertTrue((SCRIPTS_DIR / detection).is_file(), f"missing detection script {detection}")

    def test_validator_fails_without_mission(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", tmp, "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["findings"][0]["id"], "COMP-MISSION-MISSING")

    def test_validator_fails_on_placeholders(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission = Path(tmp) / "MISSION.md"
            mission.write_text(VALID_MISSION + "\n{{UNRESOLVED}}\n", encoding="utf-8")
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", tmp, "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertTrue(any(item["id"] == "COMP-AI-PLACEHOLDER" for item in payload["findings"]))

    def test_validator_passes_valid_mission(self):
        with tempfile.TemporaryDirectory() as tmp:
            mission = Path(tmp) / "MISSION.md"
            mission.write_text(VALID_MISSION, encoding="utf-8")
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", tmp, "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["findings"], [])

    def test_validator_ignores_generated_review_category_labels(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(VALID_MISSION, encoding="utf-8")
            evidence_dir = root / "docs/evidence"
            evidence_dir.mkdir(parents=True)
            (evidence_dir / "RED-TEAM-REPORT.md").write_text(
                "# VibOS Comp Red-Team Report\n\n- fake completion or demo-only evidence\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", tmp, "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "pass")

    def test_validator_still_flags_non_generated_failure_markers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(VALID_MISSION, encoding="utf-8")
            evidence_dir = root / "docs/evidence"
            evidence_dir.mkdir(parents=True)
            (evidence_dir / "FLOW-INTEGRITY.md").write_text(
                "# Flow Integrity\n\nClaimed fake completion without evidence.\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", tmp, "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertTrue(any(item["id"] == "COMP-AI-FAKE-COMPLETION" for item in payload["findings"]))


if __name__ == "__main__":
    unittest.main()
