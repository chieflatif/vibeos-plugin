#!/usr/bin/env bash
# VibeOS Codex Hook — Governance Guard
# Blocks prompts that ask Codex to bypass gates, tests, audits, hooks, or evidence.
FRAMEWORK_VERSION="2.2.0"

INPUT=$(cat)
PROMPT=$(printf '%s' "$INPUT" | jq -r '.prompt // empty' 2>/dev/null || echo "")

if [ -z "$PROMPT" ]; then
  exit 0
fi

PROMPT_LOWER=$(printf '%s' "$PROMPT" | tr '[:upper:]' '[:lower:]' 2>/dev/null || printf '%s' "$PROMPT")

block() {
  local label="$1"
  printf '{
  "decision": "block",
  "reason": "BLOCKED [governance-guard]: This request matches a governance bypass pattern (%s). VibeOS gates, tests, audits, hooks, and evidence requirements cannot be skipped silently. Fix the failing control or open a Work Order to change it."
}\n' "$label"
  exit 2
}

check_pattern() {
  local regex="$1"
  local label="$2"
  if printf '%s' "$PROMPT_LOWER" | grep -qiE "$regex" 2>/dev/null; then
    block "$label"
  fi
}

check_pattern 'skip[[:space:]]+.*gate|bypass[[:space:]]+.*gate|disable[[:space:]]+.*gate|turn[[:space:]]+off[[:space:]]+.*gate' "gate bypass"
check_pattern 'ignore[[:space:]]+.*test|skip[[:space:]]+.*test|disable[[:space:]]+.*test' "test bypass"
check_pattern 'skip[[:space:]]+.*audit|bypass[[:space:]]+.*audit|ignore[[:space:]]+.*audit' "audit bypass"
check_pattern 'no[[:space:]]+.*evidence|skip[[:space:]]+.*evidence|without[[:space:]]+evidence' "evidence bypass"
check_pattern 'disable[[:space:]]+.*hook|bypass[[:space:]]+.*hook|turn[[:space:]]+off[[:space:]]+.*hook|skip[[:space:]]+.*hook' "hook bypass"
check_pattern 'force[[:space:]]+.*deploy|force[[:space:]]+deploy' "force deploy"
check_pattern 'skip[[:space:]]+.*review|bypass[[:space:]]+.*review|no[[:space:]]+.*review' "review bypass"

exit 0
