#!/usr/bin/env bash
set -euo pipefail

# test-quality-gate.sh — Enhanced test quality enforcement gate
# Checks: fallback masking, mock density, test-to-spec mapping, git history analysis
# Exit 0 = pass, 1 = fail

FRAMEWORK_VERSION="1.0.0"

PROJECT_DIR="${1:-.}"
CONFIG_FILE="${PROJECT_DIR}/.vibeos/config.json"

# Configurable thresholds (read from config or use defaults)
MOCK_DENSITY_WARN=60
if [ -f "$CONFIG_FILE" ] && command -v jq >/dev/null 2>&1; then
  CONFIGURED_MOCK=$(jq -r '.test_quality.mock_density_warn // empty' "$CONFIG_FILE" 2>/dev/null || true)
  if [ -n "$CONFIGURED_MOCK" ]; then
    MOCK_DENSITY_WARN="$CONFIGURED_MOCK"
  fi
fi

FINDINGS=0
WARNINGS=0

echo "[test-quality] Running enhanced test quality checks on $PROJECT_DIR"
echo ""

# ============================================================
# Phase 1: Fallback Masking Detection
# ============================================================
echo "--- Phase 1: Fallback Masking Detection ---"

MASKING_COUNT=0

# Detect empty catch blocks in test files
EMPTY_CATCH=$(grep -rn 'catch.*{' "$PROJECT_DIR" \
  --include="*_test.*" --include="*.test.*" --include="*.spec.*" \
  --include="*_test.go" --include="test_*.py" 2>/dev/null | \
  grep -c '{}' 2>/dev/null || echo "0")

if [ "$EMPTY_CATCH" -gt 0 ]; then
  echo "[test-quality] WARN: $EMPTY_CATCH empty catch blocks in test files (may mask failures)"
  MASKING_COUNT=$((MASKING_COUNT + EMPTY_CATCH))
fi

# Detect catch-all exception handlers that return default values
CATCHALL=$(grep -rn -A2 'except\s*:' "$PROJECT_DIR" \
  --include="test_*.py" --include="*_test.py" 2>/dev/null | \
  grep -c 'return\|pass' 2>/dev/null || echo "0")

if [ "$CATCHALL" -gt 0 ]; then
  echo "[test-quality] WARN: $CATCHALL catch-all exception handlers in Python test files"
  MASKING_COUNT=$((MASKING_COUNT + CATCHALL))
fi

# Detect assertions inside try blocks (may not execute)
TRY_ASSERT=$(grep -rn -B2 'assert\|expect\|should' "$PROJECT_DIR" \
  --include="*_test.*" --include="*.test.*" --include="*.spec.*" 2>/dev/null | \
  grep -c 'try\|begin' 2>/dev/null || echo "0")

if [ "$TRY_ASSERT" -gt 0 ]; then
  echo "[test-quality] WARN: $TRY_ASSERT assertions potentially inside try blocks"
  MASKING_COUNT=$((MASKING_COUNT + TRY_ASSERT))
fi

if [ "$MASKING_COUNT" -eq 0 ]; then
  echo "[test-quality] PASS: No fallback masking patterns detected"
else
  echo "[test-quality] WARN: $MASKING_COUNT total fallback masking patterns found"
  WARNINGS=$((WARNINGS + MASKING_COUNT))
fi
echo ""

# ============================================================
# Phase 2: Mock Density Analysis
# ============================================================
echo "--- Phase 2: Mock Density Analysis ---"

# Count mock/stub/spy declarations across test files
MOCK_COUNT=$(grep -rn 'mock\|Mock\|stub\|Stub\|spy\|Spy\|patch\|@patch\|jest\.fn\|sinon\|vi\.fn' "$PROJECT_DIR" \
  --include="*_test.*" --include="*.test.*" --include="*.spec.*" \
  --include="test_*.py" --include="*_test.go" 2>/dev/null | \
  wc -l | tr -d ' ' || echo "0")

# Count total test lines for density calculation
TEST_LINES=$(find "$PROJECT_DIR" \
  \( -name "*_test.*" -o -name "*.test.*" -o -name "*.spec.*" -o -name "test_*.py" -o -name "*_test.go" \) \
  -type f 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}' || echo "0")

if [ "$TEST_LINES" -gt 0 ] && [ "$MOCK_COUNT" -gt 0 ]; then
  # Calculate mock density as percentage (mocks per 100 lines)
  DENSITY=$((MOCK_COUNT * 100 / TEST_LINES))
  echo "[test-quality] Mock declarations: $MOCK_COUNT across $TEST_LINES test lines (density: ${DENSITY}%)"
  if [ "$DENSITY" -gt "$MOCK_DENSITY_WARN" ]; then
    echo "[test-quality] WARN: Mock density ${DENSITY}% exceeds threshold of ${MOCK_DENSITY_WARN}%"
    WARNINGS=$((WARNINGS + 1))
  else
    echo "[test-quality] PASS: Mock density ${DENSITY}% within threshold"
  fi
