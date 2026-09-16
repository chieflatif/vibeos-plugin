"""Fail-closed tool-availability contracts for shipped quality gates."""

import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
QUALITY_GATE = REPO_ROOT / "plugins/vibeos/scripts/validate-code-quality.sh"
COMPLEXITY_GATE = REPO_ROOT / "plugins/vibeos/scripts/validate-code-complexity.sh"


def isolated_path(tools):
    python = Path(tools) / "python3"
    python.write_text(f"#!/bin/sh\nexec {shlex.quote(sys.executable)} \"$@\"\n")
    python.chmod(0o755)
    return f"{tools}:/usr/bin:/bin"


def run_gate(gate, project, source, tools, language, linter=None):
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_ROOT": str(project),
            "SOURCE_DIR": str(source),
            "LANGUAGE": language,
            "PATH": isolated_path(tools),
        }
    )
    if linter is not None:
        env["LINTER"] = linter
    return subprocess.run(
        ["/bin/bash", str(gate)], capture_output=True, text=True, env=env
    )


class GateMissingToolsTests(unittest.TestCase):
    def test_python_quality_gate_skips_nonzero_without_linter(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            source = project / "src"
            source.mkdir()
            (source / "module.py").write_text("value = 1\n")
            tools = project / "tools"
            tools.mkdir()

            result = run_gate(
                QUALITY_GATE, project, source, tools, "python", "ruff check"
            )

            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("SKIP: Required Python linter not available: ruff", result.stdout)
            self.assertNotIn("PASS", result.stdout)

    def test_typescript_quality_gate_skips_nonzero_without_compiler(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            source = project / "src"
            source.mkdir()
            (source / "module.ts").write_text("export const value = 1;\n")
            (project / "tsconfig.json").write_text("{}\n")
            tools = project / "tools"
            tools.mkdir()

            result = run_gate(QUALITY_GATE, project, source, tools, "typescript")

            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("SKIP: TypeScript compiler not available", result.stdout)
            self.assertNotIn("PASS", result.stdout)

    def test_javascript_quality_gate_skips_nonzero_without_eslint(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            source = project / "src"
            source.mkdir()
            (source / "module.js").write_text("export const value = 1;\n")
            (project / "eslint.config.js").write_text("export default [];\n")
            tools = project / "tools"
            tools.mkdir()

            result = run_gate(QUALITY_GATE, project, source, tools, "javascript")

            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("SKIP: ESLint not available", result.stdout)
            self.assertNotIn("PASS", result.stdout)

    def test_python_complexity_gate_skips_nonzero_without_primary_tool(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            source = project / "src"
            source.mkdir()
            (source / "module.py").write_text("def value():\n    return 1\n")
            tools = project / "tools"
            tools.mkdir()

            result = run_gate(COMPLEXITY_GATE, project, source, tools, "python")

            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("SKIP: Python cyclomatic complexity tool unavailable", result.stdout)
            self.assertNotIn("PASS", result.stdout)

    def test_ruff_c901_fallback_checks_parse_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            source = project / "src"
            source.mkdir()
            (source / "broken.py").write_text("def broken(:\n    return 1\n")
            tools = project / "tools"
            tools.mkdir()
            ruff = tools / "ruff"
            ruff.write_text("#!/bin/sh\nexit 0\n")
            ruff.chmod(0o755)

            result = run_gate(COMPLEXITY_GATE, project, source, tools, "python")

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("FAIL: broken.py:1: parse error", result.stdout)
            self.assertNotIn("PASS", result.stdout)

    def test_ruff_c901_unreadable_failure_is_not_a_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            source = project / "src"
            source.mkdir()
            (source / "module.py").write_text("def value():\n    return 1\n")
            tools = project / "tools"
            tools.mkdir()
            ruff = tools / "ruff"
            ruff.write_text("#!/bin/sh\nexit 1\n")
            ruff.chmod(0o755)

            result = run_gate(COMPLEXITY_GATE, project, source, tools, "python")

            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("FAIL: ruff C901 returned no readable complexity result", result.stdout)
            self.assertNotIn("PASS", result.stdout)

    def test_go_complexity_gate_skips_nonzero_without_gocyclo(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            source = project / "src"
            source.mkdir()
            (source / "module.go").write_text("package example\n")
            tools = project / "tools"
            tools.mkdir()

            result = run_gate(COMPLEXITY_GATE, project, source, tools, "go")

            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("SKIP: Go cyclomatic complexity tool unavailable", result.stdout)
            self.assertNotIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
