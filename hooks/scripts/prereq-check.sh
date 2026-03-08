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

# Check git repo
GIT_WARNING=""
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  GIT_WARNING=" Git repository not detected — convergence features (state tracking, baselines) require git. Run 'git init' to initialize."
fi

if [ ${#MISSING[@]} -gt 0 ]; then
  MISSING_LIST=$(printf ', %s' "${MISSING[@]}")
  MISSING_LIST="${MISSING_LIST:2}"
  cat << EOF
{
  "systemMessage": "WARNING: Missing tools: $MISSING_LIST. Some VibeOS gates may not work correctly.${GIT_WARNING}",
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "VibeOS Plugin prerequisite check: missing tools: $MISSING_LIST.${GIT_WARNING}"
  }
}
EOF
elif [ -n "$GIT_WARNING" ]; then
  cat << EOF
{
  "systemMessage": "VibeOS Plugin: All prerequisites available.${GIT_WARNING} Try \`/vibeos:discover\` to get started, or \`/vibeos:help\` to learn how VibeOS works.",
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "VibeOS Plugin prerequisites satisfied but git not detected.${GIT_WARNING}"
  }
}
EOF
else
  cat << 'EOF'
{
  "systemMessage": "VibeOS Plugin: All prerequisites available. Try `/vibeos:discover` to get started with a new project, or `/vibeos:help` to learn how VibeOS works.",
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "VibeOS Plugin prerequisites satisfied. Suggest /vibeos:discover for new projects or /vibeos:help for orientation."
  }
}
EOF
fi
