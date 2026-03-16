#!/usr/bin/env bash
# VibeOS Plugin — Post-Deploy Smoke Test Gate
# Runs basic endpoint checks after deployment.
#
# Usage:
#   bash scripts/smoke-test.sh
#
# Environment:
#   SMOKE_ENDPOINTS — space-separated URLs to test (required)
#   SMOKE_TIMEOUT   — request timeout in seconds (default: 10)
#
# Exit codes:
#   0 = All endpoints responded successfully
#   1 = One or more endpoints failed
#   2 = No endpoints configured (skip)
set -euo pipefail

FRAMEWORK_VERSION="2.0.0"
GATE_NAME="smoke-test"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/smoke-test.sh

Environment:
  SMOKE_ENDPOINTS  Space-separated URLs to test (required)
  SMOKE_TIMEOUT    Request timeout in seconds (default: 10)

Example:
  SMOKE_ENDPOINTS="https://api.example.com/health https://api.example.com/ready" \
    bash scripts/smoke-test.sh
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] Post-Deploy Smoke Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

SMOKE_TIMEOUT="${SMOKE_TIMEOUT:-10}"

if [[ -z "${SMOKE_ENDPOINTS:-}" ]]; then
  echo "[$GATE_NAME] SKIP: No SMOKE_ENDPOINTS configured"
  echo "[$GATE_NAME] SKIP: Set SMOKE_ENDPOINTS to enable post-deploy smoke tests"
  exit 0
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "[$GATE_NAME] WARN: curl not available"
  echo "[$GATE_NAME] SKIP: Cannot run smoke tests without curl"
  exit 0
fi

read -ra endpoints <<< "$SMOKE_ENDPOINTS"
passed=0
failed=0
total=${#endpoints[@]}

for url in "${endpoints[@]}"; do
  echo -n "  Testing $url ... "

  http_code=$(curl -sf --max-time "$SMOKE_TIMEOUT" -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")

  if [[ "$http_code" -ge 200 && "$http_code" -lt 400 ]]; then
    echo "OK ($http_code)"
    passed=$((passed + 1))
  else
    echo "FAIL ($http_code)"
    failed=$((failed + 1))
  fi
done

echo ""
if [[ $failed -gt 0 ]]; then
  echo "[$GATE_NAME] FAIL: $failed/$total endpoint(s) failed smoke test"
  exit 1
else
  echo "[$GATE_NAME] PASS: All $total endpoint(s) responded successfully"
  exit 0
fi
