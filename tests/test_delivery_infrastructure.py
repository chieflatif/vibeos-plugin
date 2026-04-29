import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "plugins/vibeos/scripts/validate-delivery-infrastructure.py"
CHECKLIST = REPO_ROOT / "plugins/vibeos/reference/comp/delivery-infrastructure-checklist.json"

PASSING_MISSION = """# Mission: Secure Client Portal

## Mission Promise

Give enterprise users a secure workflow with delivery infrastructure evidence.

## Delivery Infrastructure

- CI/CD pipeline runs tests, gates, dependency checks, security checks, and build.
- Deployment target, artifact, environment, and deploy command are explicit.
- Secrets are managed outside code with environment inventory.
- Observability, health, smoke, rollback, and runbook evidence are required.

## Observability And Operations

Health checks, logs, request IDs, smoke checks, rollback, and runbook notes are required.

## Acceptance Criteria

- Delivery evidence includes ci pipeline, deploy path, environment, secret handling, observability, health, smoke, rollback, and runbook proof.
"""


class DeliveryInfrastructureTests(unittest.TestCase):
    def test_delivery_checklist_is_valid(self):
        data = json.loads(CHECKLIST.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], "1.0")
        self.assertIn("auditing", data["lifecycle_integration"])
        ids = {dimension["id"] for dimension in data["dimensions"]}
        self.assertIn("delivery.pipeline_as_code", ids)
        self.assertIn("delivery.observability", ids)
        self.assertIn("delivery.rollback_runbook", ids)

    def test_validator_fails_when_mission_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", tmp, "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["findings"][0]["id"], "DELIVERY-MISSION-MISSING")

    def test_validator_fails_when_delivery_section_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(
                "# Mission: Thin Demo\n\n## Mission Promise\n\nDemo.\n\n## Observability And Operations\n\nLogs.\n\n## Acceptance Criteria\n\n- Works.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertIn("DELIVERY-MISSION-SECTION", {finding["id"] for finding in payload["findings"]})

    def test_validator_fails_without_delivery_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(PASSING_MISSION, encoding="utf-8")
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertIn("DELIVERY-EVIDENCE-MISSING", {finding["id"] for finding in payload["findings"]})

    def test_validator_detects_ci_and_deployment_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(PASSING_MISSION, encoding="utf-8")
            workflow_dir = root / ".github/workflows"
            workflow_dir.mkdir(parents=True)
            (workflow_dir / "ci.yml").write_text("name: ci\n", encoding="utf-8")
            (root / "Dockerfile").write_text("FROM node:22\n", encoding="utf-8")
            evidence_dir = root / "docs/evidence"
            evidence_dir.mkdir(parents=True)
            (evidence_dir / "DELIVERY-INFRASTRUCTURE.md").write_text(
                "# Delivery Infrastructure\n\nCI pipeline deploy environment secret observability health smoke rollback runbook evidence is present, but no verification command is described.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertIn(".github/workflows", payload["detected_ci_files"])
        self.assertIn("Dockerfile", payload["detected_deployment_files"])
        self.assertIn("DELIVERY-PIPELINE-GATES", {finding["id"] for finding in payload["findings"]})

    def test_validator_passes_with_explicit_delivery_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(PASSING_MISSION, encoding="utf-8")
            evidence_dir = root / "docs/evidence"
            evidence_dir.mkdir(parents=True)
            (evidence_dir / "DELIVERY-INFRASTRUCTURE.md").write_text(
                "# Delivery Infrastructure\n\nCI pipeline runs tests and gates. Deploy command, environment inventory, secret handling, observability logs, health checks, smoke checks, rollback, and runbook evidence are captured.\n",
                encoding="utf-8",
            )
            (root / "SCORECARD.md").write_text("# Scorecard\n\n## Delivery Infrastructure\n\nPass.\n", encoding="utf-8")
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["findings"], [])


if __name__ == "__main__":
    unittest.main()
