#!/usr/bin/env bash
# file-budget.sh — File size budget enforcement hook
#
# Warns at FILE_BUDGET_WARN lines and blocks at FILE_BUDGET_MAX lines for
# production code files. Enforces module size limits to keep code composable.
#
# Excluded from enforcement:
#   - Test files (test_*, *_test.*, conftest.*, tests/ directory)
#   - Documentation (.md files)
#   - Config files (.json, .yaml, .yml, .toml, .ini, .cfg)
#   - Generated files (*_pb2.py, *.generated.*, migrations/)
#   - Hook and gate scripts
#
# Hook type: PreToolUse (matcher: Edit|Write)
# Response format: JSON with hookSpecificOutput.permissionDecision = allow|deny
#
# Configuration via environment variables:
#   FILE_BUDGET_WARN — line count warning threshold (default: 250)
#   FILE_BUDGET_MAX  — line count hard limit (default: 300)
#
# Note: No set -euo pipefail — hook reads stdin via cat and uses || fallbacks
# intentionally. This is per hook convention for all VibeOS hooks.
FRAMEWORK_VERSION="2.2.0"

FILE_BUDGET_WARN="${FILE_BUDGET_WARN:-250}"
FILE_BUDGET_MAX="${FILE_BUDGET_MAX:-300}"

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

allow_with_warning() {
  local message="$1"
  cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "WARNING [file-budget]: $message"
  }
}
EOF
  exit 0
}

deny() {
  local message="BLOCKED [file-budget]: $1"
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

# No file path — nothing to enforce
if [ -z "$FILE_PATH" ]; then
  allow
fi

PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || echo ".")}"

# Normalize to a relative path for pattern matching
REL_PATH="$FILE_PATH"
if [[ "$FILE_PATH" == "$PROJECT_ROOT"/* ]]; then
  REL_PATH="${FILE_PATH#$PROJECT_ROOT/}"
fi

# Extract filename for pattern matching
FILENAME=$(basename "$REL_PATH")

# Exclude: test files and directories
case "$REL_PATH" in
  tests/*|test/*|spec/*)
    allow ;;
esac

case "$FILENAME" in
  test_*|*_test.py|*_test.ts|*_test.go|*_test.js|conftest.py|*.spec.ts|*.spec.js|*.test.ts|*.test.js)
    allow ;;
esac

# Exclude: documentation files
case "$FILENAME" in
  *.md|*.rst|*.txt)
    allow ;;
esac

# Exclude: config files
case "$FILENAME" in
  *.json|*.yaml|*.yml|*.toml|*.ini|*.cfg|*.conf|*.env|*.env.example)
    allow ;;
esac

# Exclude: generated files
case "$FILENAME" in
  *_pb2.py|*_pb2_grpc.py|*.generated.*|*.min.js|*.min.css)
    allow ;;
esac

case "$REL_PATH" in
  */migrations/*|*/alembic/versions/*)
    allow ;;
esac

# Exclude: VibeOS plugin infrastructure files (hooks, scripts, agents, skills)
case "$REL_PATH" in
  plugins/vibeos/hooks/*|plugins/vibeos/scripts/*|plugins/vibeos/agents/*|\
  plugins/vibeos/skills/*|plugins/vibeos/decision-engine/*|\
  plugins/vibeos/reference/*|plugins/vibeos/convergence/*)
    allow ;;
esac

# Only enforce on recognized source code extensions
case "$FILENAME" in
  *.py|*.ts|*.tsx|*.js|*.jsx|*.go|*.rs|*.java|*.cs|*.rb)
    ;;
  *)
    # Not a source file — skip enforcement
    allow ;;
esac

# For Write tool: count lines in the proposed content
if [ "$TOOL_NAME" = "Write" ]; then
  NEW_LINE_COUNT=$(echo "$INPUT" | jq -r '.tool_input.content // ""' 2>/dev/null | wc -l | tr -d '[:space:]')

  if [ "$NEW_LINE_COUNT" -gt "$FILE_BUDGET_MAX" ]; then
    deny "$REL_PATH would be ${NEW_LINE_COUNT} lines (hard limit: ${FILE_BUDGET_MAX}). Decompose into smaller modules before writing."
  fi

  if [ "$NEW_LINE_COUNT" -gt "$FILE_BUDGET_WARN" ]; then
    allow_with_warning "$REL_PATH would be ${NEW_LINE_COUNT} lines (warn threshold: ${FILE_BUDGET_WARN}, hard limit: ${FILE_BUDGET_MAX}). Consider decomposing into smaller modules."
  fi

  allow
fi

# For Edit tool: check current file size as a proxy for post-edit size
if [ ! -f "$FILE_PATH" ]; then
  # File does not exist yet — Edit to a nonexistent file will fail on its own
  allow
fi

LINE_COUNT=$(wc -l < "$FILE_PATH" 2>/dev/null || echo "0")
LINE_COUNT=$(echo "$LINE_COUNT" | tr -d '[:space:]')

if [ "$LINE_COUNT" -ge "$FILE_BUDGET_MAX" ]; then
  deny "$REL_PATH is already ${LINE_COUNT} lines (hard limit: ${FILE_BUDGET_MAX}). Decompose the file before adding more code."
fi

if [ "$LINE_COUNT" -ge "$FILE_BUDGET_WARN" ]; then
  allow_with_warning "$REL_PATH is ${LINE_COUNT} lines (warn threshold: ${FILE_BUDGET_WARN}, hard limit: ${FILE_BUDGET_MAX}). Consider decomposing soon."
fi

allow
