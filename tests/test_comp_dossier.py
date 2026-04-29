import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOSSIER = REPO_ROOT / "plugins/vibeos/scripts/comp-dossier.py"


class CompDossierTests(unittest.TestCase):
    def test_dossier_fails_without_required_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                ["python3", str(DOSSIER), "--project-dir", tmp, "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertIn("MISSION.md", payload["missing_required"])
        self.assertIn("SCORECARD.md", payload["missing_required"])

    def test_dossier_marks_clean_closeout_as_proven(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text("# Mission: Clean\n", encoding="utf-8")
            (root / "COMP-PLAN.md").write_text("# COMP-PLAN: Clean\n", encoding="utf-8")
            (root / "SCORECARD.md").write_text("# Scorecard\n\n## Status\n\n`pass`\n", encoding="utf-8")
            evidence = root / "docs/evidence"
            evidence.mkdir(parents=True, exist_ok=True)
            (evidence / "FLOW-INTEGRITY.md").write_text("# Flow\n\n## Status\n\n`present`\n", encoding="utf-8")
            (evidence / "SYSTEM-INVARIANTS.md").write_text("# Invariants\n\n## Status\n\n`present`\n", encoding="utf-8")
            (evidence / "DEPENDENCY-INTELLIGENCE.md").write_text("# Dependency Intelligence\n\n## Status\n\n`present`\n", encoding="utf-8")
            (evidence / "DELIVERY-INFRASTRUCTURE.md").write_text("# Delivery Infrastructure\n\n## Status\n\n`present`\n", encoding="utf-8")
            (evidence / "COMP-INTEGRATION-EVIDENCE.md").write_text("# Integration\n\n## Status\n\n`ready_for_integrated_checks`\n", encoding="utf-8")
            (evidence / "RED-TEAM-REPORT.md").write_text("# Red Team\n\n## Status\n\n`reviewed`\n", encoding="utf-8")

            result = subprocess.run(
                ["python3", str(DOSSIER), "--project-dir", tmp, "--json"],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "proven")
            text = (root / "EVIDENCE-DOSSIER.md").read_text(encoding="utf-8")
            self.assertIn("## Claim States", text)
            self.assertIn("## Artifact Index", text)
            self.assertIn("Primary user-flow and objective fidelity evidence", text)
            self.assertIn("System invariant and state safety evidence", text)
            self.assertIn("Dependency current-source, compatibility, lockfile, audit, and upgrade evidence", text)
            self.assertIn("CI/CD, deployment, observability, smoke, rollback, and runbook evidence", text)
            self.assertIn("## Speed And Rework Metrics", text)


if __name__ == "__main__":
    unittest.main()
