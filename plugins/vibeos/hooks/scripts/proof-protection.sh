#!/usr/bin/env bash
# VibeOS Plugin — Proof Protection Hook
# Blocks implementation agents from removing assertions in test files and from
# deleting evidence bundles.
#
# Hook type: PreToolUse (matcher: Edit|Write)
# Response format: JSON with hookSpecificOutput.permissionDecision = allow|deny
# Framework version: 2.1.0
# Note: No set -euo pipefail — hook reads stdin via cat and uses || fallbacks
# that would trigger errexit. This is intentional per hook convention.
FRAMEWORK_VERSION="2.1.0"

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null || echo "")
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty' 2>/dev/null || echo "")

allow() {
  cat <<'EOF'
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow"
  }
}
EOF
  exit 0
}

deny() {
  local message="BLOCKED [proof-protection]: $1"
  cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "$message"
  }
}
EOF
  exit 0
}

if [ -z "$FILE_PATH" ]; then
  allow
fi

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-.}"

# Only enforce when a VibeOS session is active
SESSION_STATE="${PROJECT_ROOT}/.vibeos/session-state.json"
SESSION_ACTIVE=false

if [ -f "$SESSION_STATE" ] && command -v jq >/dev/null 2>&1; then
  ACTIVE_VAL=$(jq -r '.active // false' "$SESSION_STATE" 2>/dev/null || echo "false")
  if [ "$ACTIVE_VAL" = "true" ]; then
    SESSION_ACTIVE=true
  fi
fi

if [ "$SESSION_ACTIVE" = false ]; then
  allow
fi

# Read current agent identity
AGENT_FILE="${PROJECT_ROOT}/.vibeos/current-agent.txt"
CURRENT_AGENT=""
if [ -f "$AGENT_FILE" ]; then
  CURRENT_AGENT=$(cat "$AGENT_FILE" 2>/dev/null || echo "")
fi

# Agents allowed to modify test files and proof files without restriction
case "$CURRENT_AGENT" in
  tester|test-auditor)
    allow
    ;;
esac

