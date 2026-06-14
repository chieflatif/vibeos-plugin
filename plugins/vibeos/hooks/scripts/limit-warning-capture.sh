#!/usr/bin/env bash
# VibeOS Plugin — Provider/Session Limit Warning Capture Hook
# Hook type: Notification
# Side-effect only: records/schedules local resume artifacts when Notification text carries a limit signal.

FRAMEWORK_VERSION="2.2.0"

INPUT=$(cat)
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEDULER=""

if [ -f "$PROJECT_ROOT/.vibeos/scripts/limit-aware-scheduler.py" ]; then
  SCHEDULER="$PROJECT_ROOT/.vibeos/scripts/limit-aware-scheduler.py"
elif [ -n "${CLAUDE_PLUGIN_ROOT:-}" ] && [ -f "$CLAUDE_PLUGIN_ROOT/scripts/limit-aware-scheduler.py" ]; then
  SCHEDULER="$CLAUDE_PLUGIN_ROOT/scripts/limit-aware-scheduler.py"
elif [ -f "$SCRIPT_DIR/../../scripts/limit-aware-scheduler.py" ]; then
  SCHEDULER="$SCRIPT_DIR/../../scripts/limit-aware-scheduler.py"
fi

if [ -z "$SCHEDULER" ]; then
  jq -n '{"ok": true, "captured": false, "reason": "limit-aware-scheduler.py not found"}'
  exit 0
fi

RESULT=$(printf '%s' "$INPUT" | python3 "$SCHEDULER" --project-dir "$PROJECT_ROOT" --source notification --input - --json 2>/dev/null)
STATUS=$?

if [ "$STATUS" -ne 0 ] || [ -z "$RESULT" ]; then
  jq -n --arg status "$STATUS" '{"ok": true, "captured": false, "reason": "limit-aware scheduler failed", "exit_code": $status}'
  exit 0
fi

SUMMARY_STATUS=$(printf '%s' "$RESULT" | jq -r '.summary.status // "unknown"' 2>/dev/null || echo "unknown")
SCHEDULED=$(printf '%s' "$RESULT" | jq -r '.summary.scheduled // false' 2>/dev/null || echo "false")

jq -n \
  --arg status "$SUMMARY_STATUS" \
  --argjson captured "$SCHEDULED" \
  --argjson report "$RESULT" \
  '{
    ok: true,
    captured: $captured,
    summary: {
      status: $status,
      scheduled: $captured
    },
    report: $report
  }'
