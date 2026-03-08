#!/usr/bin/env bash
set -euo pipefail

# token-tracker.sh — Record and aggregate token usage for agent dispatches
# Appends usage records to .vibeos/token-usage.json and calculates audit overhead.
# Exit 0 with JSON summary on stdout; exit 1 on error.

FRAMEWORK_VERSION="1.0.0"

usage() {
  echo "Usage:"
  echo "  $0 record --agent <name> --wo <WO-NNN> --input-tokens <N> --output-tokens <N>"
  echo "  $0 summary [--wo <WO-NNN>] [--phase <N>]"
  echo "  $0 overhead"
  echo ""
  echo "Commands:"
  echo "  record    Record a single agent dispatch's token usage"
  echo "  summary   Show aggregated token usage (optionally filtered by WO or phase)"
  echo "  overhead  Calculate audit overhead percentage and alert if > 30%"
  exit 1
}

VIBEOS_DIR="${CLAUDE_PROJECT_DIR:-.}/.vibeos"
TOKEN_FILE="${VIBEOS_DIR}/token-usage.json"

ensure_token_file() {
  mkdir -p "$VIBEOS_DIR"
  if [ ! -f "$TOKEN_FILE" ]; then
    echo '{"records": []}' > "$TOKEN_FILE"
  fi
}

COMMAND="${1:-}"
shift || true

case "$COMMAND" in
  record)
    AGENT=""
    WO=""
    INPUT_TOKENS=0
    OUTPUT_TOKENS=0

    while [ $# -gt 0 ]; do
      case "$1" in
        --agent) AGENT="$2"; shift 2 ;;
        --wo) WO="$2"; shift 2 ;;
        --input-tokens) INPUT_TOKENS="$2"; shift 2 ;;
        --output-tokens) OUTPUT_TOKENS="$2"; shift 2 ;;
        *) echo "[token-tracker] ERROR: Unknown argument: $1" >&2; exit 1 ;;
      esac
    done

    if [ -z "$AGENT" ] || [ -z "$WO" ]; then
      echo "[token-tracker] ERROR: --agent and --wo are required for record" >&2
      exit 1
    fi

    ensure_token_file

    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    TOTAL=$((INPUT_TOKENS + OUTPUT_TOKENS))

    # Determine if this is an audit agent
    IS_AUDIT="false"
    case "$AGENT" in
      security-auditor|architecture-auditor|correctness-auditor|test-auditor|evidence-auditor)
        IS_AUDIT="true"
        ;;
    esac

    # Create new record
    NEW_RECORD="{\"timestamp\": \"$TIMESTAMP\", \"agent\": \"$AGENT\", \"wo\": \"$WO\", \"input_tokens\": $INPUT_TOKENS, \"output_tokens\": $OUTPUT_TOKENS, \"total_tokens\": $TOTAL, \"is_audit\": $IS_AUDIT}"

    # Append to records array using jq if available, otherwise use simple approach
    if command -v jq >/dev/null 2>&1; then
      UPDATED=$(jq --argjson record "$NEW_RECORD" '.records += [$record]' "$TOKEN_FILE")
      echo "$UPDATED" > "$TOKEN_FILE"
    else
      # Fallback: read file, insert before closing bracket
      # This is fragile but works for simple cases without jq
      sed -i.bak 's/\]}/,'"$(echo "$NEW_RECORD" | sed 's/"/\\"/g')"']}/' "$TOKEN_FILE" 2>/dev/null || true
      rm -f "${TOKEN_FILE}.bak"
    fi

    echo "{\"status\": \"recorded\", \"agent\": \"$AGENT\", \"wo\": \"$WO\", \"total_tokens\": $TOTAL}"
    ;;

  summary)
    WO_FILTER=""
    PHASE_FILTER=""

    while [ $# -gt 0 ]; do
      case "$1" in
        --wo) WO_FILTER="$2"; shift 2 ;;
        --phase) PHASE_FILTER="$2"; shift 2 ;;
        *) echo "[token-tracker] ERROR: Unknown argument: $1" >&2; exit 1 ;;
      esac
    done

    ensure_token_file

    if ! command -v jq >/dev/null 2>&1; then
      echo "[token-tracker] ERROR: jq is required for summary command" >&2
      exit 1
    fi

    if [ -n "$WO_FILTER" ]; then
      jq --arg wo "$WO_FILTER" '
        .records | map(select(.wo == $wo)) |
        {
          wo: $wo,
          total_input: (map(.input_tokens) | add // 0),
          total_output: (map(.output_tokens) | add // 0),
          total_tokens: (map(.total_tokens) | add // 0),
          dispatch_count: length,
          by_agent: (group_by(.agent) | map({
            agent: .[0].agent,
            total_tokens: (map(.total_tokens) | add // 0),
            dispatches: length
          }))
        }
      ' "$TOKEN_FILE"
    elif [ -n "$PHASE_FILTER" ]; then
      # Phase filtering requires WO numbering convention (WO-NNN maps to phase)
      echo "[token-tracker] WARN: Phase filtering requires WO-to-phase mapping; showing all records" >&2
      jq '
        {
          total_input: (.records | map(.input_tokens) | add // 0),
          total_output: (.records | map(.output_tokens) | add // 0),
          total_tokens: (.records | map(.total_tokens) | add // 0),
          dispatch_count: (.records | length),
          by_wo: (.records | group_by(.wo) | map({
            wo: .[0].wo,
            total_tokens: (map(.total_tokens) | add // 0),
            dispatches: length
          }))
        }
      ' "$TOKEN_FILE"
    else
      jq '
        {
          total_input: (.records | map(.input_tokens) | add // 0),
          total_output: (.records | map(.output_tokens) | add // 0),
          total_tokens: (.records | map(.total_tokens) | add // 0),
          dispatch_count: (.records | length),
          by_wo: (.records | group_by(.wo) | map({
            wo: .[0].wo,
            total_tokens: (map(.total_tokens) | add // 0),
            dispatches: length
          }))
        }
      ' "$TOKEN_FILE"
    fi
    ;;

  overhead)
    ensure_token_file

    if ! command -v jq >/dev/null 2>&1; then
      echo "[token-tracker] ERROR: jq is required for overhead command" >&2
      exit 1
    fi

    RESULT=$(jq '
      {
        total_tokens: (.records | map(.total_tokens) | add // 0),
        audit_tokens: ([.records[] | select(.is_audit == true) | .total_tokens] | add // 0),
        non_audit_tokens: ([.records[] | select(.is_audit == false) | .total_tokens] | add // 0)
      } |
      . + {
        audit_overhead_pct: (if .total_tokens > 0 then ((.audit_tokens / .total_tokens) * 100 | . * 100 | round / 100) else 0 end),
        alert: (if .total_tokens > 0 then ((.audit_tokens / .total_tokens) * 100 > 30) else false end)
      }
    ' "$TOKEN_FILE")

    echo "$RESULT"

    # Check alert threshold
    ALERT=$(echo "$RESULT" | jq -r '.alert')
    if [ "$ALERT" = "true" ]; then
      PCT=$(echo "$RESULT" | jq -r '.audit_overhead_pct')
      echo "[token-tracker] WARN: Audit overhead is ${PCT}% (threshold: 30%)" >&2
    fi
    ;;

  *)
    usage
    ;;
esac
