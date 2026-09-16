#!/usr/bin/env bash
# VibeOS Plugin — State Flush Hook
# Hook type: SessionEnd, PreCompact

FRAMEWORK_VERSION="2.3.0"

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
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
EVENT_NAME=$(echo "$INPUT" | jq -r '.hook_event_name // .hookEventName // .event // "unknown"' 2>/dev/null || echo "unknown")
TRIGGER=$(echo "$INPUT" | jq -r '.trigger // .source // ""' 2>/dev/null || echo "")

EVENT_DIR="$PROJECT_ROOT/.vibeos/hook-events"
mkdir -p "$EVENT_DIR" 2>/dev/null || true

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")

jq -nc \
  --arg timestamp "$TIMESTAMP" \
  --arg event "$EVENT_NAME" \
  --arg trigger "$TRIGGER" \
  '{
    timestamp: $timestamp,
    event: $event,
    trigger: $trigger,
    state: "flushed"
  }' > "$EVENT_DIR/session-flush.json" 2>/dev/null || true

jq -nc \
  --arg timestamp "$TIMESTAMP" \
  --arg event "$EVENT_NAME" \
  --arg trigger "$TRIGGER" \
  '{timestamp: $timestamp, event: $event, trigger: $trigger, state: "flushed"}' >> "$EVENT_DIR/session-flush.jsonl" 2>/dev/null || true

jq -n --arg event "$EVENT_NAME" '{"ok": true, "event": $event, "state": "flushed"}'
