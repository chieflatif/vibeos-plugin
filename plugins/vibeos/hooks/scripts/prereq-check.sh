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
  "systemMessage": "VibeOS Plugin: All prerequisites available.${GIT_WARNING} Just describe what you want to build, or ask me anything about how the system works.",
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "VibeOS Plugin prerequisites satisfied but git not detected.${GIT_WARNING} Voice-led routing is active — the user can speak naturally and the intent router will suggest the right skill."
  }
}
EOF
else
  # Detect lifecycle state for context-aware welcome
  LIFECYCLE_HINT="new project"
  if [ -f "project-definition.json" ] && [ -f "docs/planning/DEVELOPMENT-PLAN.md" ]; then
    LIFECYCLE_HINT="existing project with a development plan — ready to build"
  elif [ -f "project-definition.json" ]; then
    LIFECYCLE_HINT="discovered project — ready for planning"
  elif [ -d ".vibeos" ]; then
    LIFECYCLE_HINT="project with VibeOS state"
  fi

  cat << EOF
{
  "systemMessage": "VibeOS Plugin ready (${LIFECYCLE_HINT}). Just tell me what you want to do — describe your idea, ask about progress, or say 'continue' to keep building. No commands needed.",
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "VibeOS Plugin prerequisites satisfied. Lifecycle: ${LIFECYCLE_HINT}. Voice-led routing is active — the user can speak naturally and the intent router will suggest the right skill. Follow the routing instructions in CLAUDE.md."
  }
}
EOF
fi
