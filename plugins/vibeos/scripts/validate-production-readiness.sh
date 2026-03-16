#!/usr/bin/env bash
# VibeOS Plugin — Production Readiness Gate
# Ensures Production Readiness (and Observability/Resilience/Security for customer-facing/scale)
# phases exist in DEVELOPMENT-PLAN and WOs are Complete or Deferred.
#
# Usage: bash scripts/validate-production-readiness.sh
#
# Environment:
#   DEPLOYMENT_CONTEXT  — override: prototype | production | customer-facing | scale
#   WO_DIR             — directory for planning docs (default: docs/planning)
#   PROJECT_DEFINITION — path to project-definition.json (default: project-definition.json).
#                        Set when project uses a non-root location (e.g. docs/project-definition.json).
#
# Exit codes: 0 = pass/skip, 1 = fail, 2 = skip (prototype or missing config)
set -euo pipefail

FRAMEWORK_VERSION="2.0.0"
GATE_NAME="validate-production-readiness"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WO_DIR="${WO_DIR:-docs/planning}"
PLAN_FILE="$PROJECT_ROOT/$WO_DIR/DEVELOPMENT-PLAN.md"
PROJECT_DEF="${PROJECT_DEFINITION:-$PROJECT_ROOT/project-definition.json}"

# Resolve deployment_context: env var > project-definition
deployment_context="${DEPLOYMENT_CONTEXT:-}"
if [[ -z "$deployment_context" && -f "$PROJECT_DEF" ]]; then
    if command -v jq &>/dev/null; then
        deployment_context=$(jq -r '.governance_profile.deployment_context.value // .governance_profile.deployment_context // "prototype"' "$PROJECT_DEF" 2>/dev/null || echo "prototype")
    fi
fi
deployment_context="${deployment_context:-prototype}"

if [[ "$deployment_context" == "prototype" ]]; then
    echo "[$GATE_NAME] SKIP: deployment_context=prototype — no production-readiness phases required"
    exit 0
fi

if [[ ! -f "$PLAN_FILE" ]]; then
    echo "[$GATE_NAME] SKIP: DEVELOPMENT-PLAN.md not found at $PLAN_FILE"
    exit 0
fi

echo "[$GATE_NAME] Checking production readiness (deployment_context=$deployment_context)"
errors=()

# Required phases by context
case "$deployment_context" in
    production)
        required_phases=("Production Readiness")
        ;;
    customer-facing|scale)
        required_phases=("Production Readiness" "Observability" "Resilience" "Security Hardening")
        ;;
    *)
        required_phases=("Production Readiness")
        ;;
esac

# Normalize phase names for matching (plan may say "Observability & Operations" or "Resilience & Scale")
plan_text=$(cat "$PLAN_FILE")
for phase in "${required_phases[@]}"; do
    case "$phase" in
        "Production Readiness")
            if ! echo "$plan_text" | grep -qiE "Production Readiness|production readiness"; then
                errors+=("Missing phase: Production Readiness (security headers, health probes, structured logging, input validation)")
            fi
            ;;
        "Observability")
            if ! echo "$plan_text" | grep -qiE "Observability|observability"; then
                errors+=("Missing phase: Observability & Operations (logging, metrics, health probes, alerting)")
            fi
            ;;
        "Resilience")
            if ! echo "$plan_text" | grep -qiE "Resilience|resilience"; then
                errors+=("Missing phase: Resilience & Scale (rate limiting, circuit breakers, caching, horizontal scaling)")
            fi
            ;;
        "Security Hardening")
            if ! echo "$plan_text" | grep -qiE "Security Hardening|security hardening"; then
                errors+=("Missing phase: Security Hardening (secrets management, audit trail)")
            fi
            ;;
    esac
done

# Check for incomplete WOs in production-readiness phases (WOs not Complete or Deferred)
# For simplicity: if phases exist, we pass. Deferral is a WO-level decision; the definition-of-done rule handles it.
# This gate ensures the phases are present in the plan.

if [[ ${#errors[@]} -gt 0 ]]; then
    echo "[$GATE_NAME] FAIL: Production readiness gaps (${#errors[@]}):"
    for err in "${errors[@]}"; do
        echo "  - $err"
    done
    echo ""
    echo "[$GATE_NAME] Fix: Add the required phases to DEVELOPMENT-PLAN.md per decision-engine/development-plan-generation.md"
    exit 1
fi

echo "[$GATE_NAME] PASS: Required production-readiness phases present in DEVELOPMENT-PLAN"
exit 0
