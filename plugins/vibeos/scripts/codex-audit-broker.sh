#!/usr/bin/env bash
# VibeOS — Codex Audit Broker
# Orchestrates complementary audits: runs the significance check, dispatches to the
# Codex adapter (or both adapters for dual-audit), and returns structured findings.
#
# Usage:
#   bash codex-audit-broker.sh [OPTIONS]
#
# Options:
#   --type    plan_audit|completion_audit|session_audit|manual_audit  (default: manual_audit)
#   --auditor codex|both                                               (default: codex)
#   --executor claude|codex                                            (default: claude)
#   --wo FILE          work order file path (relative to project root)
#   --context TEXT     additional free-text context for the audit
#   --session-log FILE build log or session transcript
#   --wait             run synchronously (foreground)   [default]
#   --background       run asynchronously (print status and exit)
#   --explicit         bypass significance check
#
# Exit codes:
#   0 — audit dispatched or completed successfully
#   1 — invocation error (Codex plugin not found or adapter failure)
#   2 — significance check failed (not a significant enough event)
#
# Framework: VibeOS 2.2.0 | Codex Complementary Audit Protocol

set -euo pipefail

FRAMEWORK_VERSION="2.2.0"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# ---- Defaults ----
AUDIT_TYPE="manual_audit"
AUDITOR="codex"
EXECUTOR="claude"
WO_FILE=""
CONTEXT_TEXT=""
SESSION_LOG_FILE=""
FOREGROUND=true
EXPLICIT=false

# ---- Parse arguments ----
while [[ $# -gt 0 ]]; do
  case "$1" in
    --type)        AUDIT_TYPE="$2"; shift 2 ;;
    --auditor)     AUDITOR="$2"; shift 2 ;;
    --executor)    EXECUTOR="$2"; shift 2 ;;
    --wo)          WO_FILE="$2"; shift 2 ;;
    --context)     CONTEXT_TEXT="$2"; shift 2 ;;
    --session-log) SESSION_LOG_FILE="$2"; shift 2 ;;
    --wait)        FOREGROUND=true; shift ;;
    --background)  FOREGROUND=false; shift ;;
    --explicit)    EXPLICIT=true; shift ;;
    *) shift ;;
  esac
done

# ---- Validate audit type ----
case "$AUDIT_TYPE" in
  plan_audit|completion_audit|session_audit|manual_audit) ;;
  *)
    echo "[codex-audit-broker] FAIL: unknown audit type '${AUDIT_TYPE}'" >&2
    echo "[codex-audit-broker] Valid types: plan_audit completion_audit session_audit manual_audit" >&2
    exit 1
    ;;
esac

# ---- Significance check (skip if --explicit or if manual_audit) ----
if [[ "$EXPLICIT" != "true" ]] && [[ "$AUDIT_TYPE" != "manual_audit" ]]; then
  echo "[codex-audit-broker] Running significance check..." >&2

  SIG_ARGS=""
  [[ -n "$CONTEXT_TEXT" ]] && SIG_ARGS="--context $(printf '%q' "$CONTEXT_TEXT")"

  SIG_OUTPUT=$(bash "${SCRIPT_DIR}/detect-significance.sh" ${SIG_ARGS} 2>/dev/null) || SIG_OUTPUT=""

  if [[ -z "$SIG_OUTPUT" ]]; then
    echo "[codex-audit-broker] WARN: significance check returned empty output — treating as significant" >&2
  else
    SIG_VALUE=$(printf '%s' "$SIG_OUTPUT" | grep -o '"significant":[a-z]*' | cut -d: -f2 || echo "true")
    if [[ "$SIG_VALUE" == "false" ]]; then
      SIG_REASON=$(printf '%s' "$SIG_OUTPUT" | grep -o '"reason":"[^"]*"' | cut -d'"' -f4 || echo "below threshold")
      echo "[codex-audit-broker] SKIP: not significant — ${SIG_REASON}" >&2
      echo "[codex-audit-broker] Run with --explicit to bypass the significance check." >&2
      exit 2
    fi
    echo "[codex-audit-broker] Significance check passed." >&2
  fi
fi

# ---- Prepare output directory ----
RESULTS_DIR="${PROJECT_ROOT}/.vibeos/audit/results"
mkdir -p "$RESULTS_DIR"

TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
RESULT_FILE="${RESULTS_DIR}/${AUDIT_TYPE}-${EXECUTOR}-${TIMESTAMP}.md"

# ---- Dispatch to Codex adapter ----
ADAPTER="${SCRIPT_DIR}/codex-audit-adapter.sh"

if [[ ! -f "$ADAPTER" ]]; then
  echo "[codex-audit-broker] FAIL: codex-audit-adapter.sh not found at ${ADAPTER}" >&2
  exit 1
fi

build_adapter_args() {
  local args="--type ${AUDIT_TYPE} --executor-model ${EXECUTOR} --out ${RESULT_FILE}"
  [[ -n "$WO_FILE" ]]          && args="${args} --wo $(printf '%q' "$WO_FILE")"
  [[ -n "$CONTEXT_TEXT" ]]     && args="${args} --context $(printf '%q' "$CONTEXT_TEXT")"
  [[ -n "$SESSION_LOG_FILE" ]] && args="${args} --session-log $(printf '%q' "$SESSION_LOG_FILE")"
  [[ "$FOREGROUND" == "true" ]] && args="${args} --wait" || args="${args} --background"
  printf '%s' "$args"
}

echo "[codex-audit-broker] Dispatching ${AUDIT_TYPE} — auditor=${AUDITOR}, executor=${EXECUTOR}..." >&2

if [[ "$AUDITOR" == "both" ]]; then
  # Dual-audit: Codex audits, then Claude audits via the built-in audit skill.
  # The broker dispatches the Codex adapter here; Claude's own audit is handled
  # by the skill layer (the caller is responsible for running /vibeos:audit separately).
  echo "[codex-audit-broker] Dual-audit mode: dispatching Codex adapter..." >&2
  ADAPTER_ARGS=$(build_adapter_args)
  # shellcheck disable=SC2086
  bash "$ADAPTER" $ADAPTER_ARGS
  ADAPTER_EXIT=$?
  if [[ "$ADAPTER_EXIT" -ne 0 ]]; then
    echo "[codex-audit-broker] FAIL: Codex adapter exited with code ${ADAPTER_EXIT}" >&2
    exit "$ADAPTER_EXIT"
  fi
  echo "[codex-audit-broker] Codex adapter complete. For dual-audit: also run /vibeos:audit to get Claude's perspective." >&2
else
  # Single auditor: Codex only
  ADAPTER_ARGS=$(build_adapter_args)
  # shellcheck disable=SC2086
  bash "$ADAPTER" $ADAPTER_ARGS
  ADAPTER_EXIT=$?
  if [[ "$ADAPTER_EXIT" -ne 0 ]]; then
    echo "[codex-audit-broker] FAIL: Codex adapter exited with code ${ADAPTER_EXIT}" >&2
    exit "$ADAPTER_EXIT"
  fi
fi

if [[ "$FOREGROUND" == "true" ]] && [[ -f "$RESULT_FILE" ]]; then
  echo "[codex-audit-broker] Result written to: ${RESULT_FILE}" >&2
fi

exit 0
