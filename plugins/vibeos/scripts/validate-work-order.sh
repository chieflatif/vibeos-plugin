#!/usr/bin/env bash
# VibeOS Plugin — Work Order Validation Gate
# Checks that a WO file has essential sections and required audit checkpoints.
#
# Usage:
#   bash scripts/validate-work-order.sh <WO_NUMBER>
#   bash scripts/validate-work-order.sh 001
#
# Environment:
#   WO_DIR              — directory containing work order files (default: docs/planning)
#   WO_VALIDATION_MODE  — basic | entry | completion (default: basic)
#
# Exit codes:
#   0 = All required sections present (or no WO number provided)
#   1 = Missing required sections
#   2 = WO file not found or invalid arguments
set -euo pipefail

FRAMEWORK_VERSION="2.0.0"
GATE_NAME="validate-work-order"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    echo "Usage: bash scripts/validate-work-order.sh <WO_NUMBER>"
    echo ""
    echo "Environment:"
    echo "  WO_DIR              Directory containing WO files (default: docs/planning)"
    echo "  WO_VALIDATION_MODE  basic | entry | completion (default: basic)"
    echo ""
    echo "Validates that a WO file has required sections:"
    echo "  - Objective or Scope"
    echo "  - Acceptance Criteria or Definition of Done"
    echo "  - Anchor Alignment"
    echo "  - Research & Freshness"
    echo "  - Approved Deviations"
    echo "  - Prompt engineering profile (or explicit N/A)"
    echo "  - Test Strategy (TDD: required before implementation)"
    echo "  - Tasks or Phase"
    echo "  - Status field"
    echo ""
    echo "Validation modes:"
    echo "  basic       Core WO structure only"
    echo "  entry       Requires planning + pre-implementation audits complete"
    echo "  completion  Requires planning + pre-implementation + pre-commit audits complete"
    exit 0
fi

# Graceful skip if no WO number provided via arg or env
WO_NUMBER_INPUT="${1:-${WO_NUMBER:-}}"
if [[ -z "$WO_NUMBER_INPUT" || "$WO_NUMBER_INPUT" == '$WO_NUMBER' ]]; then
    echo "[$GATE_NAME] SKIP: No WO number provided — skipping WO validation"
    exit 0
fi

WO_NUMBER="$WO_NUMBER_INPUT"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WO_VALIDATION_MODE="${WO_VALIDATION_MODE:-basic}"

# Resolve WO directory
WO_DIR="${WO_DIR:-docs/planning}"
WO_BASE="$PROJECT_ROOT/$WO_DIR"

if [[ ! -d "$WO_BASE" ]]; then
    echo "[$GATE_NAME] WARN: WO directory not found: $WO_BASE"
    echo "[$GATE_NAME] SKIP: Set WO_DIR to your work order directory"
    exit 0
fi

# Find the WO file (try common patterns)
WO_FILE=""
for candidate in \
    "$WO_BASE/WO-${WO_NUMBER}.md" \
    "$WO_BASE"/WO-"${WO_NUMBER}"*.md \
    "$WO_BASE"/WO-*-"${WO_NUMBER}"*.md; do
    if [[ -f "$candidate" ]]; then
        WO_FILE="$candidate"
        break
    fi
done

if [[ -z "$WO_FILE" ]]; then
    echo "[$GATE_NAME] FAIL: No WO file found for WO-${WO_NUMBER} in $WO_BASE"
    exit 2
fi

echo "[$GATE_NAME] Validating: $WO_FILE"

content=$(cat "$WO_FILE")
errors=()

section_block() {
    local heading="$1"
    printf '%s\n' "$content" | awk -v heading="$heading" '
        index(tolower($0), tolower(heading)) > 0 { flag=1; next }
        /^### / && flag { exit }
        flag { print }
    '
}

# For ##-level sections (Test Strategy, Evidence) — stop at next ##, not ###
section_block_h2() {
    local heading="$1"
    printf '%s\n' "$content" | awk -v heading="$heading" '
        index(tolower($0), tolower(heading)) > 0 && /^##[[:space:]]/ { flag=1; next }
        /^##[[:space:]]/ && flag { exit }
        flag { print }
    '
}

require_audit_complete() {
    local heading="$1"
    local label="$2"
    local block
    block="$(section_block "$heading")"
    if [[ -z "$block" ]]; then
        errors+=("Missing '${label}' section")
        return
    fi
    if ! printf '%s\n' "$block" | grep -qiE 'Audit Status:\s*complete'; then
        errors+=("'${label}' must have 'Audit Status: complete'")
    fi
}

# Check 1: Objective or Scope section
if ! echo "$content" | grep -qiE '^#{1,3}\s+(Objective|Scope|Goal)'; then
    errors+=("Missing 'Objective', 'Scope', or 'Goal' section")
fi

# Check 2: Acceptance Criteria or Definition of Done
if ! echo "$content" | grep -qiE '^#{1,3}\s+(Acceptance Criteria|Definition of Done|DoD|Success Criteria)'; then
    errors+=("Missing 'Acceptance Criteria' or 'Definition of Done' section")
fi

# Check 3: Tasks or Phase section
if ! echo "$content" | grep -qiE '^#{1,3}\s+(Tasks|Phase|Implementation|Deliverables)'; then
    errors+=("Missing 'Tasks', 'Phase', or 'Implementation' section")
fi

# Check 4: Status field (in YAML frontmatter or as a heading/field)
if ! echo "$content" | grep -qiE '(^status:|^#{1,3}\s+Status|Status:\s+)'; then
    errors+=("Missing 'status' field")
