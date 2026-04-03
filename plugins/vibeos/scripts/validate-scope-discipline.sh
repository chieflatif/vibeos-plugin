#!/usr/bin/env bash
# validate-scope-discipline.sh — Bounded-delta discipline gate
#
# Prevents WO scope creep by enforcing hard limits on:
#   - production files changed in a single WO
#   - new production files introduced
#   - distinct project areas (top-level directories) touched
#   - test delta required when production code changes
#
# Configuration via environment variables:
#   MAX_PRODUCTION_FILES      — max changed production files (default: 10)
#   MAX_NEW_PRODUCTION_FILES  — max new production files (default: 4)
#   MAX_AREA_COUNT            — max distinct areas touched (default: 5)
#   REQUIRE_TEST_DELTA        — require test changes alongside code (default: true)
#
# Exit codes:
#   0 — All checks pass
#   1 — Scope discipline violated (blocking)
#   2 — Configuration error
set -euo pipefail

FRAMEWORK_VERSION="2.1.0"
GATE_NAME="validate-scope-discipline"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
MAX_PRODUCTION_FILES="${MAX_PRODUCTION_FILES:-10}"
MAX_NEW_PRODUCTION_FILES="${MAX_NEW_PRODUCTION_FILES:-4}"
MAX_AREA_COUNT="${MAX_AREA_COUNT:-5}"
REQUIRE_TEST_DELTA="${REQUIRE_TEST_DELTA:-true}"

echo "[${GATE_NAME}] Starting scope discipline check (v${FRAMEWORK_VERSION})"
echo "[${GATE_NAME}] Limits — production files: ${MAX_PRODUCTION_FILES}, new files: ${MAX_NEW_PRODUCTION_FILES}, areas: ${MAX_AREA_COUNT}, require_test_delta: ${REQUIRE_TEST_DELTA}"

python3 - "${PROJECT_ROOT}" "${MAX_PRODUCTION_FILES}" "${MAX_NEW_PRODUCTION_FILES}" "${MAX_AREA_COUNT}" "${REQUIRE_TEST_DELTA}" <<'PY'
from __future__ import annotations

import subprocess
import sys
from collections import Counter
from pathlib import Path

gate_name = "validate-scope-discipline"
project_root = Path(sys.argv[1])
max_production_files = int(sys.argv[2])
max_new_production_files = int(sys.argv[3])
max_area_count = int(sys.argv[4])
require_test_delta = sys.argv[5].lower() == "true"


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(project_root), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def changed_entries() -> list[tuple[str, str]]:
    result = git("status", "--porcelain", "--untracked-files=all")
    if result.returncode != 0:
        print(f"[{gate_name}] FAIL: could not inspect git status")
        sys.exit(2)

    entries: list[tuple[str, str]] = []
    for raw in result.stdout.splitlines():
        if not raw:
            continue
        status = raw[:2]
        entry = raw[3:] if len(raw) > 3 else ""
        if " -> " in entry:
            entry = entry.split(" -> ", 1)[1]
        if entry:
            entries.append((status, entry))
    return entries


def is_production_file(path: str) -> bool:
    """
    Production files are source code files that are not tests, docs, or config.
    Includes common source directories and excludes known non-production paths.
    """
    # Excluded from production count
    excluded_prefixes = (
        "tests/",
        "test/",
        "spec/",
        "docs/",
        ".vibeos/",
        ".claude/",
        "plugins/vibeos/hooks/",
        "plugins/vibeos/scripts/",
        "plugins/vibeos/agents/",
        "plugins/vibeos/skills/",
        "plugins/vibeos/decision-engine/",
        "plugins/vibeos/reference/",
        "plugins/vibeos/convergence/",
        "scripts/",
        "hooks/",
    )
    excluded_suffixes = (
        ".md",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
        ".env",
        ".env.example",
        ".gitignore",
        ".gitattributes",
        "Dockerfile",
        "docker-compose.yml",
        "Makefile",
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml",
        "setup.py",
        "package.json",
        "package-lock.json",
    )
    excluded_patterns = (
        "test_",
        "_test.",
        "conftest",
        "fixture",
        "mock",
    )

    for prefix in excluded_prefixes:
        if path.startswith(prefix):
            return False

    for suffix in excluded_suffixes:
        if path.endswith(suffix):
            return False

    for pattern in excluded_patterns:
        filename = path.split("/")[-1]
        if pattern in filename.lower():
            return False

    # Must have a recognized source extension
    source_extensions = (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".cs", ".rb", ".sh")
    return any(path.endswith(ext) for ext in source_extensions)


def is_test_file(path: str) -> bool:
    test_prefixes = ("tests/", "test/", "spec/")
    test_patterns = ("test_", "_test.", "conftest", ".spec.", ".test.")
    for prefix in test_prefixes:
        if path.startswith(prefix):
            return True
    filename = path.split("/")[-1]
    for pattern in test_patterns:
        if pattern in filename.lower():
            return True
    return False


def area_for(path: str) -> str:
    """Map a file path to its logical top-level area for blast-radius counting."""
    parts = path.split("/")
    if len(parts) >= 3 and parts[0] == "plugins":
        # plugins/vibeos/scripts -> plugins/vibeos/scripts
        return "/".join(parts[:3])
    if len(parts) >= 2 and parts[0] in ("src", "tests", "test", "docs", "scripts", "hooks", "infra", "config"):
        return "/".join(parts[:2])
    # Fallback: top-level directory
    return parts[0]


entries = changed_entries()

if not entries:
    print(f"[{gate_name}] PASS: no changed files detected")
    sys.exit(0)

production_entries = [(status, path) for status, path in entries if is_production_file(path)]
test_entries = [(status, path) for status, path in entries if is_test_file(path)]

production_files = sorted({path for _, path in production_entries})
new_production_files = sorted(
    {
        path
        for status, path in production_entries
        if status[0] == "A" or status == "??"
    }
)
areas = sorted(set(area_for(path) for _, path in entries))

issues: list[str] = []
notes: list[str] = []

if len(production_files) > max_production_files:
    issues.append(
        f"too many production files changed at once ({len(production_files)} > {max_production_files})"
    )

if len(new_production_files) > max_new_production_files:
    issues.append(
        f"too many new production files introduced at once ({len(new_production_files)} > {max_new_production_files})"
    )

if len(areas) > max_area_count:
    issues.append(f"change set spans too many areas ({len(areas)} > {max_area_count})")

if require_test_delta and production_files and not test_entries:
    notes.append("production code changed without any test delta (REQUIRE_TEST_DELTA=true)")

print(f"[{gate_name}] Production files changed : {len(production_files)}")
print(f"[{gate_name}] New production files      : {len(new_production_files)}")
print(f"[{gate_name}] Areas touched             : {len(areas)}")
if areas:
    print(f"[{gate_name}] Area summary: {', '.join(areas)}")

if production_files:
    print(f"[{gate_name}] Production file list:")
    for f in production_files:
        print(f"  {f}")

for note in notes:
    print(f"[{gate_name}] NOTE: {note}")

if issues:
    print(f"[{gate_name}] FAIL: bounded-delta discipline violated ({len(issues)} issue(s))")
    for issue in issues:
        print(f"  - {issue}")
    sys.exit(1)

print(f"[{gate_name}] PASS: change set remains bounded and reviewable")
PY
