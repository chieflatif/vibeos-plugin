#!/usr/bin/env bash
# VibeOS Plugin — Session Start Validation Gate
# Ensures critical documentation and services are available at session start.
#
# Usage:
#   bash scripts/validate-session-start.sh
#
# Environment:
#   REQUIRED_DOCS  — space-separated required doc files (default: CLAUDE.md)
#   HEALTH_URL     — URL to check service health (optional)
#   PROJECT_ROOT   — project root (default: auto-detect)
#
# Exit codes:
#   0 = Session start checks passed
#   1 = Critical session start issues
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="1.0.0"
GATE_NAME="validate-session-start"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate-session-start.sh

Environment:
  REQUIRED_DOCS  Space-separated required doc files (default: CLAUDE.md)
  HEALTH_URL     URL to check service health (optional)
  PROJECT_ROOT   Project root (default: auto-detect)

Checks:
  - Required documentation exists (CLAUDE.md, WO-INDEX.md, etc.)
  - Git repository is clean or has a known branch
  - Health endpoint is reachable (if configured)
  - Quality gate manifest exists
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] Session Start Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"

warnings=0
errors=0

# Check 1: Required documentation
REQUIRED_DOCS="${REQUIRED_DOCS:-CLAUDE.md}"
read -ra doc_list <<< "$REQUIRED_DOCS"

for doc in "${doc_list[@]}"; do
  if [[ -f "$PROJECT_ROOT/$doc" ]]; then
    echo "[$GATE_NAME] PASS: $doc exists"
  else
    echo "[$GATE_NAME] WARN: $doc not found (recommended)"
    warnings=$((warnings + 1))
  fi
done

# Check 2: Git repository status
if git -C "$PROJECT_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  branch=$(git -C "$PROJECT_ROOT" branch --show-current 2>/dev/null || echo "unknown")
  echo "[$GATE_NAME] PASS: Git repository (branch: $branch)"

  # Check for uncommitted changes
  if git -C "$PROJECT_ROOT" diff --quiet 2>/dev/null && git -C "$PROJECT_ROOT" diff --cached --quiet 2>/dev/null; then
    echo "[$GATE_NAME] PASS: Working tree clean"
  else
    echo "[$GATE_NAME] INFO: Uncommitted changes detected (normal for active development)"
  fi
else
  echo "[$GATE_NAME] WARN: Not a git repository"
  warnings=$((warnings + 1))
fi

# Check 3: Quality gate manifest exists
if [[ -z "${MANIFEST_PATH:-}" ]]; then
  if [[ -f "$PROJECT_ROOT/.claude/quality-gate-manifest.json" ]]; then
    MANIFEST_PATH="$PROJECT_ROOT/.claude/quality-gate-manifest.json"
  elif [[ -f "$PROJECT_ROOT/quality-gate-manifest.json" ]]; then
    MANIFEST_PATH="$PROJECT_ROOT/quality-gate-manifest.json"
  else
    MANIFEST_PATH="$PROJECT_ROOT/.claude/quality-gate-manifest.json"
  fi
fi
if [[ -f "$MANIFEST_PATH" ]]; then
  if jq empty "$MANIFEST_PATH" 2>/dev/null; then
    echo "[$GATE_NAME] PASS: Quality gate manifest valid ($MANIFEST_PATH)"
  else
    echo "[$GATE_NAME] FAIL: Quality gate manifest is invalid JSON"
    errors=$((errors + 1))
  fi
else
  echo "[$GATE_NAME] INFO: No quality gate manifest found (will use defaults)"
fi

# Check 4: Health endpoint (if configured)
if [[ -n "${HEALTH_URL:-}" ]]; then
  if command -v curl >/dev/null 2>&1; then
    if curl -sf --max-time 5 "$HEALTH_URL" >/dev/null 2>&1; then
      echo "[$GATE_NAME] PASS: Health endpoint reachable ($HEALTH_URL)"
    else
      echo "[$GATE_NAME] WARN: Health endpoint unreachable ($HEALTH_URL)"
      warnings=$((warnings + 1))
    fi
  else
    echo "[$GATE_NAME] WARN: curl not available, cannot check health endpoint"
    warnings=$((warnings + 1))
  fi
fi

# Check 5: Scripts directory exists with gate scripts
if [[ -d "$PROJECT_ROOT/scripts" ]]; then
  gate_count=$(find "$PROJECT_ROOT/scripts" -name "validate-*.sh" -o -name "enforce-*.sh" -o -name "detect-*.py" 2>/dev/null | wc -l | tr -d ' ')
  echo "[$GATE_NAME] PASS: $gate_count gate script(s) found"
else
  echo "[$GATE_NAME] WARN: No scripts/ directory found"
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
  echo "[$GATE_NAME] PASS: Session start validation complete"
  exit 0
fi
