"""Contract tests for target-project resolution in the code-quality gate."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "plugins/vibeos/scripts/validate-code-quality.sh"


def write_linter(directory):
    linter = Path(directory) / "quality-linter"
    linter.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        "printf '%s\\n' \"$1\" > \"$PROJECT_ROOT/lint-target.txt\"\n"
        "test -d \"$1\"\n"
    )
    linter.chmod(0o755)
    return linter


def run_gate(project_root, source_dir, tool_dir):
    env = os.environ.copy()
    env.update(
        {
            "PROJECT_ROOT": str(project_root),
            "SOURCE_DIR": str(source_dir),
            "LANGUAGE": "python",
            "LINTER": "quality-linter",
            "PATH": f"{tool_dir}:{env['PATH']}",
        }
    )
    return subprocess.run(
        ["bash", str(GATE)], capture_output=True, text=True, env=env
    )


class CodeQualityProjectRootTests(unittest.TestCase):
    def test_relative_source_is_resolved_under_explicit_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            project = workspace / "external-project"
            source = project / "src"
            source.mkdir(parents=True)
            (source / "module.py").write_text("value = 1\n")
            tool_dir = workspace / "tools"
            tool_dir.mkdir()
            write_linter(tool_dir)

            result = run_gate(project, "src", tool_dir)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("Language: python", result.stdout)
            self.assertIn("Source directory: src", result.stdout)
            self.assertEqual((project / "lint-target.txt").read_text().strip(), str(source.resolve()))

    def test_absolute_source_dir_is_used_without_prefixing_project_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            project = workspace / "external-project"
            project.mkdir()
            source = workspace / "separate-source"
            source.mkdir()
            (source / "module.py").write_text("value = 1\n")
            tool_dir = workspace / "tools"
            tool_dir.mkdir()
            write_linter(tool_dir)

            result = run_gate(project, source, tool_dir)

            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(f"Source directory: {source}", result.stdout)
            self.assertEqual((project / "lint-target.txt").read_text().strip(), str(source))


if __name__ == "__main__":
    unittest.main()
