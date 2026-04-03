#!/usr/bin/env bash
# VibeOS — Audit Visibility Validation Gate
# Fails closed when a post-implementation audit could not actually see the code
# it is being used to validate.
#
# Usage:
#   bash .vibeos/scripts/validate-audit-visibility.sh [work-order-file] [audit-report]
#
# Environment:
#   PROJECT_ROOT         Project root (default: auto-detect)
#   WO_FILE              Explicit work-order file
#   WO_NUMBER            Work-order number (e.g. WO-058)
#   SESSION_STATE_FILE   Session-state file to inspect for active_wo and audit metadata
#   LAST_AUDIT_REPORT    Explicit audit report path
#
# Exit codes:
#   0 = audit visibility is acceptable or gate skipped
#   1 = audit visibility is invalid
#   2 = configuration error
set -euo pipefail

FRAMEWORK_VERSION="2.1.0"
GATE_NAME="validate-audit-visibility"

usage() {
  cat <<'EOF'
Usage:
  bash .vibeos/scripts/validate-audit-visibility.sh [work-order-file] [audit-report]

Validation target resolution order:
  WO:
    1. CLI argument 1
    2. WO_FILE env var
    3. WO_NUMBER resolved under docs/planning
    4. active_wo in .vibeos/session-state.json

  Audit report:
    1. CLI argument 2
    2. LAST_AUDIT_REPORT env var
    3. last_audit_report in .vibeos/session-state.json

Rules:
  - Every WO post-implementation audit must declare an audit visibility mode:
      same-tree | snapshot | committed-tree
  - If audited target files are still uncommitted, only same-tree or snapshot
    are valid.
  - Any audit report explicitly marked stale, inconclusive due to worktree
    mismatch, or unable to see the changed files is a hard failure.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}}"
SESSION_STATE_FILE="${SESSION_STATE_FILE:-$PROJECT_ROOT/.vibeos/session-state.json}"

