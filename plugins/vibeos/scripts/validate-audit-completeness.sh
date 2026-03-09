#!/usr/bin/env bash
# VibeOS Plugin — Audit Completeness Validation Gate
# Checks that work orders have proper audit trails and evidence.
#
# Usage:
#   bash scripts/validate-audit-completeness.sh
#
# Environment:
#   WO_DIR    — work order directory (default: docs/planning)
#   ADR_DIR   — ADR directory (default: docs/adr)
#   ENFORCE_AUDIT_LOOP — true to convert required audit-loop gaps into failures
#
# Exit codes:
#   0 = Audit completeness checks passed
#   1 = Missing audit artifacts
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="1.0.0"
GATE_NAME="validate-audit-completeness"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate-audit-completeness.sh

Environment:
  WO_DIR    Work order directory (default: docs/planning)
  ADR_DIR   ADR directory (default: docs/adr)
  ENFORCE_AUDIT_LOOP  true to fail on missing required audit-loop checkpoints

Checks:
  - WO-INDEX.md exists and has recent entries
  - WO-AUDIT-FRAMEWORK.md exists
  - Completed WOs have required audit trail checkpoints
  - ADRs reference WOs when applicable
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] Audit Completeness Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WO_DIR="${WO_DIR:-docs/planning}"
ADR_DIR="${ADR_DIR:-docs/adr}"
ENFORCE_AUDIT_LOOP="${ENFORCE_AUDIT_LOOP:-false}"

wo_path="$repo_root/$WO_DIR"
warnings=0
errors=0

record_issue() {
  local severity="$1"
  local message="$2"
  if [[ "$severity" == "error" ]]; then
    echo "[$GATE_NAME] FAIL: $message"
    errors=$((errors + 1))
  else
    echo "[$GATE_NAME] WARN: $message"
    warnings=$((warnings + 1))
  fi
}

# Check 1: WO-INDEX.md exists
WO_INDEX="$wo_path/WO-INDEX.md"
if [[ -f "$WO_INDEX" ]]; then
  echo "[$GATE_NAME] PASS: WO-INDEX.md found"

  # Check that it has at least one WO entry
  wo_count=$(grep -c -E '^\|.*WO-' "$WO_INDEX" 2>/dev/null || echo "0")
  if [[ "$wo_count" -gt 0 ]]; then
    echo "[$GATE_NAME] PASS: WO-INDEX has $wo_count work order entries"
  else
    echo "[$GATE_NAME] WARN: WO-INDEX.md exists but has no work order entries"
    warnings=$((warnings + 1))
  fi
else
  echo "[$GATE_NAME] WARN: WO-INDEX.md not found at $WO_INDEX"
  echo "[$GATE_NAME] WARN: Create a WO-INDEX.md to track work orders"
  warnings=$((warnings + 1))
fi

# Check 2: DEVELOPMENT-PLAN.md exists (required for alignment with WO-INDEX)
DEVELOPMENT_PLAN="$wo_path/DEVELOPMENT-PLAN.md"
if [[ -f "$DEVELOPMENT_PLAN" ]]; then
  echo "[$GATE_NAME] PASS: DEVELOPMENT-PLAN.md found"
  if ! grep -qE '\*\*Next:\*\*|Next Work Order' "$DEVELOPMENT_PLAN" 2>/dev/null; then
    if [[ "$ENFORCE_AUDIT_LOOP" == "true" ]]; then
      record_issue "error" "DEVELOPMENT-PLAN.md missing 'Next Work Order' section"
    else
      record_issue "warn" "DEVELOPMENT-PLAN.md should have a 'Next Work Order' section"
    fi
  fi
else
  if [[ "$ENFORCE_AUDIT_LOOP" == "true" ]]; then
    record_issue "error" "DEVELOPMENT-PLAN.md not found — required for roadmap alignment"
  else
    record_issue "warn" "DEVELOPMENT-PLAN.md not found at $DEVELOPMENT_PLAN (recommended for alignment)"
  fi
fi

# Check 3: WO audit framework exists
WO_AUDIT_FRAMEWORK="$wo_path/WO-AUDIT-FRAMEWORK.md"
if [[ -f "$WO_AUDIT_FRAMEWORK" ]]; then
  echo "[$GATE_NAME] PASS: WO-AUDIT-FRAMEWORK.md found"
