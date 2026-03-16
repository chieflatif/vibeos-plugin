#!/usr/bin/env bash
set -euo pipefail

# baseline-check.sh — Compare current findings against known baselines
# Supports two modes:
#   Count-based (v1.0): aggregate counts per category
#   Finding-level (v2.0): per-finding comparison using fingerprints
# Determines whether failures are pre-existing (within baseline) or new (exceeding baseline).
# Supports one-way ratcheting: baseline can only decrease, never increase.
# Exit 0 with JSON result on stdout; exit 1 on error.

FRAMEWORK_VERSION="2.0.0"

usage() {
  echo "Usage:"
  echo "  Count-based mode (v1.0):"
  echo "    $0 check --baseline-file <path> --category <name> --current-count <N>"
  echo "    $0 ratchet --baseline-file <path> --category <name> --current-count <N>"
  echo ""
  echo "  Finding-level mode (v2.0):"
  echo "    $0 check --mode finding-level --baseline-file <path> --current-findings-file <path>"
  echo "    $0 ratchet --mode finding-level --baseline-file <path> --current-findings-file <path>"
  echo "    $0 create --mode finding-level --baseline-file <path> --current-findings-file <path>"
  echo ""
  echo "Commands:"
  echo "  check    Compare current state against baseline, return PASS/FAIL/TRACKED"
  echo "  ratchet  If improvements found, lock them in (one-way ratchet)"
  echo "  create   Bootstrap a new baseline from current findings (finding-level only)"
  echo ""
  echo "Results (count-based):"
  echo "  PASS     — No failures (current count is 0)"
  echo "  TRACKED  — Failures within baseline (pre-existing, not blocking)"
  echo "  FAIL     — Failures exceed baseline (new issues, blocking)"
  echo "  RATCHET  — Baseline reduced to current count (improvement locked in)"
  echo ""
  echo "Results (finding-level):"
  echo "  PASS     — No new findings"
  echo "  FAIL     — New findings detected (not in baseline), blocking"
  echo "  TRACKED  — All findings are baselined (pre-existing)"
  echo "  RATCHET  — Fixed findings removed from baseline"
  exit 1
}

# Compute fingerprint for a finding: SHA-256 of category:file:pattern:severity
compute_fingerprint() {
  local category="$1"
  local file="$2"
  local pattern="$3"
  local severity="$4"
  echo -n "${category}:${file}:${pattern}:${severity}" | shasum -a 256 | cut -d' ' -f1
}

COMMAND="${1:-}"
shift || true

BASELINE_FILE=""
CATEGORY=""
CURRENT_COUNT=0
MODE=""
CURRENT_FINDINGS_FILE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --baseline-file) BASELINE_FILE="$2"; shift 2 ;;
    --category) CATEGORY="$2"; shift 2 ;;
    --current-count) CURRENT_COUNT="$2"; shift 2 ;;
    --mode) MODE="$2"; shift 2 ;;
    --current-findings-file) CURRENT_FINDINGS_FILE="$2"; shift 2 ;;
    --help|-h) usage ;;
    *) echo "[baseline-check] ERROR: Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [ -z "$BASELINE_FILE" ]; then
  echo "[baseline-check] ERROR: --baseline-file is required" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "[baseline-check] ERROR: jq is required" >&2
  exit 1
fi

# Auto-detect mode from baseline file version if --mode not specified
if [ -z "$MODE" ] && [ -f "$BASELINE_FILE" ]; then
  DETECTED_VERSION=$(jq -r '.version // "1.0"' "$BASELINE_FILE" 2>/dev/null || echo "1.0")
  if [ "$DETECTED_VERSION" = "2.0" ]; then
    MODE="finding-level"
  fi
fi

# Default to count-based mode
if [ -z "$MODE" ]; then
  MODE="count-based"
fi

