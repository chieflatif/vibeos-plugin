#!/usr/bin/env bash
# VibeOS Plugin — Worktree Freshness Validator
# Verifies that the current working directory is within 1 commit of the target branch HEAD.
# Intended to run at the start of any audit agent or before consuming audit results.
#
# Usage:
#   bash scripts/validate-worktree-freshness.sh [--target-branch main] [--max-behind 1]
#
# Exit codes:
#   0 = Worktree is fresh (within max-behind of target)
#   1 = Worktree is stale (behind target by more than max-behind)
#   2 = Not in a git repository or target branch not found

set -euo pipefail
FRAMEWORK_VERSION="2.0.0"
GATE_NAME="validate-worktree-freshness"

TARGET_BRANCH="main"
MAX_BEHIND=1

while [ $# -gt 0 ]; do
  case "$1" in
    --target-branch) TARGET_BRANCH="$2"; shift 2 ;;
    --max-behind) MAX_BEHIND="$2"; shift 2 ;;
    *) shift ;;
  esac
done

# Get current HEAD
CURRENT_SHA=$(git rev-parse HEAD 2>/dev/null) || { echo "[${GATE_NAME}] FAIL: Not a git repository"; exit 2; }

# Get target branch HEAD
TARGET_SHA=$(git rev-parse "origin/${TARGET_BRANCH}" 2>/dev/null || git rev-parse "${TARGET_BRANCH}" 2>/dev/null) || {
  echo "[${GATE_NAME}] FAIL: Target branch '${TARGET_BRANCH}' not found"
  exit 2
}

# Count commits behind
BEHIND=$(git rev-list --count "${CURRENT_SHA}..${TARGET_SHA}" 2>/dev/null) || BEHIND=999

if [ "$BEHIND" -gt "$MAX_BEHIND" ]; then
  echo "[${GATE_NAME}] FAIL: Worktree is ${BEHIND} commits behind ${TARGET_BRANCH} (max: ${MAX_BEHIND})"
  echo "Current:  ${CURRENT_SHA:0:12}"
  echo "Target:   ${TARGET_SHA:0:12}"
  echo "Action:   Discard these findings and re-run from HEAD"
  exit 1
fi

echo "[${GATE_NAME}] PASS: Worktree is ${BEHIND} commits behind ${TARGET_BRANCH} (within tolerance)"
echo "SHA: ${CURRENT_SHA:0:12}"
exit 0
