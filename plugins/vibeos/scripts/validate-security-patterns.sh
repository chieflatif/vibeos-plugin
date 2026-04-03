#!/usr/bin/env bash
# VibeOS Plugin — Security Pattern Validation Gate
# Scans for dangerous code patterns: eval/exec, pickle, shell=True, verify=False, etc.
#
# Usage:
#   bash scripts/validate-security-patterns.sh [path ...]
#
# Environment:
#   SCAN_DIRS — space-separated directories to scan (default: current directory)
#
# Exit codes:
#   0 = No security anti-patterns detected
#   1 = Security violations found
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="2.1.0"
GATE_NAME="validate-security-patterns"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate-security-patterns.sh [path ...]

Environment:
  SCAN_DIRS  Space-separated directories to scan (default: current directory)

What it checks (high-signal, low-false-positive):
  - No auth codes/tokens in URL query strings (?code=, ?token=, ?key=)
  - No dangerous primitives: eval/exec, pickle.loads, yaml.load (unsafe), subprocess shell=True
  - No TLS verification disabled (verify=False)
  - No fail-open auth toggles (SKIP_AUTH=true)
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] Security Pattern Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Build scan path arguments
SCAN_ARGS=()
if [[ $# -gt 0 ]]; then
  SCAN_ARGS=("$@")
elif [[ -n "${SCAN_DIRS:-}" ]]; then
  read -ra SCAN_ARGS <<< "$SCAN_DIRS"
else
  SCAN_ARGS=(".")
fi

python3 - "${SCAN_ARGS[@]}" <<'PY'
import os
import re
import sys
from pathlib import Path

paths = [Path(p) for p in sys.argv[1:]] or [Path(".")]

EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "htmlcov",
    "coverage",
    ".nyc_output",
    "dist",
    "build",
    "venv",
    ".venv",
    "vendor",
    "target",
    ".mypy_cache",
    ".tox",
}

# File extensions to scan (multi-language)
SCANNABLE_EXTENSIONS = {
    ".py", ".sh", ".bash",
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".go", ".rs", ".java", ".kt",
    ".rb", ".php",
}

def excluded(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
        if part.startswith(".venv"):
            return True
    return False

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
                if p.suffix.lower() not in SCANNABLE_EXTENSIONS:
                    continue
                # Don't scan the validator itself
                if p.name.startswith("validate-") and p.suffix in (".sh", ".py"):
                    continue
                yield p

# 1) Secrets/tokens in URLs (query strings)
url_qs = re.compile(
    r"https?://[^\s\"']+\?(?:[^\"'\s]*)(?:\b(code|token|key|apikey|api_key|signature)=)",
    re.IGNORECASE,
)

# 2) Dangerous primitives (multi-language)
danger = [
    # Python
    (re.compile(r"\beval\s*\("), "eval(...)"),
    (re.compile(r"\bexec\s*\("), "exec(...)"),
    (re.compile(r"\bpickle\.loads\s*\("), "pickle.loads(...)"),
    (re.compile(r"\byaml\.load\s*\("), "yaml.load(...) (unsafe)"),
    (re.compile(r"\bshell\s*=\s*True\b"), "subprocess shell=True"),
    (re.compile(r"\bverify\s*=\s*False\b"), "TLS verify=False"),
    # JavaScript/TypeScript
    (re.compile(r"\bchild_process\.exec\s*\("), "child_process.exec(...)"),
    (re.compile(r"\bnew\s+Function\s*\("), "new Function(...) (eval equivalent)"),
    (re.compile(r"\bdocument\.write\s*\("), "document.write(...) (XSS risk)"),
    (re.compile(r"innerHTML\s*="), "innerHTML assignment (XSS risk)"),
    (re.compile(r"\b(rejectUnauthorized|NODE_TLS_REJECT_UNAUTHORIZED)\s*[=:]\s*(false|0|'0'|\"0\")"), "TLS verification disabled"),
    # Go
    (re.compile(r"InsecureSkipVerify\s*:\s*true"), "Go TLS InsecureSkipVerify"),
    # General
    (re.compile(r"\bos\.system\s*\("), "os.system(...)"),
]

# 3) Fail-open auth toggles
fail_open = [
    (re.compile(r'SKIP_AUTH.*(?:=).*["\']true["\']', re.IGNORECASE), "SKIP_AUTH set to true"),
    (re.compile(r'setdefault\s*\(\s*["\']SKIP_AUTH["\']\s*,\s*["\']true["\']\s*\)', re.IGNORECASE), "SKIP_AUTH setdefault to true"),
    (re.compile(r'DISABLE_AUTH.*(?:=).*["\']true["\']', re.IGNORECASE), "DISABLE_AUTH set to true"),
]

failures = []

for f in iter_files():
    try:
        data = f.read_bytes()
    except Exception:
        continue
    if b"\x00" in data[:4096]:
        continue
    text = data.decode("utf-8", errors="ignore")

    is_test = "test" in str(f).lower()

    # URL query-string secrets (non-test only)
    if not is_test and url_qs.search(text):
        failures.append((f, "No secrets in URLs", "Found URL containing query token/code/key"))

    # Dangerous primitives
    for rx, label in danger:
        if rx.search(text):
            failures.append((f, "No dangerous primitives", f"Found {label}"))

    # Fail-open auth toggles (non-test only)
    if not is_test:
        for rx, label in fail_open:
            if rx.search(text):
                failures.append((f, "No fail-open auth toggles", label))

if failures:
    print(f"[validate-security-patterns] FAIL: Security violations detected ({len(failures)})")
    for f, check, msg in failures[:50]:
        print(f"  - {check}: {f} -- {msg}")
    if len(failures) > 50:
        print(f"  ... {len(failures)-50} more")
    sys.exit(1)

print("[validate-security-patterns] PASS: No security anti-patterns detected")
sys.exit(0)
PY
