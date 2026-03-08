#!/usr/bin/env bash
# test-diff-audit.sh — Detect and audit test file modifications during implementation
# PreToolUse hook: reads tool input from stdin, checks if an implementation agent
# is modifying a test file with justification-required patterns.
# Exit 0 with JSON on stdout; exit 2 on blocking error.
# Note: No pipefail — stdin/jq patterns may trigger errexit.

FRAMEWORK_VERSION="1.0.0"

# Read tool input from stdin
INPUT=$(cat)

# Extract the file path from tool input
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // ""' 2>/dev/null || echo "")

if [ -z "$FILE_PATH" ]; then
  # No file path — not a file operation, allow
  exit 0
fi

# Check if this is a test file
IS_TEST="false"
case "$FILE_PATH" in
  */tests/*|*/test/*|*/__tests__/*|*/spec/*)
    IS_TEST="true"
    ;;
esac

# Check file naming patterns
BASENAME=$(basename "$FILE_PATH")
case "$BASENAME" in
  *_test.go|*_test.py|test_*.py|*.test.js|*.test.ts|*.test.jsx|*.test.tsx|*.spec.js|*.spec.ts|*.spec.jsx|*.spec.tsx|*_spec.rb|*Test.java|*Tests.cs)
    IS_TEST="true"
    ;;
esac

if [ "$IS_TEST" != "true" ]; then
  # Not a test file — allow without audit
  exit 0
fi

# Check which agent is running
AGENT_FILE="${CLAUDE_PROJECT_DIR:-.}/.vibeos/current-agent.txt"
CURRENT_AGENT=""
if [ -f "$AGENT_FILE" ]; then
  CURRENT_AGENT=$(cat "$AGENT_FILE" 2>/dev/null || echo "")
fi

# Tester and test-auditor are allowed to modify tests freely
case "$CURRENT_AGENT" in
  tester|test-auditor)
    exit 0
    ;;
esac

# For implementation agents, analyze the diff for weakening patterns
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""' 2>/dev/null || echo "")

if [ "$TOOL_NAME" = "Edit" ]; then
  OLD_STRING=$(echo "$INPUT" | jq -r '.tool_input.old_string // ""' 2>/dev/null || echo "")
  NEW_STRING=$(echo "$INPUT" | jq -r '.tool_input.new_string // ""' 2>/dev/null || echo "")

  WEAKENING="false"
  REASON=""

  # Check for assertion removal (old has assertion, new doesn't)
  OLD_ASSERT_COUNT=$(echo "$OLD_STRING" | grep -c 'assert\|expect\|should\|assertEqual\|assertTrue\|assertFalse\|toBe\|toEqual\|toHave' 2>/dev/null || echo "0")
  NEW_ASSERT_COUNT=$(echo "$NEW_STRING" | grep -c 'assert\|expect\|should\|assertEqual\|assertTrue\|assertFalse\|toBe\|toEqual\|toHave' 2>/dev/null || echo "0")

  if [ "$OLD_ASSERT_COUNT" -gt "$NEW_ASSERT_COUNT" ]; then
    WEAKENING="true"
    REMOVED=$((OLD_ASSERT_COUNT - NEW_ASSERT_COUNT))
    REASON="$REMOVED assertion(s) removed from test file"
  fi

  # Check for threshold relaxation (numbers getting larger in comparisons)
  # This is a heuristic — look for comparison operators with changed values

  # Check for test deletion (old has test function, new is empty or smaller)
  OLD_TEST_COUNT=$(echo "$OLD_STRING" | grep -c 'def test_\|it(\|describe(\|test(\|func Test' 2>/dev/null || echo "0")
  NEW_TEST_COUNT=$(echo "$NEW_STRING" | grep -c 'def test_\|it(\|describe(\|test(\|func Test' 2>/dev/null || echo "0")

  if [ "$OLD_TEST_COUNT" -gt "$NEW_TEST_COUNT" ]; then
    WEAKENING="true"
    DELETED=$((OLD_TEST_COUNT - NEW_TEST_COUNT))
    REASON="${REASON:+$REASON; }$DELETED test function(s) removed"
  fi

  # Check for added skip/pending markers
  NEW_SKIP_COUNT=$(echo "$NEW_STRING" | grep -c '@skip\|@pytest.mark.skip\|xit(\|xdescribe(\|pending(\|\.skip' 2>/dev/null || echo "0")
  OLD_SKIP_COUNT=$(echo "$OLD_STRING" | grep -c '@skip\|@pytest.mark.skip\|xit(\|xdescribe(\|pending(\|\.skip' 2>/dev/null || echo "0")

  if [ "$NEW_SKIP_COUNT" -gt "$OLD_SKIP_COUNT" ]; then
    WEAKENING="true"
    ADDED_SKIPS=$((NEW_SKIP_COUNT - OLD_SKIP_COUNT))
    REASON="${REASON:+$REASON; }$ADDED_SKIPS skip marker(s) added"
  fi

  if [ "$WEAKENING" = "true" ]; then
    # Block: test weakening detected
    echo '{"hookSpecificOutput": {"permissionDecision": "deny", "reason": "Test weakening detected by '"$CURRENT_AGENT"' agent: '"$REASON"'. Test modifications that remove assertions, delete tests, or add skip markers require review. If this modification is justified, have the tester agent make the change instead."}}'
    exit 0
  fi
fi

# Non-weakening test modification by implementation agent — log warning but allow
# The test-file-protection.sh hook handles the harder deny for implementation agents.
# This hook provides the softer audit layer on top.
exit 0