# ============================================================
# Finding-level mode (v2.0)
# ============================================================
if [ "$MODE" = "finding-level" ]; then
  if [ -z "$CURRENT_FINDINGS_FILE" ]; then
    echo "[baseline-check] ERROR: --current-findings-file is required for finding-level mode" >&2
    exit 1
  fi

  case "$COMMAND" in
    check)
      # If no baseline file exists, all current findings are NEW
      if [ ! -f "$BASELINE_FILE" ]; then
        CURRENT_TOTAL=$(jq '.findings | length' "$CURRENT_FINDINGS_FILE" 2>/dev/null || echo "0")
        if [ "$CURRENT_TOTAL" -eq 0 ]; then
          echo "{\"result\": \"PASS\", \"mode\": \"finding-level\", \"new\": 0, \"tracked\": 0, \"fixed\": 0, \"message\": \"No findings and no baseline\"}"
        else
          echo "{\"result\": \"FAIL\", \"mode\": \"finding-level\", \"new\": $CURRENT_TOTAL, \"tracked\": 0, \"fixed\": 0, \"message\": \"$CURRENT_TOTAL new findings (no baseline exists)\"}"
        fi
        exit 0
      fi

      # Extract fingerprints from baseline, checking for expiry
      # Baseline entries with phase_added that are >2 phases old are expired
      CURRENT_PHASE="${CURRENT_PHASE:-0}"
      EXPIRY_THRESHOLD="${EXPIRY_THRESHOLD:-2}"

      if [ "$CURRENT_PHASE" -gt 0 ]; then
        # Filter out expired baseline entries — they no longer suppress findings
        EXPIRED_COUNT=$(jq --argjson phase "$CURRENT_PHASE" --argjson threshold "$EXPIRY_THRESHOLD" \
          '[.findings[]? | select(.phase_added != null and ($phase - .phase_added) > $threshold)] | length' \
          "$BASELINE_FILE" 2>/dev/null || echo "0")
        if [ "$EXPIRED_COUNT" -gt 0 ]; then
          echo "[baseline-check] WARN: $EXPIRED_COUNT baseline entries expired (older than $EXPIRY_THRESHOLD phases) — these findings are no longer suppressed"
        fi
        BASELINE_FPS=$(jq -r --argjson phase "$CURRENT_PHASE" --argjson threshold "$EXPIRY_THRESHOLD" \
          '.findings[]? | select(.phase_added == null or ($phase - .phase_added) <= $threshold) | .fingerprint // empty' \
          "$BASELINE_FILE" 2>/dev/null | sort)
      else
        BASELINE_FPS=$(jq -r '.findings[]?.fingerprint // empty' "$BASELINE_FILE" 2>/dev/null | sort)
      fi

      # Compute fingerprints for current findings and compare
      NEW_COUNT=0
      TRACKED_COUNT=0
      NEW_IDS=""

      CURRENT_COUNT_FL=$(jq '.findings | length' "$CURRENT_FINDINGS_FILE" 2>/dev/null || echo "0")

      for i in $(seq 0 $((CURRENT_COUNT_FL - 1))); do
        # Read finding fields
        FINDING=$(jq -r ".findings[$i]" "$CURRENT_FINDINGS_FILE")
        F_CAT=$(echo "$FINDING" | jq -r '.category')
        F_FILE=$(echo "$FINDING" | jq -r '.file')
        F_PATTERN=$(echo "$FINDING" | jq -r '.pattern')
        F_SEVERITY=$(echo "$FINDING" | jq -r '.severity')
        F_ID=$(echo "$FINDING" | jq -r '.id')

        # Check if fingerprint is pre-computed in the finding
        F_FP=$(echo "$FINDING" | jq -r '.fingerprint // empty')
        if [ -z "$F_FP" ]; then
          F_FP=$(compute_fingerprint "$F_CAT" "$F_FILE" "$F_PATTERN" "$F_SEVERITY")
        fi

        # Check against baseline fingerprints
        if echo "$BASELINE_FPS" | grep -q "^${F_FP}$"; then
          TRACKED_COUNT=$((TRACKED_COUNT + 1))
        else
          NEW_COUNT=$((NEW_COUNT + 1))
          if [ -n "$NEW_IDS" ]; then
            NEW_IDS="${NEW_IDS}, ${F_ID}"
          else
            NEW_IDS="$F_ID"
          fi
        fi
      done

      # Count fixed findings (in baseline but not in current)
      BASELINE_TOTAL=$(jq '.findings | length' "$BASELINE_FILE" 2>/dev/null || echo "0")
      CURRENT_FPS=""
      for i in $(seq 0 $((CURRENT_COUNT_FL - 1))); do
        FINDING=$(jq -r ".findings[$i]" "$CURRENT_FINDINGS_FILE")
        F_CAT=$(echo "$FINDING" | jq -r '.category')
        F_FILE=$(echo "$FINDING" | jq -r '.file')
        F_PATTERN=$(echo "$FINDING" | jq -r '.pattern')
        F_SEVERITY=$(echo "$FINDING" | jq -r '.severity')
        F_FP=$(echo "$FINDING" | jq -r '.fingerprint // empty')
        if [ -z "$F_FP" ]; then
          F_FP=$(compute_fingerprint "$F_CAT" "$F_FILE" "$F_PATTERN" "$F_SEVERITY")
        fi
        CURRENT_FPS="${CURRENT_FPS}${F_FP}\n"
      done

      FIXED_COUNT=0
      for i in $(seq 0 $((BASELINE_TOTAL - 1))); do
        B_FP=$(jq -r ".findings[$i].fingerprint" "$BASELINE_FILE" 2>/dev/null || echo "")
        if [ -n "$B_FP" ] && ! echo -e "$CURRENT_FPS" | grep -q "^${B_FP}$"; then
          FIXED_COUNT=$((FIXED_COUNT + 1))
        fi
      done

      if [ "$NEW_COUNT" -gt 0 ]; then
        echo "{\"result\": \"FAIL\", \"mode\": \"finding-level\", \"new\": $NEW_COUNT, \"tracked\": $TRACKED_COUNT, \"fixed\": $FIXED_COUNT, \"new_ids\": \"$NEW_IDS\", \"message\": \"$NEW_COUNT new findings detected: $NEW_IDS\"}"
      elif [ "$TRACKED_COUNT" -gt 0 ]; then
        echo "{\"result\": \"TRACKED\", \"mode\": \"finding-level\", \"new\": 0, \"tracked\": $TRACKED_COUNT, \"fixed\": $FIXED_COUNT, \"message\": \"$TRACKED_COUNT pre-existing findings tracked, $FIXED_COUNT fixed\"}"
      else
        echo "{\"result\": \"PASS\", \"mode\": \"finding-level\", \"new\": 0, \"tracked\": 0, \"fixed\": $FIXED_COUNT, \"message\": \"No findings\"}"
      fi
      ;;

    ratchet)
      if [ ! -f "$BASELINE_FILE" ]; then
        echo "{\"result\": \"SKIP\", \"mode\": \"finding-level\", \"message\": \"No baseline file to ratchet\"}"
        exit 0
      fi

      # Remove findings from baseline that no longer appear in current scan
      CURRENT_COUNT_FL=$(jq '.findings | length' "$CURRENT_FINDINGS_FILE" 2>/dev/null || echo "0")
      CURRENT_FPS=""
      for i in $(seq 0 $((CURRENT_COUNT_FL - 1))); do
        FINDING=$(jq -r ".findings[$i]" "$CURRENT_FINDINGS_FILE")
        F_CAT=$(echo "$FINDING" | jq -r '.category')
        F_FILE=$(echo "$FINDING" | jq -r '.file')
        F_PATTERN=$(echo "$FINDING" | jq -r '.pattern')
        F_SEVERITY=$(echo "$FINDING" | jq -r '.severity')
        F_FP=$(echo "$FINDING" | jq -r '.fingerprint // empty')
        if [ -z "$F_FP" ]; then
          F_FP=$(compute_fingerprint "$F_CAT" "$F_FILE" "$F_PATTERN" "$F_SEVERITY")
        fi
        CURRENT_FPS="${CURRENT_FPS}${F_FP}\n"
      done

      BASELINE_TOTAL=$(jq '.findings | length' "$BASELINE_FILE" 2>/dev/null || echo "0")
      REMOVED_COUNT=0
      KEEP_INDICES=""

      for i in $(seq 0 $((BASELINE_TOTAL - 1))); do
        B_FP=$(jq -r ".findings[$i].fingerprint" "$BASELINE_FILE" 2>/dev/null || echo "")
        if [ -n "$B_FP" ] && echo -e "$CURRENT_FPS" | grep -q "^${B_FP}$"; then
          if [ -n "$KEEP_INDICES" ]; then
            KEEP_INDICES="${KEEP_INDICES}, $i"
          else
            KEEP_INDICES="$i"
          fi
        else
          REMOVED_COUNT=$((REMOVED_COUNT + 1))
        fi
      done

      if [ "$REMOVED_COUNT" -gt 0 ]; then
        # Build updated baseline with only kept findings
        UPDATED=$(jq "[.findings | to_entries[] | select(.key | IN(${KEEP_INDICES:-})) | .value]" "$BASELINE_FILE" 2>/dev/null || echo "[]")
        jq --argjson kept "$UPDATED" '.findings = $kept' "$BASELINE_FILE" > "${BASELINE_FILE}.tmp" && mv "${BASELINE_FILE}.tmp" "$BASELINE_FILE"
        NEW_TOTAL=$(jq '.findings | length' "$BASELINE_FILE")
        echo "{\"result\": \"RATCHET\", \"mode\": \"finding-level\", \"removed\": $REMOVED_COUNT, \"remaining\": $NEW_TOTAL, \"message\": \"$REMOVED_COUNT fixed findings removed from baseline\"}"
      else
        echo "{\"result\": \"UNCHANGED\", \"mode\": \"finding-level\", \"remaining\": $BASELINE_TOTAL, \"message\": \"No findings to ratchet\"}"
      fi
      ;;

    create)
      # Bootstrap a new baseline from current findings
      if [ ! -f "$CURRENT_FINDINGS_FILE" ]; then
        echo "[baseline-check] ERROR: --current-findings-file does not exist: $CURRENT_FINDINGS_FILE" >&2
        exit 1
      fi

      CURRENT_TOTAL=$(jq '.findings | length' "$CURRENT_FINDINGS_FILE" 2>/dev/null || echo "0")

      # Build baseline with fingerprints for all current findings
      BASELINE_FINDINGS="[]"
      for i in $(seq 0 $((CURRENT_TOTAL - 1))); do
        FINDING=$(jq -r ".findings[$i]" "$CURRENT_FINDINGS_FILE")
        F_CAT=$(echo "$FINDING" | jq -r '.category')
        F_FILE=$(echo "$FINDING" | jq -r '.file')
        F_PATTERN=$(echo "$FINDING" | jq -r '.pattern')
        F_SEVERITY=$(echo "$FINDING" | jq -r '.severity')
        F_FP=$(echo "$FINDING" | jq -r '.fingerprint // empty')
        if [ -z "$F_FP" ]; then
          F_FP=$(compute_fingerprint "$F_CAT" "$F_FILE" "$F_PATTERN" "$F_SEVERITY")
        fi
        # Add fingerprint to finding and append to baseline
        UPDATED_FINDING=$(echo "$FINDING" | jq --arg fp "$F_FP" '. + {"fingerprint": $fp, "status": "baselined"}')
        BASELINE_FINDINGS=$(echo "$BASELINE_FINDINGS" | jq --argjson f "$UPDATED_FINDING" '. + [$f]')
      done

      # Count by severity
      CRITICAL=$(echo "$BASELINE_FINDINGS" | jq '[.[] | select(.severity == "critical")] | length')
      HIGH=$(echo "$BASELINE_FINDINGS" | jq '[.[] | select(.severity == "high")] | length')
      MEDIUM=$(echo "$BASELINE_FINDINGS" | jq '[.[] | select(.severity == "medium")] | length')
      LOW=$(echo "$BASELINE_FINDINGS" | jq '[.[] | select(.severity == "low")] | length')

      # Create baseline file
      NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
      BASELINE_JSON=$(jq -n \
        --arg version "2.0" \
        --arg date "$NOW" \
        --arg type "midstream" \
        --argjson findings "$BASELINE_FINDINGS" \
        --argjson critical "$CRITICAL" \
        --argjson high "$HIGH" \
        --argjson medium "$MEDIUM" \
        --argjson low "$LOW" \
        --argjson total "$CURRENT_TOTAL" \
        '{
          type: $type,
          version: $version,
          date: $date,
          findings: $findings,
          summary: {
            critical: $critical,
            high: $high,
            medium: $medium,
            low: $low,
            total: $total
          }
        }')

      # Ensure directory exists
      mkdir -p "$(dirname "$BASELINE_FILE")"
      echo "$BASELINE_JSON" > "$BASELINE_FILE"

      echo "{\"result\": \"CREATED\", \"mode\": \"finding-level\", \"findings_baselined\": $CURRENT_TOTAL, \"baseline_file\": \"$BASELINE_FILE\", \"message\": \"Baseline created with $CURRENT_TOTAL findings ($CRITICAL critical, $HIGH high, $MEDIUM medium, $LOW low)\"}"
      ;;

    *)
      usage
      ;;
  esac
  exit 0
