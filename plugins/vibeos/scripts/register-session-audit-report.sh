#!/usr/bin/env bash
# VibeOS — Session Audit Report Registrar
# Records the authoritative session-audit report path in session-state.json so
# session-end closure gates can validate the correct artifact.
#
# Usage:
#   bash .vibeos/scripts/register-session-audit-report.sh <report-path>
#
# Environment:
#   PROJECT_ROOT         Project root (default: auto-detect)
#   SESSION_STATE_FILE   Session state file to update
#
# Exit codes:
#   0 = registration succeeded
#   2 = configuration error (missing report path or file not found)
set -euo pipefail

FRAMEWORK_VERSION="2.1.0"
GATE_NAME="register-session-audit-report"

if [[ $# -lt 1 ]]; then
  echo "[$GATE_NAME] FAIL: report path required" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-${CLAUDE_PROJECT_DIR:-$(cd "$SCRIPT_DIR/../.." && pwd)}}"
SESSION_STATE_FILE="${SESSION_STATE_FILE:-$PROJECT_ROOT/.vibeos/session-state.json}"
REPORT_PATH="$1"

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

python3 - "$SESSION_STATE_FILE" "$REL_REPORT" <<'PYEOF'
import json
import os
import sys
from datetime import datetime, timezone

session_state_file, report_path = sys.argv[1:3]

data = {}
if os.path.exists(session_state_file):
    with open(session_state_file, "r", encoding="utf-8") as handle:
        data = json.load(handle)

data["last_session_audit_report"] = report_path
data["last_audited_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

with open(session_state_file, "w", encoding="utf-8") as handle:
    json.dump(data, handle, indent=2)
    handle.write("\n")
PYEOF

echo "[$GATE_NAME] PASS: Recorded session audit report $REL_REPORT"
exit 0
