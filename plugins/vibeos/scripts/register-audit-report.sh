#!/usr/bin/env bash
# VibeOS — Audit Report Registrar
# Records the authoritative audit report path and audit visibility metadata in
# session-state.json so closure gates can validate the correct report.
#
# Usage:
#   bash .vibeos/scripts/register-audit-report.sh <report-path>
#
# Environment:
#   PROJECT_ROOT          Project root (default: auto-detect)
#   SESSION_STATE_FILE    Session state file to update
#   AUDIT_VISIBILITY_MODE Optional override for visibility mode
#   AUDIT_SNAPSHOT_REF    Optional snapshot ref
#   AUDIT_REPORT_TYPE     Optional override (default: post-implementation)
#   AUDIT_WORK_ORDER      Optional override (e.g. WO-058)
#   WO_NUMBER             Alternative WO number source
#
# Exit codes:
#   0 = registration succeeded
#   2 = configuration error (missing report path or file not found)
set -euo pipefail

FRAMEWORK_VERSION="2.1.0"
GATE_NAME="register-audit-report"

if [[ $# -lt 1 ]]; then
  echo "[$GATE_NAME] FAIL: report path required" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}}"
SESSION_STATE_FILE="${SESSION_STATE_FILE:-$PROJECT_ROOT/.vibeos/session-state.json}"
REPORT_PATH="$1"

infer_work_order() {
  local explicit="${AUDIT_WORK_ORDER:-${WO_NUMBER:-}}"
  if [[ -n "$explicit" ]]; then
    printf '%s' "$explicit"
    return 0
  fi

  if [[ -f "$SESSION_STATE_FILE" ]] && command -v jq >/dev/null 2>&1; then
    local active_wo
    active_wo="$(jq -r '.active_wo // .started_from_wo // empty' "$SESSION_STATE_FILE" 2>/dev/null || echo "")"
    if [[ -n "$active_wo" ]]; then
      basename "$active_wo" | sed -nE 's/^(WO-[0-9]+).*/\1/p'
      return 0
    fi
  fi

  # Fall back to inferring from the report path filename
  basename "$REPORT_PATH" | sed -nE 's/.*((WO)-[0-9]+).*/\1/p' | head -n 1
}

if [[ "$REPORT_PATH" != /* ]]; then
  REPORT_PATH="$PROJECT_ROOT/$REPORT_PATH"
fi

if [[ ! -f "$REPORT_PATH" ]]; then
  echo "[$GATE_NAME] FAIL: report not found: $REPORT_PATH" >&2
  exit 2
fi

REL_REPORT="$REPORT_PATH"
if [[ "$REPORT_PATH" == "$PROJECT_ROOT"/* ]]; then
  REL_REPORT="${REPORT_PATH#$PROJECT_ROOT/}"
fi

mkdir -p "$PROJECT_ROOT/.vibeos"

AUDIT_REPORT_TYPE="${AUDIT_REPORT_TYPE:-post-implementation}"
AUDIT_WORK_ORDER_VALUE="$(infer_work_order)"

python3 - "$SESSION_STATE_FILE" "$REL_REPORT" "${AUDIT_VISIBILITY_MODE:-}" "${AUDIT_SNAPSHOT_REF:-}" "$AUDIT_REPORT_TYPE" "$AUDIT_WORK_ORDER_VALUE" <<'PYEOF'
import json
import os
import sys
from datetime import datetime, timezone

session_state_file, report_path, mode_override, snapshot_override, report_type, work_order = sys.argv[1:7]

data = {}
if os.path.exists(session_state_file):
    with open(session_state_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)

data["last_audit_report"] = report_path
data["last_audited_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
if mode_override:
    data["audit_visibility_mode"] = mode_override
if snapshot_override:
    data["audit_snapshot_ref"] = snapshot_override
if report_type:
    data["last_audit_report_type"] = report_type
if work_order:
    data["last_audit_work_order"] = work_order

with open(session_state_file, "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2)
    handle.write("\n")
PYEOF

echo "[$GATE_NAME] PASS: Recorded audit report $REL_REPORT"
exit 0
