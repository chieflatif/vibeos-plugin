"""Fail-closed source-scope tests for the complexity gate."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "plugins/vibeos/scripts/validate-code-complexity.sh"


def run_gate(project_root, source_dir):
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_ROOT": str(project_root),
            "SOURCE_DIR": str(source_dir),
            "LANGUAGE": "python",
            "MAX_FUNCTION_LINES": "2",
            "WARN_FUNCTION_LINES": "1",
            "MAX_PARAMS": "6",
        }
    )
    return subprocess.run(
        ["bash", str(GATE)], capture_output=True, text=True, env=env
    )


class CodeComplexityRequiredTests(unittest.TestCase):
    def test_overlong_python_function_fails_the_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            source = project / "controlled_evaluation"
            source.mkdir()
            (source / "overlong.py").write_text(
                "def overlong():\n"
                "    first = 1\n"
                "    second = 2\n"
                "    return first + second\n"
            )

            result = run_gate(project, source)

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('function "overlong" is 4 lines', result.stdout)
            self.assertIn("complexity violations found", result.stdout)

    def test_empty_explicit_source_scope_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            source = project / "controlled_evaluation"
            source.mkdir()

            result = run_gate(project, source)

            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("ERROR: No Python files found", result.stdout)
            self.assertNotIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
