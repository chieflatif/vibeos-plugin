#!/usr/bin/env bash
# VibeOS Plugin — Validate Agent Return Hook
# Hook type: SubagentStop

FRAMEWORK_VERSION="2.3.1"

# --- VibeOS project-scope guard (auto-inserted) ------------------------------
# Stay inert outside VibeOS-managed projects. The plugin is user-scoped, so
# without this every hook would fire in every project on the machine.
# Override with VIBEOS_FORCE_HOOKS=1. Definition: is-vibeos-project.sh
__VIBEOS_GUARD_LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)/is-vibeos-project.sh"
if [ -f "$__VIBEOS_GUARD_LIB" ]; then
  # shellcheck source=/dev/null
  . "$__VIBEOS_GUARD_LIB"
  is_vibeos_project || exit 0
fi
# -----------------------------------------------------------------------------


INPUT=$(cat)
AGENT_TYPE=$(echo "$INPUT" | jq -r '.agent_type // .subagent_type // .agent_name // ""' 2>/dev/null || echo "")
RESULT=$(echo "$INPUT" | jq -c '.result // .response // .subagent_result // {}' 2>/dev/null || echo "{}")

if ! echo "$RESULT" | jq empty >/dev/null 2>&1; then
  RESULT=$(jq -n --arg text "$RESULT" '{text: $text}')
fi

MSG_TYPE=$(echo "$RESULT" | jq -r '.type // ""' 2>/dev/null || echo "")
DECISION=$(echo "$RESULT" | jq -r '.decision // .status // ""' 2>/dev/null || echo "")
CRITICAL_COUNT=$(echo "$RESULT" | jq '[.findings[]? | select((.severity // "" | ascii_downcase) == "critical")] | length' 2>/dev/null || echo "0")
HIGH_COUNT=$(echo "$RESULT" | jq '[.findings[]? | select((.severity // "" | ascii_downcase) == "high")] | length' 2>/dev/null || echo "0")
FINDING_COUNT=$(echo "$RESULT" | jq '[.findings[]?] | length' 2>/dev/null || echo "0")

is_audit=false
if [ "$MSG_TYPE" = "audit_result" ] || echo "$AGENT_TYPE" | grep -qiE '(audit|review|validator|evidence|correctness|security|test)' 2>/dev/null; then
  is_audit=true
fi

if [ "$is_audit" = false ]; then
  echo '{"decision": "allow"}'
  exit 0
fi

if echo "$DECISION" | grep -qiE '^(FAIL|failed|block)$' 2>/dev/null || [ "$CRITICAL_COUNT" -gt 0 ] || [ "$HIGH_COUNT" -gt 0 ]; then
  REASON="Audit return blocked: decision=$DECISION, findings=$FINDING_COUNT, critical=$CRITICAL_COUNT, high=$HIGH_COUNT. Address blocking findings before continuing."
  jq -n --arg reason "$REASON" '{"decision": "block", "reason": $reason}'
  exit 2
fi

echo '{"decision": "allow"}'
