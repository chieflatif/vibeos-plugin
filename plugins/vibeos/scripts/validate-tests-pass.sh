#!/usr/bin/env bash
# VibeOS Plugin — Tests Must Pass Gate (TDD Enforcement)
# Runs the project's test command and fails if it fails.
# Complements validate-tests-required.sh: that gate blocks when no test files exist;
# this gate blocks when tests exist but fail (or when the test command fails).
#
# Usage:
#   bash scripts/validate-tests-pass.sh
#
# Environment:
#   TEST_CMD     — override: exact command to run (e.g. "pytest" or "pnpm test")
#   PROJECT_ROOT — project root (default: parent of scripts/)
#   LANGUAGE     — python|typescript|javascript|go|rust|java (default: auto-detect)
#
# Exit codes:
#   0 = Tests passed
#   1 = Tests failed or no test command available
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="2.2.0"
GATE_NAME="validate-tests-pass"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate-tests-pass.sh

Environment:
  TEST_CMD     Override: exact command to run (e.g. "pytest" or "pnpm test")
  PROJECT_ROOT Project root (default: parent of scripts/)
  LANGUAGE     python|typescript|javascript|go|rust|java (default: auto-detect)

Behavior:
  - Auto-detects test command from package.json, pyproject.toml, go.mod, Cargo.toml, etc.
  - Runs the command and fails (exit 1) if it returns non-zero
  - If no test command can be determined and TDD is enforced, fails with guidance
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] Tests Must Pass (TDD Enforcement)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="${PROJECT_ROOT:-$(cd "$script_dir/.." && pwd)}"
cd "$repo_root"

# If TEST_CMD is explicitly set, use it
if [[ -n "${TEST_CMD:-}" ]]; then
  echo "[$GATE_NAME] Using TEST_CMD: $TEST_CMD"
  if eval "$TEST_CMD"; then
    echo "[$GATE_NAME] PASS: Tests passed"
    exit 0
  else
    echo "[$GATE_NAME] FAIL: Test command returned non-zero"
    exit 1
  fi
fi

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

# Resolve test command by language / package manager
run_tests() {
  case "$LANGUAGE" in
    python)
      if command -v pytest &>/dev/null; then
        pytest -q --tb=short 2>/dev/null || pytest -q 2>/dev/null || pytest
      elif python3 -c "import pytest" 2>/dev/null; then
        python3 -m pytest -q --tb=short 2>/dev/null || python3 -m pytest -q 2>/dev/null || python3 -m pytest
      else
        echo "[$GATE_NAME] FAIL: pytest not installed. Install with: pip install pytest"
        return 1
      fi
      ;;
    typescript|javascript)
      if [[ -f "$repo_root/package.json" ]]; then
        if command -v pnpm &>/dev/null && { [[ -f "$repo_root/pnpm-lock.yaml" ]] || [[ -f "$repo_root/pnpm-workspace.yaml" ]]; }; then
          pnpm test 2>/dev/null || pnpm run test
        elif command -v yarn &>/dev/null && [[ -f "$repo_root/yarn.lock" ]]; then
          yarn test 2>/dev/null || yarn run test
        elif command -v npm &>/dev/null; then
          npm test 2>/dev/null || npm run test
        else
          echo "[$GATE_NAME] FAIL: No package manager (npm/yarn/pnpm) found"
          return 1
        fi
      else
        echo "[$GATE_NAME] FAIL: No package.json found"
        return 1
      fi
      ;;
    go)
      go test ./... 2>/dev/null || go test ./...
      ;;
    rust)
      cargo test 2>/dev/null || cargo test
      ;;
    java)
      if [[ -f "$repo_root/pom.xml" ]]; then
        mvn -q test 2>/dev/null || mvn test
      elif [[ -f "$repo_root/build.gradle" ]] || [[ -f "$repo_root/build.gradle.kts" ]]; then
        ./gradlew test --quiet 2>/dev/null || ./gradlew test
      else
        echo "[$GATE_NAME] FAIL: No Maven or Gradle build file found"
        return 1
      fi
      ;;
    *)
      # Try package.json test script as fallback
      if [[ -f "$repo_root/package.json" ]] && jq -e '.scripts.test' "$repo_root/package.json" &>/dev/null; then
        if command -v pnpm &>/dev/null; then
          pnpm test 2>/dev/null || pnpm run test
        elif command -v npm &>/dev/null; then
          npm test 2>/dev/null || npm run test
        elif command -v yarn &>/dev/null; then
          yarn test 2>/dev/null || yarn run test
        else
          echo "[$GATE_NAME] FAIL: package.json has test script but no npm/yarn/pnpm found"
          return 1
        fi
      else
        echo "[$GATE_NAME] FAIL: Cannot determine test command. Set TEST_CMD or add a 'test' script to package.json."
        return 1
      fi
      ;;
  esac
}

# Run tests and capture exit code
if run_tests; then
  echo "[$GATE_NAME] PASS: All tests passed"
  exit 0
else
  echo "[$GATE_NAME] FAIL: Tests failed or test command unavailable"
  exit 1
fi
