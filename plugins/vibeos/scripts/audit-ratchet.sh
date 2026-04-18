#!/usr/bin/env bash
# VibeOS audit ratchet.
#
# Ensures severity counts do not grow between phase baselines.

set -euo pipefail

FRAMEWORK_VERSION="2.1.0"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [ $# -lt 1 ]; then
  printf 'usage: audit-ratchet.sh <current-phase-id> [--save-baseline]\n' >&2
  exit 2
fi

CURRENT_PHASE="$1"
SAVE_BASELINE="false"
[ "${2:-}" = "--save-baseline" ] && SAVE_BASELINE="true"

BASELINES_DIR="$REPO_ROOT/docs/audits/baselines"
mkdir -p "$BASELINES_DIR"

CURRENT_SUMMARY="$(find "$REPO_ROOT/docs/audits" -maxdepth 2 -name summary.json -path "*phase-exit-${CURRENT_PHASE}*" | head -n 1 || true)"

if [ -z "$CURRENT_SUMMARY" ] || [ ! -f "$CURRENT_SUMMARY" ]; then
  printf 'error: no phase-exit summary found for %s\n' "$CURRENT_PHASE" >&2
  exit 1
fi

printf 'current summary: %s\n' "$CURRENT_SUMMARY"

PRIOR_BASELINE=""
prior_idx="$(python3 - <<PY
import re
label = "$CURRENT_PHASE"
m = re.match(r"phase-(\d+)", label)
if not m:
    print("")
else:
    n = int(m.group(1))
    print(f"phase-{n-1}" if n > 1 else "")
PY
)"

if [ -n "$prior_idx" ]; then
  PRIOR_BASELINE="$BASELINES_DIR/$prior_idx/summary.json"
fi

if [ -z "$PRIOR_BASELINE" ] || [ ! -f "$PRIOR_BASELINE" ]; then
  printf 'no prior baseline found; %s becomes the first baseline\n' "$CURRENT_PHASE"
  if [ "$SAVE_BASELINE" = "true" ]; then
    mkdir -p "$BASELINES_DIR/$CURRENT_PHASE"
    cp "$CURRENT_SUMMARY" "$BASELINES_DIR/$CURRENT_PHASE/summary.json"
    printf 'baseline saved: %s/summary.json\n' "$BASELINES_DIR/$CURRENT_PHASE"
  fi
  exit 0
fi

printf 'prior baseline: %s\n' "$PRIOR_BASELINE"

set +e
python3 - "$PRIOR_BASELINE" "$CURRENT_SUMMARY" <<'PY'
import json
import sys

prior = json.load(open(sys.argv[1]))
curr = json.load(open(sys.argv[2]))
prior_totals = prior.get("totals", {})
curr_totals = curr.get("totals", {})
violations = []

for sev in ("critical", "major", "minor"):
    p = int(prior_totals.get(sev, 0))
    c = int(curr_totals.get(sev, 0))
    marker = "OK" if c <= p else "GREW"
    print(f"  {sev}: prior={p}  current={c}  {marker}")
    if c > p:
        violations.append(f"{sev} count grew from {p} to {c}")

if violations:
    print()
    print("RATCHET VIOLATION:")
    for violation in violations:
        print(f"  - {violation}")
    sys.exit(1)

print()
print("ratchet OK: no severity count grew.")
PY
rc=$?
set -e

if [ "$rc" -eq 0 ] && [ "$SAVE_BASELINE" = "true" ]; then
  mkdir -p "$BASELINES_DIR/$CURRENT_PHASE"
  cp "$CURRENT_SUMMARY" "$BASELINES_DIR/$CURRENT_PHASE/summary.json"
  printf 'baseline updated: %s/summary.json\n' "$BASELINES_DIR/$CURRENT_PHASE"
fi

exit "$rc"
