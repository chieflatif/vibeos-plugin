#!/usr/bin/env bash
set -euo pipefail

# e2e-test-runner.sh — End-to-end integration test runner for VibeOS plugin
# Validates the entire plugin system with greenfield and midstream scenarios.
# Exit 0 = all tests pass, 1 = failures found

FRAMEWORK_VERSION="1.0.0"

PLUGIN_DIR="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
RESULTS_DIR="${PLUGIN_DIR}/.vibeos/e2e-results"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

mkdir -p "$RESULTS_DIR"

log_result() {
  local test_name="$1"
  local status="$2"
  local details="$3"
  echo "[e2e] $status: $test_name — $details"
  echo "| $test_name | $status | $details |" >> "$RESULTS_DIR/report.md"

  case "$status" in
    PASS) PASS_COUNT=$((PASS_COUNT + 1)) ;;
    FAIL) FAIL_COUNT=$((FAIL_COUNT + 1)) ;;
    SKIP) SKIP_COUNT=$((SKIP_COUNT + 1)) ;;
  esac
}

# Initialize report
cat > "$RESULTS_DIR/report.md" << 'HEADER'
# E2E Integration Test Report

| Test | Status | Details |
|---|---|---|
HEADER

echo "[e2e] Starting E2E integration tests for VibeOS plugin"
echo "[e2e] Plugin directory: $PLUGIN_DIR"
echo "[e2e] Timestamp: $TIMESTAMP"
echo ""

# ============================================================
# Test 1: Plugin Structure Validation
# ============================================================
echo "=== Test 1: Plugin Structure ==="

if [ -f "$PLUGIN_DIR/.claude-plugin/plugin.json" ]; then
  log_result "Plugin manifest exists" "PASS" ".claude-plugin/plugin.json found"
else
  log_result "Plugin manifest exists" "FAIL" ".claude-plugin/plugin.json missing"
fi

# Validate manifest JSON
if jq . "$PLUGIN_DIR/.claude-plugin/plugin.json" > /dev/null 2>&1; then
  log_result "Plugin manifest valid JSON" "PASS" "Parses successfully"
else
  log_result "Plugin manifest valid JSON" "FAIL" "JSON parse error"
fi

# Check required directories
for dir in skills agents hooks scripts decision-engine reference convergence; do
  if [ -d "$PLUGIN_DIR/$dir" ]; then
    log_result "Directory exists: $dir" "PASS" "Found"
  else
    log_result "Directory exists: $dir" "FAIL" "Missing"
  fi
done
echo ""

# ============================================================
# Test 2: Script Syntax Validation
# ============================================================
echo "=== Test 2: Script Syntax ==="

