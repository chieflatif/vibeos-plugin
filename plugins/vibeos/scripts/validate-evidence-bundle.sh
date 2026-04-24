#!/usr/bin/env bash
# VibeOS Plugin — Evidence Bundle Validation Gate
# Validates SOC 2 compliance evidence bundles.
#
# Usage:
#   bash scripts/validate-evidence-bundle.sh [bundle_dir]
#
# Environment:
#   EVIDENCE_DIR — evidence bundle directory (default: docs/evidence/)
#
# Exit codes:
#   0 = Evidence bundle valid
#   1 = Evidence bundle incomplete or invalid
#   2 = No evidence directory found (skip)
set -euo pipefail

FRAMEWORK_VERSION="2.2.0"
GATE_NAME="validate-evidence-bundle"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate-evidence-bundle.sh [bundle_dir]

Environment:
  EVIDENCE_DIR  Evidence bundle directory (default: docs/evidence/)

Expected bundle structure:
  evidence/
  ├── summary.md          — Human-readable summary
  ├── metadata.json       — Machine-parseable metadata
  └── gate-results/       — Gate output files
      ├── pre-commit.txt
      ├── wo-exit.txt
      └── full-audit.txt
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] Evidence Bundle Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Resolve evidence directory
if [[ $# -gt 0 && -d "$1" ]]; then
  EVIDENCE_DIR="$1"
else
  EVIDENCE_DIR="${EVIDENCE_DIR:-$PROJECT_ROOT/docs/evidence}"
fi

if [[ ! -d "$EVIDENCE_DIR" ]]; then
  echo "[$GATE_NAME] INFO: No evidence directory found at $EVIDENCE_DIR"
  echo "[$GATE_NAME] SKIP: Evidence bundles are optional (required for SOC 2 compliance)"
  exit 0
fi

echo "Evidence directory: $EVIDENCE_DIR"
warnings=0
errors=0

# Check 1: summary.md exists
if [[ -f "$EVIDENCE_DIR/summary.md" ]]; then
  echo "[$GATE_NAME] PASS: summary.md exists"
  # Check it's not empty
  if [[ -s "$EVIDENCE_DIR/summary.md" ]]; then
    echo "[$GATE_NAME] PASS: summary.md is non-empty"
  else
    echo "[$GATE_NAME] WARN: summary.md is empty"
    warnings=$((warnings + 1))
  fi
else
  echo "[$GATE_NAME] FAIL: summary.md missing from evidence bundle"
  errors=$((errors + 1))
fi

# Check 2: metadata.json exists and is valid
if [[ -f "$EVIDENCE_DIR/metadata.json" ]]; then
  if jq empty "$EVIDENCE_DIR/metadata.json" 2>/dev/null; then
    echo "[$GATE_NAME] PASS: metadata.json is valid JSON"

    # Check required fields
    has_wo=$(jq -r '.work_order // empty' "$EVIDENCE_DIR/metadata.json" 2>/dev/null)
    has_ts=$(jq -r '.timestamp // empty' "$EVIDENCE_DIR/metadata.json" 2>/dev/null)
    has_phase=$(jq -r '.phase // empty' "$EVIDENCE_DIR/metadata.json" 2>/dev/null)

    if [[ -n "$has_wo" ]]; then
      echo "[$GATE_NAME] PASS: metadata.json has work_order field"
    else
      echo "[$GATE_NAME] WARN: metadata.json missing work_order field"
      warnings=$((warnings + 1))
    fi

    if [[ -n "$has_ts" ]]; then
      echo "[$GATE_NAME] PASS: metadata.json has timestamp field"
    else
      echo "[$GATE_NAME] WARN: metadata.json missing timestamp field"
      warnings=$((warnings + 1))
    fi
  else
    echo "[$GATE_NAME] FAIL: metadata.json is invalid JSON"
    errors=$((errors + 1))
  fi
else
  echo "[$GATE_NAME] WARN: metadata.json not found (recommended for SOC 2)"
  warnings=$((warnings + 1))
fi

# Check 3: gate-results directory
if [[ -d "$EVIDENCE_DIR/gate-results" ]]; then
  result_count=$(find "$EVIDENCE_DIR/gate-results" -type f 2>/dev/null | wc -l | tr -d ' ')
  echo "[$GATE_NAME] PASS: gate-results/ contains $result_count file(s)"
else
  echo "[$GATE_NAME] WARN: gate-results/ directory not found"
  warnings=$((warnings + 1))
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
  echo "[$GATE_NAME] PASS: Evidence bundle validation complete"
  exit 0
fi
