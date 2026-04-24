#!/usr/bin/env bash
# VibeOS — Session Activation Helper
# Creates or updates session-state.json so context-aware hooks and gates
# can enforce against the active WO surface.
#
# Usage:
#   bash .vibeos/scripts/activate-session.sh <WO-ID-or-path> [agent-name]
#
# Examples:
#   bash .vibeos/scripts/activate-session.sh WO-056
#   bash .vibeos/scripts/activate-session.sh docs/planning/WO-056-session-state.md investigator
set -euo pipefail
FRAMEWORK_VERSION="2.2.0"

usage() {
  cat <<'EOF'
Usage:
  bash .vibeos/scripts/activate-session.sh <WO-ID-or-path> [agent-name]

This writes .vibeos/session-state.json with:
  - mode: autonomous
  - active: true
  - active_wo: relative path to the active work order

If [agent-name] is provided, .vibeos/current-agent.txt is updated as well.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/../.." && pwd)}"
SESSION_STATE_FILE="$PROJECT_ROOT/.vibeos/session-state.json"
CURRENT_AGENT_FILE="$PROJECT_ROOT/.vibeos/current-agent.txt"
PLANNING_DIR="$PROJECT_ROOT/docs/planning"
TARGET_REF="$1"
AGENT_NAME="${2:-}"

resolve_target() {
  local ref="$1"
  local candidate

  # Absolute path
  if [[ "$ref" == /* && -f "$ref" ]]; then
    printf '%s' "$ref"
    return 0
  fi

  # Relative path from project root
  if [[ -f "$PROJECT_ROOT/$ref" ]]; then
    printf '%s' "$PROJECT_ROOT/$ref"
    return 0
  fi

  # Try planning directory with common WO naming patterns
  for candidate in \
    "$PLANNING_DIR/${ref}.md" \
    "$PLANNING_DIR"/"${ref}"*.md \
    "$PLANNING_DIR/WO-${ref}.md" \
    "$PLANNING_DIR"/WO-"${ref}"*.md; do
    if [[ -f "$candidate" ]]; then
      printf '%s' "$candidate"
      return 0
    fi
  done

  return 1
}

TARGET_PATH="$(resolve_target "$TARGET_REF" || true)"
if [[ -z "$TARGET_PATH" ]]; then
  echo "[activate-session] FAIL: Could not resolve work order target: $TARGET_REF" >&2
  exit 2
fi

mkdir -p "$PROJECT_ROOT/.vibeos"

REL_TARGET="$TARGET_PATH"
if [[ "$TARGET_PATH" == "$PROJECT_ROOT"/* ]]; then
  REL_TARGET="${TARGET_PATH#$PROJECT_ROOT/}"
fi

SESSION_ID="${CLAUDE_SESSION_ID:-$(date -u +"%Y%m%dT%H%M%SZ")}"
NOW="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

python3 - "$SESSION_STATE_FILE" "$SESSION_ID" "$NOW" "$REL_TARGET" <<'PYEOF'
import json
import os
import sys

session_state_file, session_id, now, rel_target = sys.argv[1:5]

data = {}
if os.path.exists(session_state_file):
    with open(session_state_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)

data["session_id"] = data.get("session_id") or session_id
data["mode"] = "autonomous"
data["active"] = True
data["started_at"] = data.get("started_at") or now
data["last_updated"] = now
data["active_wo"] = rel_target
data.setdefault("completed_wos", [])
data.setdefault("phase_checkpoints", [])
data.setdefault("last_audit_report", None)
data.setdefault("last_session_audit_report", None)
data.setdefault("last_audited_at", None)
data.setdefault("audit_visibility_mode", None)
data.setdefault("audit_snapshot_ref", None)
data.setdefault("audit_dispatch_profile", None)
data.pop("ended_at", None)
data.pop("paused_at", None)

with open(session_state_file, "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2)
    handle.write("\n")
PYEOF

if [[ -n "$AGENT_NAME" ]]; then
  printf '%s\n' "$AGENT_NAME" > "$CURRENT_AGENT_FILE"
fi

echo "[activate-session] PASS: Activated session for $REL_TARGET"
if [[ -n "$AGENT_NAME" ]]; then
  echo "[activate-session] Agent identity set to $AGENT_NAME"
fi
