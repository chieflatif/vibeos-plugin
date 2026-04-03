#!/usr/bin/env bash
# VibeOS — Audit Visibility Mode Selector
# Chooses the safest audit visibility mode for the current work order without
# interrupting autonomous execution.
#
# Usage:
#   bash .vibeos/scripts/select-audit-visibility-mode.sh [work-order-file-or-id]
#
# Environment:
#   PROJECT_ROOT          Project root (default: auto-detect)
#   WO_FILE               Explicit work-order path
#   WO_NUMBER             Work-order number (e.g. WO-058)
#   SESSION_STATE_FILE    Session state file to update
#   AUDIT_VISIBILITY_MODE Optional override: same-tree | snapshot | committed-tree
#   AUDIT_SNAPSHOT_REF    Optional snapshot reference when using snapshot mode
#
# Exit codes:
#   0 = selection succeeded
#   1 = selection failed
#   2 = configuration error
set -euo pipefail

FRAMEWORK_VERSION="2.1.0"
GATE_NAME="select-audit-visibility-mode"

usage() {
  cat <<'EOF'
Usage:
  bash .vibeos/scripts/select-audit-visibility-mode.sh [work-order-file-or-id]

Chooses one of:
  - same-tree       (audit reads live uncommitted files)
  - snapshot        (audit reads a named git ref)
  - committed-tree  (audit runs in an isolated worktree from HEAD)

Selection rules:
  - If AUDIT_VISIBILITY_MODE is explicitly set, use it (with validation).
  - If the active WO has uncommitted files in its allowed write scope,
    choose same-tree.
  - Otherwise choose committed-tree.

The script also records:
  - audit_visibility_mode
  - audit_snapshot_ref
  - audit_dispatch_profile

into .vibeos/session-state.json so downstream audit and session-close logic can
use the same truth.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}}"
SESSION_STATE_FILE="${SESSION_STATE_FILE:-$PROJECT_ROOT/.vibeos/session-state.json}"
WO_DIR="$PROJECT_ROOT/docs/planning"

