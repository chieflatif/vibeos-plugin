#!/usr/bin/env bash
# VibeOS Plugin — Agent Team Governance Hook
# Hook type: TaskCreated, TaskCompleted, TeammateIdle
# Dormant by default. Enable with .vibeos/config.json:
#   {"features": {"agent_team_governance": true}}

FRAMEWORK_VERSION="2.4.0"

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
EVENT_NAME=$(echo "$INPUT" | jq -r '.hook_event_name // .hookEventName // .event // "unknown"' 2>/dev/null || echo "unknown")
CWD_VALUE=$(echo "$INPUT" | jq -r '.cwd // ""' 2>/dev/null || echo "")
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$CWD_VALUE}"
if [ -z "$PROJECT_ROOT" ]; then
  PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
fi

CONFIG_FILE="$PROJECT_ROOT/.vibeos/config.json"
ENABLED="false"
if [ -f "$CONFIG_FILE" ]; then
  ENABLED=$(jq -r '
    .features.agent_team_governance //
    .vibeos.agent_team_governance //
    .agent_team_governance //
    false
  ' "$CONFIG_FILE" 2>/dev/null || echo "false")
fi

allow() {
  jq -n --arg event "$EVENT_NAME" --arg enabled "$ENABLED" \
    '{"decision": "allow", "event": $event, "enabled": ($enabled == "true")}'
  exit 0
}

block() {
  local MESSAGE="$1"
  echo "[team-governance] BLOCKED: $MESSAGE" >&2
  exit 2
}

if [ "$ENABLED" != "true" ]; then
  allow
fi

TASK_SUBJECT=$(echo "$INPUT" | jq -r '.task_subject // ""' 2>/dev/null || echo "")
TASK_DESCRIPTION=$(echo "$INPUT" | jq -r '.task_description // ""' 2>/dev/null || echo "")
TEAM_NAME=$(echo "$INPUT" | jq -r '.team_name // ""' 2>/dev/null || echo "")
TEAMMATE_NAME=$(echo "$INPUT" | jq -r '.teammate_name // ""' 2>/dev/null || echo "")

EVENT_DIR="$PROJECT_ROOT/.vibeos/team-governance"
mkdir -p "$EVENT_DIR" 2>/dev/null || true
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")

jq -nc \
  --arg timestamp "$TIMESTAMP" \
  --arg event "$EVENT_NAME" \
  --arg team "$TEAM_NAME" \
  --arg teammate "$TEAMMATE_NAME" \
  --arg subject "$TASK_SUBJECT" \
  '{
    timestamp: $timestamp,
    event: $event,
    team: $team,
    teammate: $teammate,
    task_subject: $subject
  }' >> "$EVENT_DIR/events.jsonl" 2>/dev/null || true

case "$EVENT_NAME" in
  TaskCreated)
    if ! printf '%s\n%s\n' "$TASK_SUBJECT" "$TASK_DESCRIPTION" | grep -qE 'WO-[0-9]{3}[A-Za-z]?'; then
      block "Team tasks must cite the governing WO in the subject or description."
    fi
    if [ -z "$TASK_DESCRIPTION" ]; then
      block "Team tasks must include a task_description with scope, evidence, and handoff expectations."
    fi
    ;;
  TaskCompleted)
    if ! printf '%s\n%s\n' "$TASK_SUBJECT" "$TASK_DESCRIPTION" | grep -qE 'WO-[0-9]{3}[A-Za-z]?'; then
      block "Completed team tasks must cite the governing WO before closure."
    fi
    ;;
  TeammateIdle)
    ;;
esac

allow
