#!/usr/bin/env bash
# VibeOS Plugin — Worktree Scope Setup Hook
# Hook type: WorktreeCreate
# Creates the git worktree and copies VibeOS worktree-scope state into it.

FRAMEWORK_VERSION="2.2.0"

INPUT=$(cat)
NAME=$(echo "$INPUT" | jq -r '.name // ""' 2>/dev/null || echo "")
CWD_VALUE=$(echo "$INPUT" | jq -r '.cwd // ""' 2>/dev/null || echo "")

fail() {
  echo "[worktree-scope-setup] ERROR: $1" >&2
  exit 1
}

if [ -z "$NAME" ]; then
  fail "WorktreeCreate payload did not include a name."
fi

if ! printf '%s' "$NAME" | grep -qE '^[A-Za-z0-9._-]+$'; then
  fail "Invalid worktree name '$NAME'. Use only letters, numbers, dot, underscore, and hyphen."
fi

if [ -z "$CWD_VALUE" ]; then
  CWD_VALUE=$(pwd)
fi

PROJECT_ROOT=$(cd "$CWD_VALUE" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null) || fail "Not inside a git repository: $CWD_VALUE"
PROJECT_ROOT=$(cd "$PROJECT_ROOT" && pwd)
TARGET_DIR="$PROJECT_ROOT/.claude/worktrees/$NAME"
BRANCH="worktree-$NAME"

if [ -e "$TARGET_DIR" ]; then
  fail "Target worktree already exists: $TARGET_DIR"
fi

mkdir -p "$(dirname "$TARGET_DIR")" || fail "Could not create worktree parent directory."

BASE_REF=$(git -C "$PROJECT_ROOT" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true)
if [ -z "$BASE_REF" ]; then
  BASE_REF="HEAD"
fi

git -C "$PROJECT_ROOT" worktree add -b "$BRANCH" "$TARGET_DIR" "$BASE_REF" >&2 || fail "git worktree add failed."

SCOPES_FILE="$PROJECT_ROOT/.vibeos/worktree-scopes.json"
if [ -f "$SCOPES_FILE" ]; then
  mkdir -p "$TARGET_DIR/.vibeos" || fail "Could not create VibeOS state directory in worktree."
  cp "$SCOPES_FILE" "$TARGET_DIR/.vibeos/worktree-scopes.json" || fail "Could not copy worktree scope manifest."
fi

INCLUDE_FILE="$PROJECT_ROOT/.worktreeinclude"
if [ -f "$INCLUDE_FILE" ]; then
  while IFS= read -r include_pattern; do
    include_pattern=$(printf '%s' "$include_pattern" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
    case "$include_pattern" in
      ""|\#*|!*) continue ;;
      /*|*..*) continue ;;
    esac

    matches=()
    while IFS= read -r match; do
      [ -n "$match" ] && matches+=("$match")
    done < <(cd "$PROJECT_ROOT" && compgen -G "$include_pattern" 2>/dev/null || true)
    if [ "${#matches[@]}" -eq 0 ] && [ -e "$PROJECT_ROOT/$include_pattern" ]; then
      matches=("$include_pattern")
    fi

    for rel_path in "${matches[@]}"; do
      rel_path="${rel_path#./}"
      [ -e "$PROJECT_ROOT/$rel_path" ] || continue
      if git -C "$PROJECT_ROOT" check-ignore -q -- "$rel_path"; then
        mkdir -p "$TARGET_DIR/$(dirname "$rel_path")" || fail "Could not create include target directory."
        cp -R "$PROJECT_ROOT/$rel_path" "$TARGET_DIR/$rel_path" || fail "Could not copy included worktree file: $rel_path"
      fi
    done
  done < "$INCLUDE_FILE"
fi

printf '%s\n' "$TARGET_DIR"