resolve_wo_target() {
  local explicit="$1"
  local candidate=""

  if [[ -n "$explicit" ]]; then
    if [[ "$explicit" == /* && -f "$explicit" ]]; then
      candidate="$explicit"
    elif [[ -f "$PROJECT_ROOT/$explicit" ]]; then
      candidate="$PROJECT_ROOT/$explicit"
    else
      candidate="$(find "$WO_DIR" -maxdepth 1 -type f \( -name "${explicit}.md" -o -name "${explicit}*.md" \) | head -n 1 || true)"
      if [[ -z "$candidate" ]]; then
        candidate="$explicit"
      fi
    fi
  elif [[ -n "${WO_FILE:-}" ]]; then
    candidate="$WO_FILE"
  elif [[ -n "${WO_NUMBER:-}" ]]; then
    candidate="$(find "$WO_DIR" -maxdepth 1 -type f -name "${WO_NUMBER}*.md" | head -n 1 || true)"
  elif [[ -f "$SESSION_STATE_FILE" ]] && command -v jq >/dev/null 2>&1; then
    candidate="$(jq -r '.active_wo // .started_from_wo // empty' "$SESSION_STATE_FILE" 2>/dev/null || echo "")"
  fi

  if [[ -z "$candidate" ]]; then
    echo ""
    return 0
  fi

  if [[ "$candidate" != /* ]]; then
    candidate="$PROJECT_ROOT/$candidate"
  fi

  echo "$candidate"
}

extract_allowed_scope_paths() {
  local wo_file="$1"
  awk '
    /^## Write Scope/ { in_section=1; next }
    /^## / && in_section { exit }
    in_section {
      while (match($0, /`[^`]+`/)) {
        token=substr($0, RSTART + 1, RLENGTH - 2)
        print token
        $0=substr($0, RSTART + RLENGTH)
      }
    }
  ' "$wo_file"
}

WO_TARGET="$(resolve_wo_target "${1:-}")"
if [[ -z "$WO_TARGET" ]]; then
  echo "[$GATE_NAME] FAIL: No work-order target resolved"
  exit 2
fi

if [[ ! -f "$WO_TARGET" ]]; then
  echo "[$GATE_NAME] FAIL: Work-order not found: $WO_TARGET"
  exit 2
fi

SCOPE_PATHS=()
while IFS= read -r scope_path; do
  [[ -n "$scope_path" ]] && SCOPE_PATHS+=("$scope_path")
done < <(extract_allowed_scope_paths "$WO_TARGET")

if [[ ${#SCOPE_PATHS[@]} -eq 0 ]]; then
  echo "[$GATE_NAME] FAIL: No write-scope paths found in $(basename "$WO_TARGET")"
  exit 1
fi

MODE="${AUDIT_VISIBILITY_MODE:-}"
SNAPSHOT_REF="${AUDIT_SNAPSHOT_REF:-}"
CHANGED_TARGETS=()

for path in "${SCOPE_PATHS[@]}"; do
  # Ignore absolute-style tokens that are not repo paths.
  if [[ "$path" == /* ]]; then
    continue
  fi
  if [[ -e "$PROJECT_ROOT/$path" ]] || git -C "$PROJECT_ROOT" ls-files --error-unmatch "$path" >/dev/null 2>&1; then
    while IFS= read -r changed; do
      [[ -n "$changed" ]] && CHANGED_TARGETS+=("$changed")
    done < <(git -C "$PROJECT_ROOT" status --porcelain -- "$path")
  fi
done

if [[ -z "$MODE" ]]; then
  if [[ ${#CHANGED_TARGETS[@]} -gt 0 ]]; then
    MODE="same-tree"
  else
    MODE="committed-tree"
  fi
fi

case "$MODE" in
  same-tree)
    DISPATCH_PROFILE="same-tree"
    SNAPSHOT_REF=""
    ;;
  snapshot)
    DISPATCH_PROFILE="same-tree"
    if [[ -z "$SNAPSHOT_REF" ]]; then
      echo "[$GATE_NAME] FAIL: snapshot mode requires AUDIT_SNAPSHOT_REF"
      exit 1
    fi
    ;;
  committed-tree)
    DISPATCH_PROFILE="worktree"
    SNAPSHOT_REF=""
    if [[ ${#CHANGED_TARGETS[@]} -gt 0 ]]; then
      echo "[$GATE_NAME] FAIL: committed-tree audit is invalid while WO files are still uncommitted"
      printf '  changed: %s\n' "${CHANGED_TARGETS[@]}"
      exit 1
    fi
    ;;
  *)
    echo "[$GATE_NAME] FAIL: Unsupported audit visibility mode '$MODE'"
    exit 1
    ;;
esac

mkdir -p "$PROJECT_ROOT/.vibeos"

python3 - "$SESSION_STATE_FILE" "$MODE" "$SNAPSHOT_REF" "$DISPATCH_PROFILE" <<'PYEOF'
import json
import os
import sys

session_state_file, mode, snapshot_ref, dispatch_profile = sys.argv[1:5]

data = {}
if os.path.exists(session_state_file):
    with open(session_state_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)

data["audit_visibility_mode"] = mode
data["audit_snapshot_ref"] = snapshot_ref or None
data["audit_dispatch_profile"] = dispatch_profile

with open(session_state_file, "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2)
    handle.write("\n")
PYEOF

echo "[$GATE_NAME] PASS: Selected audit visibility mode for $(basename "$WO_TARGET")"
echo "[$GATE_NAME] audit_visibility_mode=$MODE"
echo "[$GATE_NAME] audit_dispatch_profile=$DISPATCH_PROFILE"
if [[ -n "$SNAPSHOT_REF" ]]; then
  echo "[$GATE_NAME] audit_snapshot_ref=$SNAPSHOT_REF"
fi
if [[ ${#CHANGED_TARGETS[@]} -gt 0 ]]; then
  echo "[$GATE_NAME] changed_targets=${#CHANGED_TARGETS[@]}"
fi
exit 0
