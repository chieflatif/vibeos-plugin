#!/usr/bin/env bash
set -euo pipefail

# test-quality-gate.sh — Enhanced test quality enforcement gate
# Checks: fallback masking, mock density, test-to-spec mapping, git history analysis
# Exit 0 = pass, 1 = fail

FRAMEWORK_VERSION="2.0.0"

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
# (pipefail-safe: capture output separately, default to 0)
MOCK_COUNT=$(grep -rn 'mock\|Mock\|stub\|Stub\|spy\|Spy\|patch\|@patch\|jest\.fn\|sinon\|vi\.fn' "$PROJECT_DIR" \
  --include="*_test.*" --include="*.test.*" --include="*.spec.*" \
  --include="test_*.py" --include="*_test.go" 2>/dev/null | \
  wc -l | tr -d ' ')
MOCK_COUNT="${MOCK_COUNT:-0}"

# Count total test lines for density calculation
# (pipefail-safe + macOS xargs compatibility: default empty to 0)
TEST_LINES=$(find "$PROJECT_DIR" \
  \( -name "*_test.*" -o -name "*.test.*" -o -name "*.spec.*" -o -name "test_*.py" -o -name "*_test.go" \) \
  -type f 2>/dev/null | xargs wc -l 2>/dev/null | tail -1 | awk '{print $1}')
TEST_LINES="${TEST_LINES:-0}"

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
# Phase 2b: Per-Function Mock Density Analysis (R6)
# ============================================================
echo "--- Phase 2b: Per-Function Mock Density ---"

if command -v python3 >/dev/null 2>&1; then
  PER_FUNC_OUTPUT=$(python3 - "$PROJECT_DIR" "$MOCK_DENSITY_WARN" <<'PYEOF'
import re
import sys
from pathlib import Path

project_dir = Path(sys.argv[1])
threshold = int(sys.argv[2])

TEST_PATTERNS = [
    re.compile(r"test_.*\.py$"),
    re.compile(r".*_test\.py$"),
    re.compile(r"conftest\.py$"),
]

MOCK_PATTERNS = [
    re.compile(r"@patch\b"),
    re.compile(r"\bpatch\("),
    re.compile(r"\bMagicMock\b"),
    re.compile(r"\bAsyncMock\b"),
    re.compile(r"\bMock\(\)"),
    re.compile(r"\bcreate_autospec\b"),
    re.compile(r"\bmocker\.\w+"),
]

ASSERT_PATTERNS = [
    re.compile(r"\bassert\b"),
    re.compile(r"\.assert_called"),
    re.compile(r"\.assert_awaited"),
    re.compile(r"\.assert_not_called"),
    re.compile(r"\.call_count"),
    re.compile(r"\.return_value"),
]

MOCK_ASSERT_PATTERNS = [
    re.compile(r"\.assert_called"),
    re.compile(r"\.assert_awaited"),
    re.compile(r"\.assert_not_called"),
    re.compile(r"\.call_count"),
    re.compile(r"\.return_value"),
    re.compile(r"assert.*mock"),
    re.compile(r"assert.*Mock"),
]

EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache",
    "venv", ".venv", "dist", "build", ".vibeos", ".claude",
}

