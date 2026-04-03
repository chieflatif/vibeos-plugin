#!/usr/bin/env bash
# VibeOS Plugin — Governance Guard Hook
# Blocks user prompts containing patterns that attempt to bypass quality gates,
# skip audits, disable hooks, or force unsafe operations.
#
# Hook type: UserPromptSubmit
# Response format: JSON with hookSpecificOutput.permissionDecision = allow|block
# Framework version: 2.1.0
# Note: No set -euo pipefail — hook reads stdin via cat and uses || fallbacks
# that would trigger errexit. This is intentional per hook convention.
FRAMEWORK_VERSION="2.1.0"

INPUT=$(cat)
PROMPT=$(echo "$INPUT" | jq -r '.prompt // empty' 2>/dev/null || echo "")

# If no prompt, allow silently
if [ -z "$PROMPT" ]; then
  exit 0
fi

# Lowercase prompt for case-insensitive matching
PROMPT_LOWER=$(echo "$PROMPT" | tr '[:upper:]' '[:lower:]' 2>/dev/null || echo "$PROMPT")

block() {
  local pattern="$1"
  cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "permissionDecision": "block",
    "permissionDecisionReason": "BLOCKED [governance-guard]: Your request matches a governance bypass pattern ('$pattern'). VibeOS quality gates, audits, tests, and hooks are non-negotiable enforcement mechanisms — they cannot be skipped, disabled, or bypassed. If a gate is failing, investigate the root cause and fix it. If you believe the gate is misconfigured, open a work order to change it through the proper governance process."
  }
}
EOF
  exit 2
}

# ----------------------------------------------------------------
# Default blocked patterns (governance bypass attempts)
# Each entry is a grep -E extended regex pattern paired with a label
# ----------------------------------------------------------------
check_pattern() {
  local regex="$1"
  local label="$2"
  if echo "$PROMPT_LOWER" | grep -qiE "$regex" 2>/dev/null; then
    block "$label"
  fi
}

# Configurable override: if BLOCKED_PATTERNS is set, use it as a
# newline-separated list of "regex|label" pairs instead of defaults
if [ -n "${BLOCKED_PATTERNS:-}" ]; then
  while IFS='|' read -r regex label; do
    [ -z "$regex" ] && continue
    if echo "$PROMPT_LOWER" | grep -qiE "$regex" 2>/dev/null; then
      block "${label:-$regex}"
    fi
  done <<< "$BLOCKED_PATTERNS"
  exit 0
fi

# Gate bypass patterns
check_pattern 'skip[[:space:]]+.*gate|skip[[:space:]]+the[[:space:]]+gate' "skip gate"
check_pattern 'bypass[[:space:]]+.*gate|bypass[[:space:]]+the[[:space:]]+gate' "bypass gate"
check_pattern 'disable[[:space:]]+.*gate|turn[[:space:]]+off[[:space:]]+.*gate' "disable gate"

# Test / audit bypass patterns
check_pattern 'ignore[[:space:]]+.*test|skip[[:space:]]+.*test|disable[[:space:]]+.*test' "ignore/skip/disable test"
check_pattern 'skip[[:space:]]+.*audit|bypass[[:space:]]+.*audit|ignore[[:space:]]+.*audit' "skip/bypass audit"
check_pattern 'no[[:space:]]+.*evidence|skip[[:space:]]+.*evidence|without[[:space:]]+evidence' "no evidence"

# Hook bypass patterns
check_pattern 'disable[[:space:]]+.*hook|bypass[[:space:]]+.*hook|turn[[:space:]]+off[[:space:]]+.*hook' "disable/bypass hook"
check_pattern 'skip[[:space:]]+.*hook|ignore[[:space:]]+.*hook' "skip/ignore hook"

# Check bypass patterns
check_pattern 'bypass[[:space:]]+.*check|skip[[:space:]]+.*check|disable[[:space:]]+.*check' "bypass/skip check"

# Deployment bypass patterns
check_pattern 'force[[:space:]]+.*deploy|force[[:space:]]+deploy' "force deploy"
check_pattern 'skip[[:space:]]+.*review|bypass[[:space:]]+.*review|no[[:space:]]+.*review' "skip/bypass review"

# No governance bypass detected — allow
exit 0
