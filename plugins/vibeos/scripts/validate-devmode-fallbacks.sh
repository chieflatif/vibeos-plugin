#!/usr/bin/env bash
# VibeOS — Dev-Mode Fallback Pattern Detector Gate
# Scans source code for patterns that silently return defaults in dev/test mode,
# which can mask production failures by manufacturing success.
#
# Usage:
#   bash scripts/validate-devmode-fallbacks.sh
#   bash scripts/validate-devmode-fallbacks.sh --project-dir /path/to/project
#   bash scripts/validate-devmode-fallbacks.sh --strict
#
# Environment:
#   PROJECT_ROOT  — project root directory (default: auto-detect)
#
# Exit codes:
#   0 = No dev-mode fallback patterns found (or advisory mode)
#   1 = Patterns found in strict mode
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="2.0.0"
GATE_NAME="validate-devmode-fallbacks"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
STRICT=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-dir) PROJECT_ROOT="$2"; shift 2 ;;
    --strict) STRICT=true; shift ;;
    -h|--help)
      echo "Usage: bash $0 [--project-dir PATH] [--strict]"
      exit 0
      ;;
    *) shift ;;
  esac
done

echo "[$GATE_NAME] Dev-Mode Fallback Detection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Project: $PROJECT_ROOT"
echo ""

if ! command -v python3 >/dev/null 2>&1; then
  echo "[$GATE_NAME] FAIL: python3 is required"
  exit 2
fi

# Run the detection in Python for robust multi-line and cross-language support
python3 - "$PROJECT_ROOT" "$STRICT" <<'PYEOF'
import os
import re
import sys
from pathlib import Path

project_root = Path(sys.argv[1])
strict = sys.argv[2] == "true"

GATE_NAME = "validate-devmode-fallbacks"

EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache",
    "venv", ".venv", "dist", "build", "vendor", "target",
    ".mypy_cache", ".tox", "htmlcov", "coverage", ".vibeos",
    ".claude", "test-fixture",
}

# Governance scripts that legitimately discuss these patterns
GOVERNANCE_PREFIXES = (
    "detect-", "enforce-", "validate-", "verify-", "scan-", "audit", "check-",
    "gate-runner", "test-quality", "e2e-test", "smoke-test",
)

# Test file patterns (skip these)
TEST_PATTERNS = [
    re.compile(r"test_.*\.py$"),
    re.compile(r".*_test\.py$"),
    re.compile(r"conftest\.py$"),
    re.compile(r".*\.test\.[jt]sx?$"),
    re.compile(r".*\.spec\.[jt]sx?$"),
    re.compile(r".*_test\.go$"),
]

SOURCE_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".go", ".rs", ".java", ".kt",
}

# ── Dev-mode fallback patterns ──────────────────────────────────
# Each pattern: (compiled_regex, description, language_hint)
FALLBACK_PATTERNS = [
    # Python: if dev/test mode, return default
    (re.compile(r"if\s+.*\b(dev|development|test|testing|local)\b.*mode.*:\s*return\b", re.IGNORECASE),
     "Dev-mode conditional return", "python"),
    (re.compile(r"if\s+.*\benvironment\b.*==.*\b(dev|development|test|testing|local)\b", re.IGNORECASE),
     "Environment equality check for dev/test", None),
    (re.compile(r"if\s+.*\bis_dev\b.*:\s*return\b", re.IGNORECASE),
     "is_dev guard with return", "python"),
    (re.compile(r"if\s+.*\bDEBUG\b.*:\s*return\b"),
     "DEBUG guard with return", None),
    (re.compile(r"if\s+.*\bsettings\.(environment|env)\b.*==.*\bEnvironment\.(dev|development|local|test)\b"),
     "Settings environment enum check for dev/test", "python"),
    (re.compile(r"if\s+.*\bENV\b.*(?:!=|!==).*\b(prod|production|staging)\b.*:\s*return\b", re.IGNORECASE),
     "Non-production guard with return", None),
    (re.compile(r"if\s+.*\bos\.environ\b.*get.*\b(ENV|ENVIRONMENT|NODE_ENV)\b.*(?:dev|test|local)", re.IGNORECASE),
     "os.environ check for dev/test", "python"),

    # JS/TS: process.env.NODE_ENV !== 'production'
    (re.compile(r"if\s*\(\s*process\.env\.NODE_ENV\s*[!=]==?\s*['\"](?:development|test)['\"]"),
     "NODE_ENV dev/test check", "js"),
    (re.compile(r"process\.env\.NODE_ENV\s*[!=]==?\s*['\"]production['\"].*return\b"),
     "NODE_ENV production guard with return", "js"),

    # Catch-all: except blocks that return defaults
    (re.compile(r"except\s*(?:\w+(?:\s+as\s+\w+)?)?\s*:\s*$"),
     "Bare/broad except (check if it returns a default on the next line)", "python"),

    # Go: build tags for dev
    (re.compile(r"//go:build\s+.*\bdev\b"),
     "Go build tag for dev-only code", "go"),
]

