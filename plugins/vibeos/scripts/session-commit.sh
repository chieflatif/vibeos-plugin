#!/usr/bin/env bash
# VibeOS session-scoped commit helper.
#
# Stages only named files, runs pre_commit gates when possible,
# creates a commit with an explicit Co-Authored-By trailer, and can
# push when requested.

set -euo pipefail

FRAMEWORK_VERSION="2.2.0"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

SUBJECT=""
BODY=""
FILES=()
DO_PUSH="false"
AUTHOR_TRAILER="${SESSION_COMMIT_AUTHOR_TRAILER:-Co-Authored-By: Claude Code Agent <noreply@anthropic.com>}"

while [ $# -gt 0 ]; do
  case "$1" in
    --subject) SUBJECT="$2"; shift 2 ;;
    --message) BODY="$2"; shift 2 ;;
    --file) FILES+=("$2"); shift 2 ;;
    --push) DO_PUSH="true"; shift ;;
    --author-trailer) AUTHOR_TRAILER="$2"; shift 2 ;;
    *) printf 'unknown argument: %s\n' "$1" >&2; exit 2 ;;
  esac
done

if [ -z "$SUBJECT" ]; then
  printf 'error: --subject is required\n' >&2
  exit 2
fi

if [ "${#FILES[@]}" -eq 0 ]; then
  printf 'error: at least one --file argument is required\n' >&2
  printf '\ncurrent repo status (for reference):\n'
  git status --short
  exit 2
fi

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  printf 'error: not a git repository\n' >&2
  exit 2
fi

GATE_RUNNER=""
if [ -x "$REPO_ROOT/scripts/gate-runner.sh" ]; then
  GATE_RUNNER="$REPO_ROOT/scripts/gate-runner.sh"
elif [ -x "$REPO_ROOT/.vibeos/scripts/gate-runner.sh" ]; then
  GATE_RUNNER="$REPO_ROOT/.vibeos/scripts/gate-runner.sh"
fi

if [ -n "$GATE_RUNNER" ]; then
  printf '\n--- pre-commit gate-runner ---\n'
  if ! bash "$GATE_RUNNER" pre_commit; then
    printf '\nerror: pre-commit gates failed; commit blocked\n' >&2
    exit 1
  fi
fi

printf '\n--- pre-existing dirty state (will not be committed automatically) ---\n'
set +e
dirty_before="$(git status --short)"
set -e
if [ -n "$dirty_before" ]; then
  printf '%s\n' "$dirty_before"
else
  printf '(clean — no dirty state)\n'
fi

printf '\n--- staging session-work files explicitly ---\n'
for file in "${FILES[@]}"; do
  if [ ! -e "$file" ] && ! git ls-files --deleted | grep -Fqx "$file"; then
    printf 'warning: file not present and not a known deletion: %s\n' "$file" >&2
    continue
  fi
  git add -- "$file"
  printf '  staged: %s\n' "$file"
done

staged="$(git diff --cached --name-only)"
if [ -z "$staged" ]; then
  printf 'error: no files staged after explicit adds; nothing to commit\n' >&2
  exit 1
fi

printf '\n--- commit ---\n'
commit_message="$SUBJECT"
if [ -n "$BODY" ]; then
  commit_message="$SUBJECT

$BODY"
fi
commit_message="$commit_message

$AUTHOR_TRAILER"

git commit -m "$commit_message"
commit_sha="$(git rev-parse HEAD)"
printf 'committed: %s\n' "$commit_sha"

if [ "$DO_PUSH" = "true" ]; then
  printf '\n--- push to remote ---\n'
  if ! git remote | grep -q origin; then
    printf 'no remote named origin configured; skipping push\n'
  else
    branch="$(git branch --show-current)"
    if git ls-remote --heads origin "$branch" | grep -q "$branch"; then
      git push origin "$branch"
    else
      git push -u origin "$branch"
    fi
    printf 'pushed: origin/%s -> %s\n' "$branch" "$commit_sha"
  fi
fi

printf '\n--- remaining uncommitted state ---\n'
remaining="$(git status --short)"
if [ -n "$remaining" ]; then
  printf '%s\n' "$remaining"
else
  printf '(clean)\n'
fi

printf '\nsession-commit: complete\n'
exit 0
