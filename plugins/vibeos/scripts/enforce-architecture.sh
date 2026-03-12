#!/usr/bin/env bash
# VibeOS Plugin — Config-Driven Architecture Enforcement Gate
# Reads rules from a JSON config file and enforces module boundaries.
#
# Usage:
#   bash scripts/enforce-architecture.sh
#   bash scripts/enforce-architecture.sh --rules-file path/to/rules.json
#
# Environment:
#   RULES_FILE  — path to architecture rules JSON (default: scripts/architecture-rules.json)
#   PROJECT_ROOT — project root directory (default: auto-detect)
#
# Rule types:
#   forbidden_imports    — Module A cannot import from Module B
#   forbidden_patterns   — Pattern X must not appear in Module A
#   require_parameter    — Function definitions in Module A must include parameter P
#   io_purity            — Module A cannot perform I/O operations
#   require_exports      — Module A's __init__.py must export specified symbols
#
# Exit codes:
#   0 = All rules satisfied
#   1 = Architecture violations found
#   2 = Configuration error (missing rules file, invalid JSON)
set -euo pipefail

FRAMEWORK_VERSION="1.0.0"
GATE_NAME="enforce-architecture"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/enforce-architecture.sh [--rules-file path/to/rules.json]

Environment:
  RULES_FILE    Path to architecture rules JSON (default: scripts/architecture-rules.json)
  PROJECT_ROOT  Project root directory (default: auto-detect)

Rule Types:
  forbidden_imports    Module A cannot import from Module B
  forbidden_patterns   Pattern X must not appear in Module A
  require_parameter    Functions in Module A must include parameter P
  io_purity            Module A cannot perform I/O operations
  require_exports      Module A's __init__.py must export specified symbols
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --rules-file)
      RULES_FILE="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
RULES_FILE="${RULES_FILE:-$PROJECT_ROOT/scripts/architecture-rules.json}"

echo "[$GATE_NAME] Architecture Enforcement"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Validate rules file exists
if [[ ! -f "$RULES_FILE" ]]; then
  echo "[$GATE_NAME] SKIP: No architecture rules file found at $RULES_FILE"
  echo "[$GATE_NAME] SKIP: Generate one using the decision engine or copy architecture-rules.example.json"
  exit 0
fi

# Validate JSON
if ! jq empty "$RULES_FILE" 2>/dev/null; then
  echo "[$GATE_NAME] FAIL: Invalid JSON in rules file: $RULES_FILE"
  exit 2
fi

echo "Rules file: $RULES_FILE"

# Count rules
RULE_COUNT=$(jq '.rules | length' "$RULES_FILE")
echo "Rules loaded: $RULE_COUNT"
echo ""

if [[ "$RULE_COUNT" -eq 0 ]]; then
  echo "[$GATE_NAME] SKIP: No rules defined in $RULES_FILE"
  exit 0
fi

# Run the rule engine in Python for robust regex and file handling
python3 - "$RULES_FILE" "$PROJECT_ROOT" <<'PY'
import json
import os
import re
import sys
from pathlib import Path

rules_file = Path(sys.argv[1])
project_root = Path(sys.argv[2])

with open(rules_file) as f:
    config = json.load(f)

rules = config.get("rules", [])

EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache",
    "venv", ".venv", "dist", "build", "vendor", "target",
    ".mypy_cache", ".tox", "htmlcov", "coverage",
}

