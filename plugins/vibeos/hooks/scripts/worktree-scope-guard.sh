#!/usr/bin/env bash
# VibeOS Plugin — Worktree Scope Guard
# Prevents agents from editing files that belong to a different parallel feature branch.
# Reads scope definitions from .vibeos/worktree-scopes.json in the project root.
# Shared paths (listed under shared_paths[]) are always allowed.
# Activates only on feat/* branches — passes silently on main or any other branch.
#
# Hook type: PreToolUse (matcher: Edit|Write)
# Response format: JSON with hookSpecificOutput.permissionDecision = allow|deny
# Framework version: 2.0.0
# Note: No set -euo pipefail — hook reads stdin and uses || fallbacks intentionally.
FRAMEWORK_VERSION="2.0.0"

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty' 2>/dev/null || echo "")

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo ".")
SCOPES_FILE="$PROJECT_ROOT/.vibeos/worktree-scopes.json"

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
  local MESSAGE="$1"
  printf '{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "deny",
    "permissionDecisionReason": "[worktree-scope-guard] BLOCKED: %s"
  }
}\n' "$MESSAGE"
  exit 2
}

# Only enforce inside a feat/* worktree
if [[ "$BRANCH" != feat/* ]]; then
  allow
fi

# No file path — nothing to check
if [ -z "$FILE_PATH" ]; then
  allow
fi

# No scope manifest — no restrictions defined
if [ ! -f "$SCOPES_FILE" ]; then
  allow
fi

# Check if the file is in the shared_paths list (always allowed)
while IFS= read -r shared_path; do
  [ -z "$shared_path" ] && continue
  if [[ "$FILE_PATH" == *"$shared_path"* ]]; then
    allow
  fi
done < <(jq -r '.shared_paths[]' "$SCOPES_FILE" 2>/dev/null || true)

# Check if the file belongs to another branch's exclusive territory
while IFS= read -r other_branch; do
  [ -z "$other_branch" ] && continue
  # Skip our own branch
  if [[ "$other_branch" == "$BRANCH" ]]; then
    continue
  fi
  while IFS= read -r exclusive_path; do
    [ -z "$exclusive_path" ] && continue
    if [[ "$FILE_PATH" == *"$exclusive_path"* ]]; then
      deny "File '$FILE_PATH' is exclusive territory of branch '$other_branch'. Edit files within your own scope or add this path to shared_paths if it is truly shared."
    fi
  done < <(jq -r ".branches[\"$other_branch\"].exclusive_paths[]" "$SCOPES_FILE" 2>/dev/null || true)
done < <(jq -r '.branches | keys[]' "$SCOPES_FILE" 2>/dev/null || true)

allow
