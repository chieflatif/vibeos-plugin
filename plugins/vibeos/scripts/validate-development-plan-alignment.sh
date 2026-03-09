#!/usr/bin/env bash
# VibeOS Plugin — Development Plan Alignment Gate
# Ensures DEVELOPMENT-PLAN.md, WO-INDEX.md, and WO-*.md files stay in sync.
# Prevents drift: plan status must match WO-INDEX and WO files.
#
# Usage: bash scripts/validate-development-plan-alignment.sh
#
# Environment:
#   WO_DIR  — directory for planning docs (default: docs/planning)
#
# Exit codes: 0 = aligned, 1 = drift detected, 2 = missing files / skip
set -euo pipefail

FRAMEWORK_VERSION="1.0.0"
GATE_NAME="validate-development-plan-alignment"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WO_DIR="${WO_DIR:-docs/planning}"
PLAN_FILE="$PROJECT_ROOT/$WO_DIR/DEVELOPMENT-PLAN.md"
INDEX_FILE="$PROJECT_ROOT/$WO_DIR/WO-INDEX.md"

if [[ ! -f "$PLAN_FILE" ]]; then
    echo "[$GATE_NAME] SKIP: DEVELOPMENT-PLAN.md not found at $PLAN_FILE"
    exit 0
fi

if [[ ! -f "$INDEX_FILE" ]]; then
    echo "[$GATE_NAME] FAIL: WO-INDEX.md not found — DEVELOPMENT-PLAN requires WO-INDEX"
    exit 2
fi

echo "[$GATE_NAME] Checking alignment: DEVELOPMENT-PLAN ↔ WO-INDEX ↔ WO files"
errors=()

# --- Extract all WO numbers from plan (from tables or any WO-XXX mention) ---
plan_wos=()
while IFS= read -r wo; do
    [[ -n "$wo" ]] && plan_wos+=("$wo")
done < <(grep -oE 'WO-[0-9]+' "$PLAN_FILE" | sort -u)

# --- Extract "Next:" WO ---
next_wo=""
if next_line=$(grep -E '^\*\*Next:\*\*|^Next:|Next Work Order' "$PLAN_FILE" 2>/dev/null | head -1); then
    next_wo=$(echo "$next_line" | grep -oE 'WO-[0-9]+' | head -1 || true)
fi

# --- Extract WOs from WO-INDEX ---
index_all=()
index_completed=()
# Split by section: Active vs Completed
in_active=true
in_completed=false
while IFS= read -r line; do
    if echo "$line" | grep -qi "Completed Work Orders"; then
        in_completed=true
        in_active=false
    elif echo "$line" | grep -qi "Active Work Orders"; then
        in_active=true
        in_completed=false
    fi
    for wo in $(echo "$line" | grep -oE 'WO-[0-9]+'); do
        index_all+=("$wo")
        $in_completed && index_completed+=("$wo")
    done
done < "$INDEX_FILE"

# Simpler: get all WOs from index
index_all=()
for wo in $(grep -oE 'WO-[0-9]+' "$INDEX_FILE" | sort -u); do
    index_all+=("$wo")
done

# Completed = WOs in the Completed Work Orders table (between ## Completed and next ## or ---)
index_completed=()
if grep -q "Completed Work Orders" "$INDEX_FILE"; then
    while IFS= read -r wo; do
        [[ -n "$wo" ]] && index_completed+=("$wo")
    done < <(awk '/Completed Work Orders/,/^## |^---$/ { print }' "$INDEX_FILE" | grep -oE 'WO-[0-9]+' | sort -u)
fi

# --- Check 1: Every WO in plan must exist in WO-INDEX ---
for wo in "${plan_wos[@]}"; do
    if ! echo " ${index_all[*]} " | grep -q " $wo "; then
        errors+=("DEVELOPMENT-PLAN lists $wo but it is not in WO-INDEX")
    fi
done

# --- Check 2: Every WO in plan must have a WO-*.md file ---
for wo in "${plan_wos[@]}"; do
    num="${wo#WO-}"
    found=false
    for f in "$PROJECT_ROOT/$WO_DIR"/WO-"${num}.md" "$PROJECT_ROOT/$WO_DIR"/WO-"${num}"-*.md "$PROJECT_ROOT/$WO_DIR"/WO-*-"${num}.md"; do
        [[ -f "$f" ]] && found=true && break
    done
    [[ -f "$PROJECT_ROOT/$WO_DIR/WO-${num}.md" ]] && found=true
    if ! $found; then
        errors+=("DEVELOPMENT-PLAN lists $wo but no WO-${num}.md file in $WO_DIR")
    fi
done

# --- Check 3: WO files marked Complete must be in WO-INDEX Completed ---
for wo in "${plan_wos[@]}"; do
    num="${wo#WO-}"
    wo_file="$PROJECT_ROOT/$WO_DIR/WO-${num}.md"
    [[ -f "$wo_file" ]] || continue
    wo_status=$(grep -iE '^Status:|^## Status:' "$wo_file" 2>/dev/null | head -1 | sed 's/.*:\s*//' | xargs || true)
    if echo "$wo_status" | grep -qiE 'Complete|Shipped'; then
        if ! echo " ${index_completed[*]} " | grep -q " $wo "; then
            errors+=("$wo has Status Complete but is not in WO-INDEX Completed table")
        fi
    fi
done

# --- Check 4: Next WO must exist, have a file, and not be Complete ---
if [[ -n "$next_wo" ]]; then
    if ! echo " ${plan_wos[*]} " | grep -q " $next_wo "; then
        errors+=("'Next' points to $next_wo but it is not in DEVELOPMENT-PLAN")
    else
        num="${next_wo#WO-}"
        wo_file="$PROJECT_ROOT/$WO_DIR/WO-${num}.md"
        if [[ ! -f "$wo_file" ]]; then
            errors+=("'Next' points to $next_wo but WO-${num}.md not found")
        else
            wo_status=$(grep -iE '^Status:|^## Status:' "$wo_file" 2>/dev/null | head -1 | sed 's/.*:\s*//' | xargs || true)
            if echo "$wo_status" | grep -qiE 'Complete|Shipped'; then
                errors+=("'Next' points to $next_wo but it is already Complete — update DEVELOPMENT-PLAN Next to the next pending WO")
            fi
        fi
    fi
fi

# --- Check 5: WO-INDEX Completed WOs must be in plan ---
for wo in "${index_completed[@]}"; do
    if ! echo " ${plan_wos[*]} " | grep -q " $wo "; then
        errors+=("$wo is in WO-INDEX Completed but not in DEVELOPMENT-PLAN")
    fi
done

if [[ ${#errors[@]} -gt 0 ]]; then
    echo "[$GATE_NAME] FAIL: Alignment drift (${#errors[@]} issue(s)):"
    for err in "${errors[@]}"; do
        echo "  - $err"
    done
    echo ""
    echo "[$GATE_NAME] Fix: Update DEVELOPMENT-PLAN.md and WO-INDEX.md so they match. When a WO completes: (1) mark it Complete in plan table, (2) move it to WO-INDEX Completed, (3) set Next to the next pending WO."
    exit 1
fi

echo "[$GATE_NAME] PASS: DEVELOPMENT-PLAN, WO-INDEX, and WO files aligned"
exit 0
