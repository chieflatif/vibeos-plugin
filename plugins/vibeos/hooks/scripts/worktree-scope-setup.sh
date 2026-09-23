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

# Whole-string check (grep would accept a multi-line value line by line).
# "." and ".." are rejected because they would resolve outside the worktree
# directory.
case "$NAME" in
  .|..|*[!A-Za-z0-9._-]*)
    fail "Invalid worktree name. Use only letters, numbers, dot, underscore, and hyphen (not '.' or '..')."
    ;;
esac

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

# Like Claude Code's default, refuse symlinks on the worktree path, so a
# worktree can never be created or reopened outside .claude/worktrees.
for link_candidate in "$PROJECT_ROOT/.claude" "$PROJECT_ROOT/.claude/worktrees" "$TARGET_DIR"; do
  if [ -L "$link_candidate" ]; then
    fail "Refusing a symlink on the worktree path: $link_candidate"
  fi
done

# True when DIR is a registered linked worktree of this repository (never the
# main checkout). Compares physical paths against `git worktree list`, whose
# first entry is always the main working tree.
is_linked_worktree_of_this_repo() {
  local dir_real entry entry_real first=1
  dir_real=$(cd "$1" 2>/dev/null && pwd -P) || return 1
  while IFS= read -r entry; do
    case "$entry" in
      "worktree "*) entry="${entry#worktree }" ;;
      *) continue ;;
    esac
    if [ "$first" -eq 1 ]; then
      first=0
      continue
    fi
    entry_real=$(cd "$entry" 2>/dev/null && pwd -P) || continue
    [ "$entry_real" = "$dir_real" ] && is_usable_worktree "$dir_real" && return 0
  done < <(git -C "$PROJECT_ROOT" worktree list --porcelain 2>/dev/null)
  return 1
}

# True when git itself can use DIR as a worktree of this repository: its top
# level is DIR and it shares this repository's common git directory. Rejects
# a registered worktree whose .git link is missing or broken.
is_usable_worktree() {
  local dir="$1" top_real dir_common repo_common
  top_real=$(cd "$dir" 2>/dev/null && cd "$(git rev-parse --show-toplevel 2>/dev/null)" 2>/dev/null && pwd -P) || return 1
  [ "$top_real" = "$dir" ] || return 1
  dir_common=$(cd "$dir" && cd "$(git rev-parse --git-common-dir 2>/dev/null)" 2>/dev/null && pwd -P) || return 1
  repo_common=$(cd "$PROJECT_ROOT" && cd "$(git rev-parse --git-common-dir 2>/dev/null)" 2>/dev/null && pwd -P) || return 1
  [ "$dir_common" = "$repo_common" ]
}

# Copy the VibeOS scope manifest and gitignored .worktreeinclude matches into
# the worktree. Only missing destinations are written, so a reopen completes
# an interrupted setup without overwriting anything edited in the worktree.
copy_setup_files() {
  local scopes_file="$PROJECT_ROOT/.vibeos/worktree-scopes.json"
  local include_file="$PROJECT_ROOT/.worktreeinclude"
  local include_pattern match rel_path
  if [ -f "$scopes_file" ] && [ ! -e "$TARGET_DIR/.vibeos/worktree-scopes.json" ]; then
    mkdir -p "$TARGET_DIR/.vibeos" || fail "Could not create VibeOS state directory in worktree."
    cp "$scopes_file" "$TARGET_DIR/.vibeos/worktree-scopes.json" || fail "Could not copy worktree scope manifest."
  fi
  [ -f "$include_file" ] || return 0
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
      [ -e "$TARGET_DIR/$rel_path" ] && continue
      if git -C "$PROJECT_ROOT" check-ignore -q -- "$rel_path"; then
        mkdir -p "$TARGET_DIR/$(dirname "$rel_path")" || fail "Could not create include target directory."
        cp -R "$PROJECT_ROOT/$rel_path" "$TARGET_DIR/$rel_path" || fail "Could not copy included worktree file: $rel_path"
      fi
    done
  done < "$include_file"
}

if [ -e "$TARGET_DIR" ]; then
  # Claude Code's default reopens an existing worktree of the same name.
  if is_linked_worktree_of_this_repo "$TARGET_DIR"; then
    copy_setup_files
    printf '%s\n' "$TARGET_DIR"
    exit 0
  fi
  fail "Target path exists and is not a linked worktree of this repository: $TARGET_DIR"
fi

mkdir -p "$(dirname "$TARGET_DIR")" || fail "Could not create worktree parent directory."
PARENT_REAL=$(cd "$(dirname "$TARGET_DIR")" && pwd -P) || fail "Could not resolve worktree parent directory."
EXPECTED_PARENT_REAL="$(cd "$PROJECT_ROOT" && pwd -P)/.claude/worktrees"
if [ "$PARENT_REAL" != "$EXPECTED_PARENT_REAL" ]; then
  fail "Worktree parent resolves outside the repository: $PARENT_REAL"
fi

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

copy_setup_files

printf '%s\n' "$TARGET_DIR"
