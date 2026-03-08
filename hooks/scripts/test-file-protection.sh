#!/usr/bin/env bash
# VibeOS Plugin — Test File Protection Hook
# Blocks implementation agents from modifying test files, enforcing the TDD
# boundary where only the tester agent writes tests.
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

# Determine if the target file is a test file
IS_TEST_FILE=false

# Directory-based patterns
case "$FILE_PATH" in
  */tests/*|*/test/*|*/__tests__/*|*/spec/*)
    IS_TEST_FILE=true
    ;;
esac

# File-naming patterns (language-agnostic)
case "$FILE_PATH" in
  *_test.go|*_test.py|*.test.js|*.test.ts|*.test.jsx|*.test.tsx|*.spec.js|*.spec.ts|*.spec.jsx|*.spec.tsx|*_spec.rb|*_test.rb|*Test.java|*Test.kt)
    IS_TEST_FILE=true
    ;;
esac

# Also match conftest.py, test fixtures, and test helpers inside test dirs
case "$FILE_PATH" in
  */conftest.py|*/test_*.py|*/tests/conftest.py)
    IS_TEST_FILE=true
    ;;
esac

# If it's not a test file, always allow
if [ "$IS_TEST_FILE" = false ]; then
  echo '{"hookSpecificOutput": {"permissionDecision": "allow"}}'
  exit 0
fi

# It's a test file — check agent identity
# Primary: read from .vibeos/current-agent.txt marker file
AGENT_FILE="${CLAUDE_PROJECT_DIR:-.}/.vibeos/current-agent.txt"
CURRENT_AGENT=""

if [ -f "$AGENT_FILE" ]; then
  CURRENT_AGENT=$(cat "$AGENT_FILE" 2>/dev/null || echo "")
fi

# Agents allowed to modify test files
case "$CURRENT_AGENT" in
  tester|test-auditor)
    echo '{"hookSpecificOutput": {"permissionDecision": "allow"}}'
    exit 0
    ;;
  backend|frontend|doc-writer)
    deny "Implementation agent '$CURRENT_AGENT' cannot modify test files. Test files are written by the tester agent only (TDD enforcement)."
    ;;
  "")
    # No agent identity — allow with warning (fail open)
    # This handles the case where the user is editing directly
    echo '{"hookSpecificOutput": {"permissionDecision": "allow"}}'
    exit 0
    ;;
  *)
    # Unknown agent — allow (fail open with caution)
    echo '{"hookSpecificOutput": {"permissionDecision": "allow"}}'
    exit 0
    ;;
esac