fi

# ============================================================
# Count-based mode (v1.0) — original behavior
# ============================================================

if [ -z "$CATEGORY" ]; then
  echo "[baseline-check] ERROR: --category is required for count-based mode" >&2
  exit 1
fi

case "$COMMAND" in
  check)
    # If no baseline file exists, treat baseline as 0 (all failures are new)
    if [ ! -f "$BASELINE_FILE" ]; then
      if [ "$CURRENT_COUNT" -eq 0 ]; then
        echo "{\"result\": \"PASS\", \"category\": \"$CATEGORY\", \"current\": 0, \"baseline\": 0, \"message\": \"No failures and no baseline\"}"
      else
        echo "{\"result\": \"FAIL\", \"category\": \"$CATEGORY\", \"current\": $CURRENT_COUNT, \"baseline\": 0, \"message\": \"$CURRENT_COUNT new failures (no baseline exists)\"}"
      fi
      exit 0
    fi

    # Read baseline for this category
    BASELINE=$(jq -r --arg cat "$CATEGORY" '.findings[$cat] // 0' "$BASELINE_FILE" 2>/dev/null || echo "0")

    if [ "$CURRENT_COUNT" -eq 0 ]; then
      echo "{\"result\": \"PASS\", \"category\": \"$CATEGORY\", \"current\": 0, \"baseline\": $BASELINE, \"message\": \"No failures\"}"
    elif [ "$CURRENT_COUNT" -le "$BASELINE" ]; then
      echo "{\"result\": \"TRACKED\", \"category\": \"$CATEGORY\", \"current\": $CURRENT_COUNT, \"baseline\": $BASELINE, \"message\": \"$CURRENT_COUNT pre-existing issues (within baseline of $BASELINE)\"}"
    else
      NEW_COUNT=$((CURRENT_COUNT - BASELINE))
      echo "{\"result\": \"FAIL\", \"category\": \"$CATEGORY\", \"current\": $CURRENT_COUNT, \"baseline\": $BASELINE, \"message\": \"$NEW_COUNT new failures (baseline: $BASELINE, current: $CURRENT_COUNT)\"}"
    fi
    ;;

  ratchet)
    if [ ! -f "$BASELINE_FILE" ]; then
      echo "{\"result\": \"SKIP\", \"category\": \"$CATEGORY\", \"message\": \"No baseline file to ratchet\"}"
      exit 0
    fi

    BASELINE=$(jq -r --arg cat "$CATEGORY" '.findings[$cat] // 0' "$BASELINE_FILE" 2>/dev/null || echo "0")

    if [ "$CURRENT_COUNT" -lt "$BASELINE" ]; then
      # Ratchet down: update baseline to current count
      UPDATED=$(jq --arg cat "$CATEGORY" --argjson count "$CURRENT_COUNT" '.findings[$cat] = $count' "$BASELINE_FILE")
      echo "$UPDATED" > "$BASELINE_FILE"
      echo "{\"result\": \"RATCHET\", \"category\": \"$CATEGORY\", \"previous_baseline\": $BASELINE, \"new_baseline\": $CURRENT_COUNT, \"message\": \"Baseline improved from $BASELINE to $CURRENT_COUNT\"}"
    elif [ "$CURRENT_COUNT" -eq "$BASELINE" ]; then
      echo "{\"result\": \"UNCHANGED\", \"category\": \"$CATEGORY\", \"baseline\": $BASELINE, \"message\": \"No change to baseline\"}"
    else
      # Current exceeds baseline — this is a failure, not a ratchet-up
      echo "{\"result\": \"BLOCKED\", \"category\": \"$CATEGORY\", \"baseline\": $BASELINE, \"current\": $CURRENT_COUNT, \"message\": \"Cannot increase baseline (one-way ratchet). Current $CURRENT_COUNT exceeds baseline $BASELINE.\"}"
    fi
    ;;

  *)
    usage
    ;;
esac
