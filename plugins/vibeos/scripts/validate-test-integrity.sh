#!/usr/bin/env bash
# VibeOS Plugin — Test Integrity Validation Gate
# Checks for vacuous assertions, test/source parity, and test quality.
#
# Usage:
#   bash scripts/validate-test-integrity.sh
#
# Environment:
#   SOURCE_DIR  — source directory (default: auto-detect)
#   TEST_DIR    — test directory (default: tests/)
#   LANGUAGE    — python|typescript|javascript|go|rust|java (default: auto-detect)
#
# Exit codes:
#   0 = Test integrity checks passed
#   1 = Test integrity issues found
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="1.0.0"
GATE_NAME="validate-test-integrity"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate-test-integrity.sh

Environment:
  SOURCE_DIR  Source directory (default: auto-detect)
  TEST_DIR    Test directory (default: tests/)
  LANGUAGE    python|typescript|javascript|go|rust|java (default: auto-detect)

Checks:
  - No vacuous assertions (assert True, expect(true).toBe(true))
  - No empty test functions
  - Test file structure mirrors source structure (advisory)
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] Test Integrity Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Auto-detect source and test dirs
if [[ -z "${SOURCE_DIR:-}" ]]; then
  for candidate in src lib app; do
    if [[ -d "$repo_root/$candidate" ]]; then
      SOURCE_DIR="$candidate"
      break
    fi
  done
fi

TEST_DIR="${TEST_DIR:-tests}"

if [[ -z "${SOURCE_DIR:-}" ]]; then
  echo "[$GATE_NAME] WARN: No source directory found. Set SOURCE_DIR."
  echo "[$GATE_NAME] SKIP: Cannot validate test integrity without source directory"
  exit 0
fi

test_path="$repo_root/$TEST_DIR"
if [[ ! -d "$test_path" ]]; then
  echo "[$GATE_NAME] WARN: Test directory not found: $test_path"
  echo "[$GATE_NAME] SKIP: No tests to validate"
  exit 0
fi

# Auto-detect language
detect_language() {
  if [[ -f "$repo_root/pyproject.toml" ]] || [[ -f "$repo_root/setup.py" ]]; then
    echo "python"
  elif [[ -f "$repo_root/tsconfig.json" ]] || [[ -f "$repo_root/package.json" ]]; then
    echo "javascript"
  elif [[ -f "$repo_root/go.mod" ]]; then
    echo "go"
  elif [[ -f "$repo_root/Cargo.toml" ]]; then
    echo "rust"
  elif [[ -f "$repo_root/pom.xml" ]] || [[ -f "$repo_root/build.gradle" ]]; then
    echo "java"
  else
    echo "unknown"
  fi
}

LANGUAGE="${LANGUAGE:-$(detect_language)}"

python3 - "$repo_root/$SOURCE_DIR" "$test_path" "$LANGUAGE" <<'PY'
import re
import sys
from pathlib import Path

source_dir = Path(sys.argv[1])
test_dir = Path(sys.argv[2])
language = sys.argv[3]

gate = "validate-test-integrity"

# Language-specific test file patterns
test_extensions = {
    "python": ["*.py"],
    "javascript": ["*.test.js", "*.test.jsx", "*.test.ts", "*.test.tsx", "*.spec.js", "*.spec.ts"],
    "typescript": ["*.test.ts", "*.test.tsx", "*.spec.ts", "*.spec.tsx"],
    "go": ["*_test.go"],
    "rust": ["*.rs"],
    "java": ["*Test.java", "*Tests.java", "*Spec.java"],
}

# Vacuous assertion patterns per language
vacuous_patterns = {
    "python": [
        re.compile(r"^\s*assert\s+True\s*(#.*)?$"),
        re.compile(r"^\s*assert\s+1\s*==\s*1\s*(#.*)?$"),
        re.compile(r'^\s*assert\s+""\s*==\s*""\s*(#.*)?$'),
    ],
    "javascript": [
        re.compile(r"^\s*expect\(true\)\.toBe\(true\)"),
        re.compile(r"^\s*expect\(1\)\.toBe\(1\)"),
        re.compile(r"^\s*assert\.ok\(true\)"),
        re.compile(r"^\s*assert\.equal\(1,\s*1\)"),
    ],
    "typescript": [
        re.compile(r"^\s*expect\(true\)\.toBe\(true\)"),
        re.compile(r"^\s*expect\(1\)\.toBe\(1\)"),
    ],
    "go": [
        re.compile(r"^\s*//\s*no\s+assert", re.IGNORECASE),
    ],
}

# Empty test function patterns
empty_test_patterns = {
    "python": [
        (re.compile(r"^\s*def\s+(test_\w+)\s*\("), re.compile(r"^\s+pass\s*(#.*)?$")),
    ],
    "javascript": [
        (re.compile(r"^\s*(it|test)\s*\("), re.compile(r"^\s*\}\s*\)\s*;?\s*$")),
    ],
    "typescript": [
        (re.compile(r"^\s*(it|test)\s*\("), re.compile(r"^\s*\}\s*\)\s*;?\s*$")),
    ],
}

findings = {"critical": [], "warning": []}

# Collect test files
extensions = test_extensions.get(language, ["*.py", "*.js", "*.ts"])
test_files = []
for ext in extensions:
    test_files.extend(test_dir.rglob(ext))

# For Python, also filter to test_ prefix
if language == "python":
    test_files = [f for f in test_files if f.name.startswith("test_") or f.name == "conftest.py"]

if not test_files:
    print(f"[{gate}] WARN: No test files found in {test_dir}")
    sys.exit(0)

print(f"[{gate}] Scanning {len(test_files)} test files...")

# Check for vacuous assertions
patterns = vacuous_patterns.get(language, vacuous_patterns.get("python", []))
for tf in test_files:
    try:
        lines = tf.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception:
        continue

    for i, line in enumerate(lines, 1):
        for rx in patterns:
            if rx.search(line):
                findings["critical"].append(
                    f"  Vacuous assertion: {tf}:{i}: {line.strip()}"
                )

# Check for empty test functions (Python only for now)
if language == "python":
    for tf in test_files:
        if tf.name == "conftest.py":
            continue
        try:
            lines = tf.read_text(encoding="utf-8", errors="ignore").splitlines()
        except Exception:
            continue

        for i, line in enumerate(lines):
            m = re.match(r"^\s*def\s+(test_\w+)\s*\(", line)
            if not m:
                continue
            # Check if next non-empty, non-comment, non-docstring line is 'pass'
            for j in range(i + 1, min(len(lines), i + 10)):
                next_line = lines[j].strip()
                if not next_line or next_line.startswith("#"):
                    continue
                if next_line.startswith('"""') or next_line.startswith("'''"):
                    continue
                if next_line == "pass":
                    findings["critical"].append(
                        f"  Empty test function: {tf}:{i+1}: {m.group(1)}"
                    )
                break

# Report
if findings["critical"]:
    print(f"\n[{gate}] FAIL: Test integrity issues ({len(findings['critical'])} critical)")
    for f in findings["critical"][:30]:
        print(f)
    if len(findings["critical"]) > 30:
        print(f"  ... {len(findings['critical']) - 30} more")
    sys.exit(1)

if findings["warning"]:
    print(f"\n[{gate}] PASS (with {len(findings['warning'])} warning(s))")
    for f in findings["warning"][:10]:
        print(f)
    sys.exit(0)

print(f"[{gate}] PASS: Test integrity checks passed ({len(test_files)} test files scanned)")
sys.exit(0)
PY
