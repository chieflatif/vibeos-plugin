#!/usr/bin/env bash
# VibeOS Plugin — Worktree Bash Guard
# Blocks destructive cross-branch Bash operations in parallel feature worktrees.
# Activates only on feat/* branches. Passes through silently on main or any other branch.
#
# Hook type: PreToolUse (matcher: Bash)
# Response format: JSON with hookSpecificOutput.permissionDecision = allow|deny
# Framework version: 2.2.0
# Note: No set -euo pipefail — hook reads stdin and uses || fallbacks intentionally.
FRAMEWORK_VERSION="2.2.0"

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

# Nothing to check
if [ -z "$COMMAND" ]; then
  allow
fi

# ============================================================
# RULE 1: No Alembic migrations in parallel worktrees
# Schema migrations run on main only. Parallel worktrees must not apply
# migrations — they will conflict with the canonical migration applied
# from main.
# ============================================================
if echo "$COMMAND" | grep -qE 'alembic[[:space:]]+(upgrade|downgrade|revision)'; then
  deny "Alembic migrations must run on main only. Complete your WO on $BRANCH, merge to main via PR, then run migrations. If you need to test schema changes locally, use a disposable test database — not alembic upgrade head in a worktree."
fi

# ============================================================
# RULE 2: No checking out main / master / develop
# Worktrees must stay on their assigned branch. Checking out a base branch
# inside a worktree would abandon all in-progress work on the current branch.
# (git will usually error here anyway — this guard makes the reason explicit.)
# ============================================================
if echo "$COMMAND" | grep -qE 'git[[:space:]]+checkout[[:space:]]+(main|master|develop)\b'; then
  deny "Cannot checkout main/master/develop from a parallel worktree. Main is checked out in the primary working tree. Complete this WO on $BRANCH, then create a PR. If you need to switch context, open a new Claude Code session in the main working tree."
fi

# ============================================================
# RULE 3: No merging main / master / develop INTO this worktree branch
# Use rebase to pull in upstream changes. Merge creates a merge commit
# that makes it harder to cherry-pick or revert individual WO changes.
# ============================================================
if echo "$COMMAND" | grep -qE 'git[[:space:]]+merge[[:space:]]+(origin/)?(main|master|develop)\b'; then
  deny "Do not merge main/master/develop into $BRANCH. Use 'git fetch origin && git rebase origin/main' to pull in upstream changes. Merging creates merge commits that complicate parallel WO history."
fi

# ============================================================
# RULE 4: No merging one parallel worktree branch into another
# Parallel branches are independent. If your WO depends on another feat/*
# branch, wait for that branch to land on main via PR, then rebase.
# Cross-branch merges create hard-to-untangle history.
# ============================================================
if echo "$COMMAND" | grep -qE 'git[[:space:]]+merge[[:space:]]+(origin/)?feat/'; then
  deny "Cannot merge between parallel feature worktrees. Wait for the other branch to land on main via PR, then run: git fetch origin && git rebase origin/main. Cross-branch merges bypass review and create tangled history."
fi

# ============================================================
# RULE 5: No pushing directly to main from a worktree branch
# Belt-and-suspenders: already blocked by Claude Code permissions, but
# the error message here is more actionable for the worktree context.
# ============================================================
if echo "$COMMAND" | grep -qE 'git[[:space:]]+push[[:space:]]+(origin[[:space:]]+)?main\b'; then
  deny "Cannot push directly to main from $BRANCH. Open a PR: gh pr create --base main --head $BRANCH"
fi

# ============================================================
# RULE 6: No destructive database operations in parallel worktrees
# Multiple worktrees share the development database. Destructive DB commands
# will corrupt other worktrees' test runs and are irreversible.
# Blocks: DROP DATABASE, DROP TABLE, TRUNCATE, DELETE FROM ... WHERE 1=1
# ============================================================
if echo "$COMMAND" | grep -qiE '(DROP[[:space:]]+(DATABASE|TABLE)|TRUNCATE[[:space:]]+TABLE|DELETE[[:space:]]+FROM[[:space:]]+[^[:space:]]+[[:space:]]+WHERE[[:space:]]+1[[:space:]]*=[[:space:]]*1)'; then
  deny "Destructive database operations are blocked in parallel worktrees. Multiple worktrees share the development database — DROP, TRUNCATE, and full-table DELETE commands will corrupt other worktrees' test runs. Ask the user to provision a separate test database for this worktree if you need a clean state."
fi

# All checks passed
allow
