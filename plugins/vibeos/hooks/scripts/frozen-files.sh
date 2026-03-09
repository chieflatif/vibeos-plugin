#!/usr/bin/env bash
# VibeOS Plugin — Frozen Files Hook
# Blocks edits to files designated as frozen/locked.
# Reads frozen file list from .claude/frozen-files.json if it exists in the project.
#
# Hook type: PreToolUse (matcher: Edit|Write)
# Response format: JSON with hookSpecificOutput.permissionDecision = allow|deny
# Framework version: 1.0.0
# Note: No set -euo pipefail — hook reads stdin via cat and uses || fallbacks
# that would trigger errexit. This is intentional per hook convention.
FRAMEWORK_VERSION="1.0.0"

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null || echo "")

if [ -z "$FILE_PATH" ]; then
  echo '{"hookSpecificOutput": {"permissionDecision": "allow"}}'
  exit 0
fi

deny() {
  cat << EOF
{
  "hookSpecificOutput": {
    "permissionDecision": "deny",
    "permissionDecisionReason": "BLOCKED: $1"
  }
}
EOF
  exit 0
}

# Always block .env files
if [[ "$FILE_PATH" == *".env"* && "$FILE_PATH" != *".env.example"* && "$FILE_PATH" != *".env.template"* ]]; then
  deny ".env files contain secrets and must not be edited programmatically."
fi

# Read frozen files from project config if it exists
FROZEN_CONFIG="${CLAUDE_PROJECT_DIR:-.}/.claude/frozen-files.json"
if [ -f "$FROZEN_CONFIG" ]; then
  while IFS= read -r frozen; do
    if [[ -n "$frozen" && "$FILE_PATH" == *"$frozen"* ]]; then
      deny "$frozen is FROZEN. This file is locked to prevent accidental modification."
    fi
  done < <(jq -r '.[]' "$FROZEN_CONFIG" 2>/dev/null)
fi

# Allow the operation
echo '{"hookSpecificOutput": {"permissionDecision": "allow"}}'