def is_excluded(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    return False

def find_files(module_path: str, project_root: Path) -> list[Path]:
    """Find source files matching a module path pattern.

    Supports:
      - Directory paths: "src/routers/" → all files in that directory
      - Glob patterns: "*.controller.ts" → matching files anywhere
      - Specific files: "src/app.py" → that specific file
    """
    files = []

    # Handle glob patterns (e.g., "*.controller.ts", "*/views.py")
    if "*" in module_path:
        for f in project_root.rglob(module_path):
            if f.is_file() and not is_excluded(f.relative_to(project_root)):
                files.append(f)
        return files

    # Handle directory paths
    target = project_root / module_path
    if target.is_dir():
        for f in target.rglob("*"):
            if f.is_file() and not is_excluded(f.relative_to(project_root)):
                # Only scan code files
                if f.suffix in {".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
                                ".go", ".rs", ".java", ".kt", ".rb", ".php", ".sh"}:
                    files.append(f)
        return files

    # Handle specific file
    if target.is_file():
        return [target]

    return files

def read_file(path: Path) -> str:
    try:
        data = path.read_bytes()
        if b"\x00" in data[:4096]:
            return ""
        return data.decode("utf-8", errors="ignore")
    except Exception:
        return ""


# Default I/O patterns for io_purity rule
DEFAULT_IO_PATTERNS = [
    # Python
    r"\bopen\s*\(",
    r"\bimport\s+(psycopg|httpx|requests|subprocess|socket|aiohttp|urllib)",
    r"\bfrom\s+(psycopg|httpx|requests|subprocess|socket|aiohttp|urllib)",
    r"\bos\.(path|makedirs|remove|rename|listdir|walk)\b",
    # JavaScript/TypeScript
    r"\bfs\.(read|write|mkdir|unlink|access)",
    r"\brequire\s*\(\s*['\"]fs['\"]",
    r"\bimport.*from\s+['\"]fs['\"]",
    r"\bfetch\s*\(",
    r"\baxios\.",
    # Go
    r"\bos\.(Open|Create|Remove|ReadFile|WriteFile)",
    r"\bnet\.(Dial|Listen)",
    r"\bhttp\.(Get|Post|NewRequest)",
    # Rust
    r"\bstd::fs::",
    r"\bstd::net::",
    r"\breqwest::",
    # Java
    r"\bnew\s+File\s*\(",
    r"\bFiles\.(read|write|create|delete)",
    r"\bHttpClient|HttpURLConnection|OkHttpClient",
]

violations = []
warnings = []

for rule in rules:
    name = rule.get("name", "unnamed")
    rule_type = rule.get("type", "")
    severity = rule.get("severity", "error")
    message = rule.get("message", "Architecture violation")
    source_module = rule.get("source_module", "")

    if not source_module:
        continue

    source_files = find_files(source_module, project_root)
    if not source_files:
        continue

    rule_violations = []

    # ----------------------------------------------------------------
    # FORBIDDEN IMPORTS
    # ----------------------------------------------------------------
    if rule_type == "forbidden_imports":
        target_module = rule.get("target_module", "")
        if not target_module:
            continue

        # Build import patterns based on target module
        # Normalize path separators and strip trailing slash
        target_clean = target_module.rstrip("/").replace("/", ".")
        target_path = target_module.rstrip("/")

        import_patterns = [
            # Python: from package.module import ...
            re.compile(rf"(?:from|import)\s+{re.escape(target_clean)}"),
            # Python: from package/module style (relative)
            re.compile(rf"from\s+\.+{re.escape(target_clean)}"),
            # JS/TS: import ... from './module' or '../module'
            re.compile(rf"(?:import|require)\s*\(?['\"].*/?{re.escape(target_path)}"),
            # Go: import "package/module"
            re.compile(rf'import\s+.*"{re.escape(target_path)}'),
        ]

        for f in source_files:
            content = read_file(f)
            if not content:
                continue
            rel_path = str(f.relative_to(project_root))
            for i, line in enumerate(content.splitlines(), 1):
                for rx in import_patterns:
                    if rx.search(line):
                        rule_violations.append(f"  {rel_path}:{i}: {line.strip()}")
                        break

    # ----------------------------------------------------------------
    # FORBIDDEN PATTERNS
    # ----------------------------------------------------------------
    elif rule_type == "forbidden_patterns":
        pattern_str = rule.get("pattern", "")
        if not pattern_str:
            continue

        try:
            rx = re.compile(pattern_str)
        except re.error as e:
            print(f"[enforce-architecture] WARN: Invalid regex in rule '{name}': {e}")
            continue

        for f in source_files:
            content = read_file(f)
            if not content:
                continue
            rel_path = str(f.relative_to(project_root))
            for i, line in enumerate(content.splitlines(), 1):
                if rx.search(line):
                    rule_violations.append(f"  {rel_path}:{i}: {line.strip()[:200]}")

    # ----------------------------------------------------------------
    # REQUIRE PARAMETER
    # ----------------------------------------------------------------
    elif rule_type == "require_parameter":
        parameter = rule.get("parameter", "")
        if not parameter:
            continue

        # Match function definitions and check if they include the required parameter
        func_patterns = [
            # Python: def func_name(
            re.compile(r"^\s*(async\s+)?def\s+([a-z]\w*)\s*\("),
            # JS/TS: function funcName( or funcName(
            re.compile(r"^\s*(async\s+)?function\s+(\w+)\s*\("),
            re.compile(r"^\s*(export\s+)?(async\s+)?function\s+(\w+)\s*\("),
            # Go: func FuncName(
            re.compile(r"^\s*func\s+(\w+)\s*\("),
        ]

        for f in source_files:
            content = read_file(f)
            if not content:
                continue
            rel_path = str(f.relative_to(project_root))
            lines = content.splitlines()

            for i, line in enumerate(lines):
                # Skip private/internal functions
                stripped = line.strip()
                if stripped.startswith("def _") or stripped.startswith("func _"):
                    continue

                matched = False
                for fx in func_patterns:
                    if fx.search(line):
                        matched = True
                        break

                if not matched:
                    continue

                # Check the function signature (may span multiple lines)
                sig = ""
                for j in range(i, min(len(lines), i + 6)):
                    sig += lines[j]
                    if ")" in lines[j]:
                        break

                if parameter not in sig:
                    func_name = line.strip()[:80]
                    rule_violations.append(f"  {rel_path}:{i+1}: {func_name}")

    # ----------------------------------------------------------------
    # IO PURITY
    # ----------------------------------------------------------------
    elif rule_type == "io_purity":
        io_patterns = rule.get("io_patterns", DEFAULT_IO_PATTERNS)
        compiled_patterns = []
        for p in io_patterns:
            try:
                compiled_patterns.append(re.compile(p))
            except re.error:
                continue

        for f in source_files:
            content = read_file(f)
            if not content:
                continue
            rel_path = str(f.relative_to(project_root))
            for i, line in enumerate(content.splitlines(), 1):
                for rx in compiled_patterns:
                    if rx.search(line):
                        rule_violations.append(f"  {rel_path}:{i}: {line.strip()[:200]}")
                        break

    # ----------------------------------------------------------------
    # REQUIRE EXPORTS (R9)
    # ----------------------------------------------------------------
    elif rule_type == "require_exports":
        required_symbols = rule.get("required_symbols", [])
        if not required_symbols:
            continue

        # For Python: check __init__.py in the source_module directory
        init_file = project_root / source_module / "__init__.py"
        if not init_file.exists():
            rule_violations.append(f"  {source_module}/__init__.py: file does not exist")
        else:
            init_content = read_file(init_file)
            if not init_content.strip():
                rule_violations.append(
                    f"  {source_module}/__init__.py: file is empty — "
                    f"expected exports: {', '.join(required_symbols)}"
                )
            else:
                # Check for each required symbol in the init file
                # Look for: from .module import Symbol, import Symbol,
                # Symbol = ..., __all__ containing Symbol
                for symbol in required_symbols:
                    # Check direct import/assignment patterns
                    found = False
                    symbol_patterns = [
                        re.compile(rf"\bimport\s+.*\b{re.escape(symbol)}\b"),
                        re.compile(rf"\bfrom\s+\.\w+\s+import\s+.*\b{re.escape(symbol)}\b"),
                        re.compile(rf"^{re.escape(symbol)}\s*=", re.MULTILINE),
                        re.compile(rf'["\']{re.escape(symbol)}["\']'),  # in __all__
                    ]
                    for sp in symbol_patterns:
                        if sp.search(init_content):
                            found = True
                            break
                    if not found:
                        rule_violations.append(
                            f"  {source_module}/__init__.py: missing export '{symbol}'"
                        )

    else:
        print(f"[enforce-architecture] WARN: Unknown rule type '{rule_type}' in rule '{name}'")
        continue

    if rule_violations:
        target = violations if severity == "error" else warnings
        target.append({
            "name": name,
            "message": message,
            "severity": severity,
            "count": len(rule_violations),
            "details": rule_violations,
        })

# ============================================================================
# OUTPUT
# ============================================================================

error_count = 0
warning_count = 0

if violations:
    for v in violations:
        print(f"FAIL [{v['name']}] {v['message']} ({v['count']} violation(s))")
        for detail in v["details"][:20]:
            print(detail)
        if v["count"] > 20:
            print(f"  ... {v['count'] - 20} more")
        print()
        error_count += v["count"]

if warnings:
    for w in warnings:
        print(f"WARN [{w['name']}] {w['message']} ({w['count']} violation(s))")
        for detail in w["details"][:10]:
            print(detail)
        if w["count"] > 10:
            print(f"  ... {w['count'] - 10} more")
        print()
        warning_count += w["count"]

print()
if error_count > 0:
    print(f"[enforce-architecture] FAIL: {error_count} error(s), {warning_count} warning(s)")
    sys.exit(1)
elif warning_count > 0:
    print(f"[enforce-architecture] PASS (with {warning_count} warning(s))")
    sys.exit(0)
else:
    total_rules = len(rules)
    print(f"[enforce-architecture] PASS: All {total_rules} architecture rules satisfied")
    sys.exit(0)
PY
