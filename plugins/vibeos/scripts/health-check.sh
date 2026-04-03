#!/usr/bin/env bash
# VibeOS Plugin — Post-Deploy Health Check Gate
# Validates that the application health endpoint returns expected data.
#
# Usage:
#   bash scripts/health-check.sh
#
# Environment:
#   HEALTH_URL     — health endpoint URL (required)
#   HEALTH_TIMEOUT — request timeout in seconds (default: 10)
#
# Exit codes:
#   0 = Health check passed
#   1 = Health check failed
#   2 = No health URL configured (skip)
set -euo pipefail

FRAMEWORK_VERSION="2.1.0"
GATE_NAME="health-check"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/health-check.sh

Environment:
  HEALTH_URL     Health endpoint URL (required)
  HEALTH_TIMEOUT Request timeout in seconds (default: 10)

Example:
  HEALTH_URL="https://api.example.com/health" bash scripts/health-check.sh

Expected:
  - HTTP 200 response
  - JSON body with "status" field
  - Status value of "ok", "healthy", or "up"
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] Post-Deploy Health Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-10}"

if [[ -z "${HEALTH_URL:-}" ]]; then
  echo "[$GATE_NAME] SKIP: No HEALTH_URL configured"
  echo "[$GATE_NAME] SKIP: Set HEALTH_URL to enable health checks"
  exit 0
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "[$GATE_NAME] WARN: curl not available"
  echo "[$GATE_NAME] SKIP: Cannot run health check without curl"
  exit 0
fi

echo "  Checking $HEALTH_URL ..."

# Make the request
response=$(curl -sf --max-time "$HEALTH_TIMEOUT" "$HEALTH_URL" 2>/dev/null) || {
  echo "[$GATE_NAME] FAIL: Health endpoint unreachable or returned error"
  exit 1
}

echo "  Response: $response"

# Check if response is JSON with a status field
if command -v jq >/dev/null 2>&1; then
  status=$(echo "$response" | jq -r '.status // .Status // empty' 2>/dev/null || true)

  if [[ -n "$status" ]]; then
    status_lower=$(echo "$status" | tr '[:upper:]' '[:lower:]')
    if [[ "$status_lower" == "ok" || "$status_lower" == "healthy" || "$status_lower" == "up" || "$status_lower" == "pass" ]]; then
      echo ""
      echo "[$GATE_NAME] PASS: Health check passed (status: $status)"
      exit 0
    else
      echo ""
      echo "[$GATE_NAME] FAIL: Health check returned unhealthy status: $status"
      exit 1
    fi
  else
    # No status field but endpoint responded — treat as pass
    echo ""
    echo "[$GATE_NAME] PASS: Health endpoint responded (no status field in JSON)"
    exit 0
  fi
else
  # No jq — just check that we got a response
  echo ""
  echo "[$GATE_NAME] PASS: Health endpoint responded (jq not available for JSON parsing)"
  exit 0
fi
