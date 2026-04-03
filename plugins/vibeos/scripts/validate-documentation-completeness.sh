#!/usr/bin/env bash
# VibeOS Plugin — Documentation Completeness Validation Gate
# Checks docstring coverage and required documentation files.
#
# Usage:
#   bash scripts/validate-documentation-completeness.sh
#
# Environment:
#   SOURCE_DIR          — source directory to check (default: auto-detect)
#   DOC_DIR             — documentation directory (default: docs/)
#   LANGUAGE            — python|typescript|javascript|go|rust|java (default: auto-detect)
#   MIN_DOCSTRING_PCT   — minimum docstring coverage percentage (default: 80)
#   REQUIRED_DOCS       — space-separated list of required doc files (default: ARCHITECTURE.md)
#
# Exit codes:
#   0 = Documentation checks passed
#   1 = Documentation checks failed
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="2.1.0"
GATE_NAME="validate-documentation-completeness"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate-documentation-completeness.sh

Environment:
  SOURCE_DIR          Source directory to check (default: auto-detect)
  DOC_DIR             Documentation directory (default: docs/)
  LANGUAGE            python|typescript|javascript|go|rust|java (default: auto-detect)
  MIN_DOCSTRING_PCT   Minimum docstring coverage % (default: 80)
  REQUIRED_DOCS       Space-separated required doc files (default: ARCHITECTURE.md)
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] Documentation Completeness Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

DOC_DIR="${DOC_DIR:-docs}"
MIN_DOCSTRING_PCT="${MIN_DOCSTRING_PCT:-80}"

# Check required documentation files
REQUIRED_DOCS="${REQUIRED_DOCS:-ARCHITECTURE.md}"
read -ra doc_list <<< "$REQUIRED_DOCS"

for doc in "${doc_list[@]}"; do
  doc_path="$repo_root/$DOC_DIR/$doc"
  if [[ -f "$doc_path" ]]; then
    echo "[$GATE_NAME] PASS: found $doc"
  else
    echo "[$GATE_NAME] WARN: missing recommended doc $DOC_DIR/$doc (non-blocking)"
  fi
done

# Auto-detect source directory
if [[ -z "${SOURCE_DIR:-}" ]]; then
  for candidate in src lib app; do
    if [[ -d "$repo_root/$candidate" ]]; then
      SOURCE_DIR="$candidate"
      break
    fi
  done
fi

if [[ -z "${SOURCE_DIR:-}" ]]; then
  echo "[$GATE_NAME] WARN: No source directory found. Set SOURCE_DIR."
  echo "[$GATE_NAME] SKIP: Cannot check docstring coverage without source directory"
  exit 0
fi

source_path="$repo_root/$SOURCE_DIR"
if [[ ! -d "$source_path" ]]; then
  echo "[$GATE_NAME] WARN: Source directory not found: $source_path"
  exit 0
fi

# Auto-detect language
detect_language() {
  if [[ -f "$repo_root/pyproject.toml" ]] || [[ -f "$repo_root/setup.py" ]]; then
    echo "python"
  elif [[ -f "$repo_root/tsconfig.json" ]] || [[ -f "$repo_root/package.json" ]]; then
    echo "javascript"
  elif [[ -f "$repo_root/go.mod" ]]; then
    echo "go"
  elif [[ -f "$repo_root/Cargo.toml" ]]; then
    echo "rust"
  elif [[ -f "$repo_root/pom.xml" ]] || [[ -f "$repo_root/build.gradle" ]]; then
    echo "java"
  else
    echo "unknown"
  fi
}

LANGUAGE="${LANGUAGE:-$(detect_language)}"

# Python: AST-based docstring coverage
if [[ "$LANGUAGE" == "python" ]]; then
  python3 - "$source_path" "$MIN_DOCSTRING_PCT" <<'PY'
import ast
import sys
from pathlib import Path

target_dir = Path(sys.argv[1])
min_pct = float(sys.argv[2])

public_defs = 0
documented_defs = 0
missing = []

for py in target_dir.rglob("*.py"):
    if "__pycache__" in py.parts:
        continue
    try:
        mod = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
    except Exception:
        continue
    for node in mod.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("_"):
                continue
            public_defs += 1
            if ast.get_docstring(node):
                documented_defs += 1
            else:
                if len(missing) < 50:
                    missing.append(f"{py}:{node.lineno}:{node.name}")

pct = 100.0 if public_defs == 0 else (documented_defs / public_defs) * 100.0
print(f"[validate-documentation-completeness] Docstrings: {documented_defs}/{public_defs} ({pct:.2f}%)")

