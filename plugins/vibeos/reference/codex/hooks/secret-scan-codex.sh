#!/usr/bin/env bash
# VibeOS Codex Hook — Secret Scan
# Scans supported Codex edit payloads for obvious hardcoded secrets.
FRAMEWORK_VERSION="2.2.0"

INPUT=$(cat)
CONTENT=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // .tool_input.content // .tool_input.new_string // empty' 2>/dev/null || echo "")

if [ -z "$CONTENT" ]; then
  exit 0
fi

deny() {
  local message="$1"
  printf '{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "BLOCKED [secret-scan]: %s. Store secrets in environment variables or a vault, never in code."
  }
}\n' "$message"
  exit 2
}

if printf '%s' "$CONTENT" | grep -qE 'AKIA[0-9A-Z]{16}'; then
  deny "Potential AWS access key detected"
fi

if printf '%s' "$CONTENT" | grep -qE 'sk-[a-zA-Z0-9]{48,}'; then
  deny "Potential OpenAI API key detected"
fi

if printf '%s' "$CONTENT" | grep -qE 'sk-ant-[a-zA-Z0-9-]{90,}'; then
  deny "Potential Anthropic API key detected"
fi

if printf '%s' "$CONTENT" | grep -qE 'ghp_[a-zA-Z0-9]{36}'; then
  deny "Potential GitHub token detected"
fi

if printf '%s' "$CONTENT" | grep -qE 'sk_live_[a-zA-Z0-9]{24,}'; then
  deny "Potential Stripe live key detected"
fi

if printf '%s' "$CONTENT" | grep -qiE '(password|secret|api_key|apikey|auth_token|access_token)[[:space:]]*[=:][[:space:]]*["'\''][^"'\'']{8,}["'\'']'; then
  deny "Potential hardcoded secret assignment detected"
fi

exit 0
