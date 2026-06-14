#!/usr/bin/env bash
# VibeOS Plugin — Gate Result Capture Hook
# Hook type: PostToolUse (matcher: Bash)
# Captures gate/test Bash command outcomes after tool execution.

FRAMEWORK_VERSION="2.2.0"

INPUT=$(cat)
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // .tool_input.cmd // ""' 2>/dev/null || echo "")
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_response.exit_code // .tool_response.exitCode // .exit_code // empty' 2>/dev/null || echo "")

case "$COMMAND" in
  *gate-runner.sh*|*validate-*|*pytest*|*npm\ test*|*pnpm\ test*)
    ;;
  *)
    echo '{"ok": true, "captured": false}'
    exit 0
    ;;
esac

EVENT_DIR="$PROJECT_ROOT/.vibeos/hook-events"
mkdir -p "$EVENT_DIR" 2>/dev/null || true

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
STATUS="unknown"
if [ "$EXIT_CODE" = "0" ]; then
  STATUS="pass"
elif [ -n "$EXIT_CODE" ]; then
  STATUS="fail"
fi

jq -nc \
  --arg timestamp "$TIMESTAMP" \
  --arg event "PostToolUse" \
  --arg command "$COMMAND" \
  --arg exit_code "$EXIT_CODE" \
  --arg status "$STATUS" \
  '{
    timestamp: $timestamp,
    event: $event,
    command: $command,
    exit_code: $exit_code,
    status: $status
  }' >> "$EVENT_DIR/gate-results.jsonl" 2>/dev/null || true

jq -n --arg status "$STATUS" '{"ok": true, "captured": true, "status": $status}'
