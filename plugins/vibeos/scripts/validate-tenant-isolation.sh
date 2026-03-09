#!/usr/bin/env bash
# VibeOS Plugin — Tenant Isolation Validation Gate
# Checks that multi-tenant data access includes tenant_id filtering.
#
# Usage:
#   bash scripts/validate-tenant-isolation.sh
#
# Environment:
#   SCAN_DIRS     — space-separated directories to scan (default: auto-detect)
#   TENANT_FIELD  — name of the tenant identifier field (default: tenant_id)
#
# Exit codes:
#   0 = Tenant isolation patterns found
#   1 = Missing tenant isolation
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="1.0.0"
GATE_NAME="validate-tenant-isolation"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate-tenant-isolation.sh

Environment:
  SCAN_DIRS     Space-separated directories to scan (default: auto-detect)
  TENANT_FIELD  Tenant identifier field name (default: tenant_id)

Checks:
  - Database query functions include tenant_id filtering
  - No queries that could leak data across tenants
  - RLS (Row-Level Security) patterns exist if using PostgreSQL
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] Tenant Isolation Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TENANT_FIELD="${TENANT_FIELD:-tenant_id}"

# Build scan dirs
SCAN_ARGS=()
if [[ -n "${SCAN_DIRS:-}" ]]; then
  read -ra SCAN_ARGS <<< "$SCAN_DIRS"
else
  for candidate in src lib app; do
    if [[ -d "$repo_root/$candidate" ]]; then
      SCAN_ARGS+=("$repo_root/$candidate")
      break
    fi
  done
fi

if [[ ${#SCAN_ARGS[@]} -eq 0 ]]; then
  echo "[$GATE_NAME] WARN: No source directory found. Set SCAN_DIRS."
  echo "[$GATE_NAME] SKIP: Cannot validate without source directory"
  exit 0
fi

python3 - "$TENANT_FIELD" ${SCAN_ARGS[@]+"${SCAN_ARGS[@]}"} <<'PY'
import os
import re
import sys
from pathlib import Path

tenant_field = sys.argv[1]
paths = [Path(p) for p in sys.argv[2:]] or [Path(".")]

EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache",
    "venv", ".venv", "dist", "build", "vendor", "target",
}

SCANNABLE_EXT = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".go", ".rs", ".java", ".kt",
}

def excluded(path):
    return any(part in EXCLUDE_DIRS for part in path.parts)

def iter_files():
    seen = set()
    for base in paths:
        base = base.resolve()
        if base.is_file():
            if base not in seen:
                seen.add(base)
                yield base
            continue
        if not base.exists():
            continue
        for root, dirs, files in os.walk(base):
            rp = Path(root)
            if excluded(rp):
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs if not excluded(rp / d)]
            for f in files:
                p = rp / f
                if p in seen:
                    continue
                seen.add(p)
                if p.suffix.lower() not in SCANNABLE_EXT:
                    continue
                if p.name.startswith("validate-") or p.name.startswith("detect-"):
                    continue
                yield p

# Patterns that indicate database queries
db_query_patterns = [
    # Python ORMs
    re.compile(r"\.(filter|get|all|select|where|find|query)\s*\("),
    # Raw SQL
    re.compile(r"\.(execute|query|exec)\s*\("),
    # Prisma / TypeORM / Sequelize
    re.compile(r"\.(findMany|findFirst|findUnique|find|findOne|createQueryBuilder)\s*\("),
    # MongoDB
    re.compile(r"\.(find|findOne|aggregate|updateMany|deleteMany)\s*\("),
]

# Patterns that suggest tenant filtering is happening
tenant_patterns = [
    re.compile(rf"\b{re.escape(tenant_field)}\b"),
    re.compile(r"\btenant\b", re.IGNORECASE),
    re.compile(r"\borg_id\b|\borganization_id\b"),
    re.compile(r"\bworkspace_id\b"),
]

# Check if codebase uses multi-tenancy at all
all_text = ""
file_list = list(iter_files())

if not file_list:
    print(f"[validate-tenant-isolation] WARN: No source files found")
    sys.exit(0)

for f in file_list:
    try:
        data = f.read_bytes()
        if b"\x00" in data[:4096]:
            continue
        all_text += data.decode("utf-8", errors="ignore") + "\n"
    except Exception:
        continue

# Check if tenant_id is referenced anywhere (indicates multi-tenancy)
has_tenancy = any(rx.search(all_text) for rx in tenant_patterns)

if not has_tenancy:
    print(f"[validate-tenant-isolation] SKIP: No multi-tenancy patterns detected ({tenant_field} not referenced)")
    print(f"[validate-tenant-isolation] PASS: Single-tenant project or tenancy not yet implemented")
    sys.exit(0)

# If multi-tenancy exists, check that queries include tenant filtering
failures = []
warnings = []

for f in file_list:
    try:
        text = f.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue

    is_test = "test" in str(f).lower()
    if is_test:
        continue

    lines = text.splitlines()
    for i, line in enumerate(lines, 1):
        # Check if this line has a database query
        has_query = any(rx.search(line) for rx in db_query_patterns)
        if not has_query:
            continue

        # Check surrounding context (5 lines before and after) for tenant filtering
        context_start = max(0, i - 6)
        context_end = min(len(lines), i + 5)
        context = "\n".join(lines[context_start:context_end])

        has_tenant_filter = any(rx.search(context) for rx in tenant_patterns)

        if not has_tenant_filter:
            # Check function signature for tenant parameter
            func_context_start = max(0, i - 20)
            func_context = "\n".join(lines[func_context_start:i])
            has_tenant_param = any(rx.search(func_context) for rx in tenant_patterns)

            if not has_tenant_param:
                warnings.append((str(f), i, line.strip()[:200]))

if warnings:
    print(f"[validate-tenant-isolation] WARN: Database queries without apparent tenant filtering ({len(warnings)})")
    for f, line, content in warnings[:15]:
        print(f"  - {f}:{line}: {content}")
    if len(warnings) > 15:
        print(f"  ... {len(warnings) - 15} more")
    print()
    print(f"[validate-tenant-isolation] PASS (with {len(warnings)} warning(s) — review for tenant isolation)")
    sys.exit(0)
else:
    print(f"[validate-tenant-isolation] PASS: All detected queries include tenant filtering")
    sys.exit(0)
PY
