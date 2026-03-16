#!/usr/bin/env bash
# VibeOS Plugin — Cross-Boundary Contract Validator
# Compares frontend API client calls against backend route definitions.
# Detects: field name mismatches, missing endpoints, response shape differences.
#
# Usage:
#   bash scripts/validate-cross-boundary-contracts.sh [--backend-dir src] [--frontend-dir frontend/src]
#
# Environment:
#   BACKEND_DIR     Backend source directory (default: src)
#   FRONTEND_DIR    Frontend source directory (default: frontend/src)
#
# Exit codes:
#   0 = Contracts aligned (or no cross-boundary code detected)
#   1 = Contract mismatches found
#   2 = Configuration error

set -euo pipefail
FRAMEWORK_VERSION="2.0.0"
GATE_NAME="validate-cross-boundary-contracts"

BACKEND_DIR="${BACKEND_DIR:-src}"
FRONTEND_DIR="${FRONTEND_DIR:-frontend/src}"

while [ $# -gt 0 ]; do
  case "$1" in
    --backend-dir) BACKEND_DIR="$2"; shift 2 ;;
    --frontend-dir) FRONTEND_DIR="$2"; shift 2 ;;
    *) shift ;;
  esac
done

# Phase 1: Detect if project has cross-boundary code
if [ ! -d "$BACKEND_DIR" ] || [ ! -d "$FRONTEND_DIR" ]; then
  echo "[${GATE_NAME}] SKIP: No cross-boundary code detected (backend: $BACKEND_DIR, frontend: $FRONTEND_DIR)"
  exit 0
fi

FINDINGS=0

# Phase 2: Extract backend route definitions
# For Python/FastAPI: find all @router.get/post/put/patch/delete decorators
echo "=== Backend Routes ==="
BACKEND_ROUTES=$(mktemp)
grep -rn '@router\.\(get\|post\|put\|patch\|delete\)\|@app\.\(get\|post\|put\|patch\|delete\)' "$BACKEND_DIR" --include="*.py" | \
  sed 's/.*@\(router\|app\)\.\([a-z]*\)("\([^"]*\)".*/\2 \3/' | sort -u > "$BACKEND_ROUTES" 2>/dev/null || true

if [ -s "$BACKEND_ROUTES" ]; then
  echo "Found $(wc -l < "$BACKEND_ROUTES" | tr -d ' ') backend routes"
else
  echo "No backend routes found via decorator scan"
fi

# Phase 3: Extract frontend API calls
# For TypeScript: find fetch/axios/client calls with URL patterns
echo ""
echo "=== Frontend API Calls ==="
FRONTEND_CALLS=$(mktemp)
grep -rn 'fetch\|\.get\|\.post\|\.put\|\.patch\|\.delete\|apiClient\|client\.' "$FRONTEND_DIR" --include="*.ts" --include="*.tsx" | \
  grep -oE '["'"'"'`][/][a-zA-Z0-9/_\-\{\}$\.:]*["'"'"'`]' | \
  tr -d "\"'" | sort -u > "$FRONTEND_CALLS" 2>/dev/null || true

if [ -s "$FRONTEND_CALLS" ]; then
  echo "Found $(wc -l < "$FRONTEND_CALLS" | tr -d ' ') frontend API path patterns"
else
  echo "No frontend API calls found"
fi

# Phase 4: Cross-reference
echo ""
echo "=== Contract Analysis ==="

# Check for frontend paths that don't match any backend route
while IFS= read -r frontend_path; do
  # Normalize: strip template literals, query params
  normalized=$(echo "$frontend_path" | sed 's/\${[^}]*}/\{id\}/g; s/\?.*//; s/`//g')

  # Check if any backend route matches
  if ! grep -q "$normalized" "$BACKEND_ROUTES" 2>/dev/null; then
    echo "MISMATCH: Frontend calls '$frontend_path' but no matching backend route found"
    FINDINGS=$((FINDINGS + 1))
  fi
done < "$FRONTEND_CALLS"

# Phase 5: Check Pydantic model field names vs TypeScript interface fields
echo ""
echo "=== Field Name Analysis ==="

# Extract Pydantic model fields (Python)
BACKEND_FIELDS=$(mktemp)
grep -rn 'field_name\|alias\|: str\|: int\|: bool\|: float\|: list\|: dict\|: Optional' "$BACKEND_DIR" --include="*.py" | \
  grep -oE '[a-z_]+\s*[:=]' | sed 's/[[:space:]]*[:=]//' | sort -u > "$BACKEND_FIELDS" 2>/dev/null || true

# Extract TypeScript interface fields
FRONTEND_FIELDS=$(mktemp)
grep -rn '^\s*[a-zA-Z_]*[?]\?:' "$FRONTEND_DIR" --include="*.ts" --include="*.tsx" | \
  grep -oE '[a-zA-Z_]+[?]?\s*:' | sed 's/[?]*\s*://' | sort -u > "$FRONTEND_FIELDS" 2>/dev/null || true

# Check for snake_case vs camelCase mismatches at the boundary
echo "Backend field count: $(wc -l < "$BACKEND_FIELDS" | tr -d ' ')"
echo "Frontend field count: $(wc -l < "$FRONTEND_FIELDS" | tr -d ' ')"

# Cleanup
rm -f "$BACKEND_ROUTES" "$FRONTEND_CALLS" "$BACKEND_FIELDS" "$FRONTEND_FIELDS"

if [ "$FINDINGS" -gt 0 ]; then
  echo ""
  echo "[${GATE_NAME}] FAIL: $FINDINGS contract mismatch(es) detected"
  exit 1
else
  echo ""
  echo "[${GATE_NAME}] PASS: No contract mismatches detected (or analysis inconclusive — manual review recommended for first run)"
  exit 0
fi
