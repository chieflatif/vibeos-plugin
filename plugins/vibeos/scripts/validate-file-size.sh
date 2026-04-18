#!/usr/bin/env bash
# VibeOS file-size gate.
#
# Enforces the line-count limits documented in the repo's file-size
# always-rule. Projects can use either `docs/planning/WO-*.md` or
# `docs/planning/work-orders/WO-*.md` work-order layouts.

set -euo pipefail

FRAMEWORK_VERSION="2.1.0"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  printf 'not a git repository; skipping\n'
  exit 0
fi

is_exempt_by_path() {
  local file="$1"
  case "$file" in
    uv.lock|*.lock|package-lock.json|yarn.lock|pnpm-lock.yaml|Cargo.lock) return 0 ;;
    tests/fixtures/*|tests/fixtures/**/*|tests/data/*|tests/data/**/*) return 0 ;;
    tests/*.json|tests/**/*.json|tests/*.sql|tests/**/*.sql) return 0 ;;
    migrations/*|migrations/**/*) return 0 ;;
    vendor/*|vendor/**/*|third_party/*|third_party/**/*|third-party/*|third-party/**/*) return 0 ;;
    docs/audits/*|docs/audits/**/*) return 0 ;;
  esac
  return 1
}

is_exempt_by_marker() {
  local file="$1"
  [ -f "$file" ] || return 1
  if head -n 10 "$file" 2>/dev/null | grep -qE '(GENERATED|DO NOT EDIT)'; then
    return 0
  fi
  return 1
}

has_valid_exception_marker() {
  local file="$1"
  [ -f "$file" ] || return 1

  local header ref
  header="$(head -n 10 "$file" 2>/dev/null || true)"
  if ! printf '%s\n' "$header" | grep -qE 'FILE-SIZE-EXCEPTION'; then
    return 1
  fi

  ref="$(printf '%s\n' "$header" | grep -oE '(ADR-[0-9]+|WO-[0-9]+)' | head -n 1 || true)"
  if [ -z "$ref" ]; then
    return 1
  fi

  case "$ref" in
    ADR-*)
      compgen -G "docs/architecture/decisions/${ref}*.md" >/dev/null 2>&1 && return 0
      ;;
    WO-*)
      compgen -G "docs/planning/${ref}*.md" >/dev/null 2>&1 && return 0
      compgen -G "docs/planning/work-orders/${ref}*.md" >/dev/null 2>&1 && return 0
      ;;
  esac

  return 1
}

classify() {
  local file="$1"
  case "$file" in
    docs/planning/work-orders/*|docs/planning/WO-*.md) echo "wo 600 450"; return ;;
    docs/*.md|docs/**/*.md|README.md|AGENTS.md|CLAUDE.md) echo "docs 500 300"; return ;;
    tests/*.py|tests/**/*.py|tests/*.ts|tests/**/*.ts|tests/*.tsx|tests/**/*.tsx|tests/*.js|tests/**/*.js) echo "tests 400 300"; return ;;
    src/*.py|src/**/*.py|src/*.ts|src/**/*.ts|src/*.tsx|src/**/*.tsx|src/*.js|src/**/*.js) echo "code 300 250"; return ;;
    scripts/*.sh|scripts/**/*.sh|scripts/*.py|scripts/**/*.py) echo "code 300 250"; return ;;
    .claude/rules/always/*.md) echo "docs 500 300"; return ;;
  esac
  echo "other 0 0"
}

file_list="$(mktemp)"
trap 'rm -f "$file_list"' EXIT
{
  git ls-files
  git ls-files --others --exclude-standard
} | sort -u > "$file_list"

hard_failures=0
soft_warnings=0
exceptions=0

while IFS= read -r file; do
  [ -f "$file" ] || continue
  if is_exempt_by_path "$file"; then
    continue
  fi
  if is_exempt_by_marker "$file"; then
    continue
  fi

  read -r kind hard warn <<<"$(classify "$file")"
  if [ "$kind" = "other" ]; then
    continue
  fi

  lines="$(awk 'END {print NR}' "$file")"
  if [ "$lines" -gt "$hard" ]; then
    if has_valid_exception_marker "$file"; then
      printf 'EXCEPTION: %s at %d lines (%s hard=%d) — marker valid\n' "$file" "$lines" "$kind" "$hard"
      exceptions=$((exceptions + 1))
      continue
    fi
    printf 'HARD BREACH: %s at %d lines (%s hard=%d)\n' "$file" "$lines" "$kind" "$hard"
    hard_failures=$((hard_failures + 1))
    continue
  fi

  if [ "$lines" -gt "$warn" ]; then
    printf 'soft warning: %s at %d lines (%s warn=%d)\n' "$file" "$lines" "$kind" "$warn"
    soft_warnings=$((soft_warnings + 1))
  fi
done < "$file_list"

printf '\nSummary: %d hard breach(es), %d soft warning(s), %d file(s) with valid exception markers.\n' \
  "$hard_failures" "$soft_warnings" "$exceptions"

if [ "$hard_failures" -gt 0 ]; then
  exit 1
fi
exit 0
