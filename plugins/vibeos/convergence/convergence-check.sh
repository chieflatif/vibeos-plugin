#!/usr/bin/env bash
set -euo pipefail

# convergence-check.sh — Evaluate whether a fix/audit cycle has converged
# Returns a convergence decision: CONVERGED, CONTINUE, or STUCK.
# Exit 0 with JSON result on stdout; exit 1 on error.

FRAMEWORK_VERSION="2.0.0"

usage() {
  echo "Usage: $0 --current-hash <hash> --previous-hash <hash> --iteration <N> --max-iterations <N>"
  echo "          --critical-count <N> --high-count <N> --tests-pass <true|false>"
  echo "          [--previous-critical <N>] [--previous-high <N>]"
  echo "          [--stuck-threshold <N>]"
  echo ""
  echo "Evaluates convergence criteria for fix/audit cycles."
  echo ""
  echo "Decisions:"
  echo "  CONVERGED  — Tests pass and no critical/high findings. Stop iterating."
  echo "  STUCK      — State unchanged or findings identical for stuck-threshold cycles. Escalate."
  echo "  MAX_ITER   — Maximum iteration count reached. Escalate."
  echo "  CONTINUE   — Progress being made. Continue fix cycle."
  echo ""
  echo "Options:"
  echo "  --current-hash       SHA-256 hash of current source state"
  echo "  --previous-hash      SHA-256 hash of previous cycle source state"
  echo "  --iteration          Current iteration number (1-based)"
  echo "  --max-iterations     Maximum allowed iterations (default: 5)"
  echo "  --critical-count     Number of critical findings in current cycle"
  echo "  --high-count         Number of high findings in current cycle"
  echo "  --tests-pass         Whether all tests pass (true/false)"
  echo "  --previous-critical  Critical findings from previous cycle (for trend detection)"
  echo "  --previous-high      High findings from previous cycle (for trend detection)"
  echo "  --stuck-threshold    Consecutive unchanged cycles before STUCK (default: 2)"
  exit 1
}

CURRENT_HASH=""
PREVIOUS_HASH=""
ITERATION=0
MAX_ITERATIONS=5
CRITICAL_COUNT=0
HIGH_COUNT=0
TESTS_PASS="false"
PREVIOUS_CRITICAL=-1
PREVIOUS_HIGH=-1
STUCK_THRESHOLD=2

while [ $# -gt 0 ]; do
  case "$1" in
    --current-hash)
      CURRENT_HASH="$2"
      shift 2
      ;;
    --previous-hash)
      PREVIOUS_HASH="$2"
      shift 2
      ;;
    --iteration)
      ITERATION="$2"
      shift 2
      ;;
    --max-iterations)
      MAX_ITERATIONS="$2"
      shift 2
      ;;
    --critical-count)
      CRITICAL_COUNT="$2"
      shift 2
      ;;
    --high-count)
      HIGH_COUNT="$2"
      shift 2
      ;;
    --tests-pass)
      TESTS_PASS="$2"
      shift 2
      ;;
    --previous-critical)
      PREVIOUS_CRITICAL="$2"
      shift 2
      ;;
    --previous-high)
      PREVIOUS_HIGH="$2"
      shift 2
      ;;
    --stuck-threshold)
      STUCK_THRESHOLD="$2"
      shift 2
      ;;
    --help|-h)
      usage
      ;;
    *)
      echo "[convergence-check] ERROR: Unknown argument: $1" >&2
      usage
      ;;
  esac
done

# Validate required parameters
if [ -z "$CURRENT_HASH" ] || [ -z "$PREVIOUS_HASH" ]; then
  echo "[convergence-check] ERROR: --current-hash and --previous-hash are required" >&2
  exit 1
fi

if [ "$ITERATION" -le 0 ]; then
  echo "[convergence-check] ERROR: --iteration must be positive" >&2
  exit 1
fi

# Decision logic (order matters — most urgent checks first)

# Check 1: Max iterations reached
if [ "$ITERATION" -ge "$MAX_ITERATIONS" ]; then
  echo "{\"decision\": \"MAX_ITER\", \"reason\": \"Reached maximum iteration limit ($MAX_ITERATIONS)\", \"iteration\": $ITERATION, \"critical\": $CRITICAL_COUNT, \"high\": $HIGH_COUNT}"
  exit 0
fi

# Check 2: Converged — tests pass and no critical/high findings
if [ "$TESTS_PASS" = "true" ] && [ "$CRITICAL_COUNT" -eq 0 ] && [ "$HIGH_COUNT" -eq 0 ]; then
  echo "{\"decision\": \"CONVERGED\", \"reason\": \"Tests pass with no critical or high findings\", \"iteration\": $ITERATION, \"critical\": 0, \"high\": 0}"
  exit 0
fi

# Check 3: State unchanged (code didn't change after fix attempt)
if [ "$CURRENT_HASH" = "$PREVIOUS_HASH" ]; then
  if [ "$ITERATION" -ge "$STUCK_THRESHOLD" ]; then
    echo "{\"decision\": \"STUCK\", \"reason\": \"Source state unchanged after fix attempt (hash identical for $STUCK_THRESHOLD+ cycles)\", \"iteration\": $ITERATION, \"critical\": $CRITICAL_COUNT, \"high\": $HIGH_COUNT}"
    exit 0
  fi
fi

# Check 4: Findings identical to previous cycle (no progress on findings)
if [ "$PREVIOUS_CRITICAL" -ge 0 ] && [ "$PREVIOUS_HIGH" -ge 0 ]; then
  if [ "$CRITICAL_COUNT" -eq "$PREVIOUS_CRITICAL" ] && [ "$HIGH_COUNT" -eq "$PREVIOUS_HIGH" ]; then
    if [ "$CURRENT_HASH" = "$PREVIOUS_HASH" ]; then
      echo "{\"decision\": \"STUCK\", \"reason\": \"Findings unchanged (critical: $CRITICAL_COUNT, high: $HIGH_COUNT) and code unchanged\", \"iteration\": $ITERATION, \"critical\": $CRITICAL_COUNT, \"high\": $HIGH_COUNT}"
      exit 0
    fi
  fi
fi

# Check 5: Findings increasing (regression)
if [ "$PREVIOUS_CRITICAL" -ge 0 ] && [ "$PREVIOUS_HIGH" -ge 0 ]; then
  TOTAL_CURRENT=$((CRITICAL_COUNT + HIGH_COUNT))
  TOTAL_PREVIOUS=$((PREVIOUS_CRITICAL + PREVIOUS_HIGH))
  if [ "$TOTAL_CURRENT" -gt "$TOTAL_PREVIOUS" ]; then
    echo "{\"decision\": \"STUCK\", \"reason\": \"Findings increased from $TOTAL_PREVIOUS to $TOTAL_CURRENT (regression detected)\", \"iteration\": $ITERATION, \"critical\": $CRITICAL_COUNT, \"high\": $HIGH_COUNT}"
    exit 0
  fi
fi

# Default: progress is being made, continue
echo "{\"decision\": \"CONTINUE\", \"reason\": \"Progress detected, continuing fix cycle\", \"iteration\": $ITERATION, \"critical\": $CRITICAL_COUNT, \"high\": $HIGH_COUNT}"
exit 0
