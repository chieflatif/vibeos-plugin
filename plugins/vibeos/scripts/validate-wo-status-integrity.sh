#!/usr/bin/env bash
# VibeOS Plugin — WO Status Integrity Validator
# Cross-checks WO claimed status against evidence and test results.
# Prevents status inflation (marking Complete when Dev-Mode Complete).
#
# Usage:
#   bash scripts/validate-wo-status-integrity.sh [--wo NUMBER]
#
# Exit codes:
#   0 = Status claims are consistent with evidence
#   1 = Status inflation detected
#   2 = Configuration error

set -euo pipefail
FRAMEWORK_VERSION="2.0.0"
GATE_NAME="validate-wo-status-integrity"

WO_NUMBER="${WO_NUMBER:-}"
PROJECT_DIR="${PROJECT_DIR:-.}"

while [ $# -gt 0 ]; do
  case "$1" in
    --wo) WO_NUMBER="$2"; shift 2 ;;
    --project-dir) PROJECT_DIR="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [ -z "$WO_NUMBER" ]; then
  echo "[${GATE_NAME}] SKIP: No WO_NUMBER set — run with --wo NUMBER or WO_NUMBER env var"
  exit 0
fi

WO_FILE="$PROJECT_DIR/docs/planning/WO-${WO_NUMBER}.md"
EVIDENCE_DIR="$PROJECT_DIR/docs/evidence/WO-${WO_NUMBER}"
WO_INDEX="$PROJECT_DIR/docs/planning/WO-INDEX.md"

if [ ! -f "$WO_FILE" ]; then
  echo "[${GATE_NAME}] SKIP: WO file not found at $WO_FILE"
  exit 0
fi

FINDINGS=0

# Extract claimed status from WO file
CLAIMED_STATUS=$(grep -i 'status:' "$WO_FILE" | head -1 | sed 's/.*[Ss]tatus:[[:space:]]*//' | sed 's/\*//g' | xargs)

echo "[${GATE_NAME}] WO-${WO_NUMBER} claimed status: ${CLAIMED_STATUS}"

# If claimed Complete, verify evidence exists
if echo "$CLAIMED_STATUS" | grep -qi "complete"; then

  # Check 1: Evidence bundle exists
  if [ ! -d "$EVIDENCE_DIR" ]; then
    echo "[${GATE_NAME}] FAIL: Status is 'Complete' but no evidence bundle at $EVIDENCE_DIR"
    FINDINGS=$((FINDINGS + 1))
  fi

  # Check 2: Evidence bundle has content
  if [ -d "$EVIDENCE_DIR" ]; then
    EVIDENCE_FILES=$(find "$EVIDENCE_DIR" -type f | wc -l | tr -d ' ')
    if [ "$EVIDENCE_FILES" -lt 1 ]; then
      echo "[${GATE_NAME}] FAIL: Evidence directory exists but is empty"
      FINDINGS=$((FINDINGS + 1))
    fi
  fi

  # Check 3: No mock-only markers in tests for this WO
  # Search for TODO markers indicating unverified mocks
  MOCK_TODOS=0
  for search_dir in "$PROJECT_DIR/tests/" "$PROJECT_DIR/frontend/__tests__/"; do
    if [ -d "$search_dir" ]; then
      COUNT=$(grep -rl "TODO.*validate.*against.*actual\|TODO.*contract\|TODO.*real.*backend" "$search_dir" 2>/dev/null | wc -l | tr -d ' ')
      MOCK_TODOS=$((MOCK_TODOS + COUNT))
    fi
  done
  if [ "$MOCK_TODOS" -gt 0 ]; then
    echo "[${GATE_NAME}] WARN: $MOCK_TODOS test file(s) have unresolved contract validation TODOs"
    echo "  Status should be 'Dev-Mode Complete' or 'Awaiting Real-Path Verification', not 'Complete'"
    FINDINGS=$((FINDINGS + 1))
  fi
fi

# Check 4: WO-INDEX status matches WO file status
if [ -f "$WO_INDEX" ]; then
  INDEX_STATUS=$(grep "WO-${WO_NUMBER}" "$WO_INDEX" | head -1 | grep -oE 'Complete|Draft|In Progress|Dev-Mode|Awaiting' || echo "not found")
  if [ "$INDEX_STATUS" != "not found" ]; then
    if ! echo "$CLAIMED_STATUS" | grep -qi "$INDEX_STATUS"; then
      echo "[${GATE_NAME}] WARN: WO file says '$CLAIMED_STATUS' but WO-INDEX says '$INDEX_STATUS'"
      FINDINGS=$((FINDINGS + 1))
    fi
  fi
fi

if [ "$FINDINGS" -gt 0 ]; then
  echo ""
  echo "[${GATE_NAME}] FAIL: $FINDINGS status integrity issue(s) found"
  exit 1
else
  echo "[${GATE_NAME}] PASS: Status claims are consistent with evidence"
  exit 0
fi