resolve_wo_target() {
  local explicit="$1"
  local candidate=""

  if [[ -n "$explicit" ]]; then
    if [[ "$explicit" == /* && -f "$explicit" ]]; then
      candidate="$explicit"
    elif [[ -f "$PROJECT_ROOT/$explicit" ]]; then
      candidate="$PROJECT_ROOT/$explicit"
    else
      candidate="$(find "$PROJECT_ROOT/docs/planning" -maxdepth 1 -type f \( -name "${explicit}.md" -o -name "${explicit}*.md" \) | head -n 1 || true)"
      if [[ -z "$candidate" ]]; then
        candidate="$explicit"
      fi
    fi
  elif [[ -n "${WO_FILE:-}" ]]; then
    candidate="$WO_FILE"
  elif [[ -n "${WO_NUMBER:-}" ]]; then
    candidate="$(find "$PROJECT_ROOT/docs/planning" -maxdepth 1 -type f -name "${WO_NUMBER}*.md" | head -n 1 || true)"
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

resolve_audit_target() {
  local explicit="$1"
  local candidate=""

  if [[ -n "$explicit" ]]; then
    candidate="$explicit"
  elif [[ -n "${LAST_AUDIT_REPORT:-}" ]]; then
    candidate="$LAST_AUDIT_REPORT"
  elif [[ -f "$SESSION_STATE_FILE" ]] && command -v jq >/dev/null 2>&1; then
    candidate="$(jq -r '.last_audit_report // empty' "$SESSION_STATE_FILE" 2>/dev/null || echo "")"
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
AUDIT_REPORT="$(resolve_audit_target "${2:-}")"

if [[ -z "$WO_TARGET" ]]; then
  echo "[$GATE_NAME] SKIP: No work-order target resolved"
  exit 0
fi

if [[ ! -f "$WO_TARGET" ]]; then
  echo "[$GATE_NAME] FAIL: Work-order target not found: $WO_TARGET"
  exit 2
fi

if [[ -z "$AUDIT_REPORT" ]]; then
  echo "[$GATE_NAME] FAIL: No audit report target resolved for $(basename "$WO_TARGET")"
  echo "[$GATE_NAME] Action: record last_audit_report and rerun this gate"
  exit 1
fi

if [[ ! -f "$AUDIT_REPORT" ]]; then
  echo "[$GATE_NAME] FAIL: Audit report not found: $AUDIT_REPORT"
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

AUDIT_CONTENT="$(cat "$AUDIT_REPORT")"
AUDIT_MODE=""
SNAPSHOT_REF=""

if [[ -f "$SESSION_STATE_FILE" ]] && command -v jq >/dev/null 2>&1; then
  AUDIT_MODE="$(jq -r '.audit_visibility_mode // empty' "$SESSION_STATE_FILE" 2>/dev/null || echo "")"
  SNAPSHOT_REF="$(jq -r '.audit_snapshot_ref // empty' "$SESSION_STATE_FILE" 2>/dev/null || echo "")"
fi

if [[ -z "$AUDIT_MODE" ]]; then
  AUDIT_MODE="$(printf '%s\n' "$AUDIT_CONTENT" | sed -nE 's/.*audit_visibility_mode:[[:space:]]*(same-tree|snapshot|committed-tree).*/\1/p' | head -n 1)"
fi

if [[ -z "$SNAPSHOT_REF" ]]; then
  SNAPSHOT_REF="$(printf '%s\n' "$AUDIT_CONTENT" | sed -nE 's/.*audit_snapshot_ref:[[:space:]]*([^[:space:]]+).*/\1/p' | head -n 1)"
fi

if printf '%s\n' "$AUDIT_CONTENT" | grep -qiE 'stale worktree|worktree limitation|worktree scope mismatch|false-negative\(worktree\)|couldn.?t see uncommitted|pre-implementation worktrees|inconclusive.*worktree'; then
  echo "[$GATE_NAME] FAIL: Audit report is explicitly invalid due to stale or mismatched worktree visibility"
  echo "[$GATE_NAME] Report: $AUDIT_REPORT"
  exit 1
fi

if [[ -z "$AUDIT_MODE" ]]; then
  echo "[$GATE_NAME] FAIL: Audit visibility mode missing for $(basename "$WO_TARGET")"
  echo "[$GATE_NAME] Required: audit_visibility_mode: same-tree | snapshot | committed-tree"
  exit 1
fi

if [[ "$AUDIT_MODE" != "same-tree" && "$AUDIT_MODE" != "snapshot" && "$AUDIT_MODE" != "committed-tree" ]]; then
  echo "[$GATE_NAME] FAIL: Unsupported audit visibility mode '$AUDIT_MODE'"
  exit 1
fi

if [[ ${#CHANGED_TARGETS[@]} -gt 0 ]]; then
  if [[ "$AUDIT_MODE" != "same-tree" && "$AUDIT_MODE" != "snapshot" ]]; then
    echo "[$GATE_NAME] FAIL: Uncommitted WO files require same-tree or snapshot audit visibility"
    printf '  changed: %s\n' "${CHANGED_TARGETS[@]}"
    echo "[$GATE_NAME] Current mode: $AUDIT_MODE"
    exit 1
  fi
fi

if [[ "$AUDIT_MODE" == "snapshot" && -z "$SNAPSHOT_REF" ]]; then
  echo "[$GATE_NAME] FAIL: snapshot audit visibility declared without audit_snapshot_ref"
  exit 1
fi

echo "[$GATE_NAME] PASS: Audit visibility is valid for $(basename "$WO_TARGET")"
echo "[$GATE_NAME] mode=$AUDIT_MODE"
if [[ -n "$SNAPSHOT_REF" ]]; then
  echo "[$GATE_NAME] snapshot_ref=$SNAPSHOT_REF"
fi
if [[ ${#CHANGED_TARGETS[@]} -gt 0 ]]; then
  echo "[$GATE_NAME] changed_targets=${#CHANGED_TARGETS[@]}"
fi
exit 0