fi

# Check 5: Test Strategy section (TDD — required for code WOs; can be waived for docs/config-only)
anchor_alignment_block="$(section_block_h2 "Anchor Alignment")"
research_freshness_block="$(section_block_h2 "Research & Freshness")"
approved_deviations_block="$(section_block_h2 "Approved Deviations")"

if [[ -z "$anchor_alignment_block" ]]; then
    errors+=("Missing 'Anchor Alignment' section")
elif ! echo "$anchor_alignment_block" | grep -qiE '(product promise|core workflow|experience|engineering principles)'; then
    errors+=("'Anchor Alignment' must explain how the WO supports the product promise, experience, or engineering principles")
fi

if [[ -z "$research_freshness_block" ]]; then
    errors+=("Missing 'Research & Freshness' section")
elif ! echo "$research_freshness_block" | grep -qiE '(Current evidence required|Why freshness matters|Sources to verify|Last verified on|Prompt engineering profile)'; then
    errors+=("'Research & Freshness' must include evidence requirement, source, verification details, and prompt engineering profile (or explicit N/A)")
elif ! echo "$research_freshness_block" | grep -qiE 'Prompt engineering profile'; then
    errors+=("'Research & Freshness' must include a 'Prompt engineering profile' line (use a profile name or explicit N/A)")
fi

if [[ -z "$approved_deviations_block" ]]; then
    errors+=("Missing 'Approved Deviations' section")
elif ! echo "$approved_deviations_block" | grep -qiE '(Known deviations|None|shortcut|deviation)'; then
    errors+=("'Approved Deviations' must state the known deviations or explicitly say 'None'")
fi

# Check 6: Test Strategy section (TDD — required for code WOs; can be waived for docs/config-only)
test_strategy_block="$(section_block_h2 "Test Strategy")"
test_requirement_waived=false
if [[ -z "$test_strategy_block" ]]; then
    errors+=("Missing 'Test Strategy' section — define tests or explicitly waive (e.g. N/A — documentation-only)")
elif echo "$test_strategy_block" | grep -qiE '(N/A|waived|documentation-only|docs-only|no code changes|config-only|no tests required)'; then
    # Explicit waiver — must state reason (documentation, config, etc.)
    test_requirement_waived=true
elif [[ "$WO_VALIDATION_MODE" == "entry" || "$WO_VALIDATION_MODE" == "completion" ]]; then
    # Must have substantive content (not just placeholders)
    non_placeholder=$(printf '%s\n' "$test_strategy_block" | grep -v '^\s*$' | grep -v '^\s*<!--' | grep -v '^\s*-\s*$' | grep -v '^\s*$' || true)
    if [[ -z "$non_placeholder" ]] || [[ $(printf '%s\n' "$non_placeholder" | wc -l | tr -d ' ') -lt 2 ]]; then
        errors+=("'Test Strategy' must have substantive content — or explicitly waive (e.g. N/A — documentation-only)")
    fi
fi

# Check 7: For completion — Evidence must reference tests (unless waived)
if [[ "$WO_VALIDATION_MODE" == "completion" ]] && [[ "$test_requirement_waived" != "true" ]]; then
    evidence_block="$(section_block_h2 "Evidence")"
    if [[ -z "$evidence_block" ]]; then
        errors+=("Missing 'Evidence' section — required for WO completion")
    elif ! echo "$evidence_block" | grep -qiE '(test|pytest|jest|vitest|coverage|gate-runner|wo_exit)'; then
        errors+=("'Evidence' must reference test results or gate output — TDD requires test evidence for completion")
    fi
fi

if [[ "$WO_VALIDATION_MODE" == "completion" ]]; then
    if ! echo "$approved_deviations_block" | grep -qiE '(None|DEV-[0-9]+|deviation)'; then
        errors+=("'Approved Deviations' must either reference logged deviations or explicitly state 'None' before completion")
    fi
fi

if [[ "$WO_VALIDATION_MODE" == "entry" ]]; then
    if echo "$content" | grep -qiE '(^status:|^##\s+Status:)\s*Draft\b'; then
        errors+=("WO must not remain in 'Draft' status when running entry validation")
    fi
    require_audit_complete "Planning Self-Audit" "Planning Self-Audit"
    require_audit_complete "Pre-Implementation Deep Audit" "Pre-Implementation Deep Audit"
fi

if [[ "$WO_VALIDATION_MODE" == "completion" ]]; then
    require_audit_complete "Planning Self-Audit" "Planning Self-Audit"
    require_audit_complete "Pre-Implementation Deep Audit" "Pre-Implementation Deep Audit"
    require_audit_complete "Pre-Commit Audit" "Pre-Commit Audit"
fi

if [[ "$WO_VALIDATION_MODE" != "basic" && "$WO_VALIDATION_MODE" != "entry" && "$WO_VALIDATION_MODE" != "completion" ]]; then
    echo "[$GATE_NAME] FAIL: Unsupported WO_VALIDATION_MODE '$WO_VALIDATION_MODE'"
    exit 2
fi

if [[ ${#errors[@]} -gt 0 ]]; then
    echo "[$GATE_NAME] FAIL: WO-${WO_NUMBER} validation failed (${#errors[@]} issue(s)):"
    for err in "${errors[@]}"; do
        echo "  - $err"
    done
    exit 1
fi

echo "[$GATE_NAME] PASS: WO-${WO_NUMBER} passed '$WO_VALIDATION_MODE' validation"
exit 0
