#!/usr/bin/env bash
set -euo pipefail

# baseline-check.sh — Compare current finding counts against known baselines
# Determines whether failures are pre-existing (within baseline) or new (exceeding baseline).
# Supports one-way ratcheting: baseline can only decrease, never increase.
# Exit 0 with JSON result on stdout; exit 1 on error.

FRAMEWORK_VERSION="1.0.0"

usage() {
  echo "Usage:"
  echo "  $0 check --baseline-file <path> --category <name> --current-count <N>"
  echo "  $0 ratchet --baseline-file <path> --category <name> --current-count <N>"
  echo ""
  echo "Commands:"
  echo "  check    Compare current count against baseline, return PASS/FAIL/TRACKED"
  echo "  ratchet  If current count < baseline, reduce baseline (one-way ratchet)"
  echo ""
  echo "Results:"
  echo "  PASS     — No failures (current count is 0)"
  echo "  TRACKED  — Failures within baseline (pre-existing, not blocking)"
  echo "  FAIL     — Failures exceed baseline (new issues, blocking)"
  echo "  RATCHET  — Baseline reduced to current count (improvement locked in)"
  exit 1
}

COMMAND="${1:-}"
shift || true

BASELINE_FILE=""
CATEGORY=""
CURRENT_COUNT=0

while [ $# -gt 0 ]; do
  case "$1" in
    --baseline-file) BASELINE_FILE="$2"; shift 2 ;;
    --category) CATEGORY="$2"; shift 2 ;;
    --current-count) CURRENT_COUNT="$2"; shift 2 ;;
    --help|-h) usage ;;
    *) echo "[baseline-check] ERROR: Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [ -z "$BASELINE_FILE" ] || [ -z "$CATEGORY" ]; then
  echo "[baseline-check] ERROR: --baseline-file and --category are required" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "[baseline-check] ERROR: jq is required" >&2
  exit 1
fi

case "$COMMAND" in
  check)
    # If no baseline file exists, treat baseline as 0 (all failures are new)
    if [ ! -f "$BASELINE_FILE" ]; then
      if [ "$CURRENT_COUNT" -eq 0 ]; then
        echo "{\"result\": \"PASS\", \"category\": \"$CATEGORY\", \"current\": 0, \"baseline\": 0, \"message\": \"No failures and no baseline\"}"
      else
        echo "{\"result\": \"FAIL\", \"category\": \"$CATEGORY\", \"current\": $CURRENT_COUNT, \"baseline\": 0, \"message\": \"$CURRENT_COUNT new failures (no baseline exists)\"}"
      fi
      exit 0
    fi

    # Read baseline for this category
    BASELINE=$(jq -r --arg cat "$CATEGORY" '.findings[$cat] // 0' "$BASELINE_FILE" 2>/dev/null || echo "0")

    if [ "$CURRENT_COUNT" -eq 0 ]; then
      echo "{\"result\": \"PASS\", \"category\": \"$CATEGORY\", \"current\": 0, \"baseline\": $BASELINE, \"message\": \"No failures\"}"
    elif [ "$CURRENT_COUNT" -le "$BASELINE" ]; then
      echo "{\"result\": \"TRACKED\", \"category\": \"$CATEGORY\", \"current\": $CURRENT_COUNT, \"baseline\": $BASELINE, \"message\": \"$CURRENT_COUNT pre-existing issues (within baseline of $BASELINE)\"}"
    else
      NEW_COUNT=$((CURRENT_COUNT - BASELINE))
      echo "{\"result\": \"FAIL\", \"category\": \"$CATEGORY\", \"current\": $CURRENT_COUNT, \"baseline\": $BASELINE, \"message\": \"$NEW_COUNT new failures (baseline: $BASELINE, current: $CURRENT_COUNT)\"}"
    fi
    ;;

  ratchet)
    if [ ! -f "$BASELINE_FILE" ]; then
      echo "{\"result\": \"SKIP\", \"category\": \"$CATEGORY\", \"message\": \"No baseline file to ratchet\"}"
      exit 0
    fi

    BASELINE=$(jq -r --arg cat "$CATEGORY" '.findings[$cat] // 0' "$BASELINE_FILE" 2>/dev/null || echo "0")

    if [ "$CURRENT_COUNT" -lt "$BASELINE" ]; then
      # Ratchet down: update baseline to current count
      UPDATED=$(jq --arg cat "$CATEGORY" --argjson count "$CURRENT_COUNT" '.findings[$cat] = $count' "$BASELINE_FILE")
      echo "$UPDATED" > "$BASELINE_FILE"
      echo "{\"result\": \"RATCHET\", \"category\": \"$CATEGORY\", \"previous_baseline\": $BASELINE, \"new_baseline\": $CURRENT_COUNT, \"message\": \"Baseline improved from $BASELINE to $CURRENT_COUNT\"}"
    elif [ "$CURRENT_COUNT" -eq "$BASELINE" ]; then
      echo "{\"result\": \"UNCHANGED\", \"category\": \"$CATEGORY\", \"baseline\": $BASELINE, \"message\": \"No change to baseline\"}"
    else
      # Current exceeds baseline — this is a failure, not a ratchet-up
      echo "{\"result\": \"BLOCKED\", \"category\": \"$CATEGORY\", \"baseline\": $BASELINE, \"current\": $CURRENT_COUNT, \"message\": \"Cannot increase baseline (one-way ratchet). Current $CURRENT_COUNT exceeds baseline $BASELINE.\"}"
    fi
    ;;

  *)
    usage
    ;;
esac
