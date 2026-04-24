#!/usr/bin/env bash
# VibeOS commit-message format validator.
#
# Enforces a practical subset of the session-scoped git discipline:
# real subject, no throwaway generic subjects, Co-Authored-By trailer,
# and no emoji characters.

set -euo pipefail

FRAMEWORK_VERSION="2.2.0"

if [ $# -lt 1 ]; then
  printf 'usage: %s <commit-message-file>\n' "$0" >&2
  exit 2
fi

MSG_FILE="$1"
if [ ! -f "$MSG_FILE" ]; then
  printf 'commit message file not found: %s\n' "$MSG_FILE" >&2
  exit 2
fi

MSG="$(sed -e '/^#/d' "$MSG_FILE")"
SUBJECT="$(printf '%s\n' "$MSG" | awk 'NF>0 {print; exit}')"

if [ -z "$SUBJECT" ]; then
  printf 'commit-msg: empty subject\n' >&2
  exit 1
fi

subj_len="${#SUBJECT}"
if [ "$subj_len" -gt 72 ]; then
  printf 'commit-msg: subject exceeds 72 chars (%d)\n' "$subj_len" >&2
  printf '  subject: %s\n' "$SUBJECT" >&2
  exit 1
fi

case "$SUBJECT" in
  *WIP*|*"wip"*|*"fix stuff"*|*"Fix stuff"*|*"update files"*|*"Update files"*|*"updates"|*"stuff"*)
    printf 'commit-msg: subject uses a forbidden generic pattern\n' >&2
    printf '  subject: %s\n' "$SUBJECT" >&2
    exit 1
    ;;
esac

if ! printf '%s\n' "$MSG" | grep -qE '^Co-Authored-By:'; then
  printf 'commit-msg: Co-Authored-By trailer missing\n' >&2
  exit 1
fi

if printf '%s' "$MSG" | LC_ALL=C grep -P '[\x{1F000}-\x{1FFFF}\x{2600}-\x{27FF}]' >/dev/null 2>&1; then
  printf 'commit-msg: message contains emoji characters (forbidden)\n' >&2
  exit 1
fi

exit 0