def is_excluded(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    return False

high_density_funcs = []

for test_file in project_dir.rglob("*.py"):
    if not test_file.is_file():
        continue
    rel = test_file.relative_to(project_dir)
    if is_excluded(rel):
        continue
    if not any(p.search(test_file.name) for p in TEST_PATTERNS):
        continue

    try:
        content = test_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        continue

    lines = content.splitlines()
    func_name = None
    func_start = 0
    func_lines = []

    def analyze_func():
        if not func_name or not func_lines:
            return
        total_asserts = 0
        mock_asserts = 0
        mock_decls = 0
        for fl in func_lines:
            if any(p.search(fl) for p in ASSERT_PATTERNS):
                total_asserts += 1
            if any(p.search(fl) for p in MOCK_ASSERT_PATTERNS):
                mock_asserts += 1
            if any(p.search(fl) for p in MOCK_PATTERNS):
                mock_decls += 1
        if total_asserts > 0:
            density = int(mock_asserts * 100 / total_asserts)
            if density > threshold:
                high_density_funcs.append({
                    "file": str(rel),
                    "func": func_name,
                    "line": func_start + 1,
                    "density": density,
                    "mock_asserts": mock_asserts,
                    "total_asserts": total_asserts,
                    "mock_decls": mock_decls,
                })

    for idx, line in enumerate(lines):
        match = re.match(r"^(\s*)(async\s+)?def\s+(test_\w+)\s*\(", line)
        if match:
            analyze_func()
            func_name = match.group(3)
            func_start = idx
            func_lines = [line]
        elif func_name is not None:
            func_lines.append(line)

    analyze_func()

if high_density_funcs:
    print(f"HIGH_DENSITY:{len(high_density_funcs)}")
    for f in high_density_funcs[:10]:
        print(f"  {f['file']}:{f['line']}: {f['func']} — "
              f"{f['density']}% mock density "
              f"({f['mock_asserts']}/{f['total_asserts']} assertions against mocks, "
              f"{f['mock_decls']} mock declarations)")
    if len(high_density_funcs) > 10:
        print(f"  ... {len(high_density_funcs) - 10} more")
else:
    print("CLEAN:0")
PYEOF
  )

  if echo "$PER_FUNC_OUTPUT" | grep -q "^HIGH_DENSITY:"; then
    HIGH_COUNT=$(echo "$PER_FUNC_OUTPUT" | head -1 | cut -d: -f2)
    echo "[test-quality] WARN: $HIGH_COUNT test function(s) exceed ${MOCK_DENSITY_WARN}% mock density"
    echo "$PER_FUNC_OUTPUT" | tail -n +2
    WARNINGS=$((WARNINGS + HIGH_COUNT))
  elif echo "$PER_FUNC_OUTPUT" | grep -q "^CLEAN:"; then
    echo "[test-quality] PASS: No test functions exceed ${MOCK_DENSITY_WARN}% mock density threshold"
  fi
else
  echo "[test-quality] SKIP: python3 not available for per-function analysis"
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
    -type f 2>/dev/null | wc -l | tr -d ' ')
  TEST_FILE_COUNT="${TEST_FILE_COUNT:-0}"

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
  # (pipefail-safe: no || fallback on multi-stage pipelines)
  TEST_MODIFICATIONS=$(git -C "$PROJECT_DIR" log --oneline -10 --name-only -- \
    '*_test.*' '*.test.*' '*.spec.*' 'test_*.py' '*_test.go' 2>/dev/null | \
    grep -v '^[a-f0-9]' | sort -u | wc -l | tr -d ' ')
  TEST_MODIFICATIONS="${TEST_MODIFICATIONS:-0}"

  IMPL_MODIFICATIONS=$(git -C "$PROJECT_DIR" log --oneline -10 --name-only -- \
    '*.py' '*.js' '*.ts' '*.go' '*.rs' '*.java' 2>/dev/null | \
    grep -v '^[a-f0-9]' | grep -v 'test\|spec\|_test' | sort -u | wc -l | tr -d ' ')
  IMPL_MODIFICATIONS="${IMPL_MODIFICATIONS:-0}"

  echo "[test-quality] Recent test file changes: $TEST_MODIFICATIONS"
  echo "[test-quality] Recent implementation file changes: $IMPL_MODIFICATIONS"

  # Check for test files modified AFTER implementation in the same commit range
  # This is a heuristic — not definitive proof of TDD violation
  SUSPECT_COMMITS=$(git -C "$PROJECT_DIR" log --oneline -10 --name-only 2>/dev/null | \
    awk '/^[a-f0-9]/{commit=$0; saw_impl=0; next} /test|spec|_test/{if(saw_impl) print commit": "$0; next} {saw_impl=1}' 2>/dev/null | \
    wc -l | tr -d ' ')
  SUSPECT_COMMITS="${SUSPECT_COMMITS:-0}"

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