# Patterns for "return default" that commonly follow dev-mode guards
DEFAULT_RETURN_PATTERNS = [
    re.compile(r"^\s+return\s+\[\]"),
    re.compile(r"^\s+return\s+\{\}"),
    re.compile(r"^\s+return\s+None\b"),
    re.compile(r"^\s+return\s+null\b"),
    re.compile(r"^\s+return\s+\"\""),
    re.compile(r"^\s+return\s+''"),
    re.compile(r"^\s+return\s+0\b"),
    re.compile(r"^\s+return\s+false\b", re.IGNORECASE),
    re.compile(r"^\s+return\s+default\b", re.IGNORECASE),
]

def is_excluded(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    return False

def is_test_file(path: Path) -> bool:
    name = path.name
    for part in path.parts:
        if part in ("tests", "test", "__tests__", "test_utils"):
            return True
    return any(p.search(name) for p in TEST_PATTERNS)

def is_governance_script(path: Path) -> bool:
    name = path.name
    return any(name.startswith(prefix) for prefix in GOVERNANCE_PREFIXES)

def collect_files(root: Path) -> list:
    files = []
    for ext in SOURCE_EXTENSIONS:
        for f in root.rglob(f"*{ext}"):
            if not f.is_file():
                continue
            rel = f.relative_to(root)
            if is_excluded(rel):
                continue
            if is_test_file(f):
                continue
            if is_governance_script(f):
                continue
            files.append(f)
    return sorted(files)

# ── Scan ────────────────────────────────────────────────────────
findings = []

files = collect_files(project_root)

if not files:
    print(f"[{GATE_NAME}] SKIP: No source files found to scan")
    sys.exit(0)

for filepath in files:
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except OSError:
        continue

    lines = content.splitlines()
    rel_path = str(filepath.relative_to(project_root))

    for idx, line in enumerate(lines):
        for pattern, description, lang_hint in FALLBACK_PATTERNS:
            if not pattern.search(line):
                continue

            # Check if the next 1-3 lines contain a default return
            has_default_return = False
            for lookahead in range(1, min(4, len(lines) - idx)):
                next_line = lines[idx + lookahead]
                if any(rp.search(next_line) for rp in DEFAULT_RETURN_PATTERNS):
                    has_default_return = True
                    break
                # Stop looking if we hit another statement
                stripped = next_line.strip()
                if stripped and not stripped.startswith("#") and not stripped.startswith("//"):
                    break

            # Also flag if the pattern itself contains "return"
            if "return" in line.lower():
                has_default_return = True

            if has_default_return:
                trimmed = line.strip()[:200]
                findings.append({
                    "file": rel_path,
                    "line": idx + 1,
                    "pattern": description,
                    "content": trimmed,
                })
                break  # One finding per line

# ── Output ──────────────────────────────────────────────────────
print(f"Files scanned: {len(files)}")
print()

if findings:
    print(f"FINDINGS ({len(findings)}):")
    print()
    for f in findings:
        print(f"  {f['file']}:{f['line']}: {f['pattern']}")
        print(f"    {f['content']}")
        print(f"    ^ Ensure this code path is not the only one exercised by tests.")
        print()

print(f"[{GATE_NAME}] Total: {len(findings)} dev-mode fallback pattern(s) detected")

if findings:
    if strict:
        print(f"[{GATE_NAME}] FAIL: {len(findings)} pattern(s) found (strict mode)")
        sys.exit(1)
    else:
        print(f"[{GATE_NAME}] WARN: {len(findings)} pattern(s) found (advisory mode)")
        print(f"[{GATE_NAME}] NOTE: Use --strict to make this gate blocking")
        sys.exit(0)
else:
    print(f"[{GATE_NAME}] PASS: No dev-mode fallback patterns detected")
    sys.exit(0)
PYEOF
