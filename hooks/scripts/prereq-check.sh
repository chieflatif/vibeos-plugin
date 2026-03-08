#!/usr/bin/env bash
# VibeOS Plugin — Session Start Prerequisite Check
# Warns if required tools (bash, python3, jq, git) are not available.
#
# Hook type: SessionStart
# Framework version: 1.0.0
FRAMEWORK_VERSION="1.0.0"
set -euo pipefail

MISSING=()

for tool in bash python3 jq git; do
  if ! command -v "$tool" &> /dev/null; then
    MISSING+=("$tool")
  fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
  MISSING_LIST=$(printf ', %s' "${MISSING[@]}")
  MISSING_LIST="${MISSING_LIST:2}"
  cat << EOF
{
  "systemMessage": "WARNING: Missing tools: $MISSING_LIST. Some VibeOS gates may not work correctly.",
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "VibeOS Plugin prerequisite check: missing tools: $MISSING_LIST. Install them for full gate support."
  }
}
EOF
else
  cat << 'EOF'
{
  "systemMessage": "VibeOS Plugin: All prerequisites available (bash, python3, jq, git).",
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "VibeOS Plugin prerequisites satisfied."
  }
}
EOF
fi
