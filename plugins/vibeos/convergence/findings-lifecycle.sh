#!/usr/bin/env bash
# VibeOS Plugin — Finding Lifecycle Manager
# Manages the findings registry: deduplication, regression detection, status tracking.
#
# Usage:
#   bash convergence/findings-lifecycle.sh record --findings-file <path> --registry <path>
#   bash convergence/findings-lifecycle.sh resolve --finding-id <id> --registry <path> --wo <WO-NNN> --commit <sha>
#   bash convergence/findings-lifecycle.sh false-positive --finding-id <id> --registry <path> --reason <text>
#   bash convergence/findings-lifecycle.sh stats --registry <path>
#
# Exit codes:
#   0 = Success
#   1 = Regressions detected (previously resolved findings re-appeared)
#   2 = Configuration error

set -euo pipefail
FRAMEWORK_VERSION="2.0.0"

COMMAND="${1:-}"
shift || true

FINDINGS_FILE=""
REGISTRY=""
FINDING_ID=""
WO=""
COMMIT=""
REASON=""

while [ $# -gt 0 ]; do
  case "$1" in
    --findings-file) FINDINGS_FILE="$2"; shift 2 ;;
    --registry) REGISTRY="$2"; shift 2 ;;
    --finding-id) FINDING_ID="$2"; shift 2 ;;
    --wo) WO="$2"; shift 2 ;;
    --commit) COMMIT="$2"; shift 2 ;;
    --reason) REASON="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [ -z "$REGISTRY" ]; then
  echo "[findings-lifecycle] ERROR: --registry is required" >&2
  exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "[findings-lifecycle] ERROR: jq is required" >&2
  exit 2
fi

# Initialize registry if it doesn't exist
init_registry() {
  if [ ! -f "$REGISTRY" ]; then
    mkdir -p "$(dirname "$REGISTRY")"
    NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo "{\"version\": \"2.0.0\", \"created\": \"$NOW\", \"entries\": [], \"pattern_stats\": {}}" > "$REGISTRY"
  fi
}