if pct + 1e-9 < min_pct:
    print(f"[validate-documentation-completeness] FAIL: docstring coverage below threshold (min {min_pct:.2f}%)")
    for m in missing[:25]:
        print(f"  - {m}")
    sys.exit(1)

print(f"[validate-documentation-completeness] PASS: docstring coverage meets threshold (min {min_pct:.2f}%)")
sys.exit(0)
PY

# Go: Check for package comments and exported function comments
elif [[ "$LANGUAGE" == "go" ]]; then
  echo "=== Go Documentation Check ==="
  # Count exported functions and those with comments
  python3 - "$source_path" "$MIN_DOCSTRING_PCT" <<'PY'
import re
import sys
from pathlib import Path

target_dir = Path(sys.argv[1])
min_pct = float(sys.argv[2])

exported = 0
documented = 0
missing = []

for go_file in target_dir.rglob("*.go"):
    if "_test.go" in go_file.name:
        continue
    try:
        lines = go_file.read_text(encoding="utf-8").splitlines()
    except Exception:
        continue
    for i, line in enumerate(lines):
        m = re.match(r'^func\s+([A-Z]\w*)\s*\(', line)
        if not m:
            m = re.match(r'^func\s+\(\w+\s+\*?\w+\)\s+([A-Z]\w*)\s*\(', line)
        if m:
            exported += 1
            # Check if previous non-empty line is a comment
            has_doc = False
            for j in range(i - 1, max(0, i - 3) - 1, -1):
                prev = lines[j].strip()
                if prev.startswith("//"):
                    has_doc = True
                    break
                if prev:
                    break
            if has_doc:
                documented += 1
            else:
                if len(missing) < 50:
                    missing.append(f"{go_file}:{i+1}:{m.group(1)}")

pct = 100.0 if exported == 0 else (documented / exported) * 100.0
print(f"[validate-documentation-completeness] Go docs: {documented}/{exported} ({pct:.2f}%)")

if pct + 1e-9 < min_pct:
    print(f"[validate-documentation-completeness] FAIL: doc coverage below threshold (min {min_pct:.2f}%)")
    for m in missing[:25]:
        print(f"  - {m}")
    sys.exit(1)

print(f"[validate-documentation-completeness] PASS: doc coverage meets threshold (min {min_pct:.2f}%)")
sys.exit(0)
PY

# JavaScript/TypeScript: Check for JSDoc comments on exported functions
elif [[ "$LANGUAGE" == "javascript" || "$LANGUAGE" == "typescript" ]]; then
  echo "=== JS/TS Documentation Check ==="
  python3 - "$source_path" "$MIN_DOCSTRING_PCT" <<'PY'
import re
import sys
from pathlib import Path

target_dir = Path(sys.argv[1])
min_pct = float(sys.argv[2])

exported = 0
documented = 0
missing = []

for ext in ["*.js", "*.jsx", "*.ts", "*.tsx", "*.mjs"]:
    for f in target_dir.rglob(ext):
        if "node_modules" in f.parts or "__tests__" in f.parts or ".test." in f.name or ".spec." in f.name:
            continue
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for i, line in enumerate(lines):
            # Match exported functions/classes
            if re.match(r'^\s*export\s+(async\s+)?function\s+\w+', line) or \
               re.match(r'^\s*export\s+(default\s+)?class\s+\w+', line) or \
               re.match(r'^\s*export\s+const\s+\w+\s*=\s*(async\s+)?\(', line):
                exported += 1
                # Check for JSDoc above
                has_doc = False
                for j in range(i - 1, max(0, i - 5) - 1, -1):
                    prev = lines[j].strip()
                    if prev.endswith("*/"):
                        has_doc = True
                        break
                    if prev and not prev.startswith("*") and not prev.startswith("//"):
                        break
                if has_doc:
                    documented += 1
                else:
                    if len(missing) < 50:
                        missing.append(f"{f}:{i+1}")

pct = 100.0 if exported == 0 else (documented / exported) * 100.0
print(f"[validate-documentation-completeness] JS/TS docs: {documented}/{exported} ({pct:.2f}%)")

if pct + 1e-9 < min_pct:
    print(f"[validate-documentation-completeness] FAIL: doc coverage below threshold (min {min_pct:.2f}%)")
    for m in missing[:25]:
        print(f"  - {m}")
    sys.exit(1)

print(f"[validate-documentation-completeness] PASS: doc coverage meets threshold (min {min_pct:.2f}%)")
sys.exit(0)
PY

else
  echo "[$GATE_NAME] WARN: Docstring coverage not supported for language '$LANGUAGE'"
  echo "[$GATE_NAME] SKIP: Only required docs check performed"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[$GATE_NAME] Documentation completeness validation complete"
