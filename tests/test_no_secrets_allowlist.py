"""WO-108: secret-scanner allowlist + pytest scoping.

The fixture's intentional fake AWS key must be exempted by the allowlist while
real-pattern secrets anywhere else still fail the scan. The fake key is built by
concatenation and written as bare file content so this test source does not
itself contain a literal AWS-key match or a hardcoded-credential assignment
(the repo's own pre-write secret hook would otherwise block it).
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCANNER = REPO_ROOT / "plugins/vibeos/scripts/validate-no-secrets.sh"

# AKIA + 16 chars in [0-9A-Z] — matches the scanner's aws_access_key_id pattern.
FAKE_AWS_KEY = "AKIA" + "1234567890" + "ABCDEF"


def _run_scanner(*args, cwd=None):
    return subprocess.run(
        ["bash", str(SCANNER), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
    )


class SecretAllowlistTests(unittest.TestCase):
    def test_fixture_secret_is_allowlisted(self):
        # Real path: scan the whole repo (git mode). The fixture's fake key is
        # the only secret hit and must be exempted by the allowlist → clean pass.
        result = _run_scanner(cwd=str(REPO_ROOT))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)

    def test_real_secret_outside_allowlist_is_detected(self):
        # A non-git temp dir forces the filesystem-walk path. A secret here is
        # NOT in the allowlist (different path) → must still be detected.
        with tempfile.TemporaryDirectory() as tmp:
            leak = Path(tmp) / "leak.py"
            leak.write_text(FAKE_AWS_KEY + "\n")
            result = _run_scanner(".", cwd=tmp)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("aws_access_key_id", result.stdout)

    def test_allowlist_does_not_exempt_same_key_at_other_path(self):
        # Same fake value at a different path → allowlist is path-scoped,
        # so the secret is still caught.
        with tempfile.TemporaryDirectory() as tmp:
            other = Path(tmp) / "src" / "other.py"
            other.parent.mkdir(parents=True)
            other.write_text(FAKE_AWS_KEY + "\n")
            result = _run_scanner(".", cwd=tmp)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)


class AllowlistHardeningTests(unittest.TestCase):
    """Regression tests for the WO-108 correctness-audit fixes."""

    def _scan_repo_with_allowlist(self, entries):
        with tempfile.TemporaryDirectory() as tmp:
            al = Path(tmp) / "al.json"
            al.write_text(json.dumps({"allowlist": entries}))
            env = {**os.environ, "SECRETS_ALLOWLIST": str(al)}
            return subprocess.run(
                ["bash", str(SCANNER)],
                capture_output=True,
                text=True,
                cwd=str(REPO_ROOT),
                env=env,
            )

    def test_value_contains_pins_to_token_not_whole_line(self):
        # "API_KEY" appears on the fixture line but NOT inside the secret token.
        # Pinning against the token means this entry must NOT exempt the fixture.
        result = self._scan_repo_with_allowlist([{
            "path": "plugins/vibeos/test-fixture/src/app.py",
            "pattern": "aws_access_key_id",
            "value_contains": "API_KEY",
        }])
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_entry_without_value_contains_never_exempts(self):
        # A path+pattern entry with no value pin must not blanket-exempt.
        result = self._scan_repo_with_allowlist([{
            "path": "plugins/vibeos/test-fixture/src/app.py",
            "pattern": "aws_access_key_id",
        }])
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_suffix_path_collision_does_not_exempt(self):
        # An entry path that is only a suffix of the real fixture path must not
        # match (exact repo-relative match required).
        result = self._scan_repo_with_allowlist([{
            "path": "src/app.py",
            "pattern": "aws_access_key_id",
            "value_contains": "1234567890ABCDEF",
        }])
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)


class PytestScopingTests(unittest.TestCase):
    def test_pytest_ini_scopes_to_tests_dir(self):
        ini = REPO_ROOT / "pytest.ini"
        self.assertTrue(ini.exists(), "pytest.ini must exist to scope collection")
        self.assertRegex(ini.read_text(), r"testpaths\s*=\s*tests")

    def test_bare_pytest_collection_excludes_fixture(self):
        # Bare collection from repo root must not pull in the fixture sample
        # (which fails import) once testpaths is scoped to tests/.
        result = subprocess.run(
            ["python3", "-m", "pytest", "--co", "-q"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("test-fixture", result.stdout)


if __name__ == "__main__":
    unittest.main()