elif [ "$TEST_LINES" -eq 0 ]; then
  echo "[test-quality] SKIP: No test files found"
else
  echo "[test-quality] PASS: No mock declarations found"
fi
echo ""

# ============================================================
# Phase 3: Test-to-Spec Mapping (if WO context available)
# ============================================================
echo "--- Phase 3: Test-to-Spec Mapping ---"

# Check if there's a current WO with acceptance criteria
CURRENT_WO=""
if [ -d "$PROJECT_DIR/docs/planning" ]; then
  # Find the most recent non-complete WO
  CURRENT_WO=$(grep -rl 'Status.*Implementation Ready\|Status.*In Progress' "$PROJECT_DIR/docs/planning/WO-"*.md 2>/dev/null | head -1 || true)
fi

if [ -n "$CURRENT_WO" ]; then
  AC_COUNT=$(grep -c '^\- \[.\] AC-' "$CURRENT_WO" 2>/dev/null || echo "0")
  TEST_FILE_COUNT=$(find "$PROJECT_DIR" \
    \( -name "*_test.*" -o -name "*.test.*" -o -name "*.spec.*" -o -name "test_*.py" -o -name "*_test.go" \) \
    -type f 2>/dev/null | wc -l | tr -d ' ' || echo "0")

  echo "[test-quality] Current WO has $AC_COUNT acceptance criteria"
  echo "[test-quality] Found $TEST_FILE_COUNT test files"

  if [ "$AC_COUNT" -gt 0 ] && [ "$TEST_FILE_COUNT" -eq 0 ]; then
    echo "[test-quality] FAIL: WO has $AC_COUNT ACs but no test files found"
    FINDINGS=$((FINDINGS + 1))
  elif [ "$AC_COUNT" -gt 0 ]; then
    echo "[test-quality] INFO: Manual review recommended — verify test coverage maps to all $AC_COUNT ACs"
  fi
else
  echo "[test-quality] SKIP: No active WO found for spec mapping"
fi
echo ""

# ============================================================
# Phase 4: Git History Analysis (TDD Violation Detection)
# ============================================================
echo "--- Phase 4: Git History Analysis ---"

if command -v git >/dev/null 2>&1 && git -C "$PROJECT_DIR" rev-parse --git-dir >/dev/null 2>&1; then
  # Find test files modified in the last 10 commits
  TEST_MODIFICATIONS=$(git -C "$PROJECT_DIR" log --oneline -10 --name-only -- \
    '*_test.*' '*.test.*' '*.spec.*' 'test_*.py' '*_test.go' 2>/dev/null | \
    grep -v '^[a-f0-9]' | sort -u | wc -l | tr -d ' ' || echo "0")

  IMPL_MODIFICATIONS=$(git -C "$PROJECT_DIR" log --oneline -10 --name-only -- \
    '*.py' '*.js' '*.ts' '*.go' '*.rs' '*.java' 2>/dev/null | \
    grep -v '^[a-f0-9]' | grep -v 'test\|spec\|_test' | sort -u | wc -l | tr -d ' ' || echo "0")

  echo "[test-quality] Recent test file changes: $TEST_MODIFICATIONS"
  echo "[test-quality] Recent implementation file changes: $IMPL_MODIFICATIONS"

  # Check for test files modified AFTER implementation in the same commit range
  # This is a heuristic — not definitive proof of TDD violation
  SUSPECT_COMMITS=$(git -C "$PROJECT_DIR" log --oneline -10 --name-only 2>/dev/null | \
    awk '/^[a-f0-9]/{commit=$0; next} /test|spec|_test/{if(saw_impl) print commit": "$0; next} {saw_impl=1}' 2>/dev/null | \
    wc -l | tr -d ' ' || echo "0")

  if [ "$SUSPECT_COMMITS" -gt 0 ]; then
    echo "[test-quality] WARN: $SUSPECT_COMMITS commits contain both implementation and test changes (potential TDD violation)"
    WARNINGS=$((WARNINGS + 1))
  else
    echo "[test-quality] PASS: No obvious TDD violations in recent history"
  fi
else
  echo "[test-quality] SKIP: Not a git repository"
fi
echo ""

# ============================================================
# Summary
# ============================================================
echo "=== Test Quality Summary ==="
echo "Findings (blocking): $FINDINGS"
echo "Warnings (non-blocking): $WARNINGS"

if [ "$FINDINGS" -gt 0 ]; then
  echo "[test-quality] FAIL: $FINDINGS blocking findings"
  exit 1
else
  echo "[test-quality] PASS: No blocking findings ($WARNINGS warnings)"
  exit 0
fi