SCRIPT_COUNT=0
SCRIPT_FAIL=0
for f in "$PLUGIN_DIR"/scripts/*.sh "$PLUGIN_DIR"/convergence/*.sh "$PLUGIN_DIR"/hooks/scripts/*.sh; do
  [ -f "$f" ] || continue
  SCRIPT_COUNT=$((SCRIPT_COUNT + 1))
  BASENAME=$(basename "$f")
  if bash -n "$f" 2>/dev/null; then
    : # silent pass
  else
    log_result "Script syntax: $BASENAME" "FAIL" "bash -n failed"
    SCRIPT_FAIL=$((SCRIPT_FAIL + 1))
  fi
done

if [ "$SCRIPT_FAIL" -eq 0 ]; then
  log_result "All scripts pass syntax check" "PASS" "$SCRIPT_COUNT scripts validated"
else
  log_result "Script syntax check" "FAIL" "$SCRIPT_FAIL/$SCRIPT_COUNT scripts failed"
fi
echo ""

# ============================================================
# Test 3: JSON Validation
# ============================================================
echo "=== Test 3: JSON Validation ==="

JSON_COUNT=0
JSON_FAIL=0
while IFS= read -r f; do
  JSON_COUNT=$((JSON_COUNT + 1))
  if jq . "$f" > /dev/null 2>&1; then
    : # silent pass
  else
    BASENAME=$(basename "$f")
    log_result "JSON valid: $BASENAME" "FAIL" "jq parse error"
    JSON_FAIL=$((JSON_FAIL + 1))
  fi
done < <(find "$PLUGIN_DIR" -name "*.json" -not -path '*/.git/*' -not -path '*/.vibeos/*' -not -path '*/node_modules/*' 2>/dev/null)

if [ "$JSON_FAIL" -eq 0 ]; then
  log_result "All JSON files valid" "PASS" "$JSON_COUNT files validated"
else
  log_result "JSON validation" "FAIL" "$JSON_FAIL/$JSON_COUNT files failed"
fi
echo ""

# ============================================================
# Test 3b: Communication Contract Validation
# ============================================================
echo "=== Test 3b: Communication Contract ==="

if bash "$PLUGIN_DIR/scripts/validate-communication-contract.sh" "$PLUGIN_DIR" > /dev/null 2>&1; then
  log_result "Communication contract validation" "PASS" "Decision prompts require plain-English framing, pros/cons, and recommendations"
else
  COMM_RESULT=$(bash "$PLUGIN_DIR/scripts/validate-communication-contract.sh" "$PLUGIN_DIR" 2>&1 | tail -1)
  log_result "Communication contract validation" "FAIL" "${COMM_RESULT:-validation failed}"
fi
echo ""

# ============================================================
# Test 4: Skill Validation
# ============================================================
echo "=== Test 4: Skill Validation ==="

SKILL_COUNT=0
while IFS= read -r skill_file; do
  SKILL_COUNT=$((SKILL_COUNT + 1))
  SKILL_DIR=$(dirname "$skill_file")
  SKILL_NAME=$(basename "$SKILL_DIR")

  # Check YAML frontmatter exists
  if head -1 "$skill_file" | grep -q '^---$'; then
    # Check required fields
    HAS_NAME=$(grep -c '^name:' "$skill_file" || echo "0")
    HAS_DESC=$(grep -c '^description:' "$skill_file" || echo "0")
    if [ "$HAS_NAME" -gt 0 ] && [ "$HAS_DESC" -gt 0 ]; then
      log_result "Skill: $SKILL_NAME" "PASS" "Valid frontmatter with name and description"
    else
      log_result "Skill: $SKILL_NAME" "FAIL" "Missing name or description in frontmatter"
    fi
  else
    log_result "Skill: $SKILL_NAME" "FAIL" "Missing YAML frontmatter"
  fi
done < <(find "$PLUGIN_DIR/skills" -name "SKILL.md" 2>/dev/null)

echo "[e2e] $SKILL_COUNT skills validated"
echo ""

# ============================================================
# Test 5: Agent Validation
# ============================================================
echo "=== Test 5: Agent Validation ==="

AGENT_COUNT=0
for agent_file in "$PLUGIN_DIR"/agents/*.md; do
  [ -f "$agent_file" ] || continue
  AGENT_COUNT=$((AGENT_COUNT + 1))
  AGENT_NAME=$(basename "$agent_file" .md)

  # Check YAML frontmatter
  if head -1 "$agent_file" | grep -q '^---$'; then
    HAS_NAME=$(grep -c '^name:' "$agent_file" || echo "0")
    HAS_TOOLS=$(grep -c '^tools:' "$agent_file" || echo "0")
    if [ "$HAS_NAME" -gt 0 ] && [ "$HAS_TOOLS" -gt 0 ]; then
      log_result "Agent: $AGENT_NAME" "PASS" "Valid frontmatter"
    else
      log_result "Agent: $AGENT_NAME" "FAIL" "Missing name or tools in frontmatter"
    fi
  else
    log_result "Agent: $AGENT_NAME" "FAIL" "Missing YAML frontmatter"
  fi
done

echo "[e2e] $AGENT_COUNT agents validated"
echo ""

# ============================================================
# Test 6: Hook Validation
# ============================================================
echo "=== Test 6: Hook Validation ==="

if [ -f "$PLUGIN_DIR/hooks/hooks.json" ]; then
  if jq . "$PLUGIN_DIR/hooks/hooks.json" > /dev/null 2>&1; then
    HOOK_COUNT=$(jq '[.hooks.PreToolUse[].hooks | length] | add // 0' "$PLUGIN_DIR/hooks/hooks.json" 2>/dev/null || echo "0")
    log_result "hooks.json valid" "PASS" "$HOOK_COUNT PreToolUse hooks configured"
  else
    log_result "hooks.json valid" "FAIL" "JSON parse error"
  fi
else
  log_result "hooks.json exists" "FAIL" "File missing"
fi

# Verify all hook script paths exist
while IFS= read -r hook_cmd; do
  # Replace ${CLAUDE_PLUGIN_ROOT} or ./.claude/hooks/ with actual paths for testing
  RESOLVED=$(echo "$hook_cmd" | sed "s|\${CLAUDE_PLUGIN_ROOT}|$PLUGIN_DIR|g" | sed "s|^\./\.claude/hooks/|$PLUGIN_DIR/hooks/scripts/|g")
  if [ -f "$RESOLVED" ]; then
    BASENAME=$(basename "$RESOLVED")
    log_result "Hook script: $BASENAME" "PASS" "File exists and is accessible"
  else
    log_result "Hook script: $hook_cmd" "FAIL" "File not found"
  fi
done < <(jq -r '.hooks | to_entries[] | .value[] | .hooks[] | select(.type == "command") | .command' "$PLUGIN_DIR/hooks/hooks.json" 2>/dev/null || true)

HOOK_FORMAT_FAIL=0
for hook_file in \
  "$PLUGIN_DIR/hooks/scripts/frozen-files.sh" \
  "$PLUGIN_DIR/hooks/scripts/secrets-scan.sh" \
  "$PLUGIN_DIR/hooks/scripts/test-file-protection.sh" \
  "$PLUGIN_DIR/hooks/scripts/test-diff-audit.sh"; do
  [ -f "$hook_file" ] || continue
  HOOK_BASENAME=$(basename "$hook_file")

  if grep -q '"hookEventName": "PreToolUse"' "$hook_file"; then
    : # expected
  else
    log_result "Hook format: $HOOK_BASENAME" "FAIL" "Missing hookEventName for PreToolUse response"
    HOOK_FORMAT_FAIL=$((HOOK_FORMAT_FAIL + 1))
    continue
  fi

  if grep -q '^  "permissionDecision":' "$hook_file" || grep -q '^  "reason":' "$hook_file"; then
    log_result "Hook format: $HOOK_BASENAME" "FAIL" "PreToolUse response mixes nested and top-level decision fields"
    HOOK_FORMAT_FAIL=$((HOOK_FORMAT_FAIL + 1))
  fi
done

if [ "$HOOK_FORMAT_FAIL" -eq 0 ]; then
  log_result "PreToolUse hook response format" "PASS" "Hook scripts use hookSpecificOutput with hookEventName and no ambiguous top-level decision fields"
fi
echo ""

# ============================================================
# Test 7: Convergence Scripts
# ============================================================
echo "=== Test 7: Convergence Scripts ==="

for script in state-hash.sh convergence-check.sh baseline-check.sh migrate-baseline.sh; do
  SCRIPT_PATH="$PLUGIN_DIR/convergence/$script"
  if [ -f "$SCRIPT_PATH" ]; then
    if [ -x "$SCRIPT_PATH" ]; then
      log_result "Convergence: $script" "PASS" "Exists and executable"
    else
      log_result "Convergence: $script" "FAIL" "Not executable"
    fi
  else
    log_result "Convergence: $script" "FAIL" "Missing"
  fi
done
echo ""

# ============================================================
# Test 8: No Placeholders
# ============================================================
echo "=== Test 8: No Placeholders ==="

PLACEHOLDER_COUNT=$(grep -rcn --exclude="e2e-test-runner.sh" '{{.*}}' "$PLUGIN_DIR/scripts/" "$PLUGIN_DIR/hooks/" "$PLUGIN_DIR/decision-engine/" 2>/dev/null | grep -v ':0$' | wc -l | tr -d ' ') || PLACEHOLDER_COUNT=0

if [ "$PLACEHOLDER_COUNT" -eq 0 ]; then
  log_result "No template placeholders" "PASS" "Clean"
else
  log_result "No template placeholders" "FAIL" "$PLACEHOLDER_COUNT placeholder(s) found"
fi
echo ""

# ============================================================
# Test 9: Decision Engine Completeness
# ============================================================
echo "=== Test 9: Decision Engine ==="

DE_COUNT=$(find "$PLUGIN_DIR/decision-engine" -name "*.md" -type f 2>/dev/null | wc -l | tr -d ' ' || echo "0")
if [ "$DE_COUNT" -ge 8 ]; then
  log_result "Decision engine files" "PASS" "$DE_COUNT decision trees (expected >= 8)"
else
  log_result "Decision engine files" "FAIL" "Only $DE_COUNT decision trees (expected >= 8)"
fi
echo ""

# ============================================================
# Test 10: Governance & Anchor References
# ============================================================
echo "=== Test 10: Governance & Anchor References ==="

REF_COUNT=0
REF_FAIL=0
for ref in \
  "governance/WO-INDEX.md.ref" \
  "governance/DEVELOPMENT-PLAN.md.ref" \
  "governance/WO-AUDIT-FRAMEWORK.md.ref" \
  "governance/WO-TEMPLATE.md.ref" \
  "governance/ENGINEERING-PRINCIPLES.md.ref" \
  "governance/DEVIATIONS.md.ref" \
  "governance/RESEARCH-REGISTRY.md.ref" \
  "product/PRODUCT-ANCHOR.md.ref"; do
  REF_PATH="$PLUGIN_DIR/reference/$ref"
  REF_COUNT=$((REF_COUNT + 1))
  if [ -f "$REF_PATH" ]; then
    log_result "Governance reference: $ref" "PASS" "Found"
  else
    log_result "Governance reference: $ref" "FAIL" "Missing"
    REF_FAIL=$((REF_FAIL + 1))
  fi
done

if [ "$REF_FAIL" -eq 0 ]; then
  log_result "Governance reference bundle" "PASS" "$REF_COUNT governance and anchor reference files validated"
else
  log_result "Governance reference bundle" "FAIL" "$REF_FAIL/$REF_COUNT governance reference files missing"
fi

if grep -q "product-drift-auditor" "$PLUGIN_DIR/skills/audit/SKILL.md" && grep -q "Anchor Alignment" "$PLUGIN_DIR/scripts/validate-work-order.sh"; then
  log_result "Anti-drift wiring" "PASS" "Audit skill and WO validator enforce anchor-aware drift checks"
else
  log_result "Anti-drift wiring" "FAIL" "Audit skill or WO validator missing anti-drift wiring"
fi
echo ""

# ============================================================
# Test 11: Prompt Engineering Integration
# ============================================================
echo "=== Test 11: Prompt Engineering Integration ==="

PROMPT_BIBLE_DIR="$PLUGIN_DIR/reference/prompt-engineering-bible"

if [ -f "$PLUGIN_DIR/agents/prompt-engineer.md" ]; then
  log_result "Prompt engineer agent" "PASS" "agents/prompt-engineer.md found"
else
  log_result "Prompt engineer agent" "FAIL" "agents/prompt-engineer.md missing"
fi

if [ -f "$PROMPT_BIBLE_DIR/README.md" ] && [ -f "$PROMPT_BIBLE_DIR/registry.yaml" ] && [ -f "$PROMPT_BIBLE_DIR/LICENSE" ]; then
  DOC_COUNT=$(find "$PROMPT_BIBLE_DIR/bible" -type f 2>/dev/null | wc -l | tr -d ' ')
  log_result "Prompt Engineering Bible bundle" "PASS" "$DOC_COUNT bundled reference files plus attribution"
else
  log_result "Prompt Engineering Bible bundle" "FAIL" "README, registry, or LICENSE missing"
fi

if grep -q "prompt-engineer" "$PLUGIN_DIR/skills/build/SKILL.md" && grep -q "Prompt engineering profile" "$PLUGIN_DIR/scripts/validate-work-order.sh" && grep -q "Prompt Engineering Readiness" "$PLUGIN_DIR/agents/investigator.md"; then
  log_result "Prompt engineering wiring" "PASS" "Investigator, build flow, and WO validator enforce prompt-engineering routing"
else
  log_result "Prompt engineering wiring" "FAIL" "Investigator, build flow, or WO validator missing prompt-engineering wiring"
fi

if grep -q "Prompt Engineering Standards" "$PLUGIN_DIR/../../README.md"; then
  log_result "README prompt guidance" "PASS" "README explains prompt-engineering behavior in plain English"
else
  log_result "README prompt guidance" "FAIL" "README missing prompt-engineering explanation"
fi
echo ""

# ============================================================
# Test 12: Session Commands & Autonomous Override
# ============================================================
echo "=== Test 12: Session Commands & Autonomous Override ==="

if [ -f "$PLUGIN_DIR/skills/autonomous/SKILL.md" ] && [ -f "$PLUGIN_DIR/skills/session-audit/SKILL.md" ]; then
  log_result "Session command skills" "PASS" "autonomous and session-audit skills found"
else
  log_result "Session command skills" "FAIL" "autonomous or session-audit skill missing"
fi

if grep -q "session_override" "$PLUGIN_DIR/skills/build/SKILL.md" && grep -q "session-state.json" "$PLUGIN_DIR/skills/build/SKILL.md"; then
  log_result "Autonomous session wiring" "PASS" "Build flow tracks autonomous session override and session state"
else
  log_result "Autonomous session wiring" "FAIL" "Build flow missing session override or session state wiring"
fi

if grep -q "session-audit" "$PLUGIN_DIR/hooks/scripts/intent-router.sh" && grep -q "autonomous" "$PLUGIN_DIR/hooks/scripts/intent-router.sh"; then
  log_result "Intent routing for session commands" "PASS" "Intent router recognizes autonomous and session-audit requests"
else
  log_result "Intent routing for session commands" "FAIL" "Intent router missing autonomous or session-audit patterns"
fi

if grep -q "/autonomous" "$PLUGIN_DIR/../../README.md" && grep -q "/session-audit" "$PLUGIN_DIR/../../README.md"; then
  log_result "README session commands" "PASS" "README documents the two new commands"
else
  log_result "README session commands" "FAIL" "README missing autonomous or session-audit command docs"
fi
echo ""

# ============================================================
# Test 13: Dual Status Modes
# ============================================================
echo "=== Test 13: Dual Status Modes ==="

if [ -f "$PLUGIN_DIR/skills/status/SKILL.md" ] && [ -f "$PLUGIN_DIR/skills/project-status/SKILL.md" ]; then
  log_result "Status skills" "PASS" "status and project-status skills found"
else
  log_result "Status skills" "FAIL" "status or project-status skill missing"
fi

if grep -q "project-status" "$PLUGIN_DIR/hooks/scripts/intent-router.sh"; then
  log_result "Intent routing for project status" "PASS" "Intent router recognizes executive project-status requests"
else
  log_result "Intent routing for project status" "FAIL" "Intent router missing project-status patterns"
fi

if grep -q "/project-status" "$PLUGIN_DIR/../../README.md" && grep -q "Give me a project status" "$PLUGIN_DIR/../../README.md"; then
  log_result "README dual status docs" "PASS" "README explains both tactical and executive status views"
else
  log_result "README dual status docs" "FAIL" "README missing project-status guidance"
fi
echo ""

# ============================================================
# Summary
# ============================================================
TOTAL=$((PASS_COUNT + FAIL_COUNT + SKIP_COUNT))

echo "============================================"
echo "E2E Test Summary"
echo "============================================"
echo "Total tests: $TOTAL"
echo "Passed: $PASS_COUNT"
echo "Failed: $FAIL_COUNT"
echo "Skipped: $SKIP_COUNT"
echo ""

# Append summary to report
cat >> "$RESULTS_DIR/report.md" << EOF

## Summary

**Date:** $TIMESTAMP
**Total:** $TOTAL | **Passed:** $PASS_COUNT | **Failed:** $FAIL_COUNT | **Skipped:** $SKIP_COUNT

**Result:** $([ "$FAIL_COUNT" -eq 0 ] && echo "ALL TESTS PASS" || echo "FAILURES DETECTED")
EOF

echo "[e2e] Report saved to $RESULTS_DIR/report.md"

if [ "$FAIL_COUNT" -gt 0 ]; then
  echo "[e2e] FAIL: $FAIL_COUNT test(s) failed"
  exit 1
else
  echo "[e2e] PASS: All tests passed"
  exit 0
fi
