#!/usr/bin/env bash
# VibeOS Plugin — Worktree Bash Guard
# Blocks destructive cross-branch Bash operations in parallel feature worktrees.
# Activates only on feat/* branches. Passes through silently on main or any other branch.
#
# Hook type: PreToolUse (matcher: Bash)
# Response format: JSON with hookSpecificOutput.permissionDecision = allow|deny
# Framework version: 2.0.0
# Note: No set -euo pipefail — hook reads stdin and uses || fallbacks intentionally.
FRAMEWORK_VERSION="2.0.0"

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null || echo "")

BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")

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
    "permissionDecisionReason": "[worktree-bash-guard] BLOCKED: %s"
  }
}\n' "$MESSAGE"
  exit 2
}

# Only enforce inside a feat/* worktree
if [[ "$BRANCH" != feat/* ]]; then
  allow
fi

# Alembic migrations must run on main only
if echo "$COMMAND" | grep -qE 'alembic[[:space:]]+(upgrade|downgrade|revision)'; then
  deny "Alembic migrations must run on main only. Complete your WO, merge to main, then run migrations."
fi

# Checking out main from inside a feature worktree corrupts the worktree
if echo "$COMMAND" | grep -qE 'git[[:space:]]+checkout[[:space:]]+main'; then
  deny "Cannot checkout main from a feature worktree. Use your dedicated worktree or open main separately."
fi

# Merge from main in a worktree creates messy history — use rebase instead
if echo "$COMMAND" | grep -qE 'git[[:space:]]+merge[[:space:]]+origin/main'; then
  deny "Use 'git rebase origin/main' instead of merge to keep history clean in parallel worktrees."
fi

# Merging between parallel feat/* branches bypasses review — wait for main, then rebase
if echo "$COMMAND" | grep -qE 'git[[:space:]]+merge[[:space:]]+feat/'; then
  deny "Cannot merge between parallel feature worktrees. Wait for the other branch to land on main, then rebase."
fi

# Pushing directly to main from a worktree bypasses PR workflow
if echo "$COMMAND" | grep -qE 'git[[:space:]]+push[[:space:]]+origin[[:space:]]+main'; then
  deny "Cannot push directly to main from a feature worktree. Open a PR instead."
fi

# Destructive DB operations are irreversible — never run in an isolated worktree
if echo "$COMMAND" | grep -qiE '(DROP[[:space:]]+DATABASE|TRUNCATE[[:space:]]+TABLE)'; then
  deny "Destructive database commands are blocked in feature worktrees. Run only from main after team review."
fi

allow