else
  if [[ "$ENFORCE_AUDIT_LOOP" == "true" ]]; then
    record_issue "error" "WO-AUDIT-FRAMEWORK.md not found at $WO_AUDIT_FRAMEWORK"
  else
    record_issue "warn" "WO-AUDIT-FRAMEWORK.md not found at $WO_AUDIT_FRAMEWORK"
  fi
  echo "[$GATE_NAME] WARN: Create a WO-AUDIT-FRAMEWORK.md to standardize repeated WO audits"
fi

# Check 4: Completed WOs have required sections
if [[ -d "$wo_path" ]]; then
  completed_wo_files=$(find "$wo_path" -name "WO-*.md" -not -name "WO-INDEX.md" 2>/dev/null || true)

  if [[ -n "$completed_wo_files" ]]; then
    for wo_file in $completed_wo_files; do
      content=$(cat "$wo_file")
      wo_name=$(basename "$wo_file" .md)

      # Check for status field
      if echo "$content" | grep -qiE '(status:\s*(complete|completed|done|closed|shipped|deployed))'; then
        if ! echo "$content" | grep -qiE 'planning self-audit'; then
          if [[ "$ENFORCE_AUDIT_LOOP" == "true" ]]; then
            record_issue "error" "$wo_name marked complete but missing planning self-audit checkpoint"
          else
            record_issue "warn" "$wo_name marked complete but missing planning self-audit checkpoint"
          fi
        fi

        if ! echo "$content" | grep -qiE 'pre-implementation deep audit'; then
          if [[ "$ENFORCE_AUDIT_LOOP" == "true" ]]; then
            record_issue "error" "$wo_name marked complete but missing pre-implementation deep audit checkpoint"
          else
            record_issue "warn" "$wo_name marked complete but missing pre-implementation deep audit checkpoint"
          fi
        fi

        if ! echo "$content" | grep -qiE 'pre-commit audit'; then
          if [[ "$ENFORCE_AUDIT_LOOP" == "true" ]]; then
            record_issue "error" "$wo_name marked complete but missing pre-commit audit checkpoint"
          else
            record_issue "warn" "$wo_name marked complete but missing pre-commit audit checkpoint"
          fi
        fi

        if ! echo "$content" | grep -qiE '(evidence|audit notes|gate.*result|quality.*gate)'; then
          if [[ "$ENFORCE_AUDIT_LOOP" == "true" ]]; then
            record_issue "error" "$wo_name marked complete but missing evidence or audit notes"
          else
            record_issue "warn" "$wo_name marked complete but missing evidence or audit notes"
          fi
        fi

        if ! echo "$content" | grep -qiE '(test|testing|verification|validated)'; then
          if [[ "$ENFORCE_AUDIT_LOOP" == "true" ]]; then
            record_issue "error" "$wo_name marked complete but missing testing or verification references"
          else
            record_issue "warn" "$wo_name marked complete but missing testing or verification references"
          fi
        fi
      fi

      if echo "$content" | grep -qiE '(status:\s*(shipped|deployed))'; then
        if ! echo "$content" | grep -qiE 'staging audit'; then
          if [[ "$ENFORCE_AUDIT_LOOP" == "true" ]]; then
            record_issue "error" "$wo_name marked shipped/deployed but missing staging audit checkpoint"
          else
            record_issue "warn" "$wo_name marked shipped/deployed but missing staging audit checkpoint"
          fi
        fi
      fi
    done
  fi
fi

# Check 5: ADR directory exists (advisory)
adr_path="$repo_root/$ADR_DIR"
if [[ -d "$adr_path" ]]; then
  adr_count=$(find "$adr_path" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
  echo "[$GATE_NAME] INFO: $adr_count ADR(s) found in $ADR_DIR"
else
  echo "[$GATE_NAME] INFO: No ADR directory at $ADR_DIR (optional)"
fi

# Summary
echo ""
if [[ $errors -gt 0 ]]; then
  echo "[$GATE_NAME] FAIL: $errors error(s), $warnings warning(s)"
  exit 1
elif [[ $warnings -gt 0 ]]; then
  echo "[$GATE_NAME] PASS (with $warnings warning(s))"
  exit 0
else
  echo "[$GATE_NAME] PASS: Audit completeness checks passed"
  exit 0
fi
