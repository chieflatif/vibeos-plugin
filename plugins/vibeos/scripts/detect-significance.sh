#!/usr/bin/env bash
# VibeOS — Codex Audit Significance Detector
# Determines whether a recent event warrants a complementary Codex audit.
#
# Usage:
#   bash detect-significance.sh [OPTIONS]
#
# Options:
#   --files N          Override: assert N files were changed
#   --lines N          Override: assert N lines were changed
#   --context TEXT     Free-text description of the work (checked for event keywords)
#   --explicit         Force significant=true regardless of other signals
#   --base REF         Git base ref to diff against (default: HEAD~1)
#
# Output (stdout): JSON
#   {"significant": true|false, "reason": "...", "audit_type": "...", "basis": [...],
#    "file_count": N, "line_count": N, "confidence": "high|medium|low"}
#
# Exit codes:
#   0 — completed (check JSON "significant" field for verdict)
#   1 — error running git commands (treated as significant to be safe)
#
# Framework: VibeOS 2.1.0 | Codex Complementary Audit Protocol
# Bash 3.2+ compatible — no associative arrays

set -euo pipefail

FRAMEWORK_VERSION="2.1.0"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ---- Significance thresholds ----
THRESHOLD_FILES=5
THRESHOLD_LINES=300

# ---- Pattern groups for keyword matching ----
WO_CLOSURE_PATTERNS="wo.*(complete|closed|done|finished)|work.order.*(complete|closed|done)|marked.*done|wo closure|completion.commit"
PLAN_PATTERNS="plan.*final|plan.*approved|plan.*handoff|finalized.*plan|approved.*plan|plan.*tranche|tranche.*approved"
SESSION_PATTERNS="session.*closeout|session.*audit|session.*close|close.*session|end.*session|session.*summary"
ARCH_PATTERNS="architecture|migration|schema|contract|auth|security|observability|deployment|persistence|public.*api|api.*public|infrastructure"
GOVERNANCE_PATTERNS="work.?order|planning|governance|audit|phase|development.?plan|wo.?index"
DEPENDENCY_PATTERNS="requirements\.txt|pyproject\.toml|package\.json|package-lock|uv\.lock|Pipfile|Cargo\.toml"

# ---- Parse arguments ----
OVERRIDE_FILES=""
OVERRIDE_LINES=""
CONTEXT_TEXT=""
EXPLICIT=false
BASE_REF="HEAD~1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --files)    OVERRIDE_FILES="$2"; shift 2 ;;
    --lines)    OVERRIDE_LINES="$2"; shift 2 ;;
    --context)  CONTEXT_TEXT="$2"; shift 2 ;;
    --explicit) EXPLICIT=true; shift ;;
    --base)     BASE_REF="$2"; shift 2 ;;
    *) shift ;;
  esac
done

# ---- Short-circuit: explicit override ----
if [[ "$EXPLICIT" == "true" ]]; then
  printf '{"significant":true,"reason":"explicit_override","audit_type":"manual_audit","basis":["explicit_override"],"file_count":0,"line_count":0,"confidence":"high"}\n'
  exit 0
fi

# ---- Collect git metrics ----
FILE_COUNT=0
LINE_COUNT=0
CHANGED_PATHS=""

if [[ -n "$OVERRIDE_FILES" ]]; then
  FILE_COUNT="$OVERRIDE_FILES"
else
  FILE_COUNT=$(git diff --name-only "${BASE_REF}" HEAD 2>/dev/null | wc -l | tr -d ' ') || FILE_COUNT=0
  # Fall back to working-tree diff when no committed diff is found
  if [[ "$FILE_COUNT" -eq 0 ]]; then
    WT=$(git diff --name-only 2>/dev/null | wc -l | tr -d ' ') || WT=0
    ST=$(git diff --name-only --cached 2>/dev/null | wc -l | tr -d ' ') || ST=0
    FILE_COUNT=$((WT + ST))
  fi
fi

if [[ -n "$OVERRIDE_LINES" ]]; then
  LINE_COUNT="$OVERRIDE_LINES"
else
  SHORTSTAT=$(git diff --shortstat "${BASE_REF}" HEAD 2>/dev/null || echo "")
  if [[ -z "$SHORTSTAT" ]]; then
    SS_WT=$(git diff --shortstat 2>/dev/null || echo "")
    SS_ST=$(git diff --shortstat --cached 2>/dev/null || echo "")
    INS=$(printf '%s\n%s' "$SS_WT" "$SS_ST" | grep -o '[0-9]* insertion' | awk '{sum+=$1} END{print sum+0}')
    DEL=$(printf '%s\n%s' "$SS_WT" "$SS_ST" | grep -o '[0-9]* deletion' | awk '{sum+=$1} END{print sum+0}')
  else
    INS=$(printf '%s' "$SHORTSTAT" | grep -o '[0-9]* insertion' | awk '{print $1+0}')
    DEL=$(printf '%s' "$SHORTSTAT" | grep -o '[0-9]* deletion' | awk '{print $1+0}')
  fi
  LINE_COUNT=$((${INS:-0} + ${DEL:-0}))
fi

# Collect changed file paths for pattern matching
CHANGED_PATHS=$(git diff --name-only "${BASE_REF}" HEAD 2>/dev/null || git diff --name-only 2>/dev/null || echo "")
if [[ -z "$CHANGED_PATHS" ]]; then
  CHANGED_PATHS=$(git diff --name-only --cached 2>/dev/null || echo "")
fi

