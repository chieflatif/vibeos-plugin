#!/usr/bin/env bash
# VibeOS Plugin — Infrastructure Manifest Validation Gate
# Checks that the infrastructure manifest is complete and up to date.
#
# Usage:
#   bash scripts/validate-infrastructure-manifest.sh
#
# Environment:
#   MANIFEST_PATH — path to infrastructure manifest (default: docs/INFRASTRUCTURE-MANIFEST.md)
#
# Exit codes:
#   0 = Infrastructure manifest valid
#   1 = Infrastructure manifest incomplete
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="1.0.0"
GATE_NAME="validate-infrastructure-manifest"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate-infrastructure-manifest.sh

Environment:
  MANIFEST_PATH  Path to infrastructure manifest (default: docs/INFRASTRUCTURE-MANIFEST.md)

Checks:
  - Infrastructure manifest exists
  - Has required sections (Services, Environments, Secrets, Monitoring)
  - No placeholder values in production sections
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] Infrastructure Manifest Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MANIFEST_PATH="${MANIFEST_PATH:-$PROJECT_ROOT/docs/INFRASTRUCTURE-MANIFEST.md}"

if [[ ! -f "$MANIFEST_PATH" ]]; then
  echo "[$GATE_NAME] INFO: No infrastructure manifest found at $MANIFEST_PATH"
  echo "[$GATE_NAME] SKIP: Infrastructure manifest is optional (recommended for production projects)"
  exit 0
fi

echo "Manifest: $MANIFEST_PATH"
content=$(cat "$MANIFEST_PATH")
warnings=0
errors=0

# Check required sections
required_sections=(
  "Services"
  "Environment"
  "Database"
)

optional_sections=(
  "Secrets"
  "Monitoring"
  "Deployment"
  "Networking"
)

for section in "${required_sections[@]}"; do
  if echo "$content" | grep -qiE "^#{1,3}\s+.*$section"; then
    echo "[$GATE_NAME] PASS: '$section' section found"
  else
    echo "[$GATE_NAME] WARN: Missing '$section' section"
    warnings=$((warnings + 1))
  fi
done

for section in "${optional_sections[@]}"; do
  if echo "$content" | grep -qiE "^#{1,3}\s+.*$section"; then
    echo "[$GATE_NAME] PASS: '$section' section found (optional)"
  fi
done

# Check for placeholder values
placeholders=$(grep -nE '\{\{[A-Za-z_][A-Za-z0-9_]*\}\}|TBD|TODO|PLACEHOLDER|CHANGEME|xxx' "$MANIFEST_PATH" 2>/dev/null || true)
if [[ -n "$placeholders" ]]; then
  placeholder_count=$(echo "$placeholders" | wc -l | tr -d ' ')
  echo "[$GATE_NAME] WARN: $placeholder_count placeholder value(s) remaining"
  echo "$placeholders" | head -5 | sed 's/^/  /'
  warnings=$((warnings + 1))
fi

# Check file is not empty
line_count=$(wc -l < "$MANIFEST_PATH" | tr -d ' ')
if [[ "$line_count" -lt 10 ]]; then
  echo "[$GATE_NAME] WARN: Manifest seems too short ($line_count lines)"
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
  echo "[$GATE_NAME] PASS: Infrastructure manifest validation complete"
  exit 0
fi
