#!/usr/bin/env bash
# VibeOS Plugin — Secrets Scan Hook
# Blocks Edit/Write operations that contain hardcoded secrets.
#
# Hook type: PreToolUse (matcher: Edit|Write)
# Response format: JSON with hookSpecificOutput.permissionDecision = allow|deny
# Framework version: 1.0.0
# Note: No set -euo pipefail — hook reads stdin via cat and uses || fallbacks
# that would trigger errexit. This is intentional per hook convention.
FRAMEWORK_VERSION="1.0.0"

INPUT=$(cat)
CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // .tool_input.new_string // empty' 2>/dev/null || echo "")

# If no content to check, allow
if [ -z "$CONTENT" ]; then
  echo '{"hookSpecificOutput": {"permissionDecision": "allow"}}'
  exit 0
fi

deny() {
  cat << EOF
{
  "hookSpecificOutput": {
    "permissionDecision": "deny",
    "permissionDecisionReason": "BLOCKED: $1. Store secrets in environment variables or a vault, never in code."
  }
}
EOF
  exit 0
}

# AWS Access Keys
if echo "$CONTENT" | grep -qE 'AKIA[0-9A-Z]{16}'; then
  deny "Potential AWS Access Key detected (AKIA...)"
fi

# OpenAI API keys
if echo "$CONTENT" | grep -qE 'sk-[a-zA-Z0-9]{48,}'; then
  deny "Potential OpenAI API key detected (sk-...)"
fi

# Anthropic API keys
if echo "$CONTENT" | grep -qE 'sk-ant-[a-zA-Z0-9-]{90,}'; then
  deny "Potential Anthropic API key detected (sk-ant-...)"
fi

# GitHub tokens
if echo "$CONTENT" | grep -qE 'ghp_[a-zA-Z0-9]{36}'; then
  deny "Potential GitHub token detected (ghp_...)"
fi

# Stripe live keys
if echo "$CONTENT" | grep -qE 'sk_live_[a-zA-Z0-9]{24,}'; then
  deny "Potential Stripe live key detected (sk_live_...)"
fi

# Generic hardcoded secret assignments
if echo "$CONTENT" | grep -qiE '(password|secret|api_key|apikey|auth_token|access_token)\s*[=:]\s*["\x27][^"\x27]{8,}["\x27]'; then
  deny "Potential hardcoded secret detected in variable assignment"
fi

# .env file protection
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null || echo "")
if [[ "$FILE_PATH" == *".env"* && "$FILE_PATH" != *".env.example"* && "$FILE_PATH" != *".env.template"* ]]; then
  deny ".env files contain secrets and must not be edited programmatically"
fi

# Allow the operation
echo '{"hookSpecificOutput": {"permissionDecision": "allow"}}'
