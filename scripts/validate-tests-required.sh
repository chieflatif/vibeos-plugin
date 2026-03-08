#!/usr/bin/env bash
# VibeOS Plugin — Tests Required Gate (TDD Enforcement)
# Fails when no test files exist. Ensures the project has at least one test.
#
# Usage:
#   bash scripts/validate-tests-required.sh
#
# Environment:
#   TEST_DIR    — test directory (default: auto-detect)
#   SOURCE_DIR  — source directory for mirror check (default: auto-detect)
#   LANGUAGE    — python|typescript|javascript|go|rust|java (default: auto-detect)
#   MIN_TESTS   — minimum number of test files required (default: 1)
#
# Exit codes:
#   0 = Tests exist (requirement met)
#   1 = No tests found (blocks commit/WO completion)
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="1.0.0"
GATE_NAME="validate-tests-required"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate-tests-required.sh

Environment:
  TEST_DIR    Test directory (default: auto-detect tests/, __tests__/, src/)
  SOURCE_DIR  Source directory (default: auto-detect)
  LANGUAGE    python|typescript|javascript|go|rust|java (default: auto-detect)
  MIN_TESTS   Minimum test files required (default: 1)

Behavior:
  FAIL if no test files exist — enforces TDD. Use known_baselines for existing
  projects with no tests during adoption.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] Tests Required (TDD Enforcement)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MIN_TESTS="${MIN_TESTS:-1}"

# Auto-detect language
detect_language() {
  if [[ -f "$repo_root/pyproject.toml" ]] || [[ -f "$repo_root/setup.py" ]] || [[ -f "$repo_root/requirements.txt" ]]; then
    echo "python"
  elif [[ -f "$repo_root/tsconfig.json" ]]; then
    echo "typescript"
  elif [[ -f "$repo_root/package.json" ]]; then
    echo "javascript"
  elif [[ -f "$repo_root/go.mod" ]]; then
    echo "go"
  elif [[ -f "$repo_root/Cargo.toml" ]]; then
    echo "rust"
  elif [[ -f "$repo_root/pom.xml" ]] || [[ -f "$repo_root/build.gradle" ]] || [[ -f "$repo_root/build.gradle.kts" ]]; then
    echo "java"
  else
    echo "unknown"
  fi
}

LANGUAGE="${LANGUAGE:-$(detect_language)}"

# Count test files using language-specific patterns
count_tests() {
  local count=0
  local test_dirs=()

  # Collect test directories to scan
  if [[ -n "${TEST_DIR:-}" ]]; then
    test_dirs+=("$repo_root/$TEST_DIR")
  else
    # Auto-detect: tests/, __tests__/, src/ (for colocated tests)
    for d in tests __tests__ test; do
      [[ -d "$repo_root/$d" ]] && test_dirs+=("$repo_root/$d")
    done
    # JS/TS: src/**/*.test.* colocated
    if [[ -d "$repo_root/src" ]] && [[ "$LANGUAGE" == "javascript" || "$LANGUAGE" == "typescript" ]]; then
      test_dirs+=("$repo_root/src")
    fi
    # Go/Rust: tests live alongside source
    if [[ -d "$repo_root" ]]; then
      case "$LANGUAGE" in
        go)   test_dirs+=("$repo_root") ;;
        rust) [[ -d "$repo_root/tests" ]] && test_dirs+=("$repo_root/tests"); test_dirs+=("$repo_root") ;;
        java) [[ -d "$repo_root/src/test" ]] && test_dirs+=("$repo_root/src/test") ;;
      esac
    fi
  fi

  # If no dirs found, try default (ensure non-empty for set -u safe iteration)
  if [[ ${#test_dirs[@]} -eq 0 ]]; then
    [[ -d "$repo_root/tests" ]] && test_dirs+=("$repo_root/tests")
  fi
  if [[ ${#test_dirs[@]} -eq 0 ]]; then
    test_dirs+=("$repo_root")
  fi

  case "$LANGUAGE" in
    python)
      for d in "${test_dirs[@]}"; do
        [[ -d "$d" ]] || continue
        count=$((count + $(find "$d" -maxdepth 5 \( -name "test_*.py" -o -name "*_test.py" \) 2>/dev/null | wc -l | tr -d ' ')))
      done
      ;;
    typescript|javascript)
      for d in "${test_dirs[@]}"; do
        [[ -d "$d" ]] || continue
        count=$((count + $(find "$d" -maxdepth 6 \( -name "*.test.ts" -o -name "*.test.tsx" -o -name "*.test.js" -o -name "*.test.jsx" -o -name "*.spec.ts" -o -name "*.spec.tsx" -o -name "*.spec.js" \) 2>/dev/null | wc -l | tr -d ' ')))
      done
      ;;
    go)
      for d in "${test_dirs[@]}"; do
        [[ -d "$d" ]] || continue
        count=$((count + $(find "$d" -maxdepth 6 -name "*_test.go" 2>/dev/null | wc -l | tr -d ' ')))
      done
      ;;
    rust)
      for d in "${test_dirs[@]}"; do
        [[ -d "$d" ]] || continue
        # Integration tests in tests/, unit tests in *_test modules
        count=$((count + $(find "$d" -maxdepth 3 -name "*.rs" -path "*/tests/*" 2>/dev/null | wc -l | tr -d ' ')))
        count=$((count + $(find "$d" -maxdepth 6 -name "*.rs" -exec grep -l '#\[cfg(test)\]' {} \; 2>/dev/null | wc -l | tr -d ' ')))
      done
      # If still 0, check for any tests/ dir with .rs files
      if [[ $count -eq 0 ]] && [[ -d "$repo_root/tests" ]]; then
        count=$(find "$repo_root/tests" -name "*.rs" 2>/dev/null | wc -l | tr -d ' ')
      fi
      ;;
    java)
      for d in "${test_dirs[@]}"; do
        [[ -d "$d" ]] || continue
        count=$((count + $(find "$d" -maxdepth 6 \( -name "*Test.java" -o -name "*Tests.java" -o -name "*Spec.java" \) 2>/dev/null | wc -l | tr -d ' ')))
      done
      ;;
    *)
      # Fallback: any common test patterns
      for d in "${test_dirs[@]}"; do
        [[ -d "$d" ]] || continue
        count=$((count + $(find "$d" -maxdepth 5 \( -name "test_*.py" -o -name "*_test.py" -o -name "*.test.*" -o -name "*.spec.*" -o -name "*_test.go" \) 2>/dev/null | wc -l | tr -d ' ')))
      done
      ;;
  esac

  echo "$count"
}

count=$(count_tests)

if [[ "$count" -lt "$MIN_TESTS" ]]; then
  echo "[$GATE_NAME] FAIL: No test files found (required: >= $MIN_TESTS)"
  echo "[$GATE_NAME] TDD requires at least one test. Add tests to tests/, __tests__/, or colocate with source."
  echo "[$GATE_NAME] For existing projects: add to known_baselines during Phase 6 adoption."
  exit 1
fi

echo "[$GATE_NAME] PASS: $count test file(s) found"
exit 0
