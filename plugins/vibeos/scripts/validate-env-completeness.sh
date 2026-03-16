#!/usr/bin/env bash
# VibeOS — Environment Variable Completeness Gate
# Reads .env.example (or .env.template/.env.sample) and verifies all listed
# variables are present in the runtime environment or documented as optional.
#
# Usage:
#   bash scripts/validate-env-completeness.sh
#   bash scripts/validate-env-completeness.sh --project-dir /path/to/project
#   bash scripts/validate-env-completeness.sh --strict
#
# Environment:
#   PROJECT_ROOT  — project root directory (default: auto-detect)
#
# Exit codes:
#   0 = All required variables present (or advisory mode)
#   1 = Missing required variables in strict mode
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="2.0.0"
GATE_NAME="validate-env-completeness"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
STRICT=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-dir) PROJECT_ROOT="$2"; shift 2 ;;
    --strict) STRICT=true; shift ;;
    -h|--help)
      echo "Usage: bash $0 [--project-dir PATH] [--strict]"
      exit 0
      ;;
    *) shift ;;
  esac
done

echo "[$GATE_NAME] Environment Variable Completeness Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Project: $PROJECT_ROOT"
echo ""

# Find the env example file
ENV_FILE=""
for candidate in "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env.template" "$PROJECT_ROOT/.env.sample"; do
  if [[ -f "$candidate" ]]; then
    ENV_FILE="$candidate"
    break
  fi
done

if [[ -z "$ENV_FILE" ]]; then
  echo "[$GATE_NAME] SKIP: No .env.example, .env.template, or .env.sample found"
  echo "[$GATE_NAME] SKIP: Create one to enable environment variable validation"
  exit 0
fi

echo "Source: $(basename "$ENV_FILE")"
echo ""

TOTAL=0
PRESENT=0
MISSING=0
OPTIONAL_MISSING=0

declare -a MISSING_VARS=()
declare -a OPTIONAL_VARS=()

while IFS= read -r line || [[ -n "$line" ]]; do
  # Skip empty lines
  [[ -z "$line" ]] && continue

  # Detect optional markers in comments above the variable
  # Format: # optional or # Optional: description
  OPTIONAL_COMMENT_RE='^#.*[Oo]ptional'
  if [[ "$line" =~ $OPTIONAL_COMMENT_RE ]]; then
    NEXT_IS_OPTIONAL=true
    continue
  fi

  # Skip pure comment lines (not optional markers)
  COMMENT_RE='^#'
  if [[ "$line" =~ $COMMENT_RE ]]; then
    NEXT_IS_OPTIONAL=false
    continue
  fi

  # Extract variable name (everything before = or first space)
  VAR_NAME="${line%%=*}"
  VAR_NAME="${VAR_NAME%%[[:space:]]*}"

  # Skip invalid variable names
  if [[ ! "$VAR_NAME" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]]; then
    continue
  fi

  # Check if the example file marks it as optional inline
  IS_OPTIONAL=false
  if [[ "${NEXT_IS_OPTIONAL:-false}" == "true" ]]; then
    IS_OPTIONAL=true
    NEXT_IS_OPTIONAL=false
  fi

  # Check inline comment for optional marker
  OPTIONAL_INLINE_RE='#.*[Oo]ptional'
  if [[ "$line" =~ $OPTIONAL_INLINE_RE ]]; then
    IS_OPTIONAL=true
  fi

  TOTAL=$((TOTAL + 1))

  # Check if variable is set in the current environment
  if [[ -n "${!VAR_NAME+x}" ]]; then
    # Variable exists — check if non-empty
    if [[ -n "${!VAR_NAME}" ]]; then
      PRESENT=$((PRESENT + 1))
    else
      # Variable set but empty
      if [[ "$IS_OPTIONAL" == "true" ]]; then
        OPTIONAL_MISSING=$((OPTIONAL_MISSING + 1))
        OPTIONAL_VARS+=("$VAR_NAME (empty)")
      else
        MISSING=$((MISSING + 1))
        MISSING_VARS+=("$VAR_NAME (empty)")
      fi
    fi
  else
    # Variable not set at all
    if [[ "$IS_OPTIONAL" == "true" ]]; then
      OPTIONAL_MISSING=$((OPTIONAL_MISSING + 1))
      OPTIONAL_VARS+=("$VAR_NAME")
    else
      MISSING=$((MISSING + 1))
      MISSING_VARS+=("$VAR_NAME")
    fi
  fi

done < "$ENV_FILE"

# ─── Output ─────────────────────────────────────────────────────
echo "Variables declared: $TOTAL"
echo "Present and non-empty: $PRESENT"
echo ""

if [[ ${#MISSING_VARS[@]} -gt 0 ]]; then
  echo "MISSING REQUIRED (${#MISSING_VARS[@]}):"
  for var in "${MISSING_VARS[@]}"; do
    echo "  - $var"
  done
  echo ""
fi

if [[ ${#OPTIONAL_VARS[@]} -gt 0 ]]; then
  echo "MISSING OPTIONAL (${#OPTIONAL_VARS[@]}):"
  for var in "${OPTIONAL_VARS[@]}"; do
    echo "  - $var"
  done
  echo ""
fi

# ─── Verdict ────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ $MISSING -gt 0 ]]; then
  if [[ "$STRICT" == "true" ]]; then
    echo "[$GATE_NAME] FAIL: $MISSING required variable(s) missing (strict mode)"
    exit 1
  else
    echo "[$GATE_NAME] WARN: $MISSING required variable(s) missing (advisory mode)"
    echo "[$GATE_NAME] NOTE: Use --strict to make this gate blocking"
    exit 0
  fi
elif [[ $OPTIONAL_MISSING -gt 0 ]]; then
  echo "[$GATE_NAME] PASS: All required variables present ($OPTIONAL_MISSING optional missing)"
  exit 0
else
  echo "[$GATE_NAME] PASS: All $TOTAL variable(s) present"
  exit 0
fi
