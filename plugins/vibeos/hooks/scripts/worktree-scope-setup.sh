#!/usr/bin/env bash
# VibeOS Plugin — Worktree Scope Setup Hook
# Hook type: WorktreeCreate
# Creates the git worktree for Claude Code and copies VibeOS worktree-scope
# state into it when present.
#
# A registered WorktreeCreate hook REPLACES Claude Code's default worktree
# creation in every repository (this plugin is user-scoped), and a hook that
# prints no path makes creation fail. So, unlike the other VibeOS hooks, this
# one deliberately has no VibeOS project-scope guard: it must behave like the
# default in any git repository (WO-168). Output contract: the worktree's
# absolute path is the only stdout line; everything else goes to stderr.

FRAMEWORK_VERSION="2.4.2"

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

# Claude Code's worktree.baseRef setting: "fresh" (default) branches from
# origin/<default-branch>; "head" branches from the current checkout's HEAD.
# The hook payload does not carry it, so read the settings files in Claude
# Code's precedence order: local > project > user. Missing, malformed or
# unrecognised values fall through to the next file, then to "fresh".
read_base_ref_mode() {
  local settings_file value
  for settings_file in \
    "$PROJECT_ROOT/.claude/settings.local.json" \
    "$PROJECT_ROOT/.claude/settings.json" \
    "${HOME:-}/.claude/settings.json"; do
    [ -f "$settings_file" ] || continue
    value=$(jq -r '.worktree.baseRef // empty' "$settings_file" 2>/dev/null) || continue
    case "$value" in
      head|fresh)
        printf '%s' "$value"
        return 0
        ;;
    esac
  done
  printf 'fresh'
}

# True when DIR is the top of a linked worktree of the same repository.
is_worktree_of_this_repo() {
  local dir="$1" top dir_real top_real dir_common repo_common
  top=$(cd "$dir" 2>/dev/null && git rev-parse --show-toplevel 2>/dev/null) || return 1
  dir_real=$(cd "$dir" && pwd -P) || return 1
  top_real=$(cd "$top" && pwd -P) || return 1
  [ "$dir_real" = "$top_real" ] || return 1
  dir_common=$(cd "$dir" && cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P) || return 1
  repo_common=$(cd "$PROJECT_ROOT" && cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P) || return 1
  [ "$dir_common" = "$repo_common" ]
}

if [ -e "$TARGET_DIR" ]; then
  # Claude Code's default reopens an existing worktree of the same name.
  if is_worktree_of_this_repo "$TARGET_DIR"; then
    printf '%s\n' "$TARGET_DIR"
    exit 0
  fi
  fail "Target path exists and is not a worktree of this repository: $TARGET_DIR"
fi

mkdir -p "$(dirname "$TARGET_DIR")" || fail "Could not create worktree parent directory."

BASE_MODE=$(read_base_ref_mode)
BASE_REF=""
if [ "$BASE_MODE" = "fresh" ]; then
  BASE_REF=$(git -C "$PROJECT_ROOT" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true)
  if [ -n "$BASE_REF" ] && ! git -C "$PROJECT_ROOT" rev-parse --verify --quiet "${BASE_REF}^{commit}" >/dev/null 2>&1; then
    BASE_REF=""
  fi
fi
if [ -z "$BASE_REF" ]; then
  # "head", or "fresh" with no usable origin default branch: the current HEAD.
  BASE_REF=$(git -C "$PROJECT_ROOT" rev-parse --verify --quiet "HEAD^{commit}" 2>/dev/null) || fail "Repository has no commit to branch from: $PROJECT_ROOT"
fi
echo "[worktree-scope-setup] baseRef=$BASE_MODE base=$BASE_REF" >&2

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
