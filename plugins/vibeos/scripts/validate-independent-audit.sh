#!/usr/bin/env bash
# VibeOS — Independent Audit Validation Gate
# Fails closed when an active WO reaches closeout without a dedicated
# post-implementation audit report for that same work order.
#
# Usage:
#   bash .vibeos/scripts/validate-independent-audit.sh [work-order-file] [audit-report]
#
# Environment:
#   PROJECT_ROOT         Project root (default: auto-detect)
#   WO_FILE              Explicit work-order file
#   WO_NUMBER            Work-order number (e.g. WO-058)
#   SESSION_STATE_FILE   Session-state file to inspect for active_wo
#   LAST_AUDIT_REPORT    Explicit audit report path
#
# Exit codes:
#   0 = pass or skip
#   1 = validation failed
#   2 = configuration error
set -euo pipefail

FRAMEWORK_VERSION="2.4.0"
GATE_NAME="validate-independent-audit"

usage() {
  cat <<'EOF'
Usage:
  bash .vibeos/scripts/validate-independent-audit.sh [work-order-file] [audit-report]

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
  - Active WOs must have a dedicated audit report under .vibeos/audit-reports/
  - Session audits cannot satisfy post-implementation audit closure
  - Audit report metadata must target the active WO
  - Audit reports must look like independent audit output, not a builder summary
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
      [[ -z "$candidate" ]] && candidate="$explicit"
    fi
  elif [[ -n "${WO_FILE:-}" ]]; then
    candidate="$WO_FILE"
  elif [[ -n "${WO_NUMBER:-}" ]]; then
    candidate="$(find "$PROJECT_ROOT/docs/planning" -maxdepth 1 -type f -name "${WO_NUMBER}*.md" | head -n 1 || true)"
  elif [[ -f "$SESSION_STATE_FILE" ]] && command -v jq >/dev/null 2>&1; then
    candidate="$(jq -r '.active_wo // .started_from_wo // empty' "$SESSION_STATE_FILE" 2>/dev/null || echo "")"
  fi

  [[ -z "$candidate" ]] && { echo ""; return 0; }
  [[ "$candidate" != /* ]] && candidate="$PROJECT_ROOT/$candidate"
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

  [[ -z "$candidate" ]] && { echo ""; return 0; }
  [[ "$candidate" != /* ]] && candidate="$PROJECT_ROOT/$candidate"
  echo "$candidate"
}

extract_wo_number() {
  # Match WO-NNN patterns (e.g. WO-058, WO-123)
  basename "$1" | sed -nE 's/^(WO-[0-9]+).*/\1/p'
}

WO_TARGET="$(resolve_wo_target "${1:-}")"
if [[ -z "$WO_TARGET" ]]; then
  echo "[$GATE_NAME] SKIP: No active work-order target resolved"
  exit 0
fi

if [[ ! -f "$WO_TARGET" ]]; then
  echo "[$GATE_NAME] FAIL: Work-order target not found: $WO_TARGET"
  exit 2
fi

ACTIVE_WO="$(extract_wo_number "$WO_TARGET")"
if [[ -z "$ACTIVE_WO" ]]; then
  echo "[$GATE_NAME] SKIP: Target does not match WO naming convention: $(basename "$WO_TARGET")"
  exit 0
fi

AUDIT_REPORT="$(resolve_audit_target "${2:-}")"
if [[ -z "$AUDIT_REPORT" ]]; then
  echo "[$GATE_NAME] FAIL: No independent audit report registered for $ACTIVE_WO"
  echo "[$GATE_NAME] Action: dispatch the independent audit agents and run scripts/register-audit-report.sh"
  exit 1
fi

if [[ ! -f "$AUDIT_REPORT" ]]; then
  echo "[$GATE_NAME] FAIL: Audit report not found: $AUDIT_REPORT"
  exit 2
fi

REL_AUDIT_REPORT="$AUDIT_REPORT"
if [[ "$AUDIT_REPORT" == "$PROJECT_ROOT"/* ]]; then
  REL_AUDIT_REPORT="${AUDIT_REPORT#$PROJECT_ROOT/}"
fi

if [[ "$REL_AUDIT_REPORT" != .vibeos/audit-reports/* ]]; then
  echo "[$GATE_NAME] FAIL: Active WO audits must be registered under .vibeos/audit-reports/"
  echo "[$GATE_NAME] Current report: $REL_AUDIT_REPORT"
  exit 1
fi

SESSION_AUDIT_KIND=""
SESSION_AUDIT_WO=""
COMPANION_RECEIPT=""
if [[ -f "$SESSION_STATE_FILE" ]] && command -v jq >/dev/null 2>&1; then
  SESSION_AUDIT_KIND="$(jq -r '.last_audit_report_type // empty' "$SESSION_STATE_FILE" 2>/dev/null || echo "")"
  SESSION_AUDIT_WO="$(jq -r '.last_audit_work_order // empty' "$SESSION_STATE_FILE" 2>/dev/null || echo "")"
  COMPANION_RECEIPT="$(jq -r '.last_claude_companion_receipt // empty' "$SESSION_STATE_FILE" 2>/dev/null || echo "")"
fi

if [[ -n "$SESSION_AUDIT_KIND" && "$SESSION_AUDIT_KIND" != "post-implementation" ]]; then
  echo "[$GATE_NAME] FAIL: last_audit_report_type must be post-implementation, found '$SESSION_AUDIT_KIND'"
  exit 1
fi

if [[ -n "$SESSION_AUDIT_WO" && "$SESSION_AUDIT_WO" != "$ACTIVE_WO" ]]; then
  echo "[$GATE_NAME] FAIL: Registered audit targets '$SESSION_AUDIT_WO' but active WO is '$ACTIVE_WO'"
  exit 1
fi

COMPANION_REQUIRED="false"
COMPANION_GATE_CONFIGURED="false"
COMPANION_GATE_MANIFEST="$PROJECT_ROOT/.claude/quality-gate-manifest.json"
if [[ -f "$COMPANION_GATE_MANIFEST" ]]; then
  if ! COMPANION_GATE_CONFIGURED="$(python3 - "$COMPANION_GATE_MANIFEST" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        manifest = json.load(handle)
    gates = manifest.get("gates", [])
    configured = any(
        isinstance(gate, dict)
        and gate.get("name") == "claude-companion-audit-closure"
        and gate.get("enabled", True) is not False
        for gate in gates
    )
except (OSError, TypeError, ValueError):
    raise SystemExit(2)
print("true" if configured else "false")
PY
  )"; then
    echo "[$GATE_NAME] FAIL: quality-gate-manifest.json is invalid"
    exit 2
  fi
fi

if [[ "$COMPANION_GATE_CONFIGURED" == "true" ]]; then
  if [[ ! -f "$PROJECT_ROOT/.vibeos/project-profile.json" ]]; then
    echo "[$GATE_NAME] FAIL: Claude companion gate is configured but project-profile.json is missing"
    exit 1
  fi
fi

COMPANION_PROFILE="$PROJECT_ROOT/.vibeos/project-profile.json"
if [[ -f "$COMPANION_PROFILE" ]]; then
  if ! MODULE_STATE="$(python3 - "$COMPANION_PROFILE" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], encoding="utf-8") as handle:
        profile = json.load(handle)
    modules = profile.get("active_modules", [])
    if not isinstance(modules, list) or any(
        not isinstance(module, str) for module in modules
    ):
        raise TypeError("active_modules must be a list of strings")
except (OSError, TypeError, ValueError):
    raise SystemExit(2)

if "claude-companion-audit" not in modules:
    print("inactive")
elif profile.get("phase_audit_runtime") != "claude":
    print("runtime-mismatch")
else:
    print("active")
PY
  )"; then
    echo "[$GATE_NAME] FAIL: project-profile.json is invalid"
    exit 2
  fi
  if [[ "$MODULE_STATE" == "runtime-mismatch" ]]; then
    echo "[$GATE_NAME] FAIL: Active Claude companion audit requires phase_audit_runtime=claude"
    exit 1
  fi
  [[ "$MODULE_STATE" == "active" ]] && COMPANION_REQUIRED="true"
fi

if [[ "$COMPANION_GATE_CONFIGURED" == "true" ]]; then
  if [[ "$COMPANION_REQUIRED" != "true" ]]; then
    echo "[$GATE_NAME] FAIL: Claude companion gate requires an active module and phase_audit_runtime=claude"
    exit 1
  fi
fi

if [[ "$COMPANION_REQUIRED" == "true" ]]; then
  if [[ -z "$COMPANION_RECEIPT" ]]; then
    echo "[$GATE_NAME] FAIL: Claude companion audit is enabled but no receipt is registered"
    exit 1
  fi
  if [[ "$COMPANION_RECEIPT" != /* ]]; then
    COMPANION_RECEIPT="$PROJECT_ROOT/$COMPANION_RECEIPT"
  fi
  COMPANION_VALIDATOR="$PROJECT_ROOT/.vibeos/scripts/claude-companion-audit.py"
  if [[ ! -f "$COMPANION_VALIDATOR" ]]; then
    echo "[$GATE_NAME] FAIL: Claude companion validator is missing: $COMPANION_VALIDATOR"
    exit 2
  fi
  if ! python3 "$COMPANION_VALIDATOR" validate \
    --project-dir "$PROJECT_ROOT" \
    --receipt "${COMPANION_RECEIPT#$PROJECT_ROOT/}" \
    --work-order "$ACTIVE_WO"; then
    echo "[$GATE_NAME] FAIL: Claude companion receipt is absent, stale, unresolved, or has unproved provenance"
    exit 1
  fi
  if ! python3 - "$PROJECT_ROOT" "$COMPANION_RECEIPT" "$AUDIT_REPORT" <<'PY'
import json, pathlib, sys
root, receipt_path, requested = map(pathlib.Path, sys.argv[1:])
root = root.resolve()
try:
    report = json.loads(receipt_path.read_text())["artifacts"]["report_path"]
    bound = (root / report).resolve()
    bound.relative_to(root)
except (KeyError, OSError, TypeError, ValueError):
    raise SystemExit(1)
raise SystemExit(0 if bound == requested.resolve() else 1)
PY
  then
    echo "[$GATE_NAME] FAIL: Supplied audit report is not the report bound by the registered Claude companion receipt"
    exit 1
  fi
fi

AUDIT_CONTENT="$(cat "$AUDIT_REPORT")"
if ! printf '%s\n' "$AUDIT_CONTENT" | grep -qiE '(^|\*\*)auditors dispatched(:|\*\*)|(^|\*\*)auditors(:|\*\*)|## Auditor Summary|### Auditor Summary'; then
  echo "[$GATE_NAME] FAIL: Audit report does not look like an independent auditor report"
  echo "[$GATE_NAME] Required: auditor list or auditor summary section"
  exit 1
fi

if ! printf '%s\n' "$AUDIT_CONTENT" | grep -qiE 'security|architecture|correctness|test quality|test-auditor|evidence|product drift|red team|contract'; then
  echo "[$GATE_NAME] FAIL: Audit report does not reference any independent auditor identities"
  exit 1
fi

if [[ "$SESSION_AUDIT_WO" != "$ACTIVE_WO" ]] && ! printf '%s\n' "$AUDIT_CONTENT" | grep -q "$ACTIVE_WO"; then
  echo "[$GATE_NAME] FAIL: Audit report does not reference active work order $ACTIVE_WO"
  exit 1
fi

echo "[$GATE_NAME] PASS: Independent audit is registered for $ACTIVE_WO"
echo "[$GATE_NAME] report=$REL_AUDIT_REPORT"
exit 0
