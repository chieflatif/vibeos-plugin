import json
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = REPO_ROOT / "plugins/vibeos/scripts/validate-dependency-intelligence.py"
CHECKLIST = REPO_ROOT / "plugins/vibeos/reference/comp/dependency-intelligence-checklist.json"
STACK_CURRENCY = REPO_ROOT / "plugins/vibeos/reference/comp/stack-dependency-currency.json"

PASSING_MISSION = """# Mission: Secure Client Portal

## Mission Promise

Give enterprise users a secure workflow with current dependency evidence.

## Enterprise Foundation Baseline

Dependency freshness, security, lockfile discipline, compatibility, and evidence are required.

## Dependency Intelligence

- Dependency versions must be verified against current source evidence.
- Lockfile-backed installs must preserve package manager compatibility.
- Security audit evidence must be attached for package changes.

## Acceptance Criteria

- Dependency decisions include source, verified date, compatibility, audit, and lockfile evidence.
"""


class DependencyIntelligenceTests(unittest.TestCase):
    def test_dependency_checklist_is_valid(self):
        data = json.loads(CHECKLIST.read_text(encoding="utf-8"))
        self.assertEqual(data["schema_version"], "1.0")
        self.assertIn("auditing", data["lifecycle_integration"])
        ids = {dimension["id"] for dimension in data["dimensions"]}
        self.assertIn("dependencies.current_evidence", ids)
        self.assertIn("dependencies.compatibility", ids)
        self.assertIn("dependencies.security_audit", ids)

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
        self.assertEqual(payload["findings"][0]["id"], "DEP-MISSION-MISSING")

    def test_validator_fails_when_dependency_section_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(
                "# Mission: Thin Demo\n\n## Mission Promise\n\nDemo.\n\n## Enterprise Foundation Baseline\n\nSecurity.\n\n## Acceptance Criteria\n\n- Works.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertIn("DEP-MISSION-SECTION", {finding["id"] for finding in payload["findings"]})

    def test_validator_fails_when_manifest_has_no_lockfile_or_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(PASSING_MISSION, encoding="utf-8")
            (root / "package.json").write_text('{"dependencies":{"react":"19.1.0"}}\n', encoding="utf-8")
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        ids = {finding["id"] for finding in payload["findings"]}
        self.assertIn("DEP-LOCKFILE-MISSING", ids)
        self.assertIn("DEP-EVIDENCE-MISSING", ids)

    def test_validator_passes_with_explicit_dependency_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(PASSING_MISSION, encoding="utf-8")
            (root / "package.json").write_text('{"dependencies":{"react":"19.1.0"}}\n', encoding="utf-8")
            (root / "package-lock.json").write_text('{"lockfileVersion":3}\n', encoding="utf-8")
            evidence_dir = root / "docs/evidence"
            evidence_dir.mkdir(parents=True)
            (evidence_dir / "DEPENDENCY-INTELLIGENCE.md").write_text(
                "# Dependency Intelligence\n\nSource verified on 2026-04-29. Compatibility checked. Audit command captured. Lockfile present.\n",
                encoding="utf-8",
            )
            (root / "SCORECARD.md").write_text("# Scorecard\n\n## Dependency Intelligence\n\nPass.\n", encoding="utf-8")
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["findings"], [])

    def test_validator_fails_when_stack_currency_context_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(PASSING_MISSION, encoding="utf-8")
            (root / "package.json").write_text('{"dependencies":{"react":"19.1.0"}}\n', encoding="utf-8")
            (root / "package-lock.json").write_text('{"lockfileVersion":3}\n', encoding="utf-8")
            reference_dir = root / ".vibeos/reference/comp"
            reference_dir.mkdir(parents=True)
            (reference_dir / "stack-dependency-currency.json").write_text(
                STACK_CURRENCY.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            evidence_dir = root / "docs/evidence"
            evidence_dir.mkdir(parents=True)
            (evidence_dir / "DEPENDENCY-INTELLIGENCE.md").write_text(
                "# Dependency Intelligence\n\nSource verified on 2026-04-29. Compatibility checked. Audit command captured. Lockfile present.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertIn("typescript_node", payload["detected_currency_packs"])
        self.assertIn("frontend_app", payload["detected_currency_packs"])
        self.assertIn("DEP-STACK-EVIDENCE", {finding["id"] for finding in payload["findings"]})

    def test_validator_passes_with_stack_currency_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "MISSION.md").write_text(PASSING_MISSION, encoding="utf-8")
            (root / "package.json").write_text('{"dependencies":{"react":"19.1.0"}}\n', encoding="utf-8")
            (root / "package-lock.json").write_text('{"lockfileVersion":3}\n', encoding="utf-8")
            reference_dir = root / ".vibeos/reference/comp"
            reference_dir.mkdir(parents=True)
            (reference_dir / "stack-dependency-currency.json").write_text(
                STACK_CURRENCY.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            evidence_dir = root / "docs/evidence"
            evidence_dir.mkdir(parents=True)
            (evidence_dir / "DEPENDENCY-INTELLIGENCE.md").write_text(
                "# Dependency Intelligence\n\nSource verified on 2026-04-29. Node package manager compatibility checked. Lockfile present. Security audit captured. Frontend framework router browser build compatibility documented.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["python3", str(VALIDATOR), "--project-dir", str(root), "--json"],
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "pass")


if __name__ == "__main__":
    unittest.main()