# Also inspect the last 5 commit messages for event signals
RECENT_COMMITS=$(git log --oneline -5 2>/dev/null || echo "")

# Build corpus for keyword matching (lowercase)
SEARCH_CORPUS=$(printf '%s\n%s\n%s' "$CHANGED_PATHS" "$CONTEXT_TEXT" "$RECENT_COMMITS" | tr '[:upper:]' '[:lower:]')

# ---- Evaluate signals ----
BASIS_ITEMS=""
SIGNIFICANT=false
CONFIDENCE="medium"
REASON=""
AUDIT_TYPE="manual_audit"

# Signal: WO closure event
if printf '%s' "$SEARCH_CORPUS" | grep -qiE "$WO_CLOSURE_PATTERNS"; then
  SIGNIFICANT=true
  BASIS_ITEMS="${BASIS_ITEMS}\"wo_closure\","
  AUDIT_TYPE="completion_audit"
  REASON="WO closure detected"
  CONFIDENCE="high"
fi

# Signal: Plan finalization event
if printf '%s' "$SEARCH_CORPUS" | grep -qiE "$PLAN_PATTERNS"; then
  SIGNIFICANT=true
  BASIS_ITEMS="${BASIS_ITEMS}\"plan_finalized\","
  if [[ "$AUDIT_TYPE" == "manual_audit" ]]; then
    AUDIT_TYPE="plan_audit"
    REASON="Plan finalization detected"
  fi
  CONFIDENCE="high"
fi

# Signal: Session closeout event
if printf '%s' "$SEARCH_CORPUS" | grep -qiE "$SESSION_PATTERNS"; then
  SIGNIFICANT=true
  BASIS_ITEMS="${BASIS_ITEMS}\"session_closeout\","
  if [[ "$AUDIT_TYPE" == "manual_audit" ]]; then
    AUDIT_TYPE="session_audit"
    REASON="Session closeout detected"
  fi
  CONFIDENCE="high"
fi

# Signal: File count threshold
if [[ "$FILE_COUNT" -ge "$THRESHOLD_FILES" ]]; then
  SIGNIFICANT=true
  BASIS_ITEMS="${BASIS_ITEMS}\"file_count_threshold\","
  if [[ -z "$REASON" ]]; then
    REASON="${FILE_COUNT} files changed (threshold: ${THRESHOLD_FILES})"
  fi
fi

# Signal: Line count threshold
if [[ "$LINE_COUNT" -ge "$THRESHOLD_LINES" ]]; then
  SIGNIFICANT=true
  BASIS_ITEMS="${BASIS_ITEMS}\"line_count_threshold\","
  if [[ -z "$REASON" ]]; then
    REASON="${LINE_COUNT} lines changed (threshold: ${THRESHOLD_LINES})"
  fi
fi

# Signal: Architecture or cross-cutting patterns
if printf '%s' "$SEARCH_CORPUS" | grep -qiE "$ARCH_PATTERNS"; then
  SIGNIFICANT=true
  BASIS_ITEMS="${BASIS_ITEMS}\"cross_cutting_architecture\","
  CONFIDENCE="high"
  if [[ -z "$REASON" ]]; then
    REASON="Architecture or security-related changes detected"
  fi
fi

# Signal: Governance or planning patterns
if printf '%s' "$SEARCH_CORPUS" | grep -qiE "$GOVERNANCE_PATTERNS"; then
  SIGNIFICANT=true
  BASIS_ITEMS="${BASIS_ITEMS}\"governance_planning\","
  if [[ -z "$REASON" ]]; then
    REASON="Governance or planning artifacts changed"
  fi
fi

# Signal: Dependency file changes
if printf '%s' "$SEARCH_CORPUS" | grep -qiE "$DEPENDENCY_PATTERNS"; then
  SIGNIFICANT=true
  BASIS_ITEMS="${BASIS_ITEMS}\"dependency_change\","
  if [[ -z "$REASON" ]]; then
    REASON="Dependency manifest changed"
  fi
fi

# Signal: Multiple new untracked directories (suggests new modules)
UNTRACKED_DIRS=$(git status --short 2>/dev/null | grep '^\?\?' | grep '/$' | wc -l | tr -d ' ') || UNTRACKED_DIRS=0
if [[ "$UNTRACKED_DIRS" -ge 2 ]]; then
  SIGNIFICANT=true
  BASIS_ITEMS="${BASIS_ITEMS}\"new_modules_introduced\","
  CONFIDENCE="medium"
  if [[ -z "$REASON" ]]; then
    REASON="${UNTRACKED_DIRS} new directories introduced"
  fi
fi

# Default reason if nothing set
if [[ -z "$REASON" ]]; then
  REASON="no significant signals detected"
fi

# Trim trailing comma
BASIS_ITEMS="${BASIS_ITEMS%,}"

# Build JSON output (bash 3.2 compatible string construction)
if [[ "$SIGNIFICANT" == "true" ]]; then
  SIG_VAL="true"
else
  SIG_VAL="false"
fi

# Escape double quotes in reason for JSON safety
REASON_ESC=$(printf '%s' "$REASON" | sed 's/"/\\"/g')

printf '{"significant":%s,"reason":"%s","audit_type":"%s","basis":[%s],"file_count":%s,"line_count":%s,"confidence":"%s"}\n' \
  "$SIG_VAL" \
  "$REASON_ESC" \
  "$AUDIT_TYPE" \
  "$BASIS_ITEMS" \
  "$FILE_COUNT" \
  "$LINE_COUNT" \
  "$CONFIDENCE"

exit 0