# Resolve path relative to project root for pattern matching
REL_PATH="$FILE_PATH"
if [[ "$FILE_PATH" == "$PROJECT_ROOT"/* ]]; then
  REL_PATH="${FILE_PATH#$PROJECT_ROOT/}"
fi

# ----------------------------------------------------------------
# Evidence bundle protection
# Blocks implementation agents from deleting or overwriting evidence
# ----------------------------------------------------------------
IS_EVIDENCE_FILE=false
case "$REL_PATH" in
  docs/evidence/*|docs/evidence/*)
    IS_EVIDENCE_FILE=true
    ;;
esac

if [ "$IS_EVIDENCE_FILE" = true ]; then
  case "$CURRENT_AGENT" in
    backend|frontend|doc-writer|prompt-engineer)
      BUILD_LOG="${PROJECT_ROOT}/.vibeos/build-log.md"
      if [ -d "${PROJECT_ROOT}/.vibeos" ]; then
        TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
        echo "| $TIMESTAMP | proof-protection | BLOCKED: $CURRENT_AGENT attempted to modify evidence bundle $REL_PATH | Evidence protected |" >> "$BUILD_LOG" 2>/dev/null || true
      fi
      deny "Implementation agent '$CURRENT_AGENT' cannot modify evidence bundles in docs/evidence/. Evidence is write-once audit proof."
      ;;
  esac
fi

# ----------------------------------------------------------------
# Test file assertion protection
# Blocks implementation agents from removing assertions in test files
# ----------------------------------------------------------------
IS_TEST_FILE=false

case "$FILE_PATH" in
  */tests/*|*/test/*|*/__tests__/*|*/spec/*)
    IS_TEST_FILE=true
    ;;
esac

case "$FILE_PATH" in
  *_test.go|*_test.py|*.test.js|*.test.ts|*.test.jsx|*.test.tsx|*.spec.js|*.spec.ts|*.spec.jsx|*.spec.tsx|*_spec.rb|*_test.rb|*Test.java|*Test.kt)
    IS_TEST_FILE=true
    ;;
esac

case "$FILE_PATH" in
  */conftest.py|*/test_*.py)
    IS_TEST_FILE=true
    ;;
esac

if [ "$IS_TEST_FILE" = false ]; then
  allow
fi

# Test file targeted by an implementation agent — check for assertion removal
case "$CURRENT_AGENT" in
  backend|frontend|doc-writer|prompt-engineer)
    # For Write tool: check if content is empty (file deletion via write)
    if [ "$TOOL_NAME" = "Write" ]; then
      NEW_CONTENT=$(echo "$INPUT" | jq -r '.tool_input.content // empty' 2>/dev/null || echo "")
      if [ -z "$NEW_CONTENT" ]; then
        BUILD_LOG="${PROJECT_ROOT}/.vibeos/build-log.md"
        if [ -d "${PROJECT_ROOT}/.vibeos" ]; then
          TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
          echo "| $TIMESTAMP | proof-protection | BLOCKED: $CURRENT_AGENT attempted to delete test file $REL_PATH | TDD proof protected |" >> "$BUILD_LOG" 2>/dev/null || true
        fi
        deny "Implementation agent '$CURRENT_AGENT' cannot delete test file $REL_PATH. Test files are proof — only the tester agent may modify them."
      fi
    fi

    # For Edit tool: check if assertions are removed
    if [ "$TOOL_NAME" = "Edit" ]; then
      OLD_STRING=$(echo "$INPUT" | jq -r '.tool_input.old_string // empty' 2>/dev/null || echo "")
      NEW_STRING=$(echo "$INPUT" | jq -r '.tool_input.new_string // empty' 2>/dev/null || echo "")

      # Block content deletion (replace with empty)
      if [ -n "$OLD_STRING" ] && [ -z "$NEW_STRING" ]; then
        BUILD_LOG="${PROJECT_ROOT}/.vibeos/build-log.md"
        if [ -d "${PROJECT_ROOT}/.vibeos" ]; then
          TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
          echo "| $TIMESTAMP | proof-protection | BLOCKED: $CURRENT_AGENT attempted to delete content from test file $REL_PATH | TDD proof protected |" >> "$BUILD_LOG" 2>/dev/null || true
        fi
        deny "Implementation agent '$CURRENT_AGENT' cannot delete content from test file $REL_PATH. Test assertions are proof."
      fi

      # Block removal of assertion statements (assert, expect, should, must, verify, raise)
      if echo "$OLD_STRING" | grep -qiE '(assert|expect|should|must|verify|raise)' 2>/dev/null; then
        if ! echo "$NEW_STRING" | grep -qiE '(assert|expect|should|must|verify|raise)' 2>/dev/null; then
          BUILD_LOG="${PROJECT_ROOT}/.vibeos/build-log.md"
          if [ -d "${PROJECT_ROOT}/.vibeos" ]; then
            TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
            echo "| $TIMESTAMP | proof-protection | BLOCKED: $CURRENT_AGENT attempted to remove assertions from $REL_PATH | Test integrity protected |" >> "$BUILD_LOG" 2>/dev/null || true
          fi
          deny "Implementation agent '$CURRENT_AGENT' appears to be removing assertions from test file $REL_PATH. This weakens test proof. Fix the implementation to make the tests pass — do not weaken the tests."
        fi
      fi
    fi
    ;;
  "")
    # Unknown agent — allow with audit log (fail open)
    BUILD_LOG="${PROJECT_ROOT}/.vibeos/build-log.md"
    if [ -d "${PROJECT_ROOT}/.vibeos" ]; then
      TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
      echo "| $TIMESTAMP | proof-protection | WARNING: Agent identity unknown, allowing write to $REL_PATH | Fail-open |" >> "$BUILD_LOG" 2>/dev/null || true
    fi
    allow
    ;;
esac

allow
