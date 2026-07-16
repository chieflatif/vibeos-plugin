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
# Pure-bash subject extraction: awk exiting after the first line races SIGPIPE
# against printf under `set -euo pipefail` on longer messages (exit 141).
SUBJECT=""
while IFS= read -r line; do
  if [ -n "$line" ]; then
    SUBJECT="$line"
    break
  fi
done <<< "$MSG"

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

trailer_found="no"
while IFS= read -r line; do
  case "$line" in
    Co-Authored-By:*) trailer_found="yes"; break ;;
  esac
done <<< "$MSG"
if [ "$trailer_found" != "yes" ]; then
  printf 'commit-msg: Co-Authored-By trailer missing\n' >&2
  exit 1
fi

# python3 instead of grep -P: BSD grep has no -P, which made this check a
# silent no-op on macOS; python reads all of stdin, so no SIGPIPE either.
emoji_found="$(printf '%s' "$MSG" | python3 -c 'import sys, re; print("yes" if re.search("[\U0001F000-\U0001FFFF\u2600-\u27FF]", sys.stdin.read()) else "no")')"
if [ "$emoji_found" = "yes" ]; then
  printf 'commit-msg: message contains emoji characters (forbidden)\n' >&2
  exit 1
fi

exit 0