case "$COMMAND" in
  record)
    if [ -z "$FINDINGS_FILE" ]; then
      echo "[findings-lifecycle] ERROR: --findings-file is required for record" >&2
      exit 2
    fi
    if [ ! -f "$FINDINGS_FILE" ]; then
      echo "[findings-lifecycle] SKIP: Findings file not found: $FINDINGS_FILE"
      exit 0
    fi

    init_registry
    NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    REGRESSIONS=0
    NEW_COUNT=0
    UPDATED_COUNT=0
    SUPPRESSED_COUNT=0

    FINDING_COUNT=$(jq '.findings | length' "$FINDINGS_FILE" 2>/dev/null || echo "0")

    for i in $(seq 0 $((FINDING_COUNT - 1))); do
      FINDING=$(jq -r ".findings[$i]" "$FINDINGS_FILE")
      F_FP=$(echo "$FINDING" | jq -r '.fingerprint // empty')
      F_CAT=$(echo "$FINDING" | jq -r '.category // "unknown"')
      F_FILE=$(echo "$FINDING" | jq -r '.file // "unknown"')
      F_PATTERN=$(echo "$FINDING" | jq -r '.pattern // "unknown"')
      F_SEVERITY=$(echo "$FINDING" | jq -r '.severity // "medium"')
      F_ID=$(echo "$FINDING" | jq -r '.id // empty')

      if [ -z "$F_FP" ]; then
        F_FP=$(echo -n "${F_CAT}:${F_FILE}:${F_PATTERN}:${F_SEVERITY}" | shasum -a 256 | cut -d' ' -f1)
      fi

      # Check registry for existing entry
      EXISTING=$(jq --arg fp "$F_FP" '.entries[] | select(.fingerprint == $fp)' "$REGISTRY" 2>/dev/null || echo "")

      if [ -n "$EXISTING" ]; then
        STATUS=$(echo "$EXISTING" | jq -r '.status')
        case "$STATUS" in
          false_positive)
            SUPPRESSED_COUNT=$((SUPPRESSED_COUNT + 1))
            ;;
          resolved)
            # REGRESSION: previously fixed, now re-appeared
            REGRESSIONS=$((REGRESSIONS + 1))
            jq --arg fp "$F_FP" --arg now "$NOW" \
              '(.entries[] | select(.fingerprint == $fp)) |= . + {"status": "open", "last_seen": $now, "times_reported": ((.times_reported // 1) + 1)}' \
              "$REGISTRY" > "${REGISTRY}.tmp" && mv "${REGISTRY}.tmp" "$REGISTRY"
            echo "[findings-lifecycle] REGRESSION: $F_ID ($F_PATTERN in $F_FILE) was resolved but re-appeared"
            ;;
          open|deferred)
            UPDATED_COUNT=$((UPDATED_COUNT + 1))
            jq --arg fp "$F_FP" --arg now "$NOW" \
              '(.entries[] | select(.fingerprint == $fp)) |= . + {"last_seen": $now, "times_reported": ((.times_reported // 1) + 1)}' \
              "$REGISTRY" > "${REGISTRY}.tmp" && mv "${REGISTRY}.tmp" "$REGISTRY"
            ;;
        esac
      else
        # New finding
        NEW_COUNT=$((NEW_COUNT + 1))
        NEXT_ID="F-$(printf '%03d' $(($(jq '.entries | length' "$REGISTRY") + 1)))"
        NEW_ENTRY=$(jq -n \
          --arg id "$NEXT_ID" \
          --arg fp "$F_FP" \
          --arg now "$NOW" \
          --arg cat "$F_CAT" \
          --arg file "$F_FILE" \
          --arg pattern "$F_PATTERN" \
          --arg severity "$F_SEVERITY" \
          --arg wo "${WO:-unknown}" \
          '{
            "id": $id,
            "fingerprint": $fp,
            "first_seen": $now,
            "last_seen": $now,
            "status": "open",
            "pattern_tag": $pattern,
            "severity": $severity,
            "file": $file,
            "category": $cat,
            "times_reported": 1,
            "wo_introduced": $wo
          }')
        jq --argjson entry "$NEW_ENTRY" '.entries += [$entry]' "$REGISTRY" > "${REGISTRY}.tmp" && mv "${REGISTRY}.tmp" "$REGISTRY"
      fi
    done

    # Update pattern stats
    for pattern in $(jq -r '.entries[].pattern_tag // empty' "$REGISTRY" 2>/dev/null | sort -u); do
      TOTAL=$(jq --arg p "$pattern" '[.entries[] | select(.pattern_tag == $p)] | length' "$REGISTRY")
      SUPPRESSED=$(jq --arg p "$pattern" '[.entries[] | select(.pattern_tag == $p and .status == "false_positive")] | length' "$REGISTRY")
      jq --arg p "$pattern" --argjson t "$TOTAL" --argjson s "$SUPPRESSED" \
        '.pattern_stats[$p] = {"total": $t, "suppressed": $s}' \
        "$REGISTRY" > "${REGISTRY}.tmp" && mv "${REGISTRY}.tmp" "$REGISTRY"
    done

    echo "{\"new\": $NEW_COUNT, \"updated\": $UPDATED_COUNT, \"suppressed\": $SUPPRESSED_COUNT, \"regressions\": $REGRESSIONS}"

    if [ "$REGRESSIONS" -gt 0 ]; then
      exit 1
    fi
    ;;

  resolve)
    if [ -z "$FINDING_ID" ]; then
      echo "[findings-lifecycle] ERROR: --finding-id is required for resolve" >&2
      exit 2
    fi
    init_registry
    NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    jq --arg id "$FINDING_ID" --arg now "$NOW" --arg wo "${WO:-}" --arg commit "${COMMIT:-}" \
      '(.entries[] | select(.id == $id)) |= . + {"status": "resolved", "resolved_at": $now, "wo_resolved": $wo, "commit_sha": $commit}' \
      "$REGISTRY" > "${REGISTRY}.tmp" && mv "${REGISTRY}.tmp" "$REGISTRY"
    echo "[findings-lifecycle] Resolved: $FINDING_ID"
    ;;

  false-positive)
    if [ -z "$FINDING_ID" ]; then
      echo "[findings-lifecycle] ERROR: --finding-id is required for false-positive" >&2
      exit 2
    fi
    init_registry
    NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    jq --arg id "$FINDING_ID" --arg now "$NOW" --arg reason "${REASON:-No reason provided}" \
      '(.entries[] | select(.id == $id)) |= . + {"status": "false_positive", "suppressed_at": $now, "resolution": $reason}' \
      "$REGISTRY" > "${REGISTRY}.tmp" && mv "${REGISTRY}.tmp" "$REGISTRY"
    echo "[findings-lifecycle] Marked false positive: $FINDING_ID — $REASON"
    ;;

  stats)
    init_registry
    TOTAL=$(jq '.entries | length' "$REGISTRY")
    OPEN=$(jq '[.entries[] | select(.status == "open")] | length' "$REGISTRY")
    RESOLVED=$(jq '[.entries[] | select(.status == "resolved")] | length' "$REGISTRY")
    FALSE_POS=$(jq '[.entries[] | select(.status == "false_positive")] | length' "$REGISTRY")
    DEFERRED=$(jq '[.entries[] | select(.status == "deferred")] | length' "$REGISTRY")
    echo "Total entries: $TOTAL"
    echo "Open: $OPEN"
    echo "Resolved: $RESOLVED"
    echo "False positives: $FALSE_POS"
    echo "Deferred: $DEFERRED"
    echo ""
    echo "Pattern stats:"
    jq -r '.pattern_stats | to_entries[] | "  \(.key): \(.value.total) total, \(.value.suppressed) suppressed"' "$REGISTRY" 2>/dev/null || echo "  (none)"
    ;;

  *)
    echo "Usage: $0 {record|resolve|false-positive|stats} [options]" >&2
    exit 2
    ;;
esac
