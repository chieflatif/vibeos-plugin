#!/usr/bin/env bash
set -euo pipefail

# migrate-baseline.sh — Convert count-based baselines (v1.0) to finding-level (v2.0)
# Creates generic finding entries from aggregate counts since individual findings
# are not available in count-based baselines. Marks all entries as
# "pre-existing-unmigrated" disposition for user review.
# Exit 0 on success; exit 1 on error.

FRAMEWORK_VERSION="2.0.0"

usage() {
  echo "Usage:"
  echo "  $0 --input <count-based-baseline.json> --output <finding-level-baseline.json>"
  echo ""
  echo "Converts a count-based baseline (v1.0) to finding-level format (v2.0)."
  echo "Generated entries use 'pre-existing-unmigrated' disposition — user must review."
  exit 1
}

INPUT_FILE=""
OUTPUT_FILE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --input) INPUT_FILE="$2"; shift 2 ;;
    --output) OUTPUT_FILE="$2"; shift 2 ;;
    --help|-h) usage ;;
    *) echo "[migrate-baseline] ERROR: Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [ -z "$INPUT_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
  echo "[migrate-baseline] ERROR: --input and --output are required" >&2
  exit 1
fi

if [ ! -f "$INPUT_FILE" ]; then
  echo "[migrate-baseline] ERROR: Input file does not exist: $INPUT_FILE" >&2
  exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "[migrate-baseline] ERROR: jq is required" >&2
  exit 1
fi

# Read input baseline version
INPUT_VERSION=$(jq -r '.version // "1.0"' "$INPUT_FILE" 2>/dev/null || echo "1.0")

if [ "$INPUT_VERSION" = "2.0" ]; then
  echo "[migrate-baseline] SKIP: Input is already finding-level format (v2.0)"
  exit 0
fi

# Read aggregate counts from input
DATE=$(jq -r '.date // "unknown"' "$INPUT_FILE" 2>/dev/null || echo "unknown")
SOURCE_FILES=$(jq -r '.source_files // 0' "$INPUT_FILE" 2>/dev/null || echo "0")

# Generate finding entries from counts
# Categories in findings object: critical, high, medium, low
FINDINGS="[]"
ID_COUNTER=0

for SEVERITY in critical high medium low; do
  COUNT=$(jq -r --arg sev "$SEVERITY" '.findings[$sev] // 0' "$INPUT_FILE" 2>/dev/null || echo "0")
  for i in $(seq 1 "$COUNT"); do
    ID_COUNTER=$((ID_COUNTER + 1))
    PADDED_ID=$(printf "%03d" "$ID_COUNTER")
    PREFIX=$(echo "$SEVERITY" | cut -c1 | tr '[:lower:]' '[:upper:]')
    FINDING_ID="MIG-${PREFIX}${PADDED_ID}"
    FP=$(echo -n "migrated:unknown:migrated-${SEVERITY}-${i}:${SEVERITY}" | shasum -a 256 | cut -d' ' -f1)

    ENTRY=$(jq -n \
      --arg id "$FINDING_ID" \
      --arg sev "$SEVERITY" \
      --arg fp "$FP" \
      --arg desc "Migrated from count-based baseline (original count: ${COUNT} ${SEVERITY})" \
      '{
        "id": $id,
        "category": "migrated",
        "severity": $sev,
        "fingerprint": $fp,
        "file": "unknown",
        "line": 0,
        "pattern": ("migrated-" + $sev),
        "description": $desc,
        "disposition": "pre-existing-unmigrated",
        "baselined_at": "migrated",
        "status": "open"
      }')

    FINDINGS=$(echo "$FINDINGS" | jq --argjson entry "$ENTRY" '. + [$entry]')
  done
done

# Build summary from original counts
CRITICAL=$(jq -r '.findings.critical // 0' "$INPUT_FILE" 2>/dev/null || echo "0")
HIGH=$(jq -r '.findings.high // 0' "$INPUT_FILE" 2>/dev/null || echo "0")
MEDIUM=$(jq -r '.findings.medium // 0' "$INPUT_FILE" 2>/dev/null || echo "0")
LOW=$(jq -r '.findings.low // 0' "$INPUT_FILE" 2>/dev/null || echo "0")
TOTAL=$((CRITICAL + HIGH + MEDIUM + LOW))

# Write output
jq -n \
  --arg date "$DATE" \
  --argjson source_files "$SOURCE_FILES" \
  --argjson findings "$FINDINGS" \
  --argjson critical "$CRITICAL" \
  --argjson high "$HIGH" \
  --argjson medium "$MEDIUM" \
  --argjson low "$LOW" \
  --argjson total "$TOTAL" \
  '{
    "type": "midstream",
    "version": "2.0",
    "migrated_from": "1.0",
    "date": $date,
    "source_files": $source_files,
    "findings": $findings,
    "summary": {
      "critical": $critical,
      "high": $high,
      "medium": $medium,
      "low": $low,
      "total": $total,
      "migrated": true,
      "note": "All findings are generic entries migrated from count-based baseline. Review and update dispositions."
    }
  }' > "$OUTPUT_FILE"

echo "[migrate-baseline] PASS: Migrated $TOTAL findings from v1.0 to v2.0 format"
echo "[migrate-baseline] Output: $OUTPUT_FILE"
echo "[migrate-baseline] WARN: All entries have disposition 'pre-existing-unmigrated' — user review required"
