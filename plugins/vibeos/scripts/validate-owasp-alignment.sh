#!/usr/bin/env bash
# VibeOS Plugin — OWASP Top 10 Alignment Validation Gate
# Checks for common OWASP Top 10 vulnerabilities in code patterns.
#
# Usage:
#   bash scripts/validate-owasp-alignment.sh
#
# Environment:
#   SCAN_DIRS  — space-separated directories to scan (default: auto-detect)
#   LANGUAGE   — python|typescript|javascript|go|rust|java (default: auto-detect)
#
# Exit codes:
#   0 = No OWASP alignment issues detected
#   1 = Potential vulnerabilities found
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="2.2.0"
GATE_NAME="validate-owasp-alignment"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate-owasp-alignment.sh

Environment:
  SCAN_DIRS  Space-separated directories to scan (default: auto-detect)
  LANGUAGE   python|typescript|javascript|go|rust|java (default: auto-detect)

OWASP Top 10 checks:
  A01 - Broken Access Control
  A02 - Cryptographic Failures
  A03 - Injection
  A04 - Insecure Design (partial)
  A07 - Auth Failures
  A09 - Security Logging Failures
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] OWASP Top 10 Alignment Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

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

python3 - ${SCAN_ARGS[@]+"${SCAN_ARGS[@]}"} <<'PY'
import os
import re
import sys
from pathlib import Path

paths = [Path(p) for p in sys.argv[1:]] or [Path(".")]

EXCLUDE_DIRS = {
    ".git", "node_modules", "__pycache__", ".pytest_cache",
    "venv", ".venv", "dist", "build", "vendor", "target",
}

SCANNABLE_EXT = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".go", ".rs", ".java", ".kt", ".rb", ".php",
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

# OWASP checks grouped by risk category
CHECKS = {
    # A01: Broken Access Control
    "A01-hardcoded-role-bypass": (
        re.compile(r'(is_admin|is_superuser|role)\s*[=:]\s*(True|true|"admin"|\'admin\')', re.IGNORECASE),
        "A01: Hardcoded admin/role bypass",
    ),
    "A01-cors-wildcard": (
        re.compile(r'(Access-Control-Allow-Origin|cors).*\*|allow_origins.*\[.*\*.*\]', re.IGNORECASE),
        "A01: CORS wildcard origin",
    ),

    # A02: Cryptographic Failures
    "A02-weak-hash": (
        re.compile(r'\b(md5|sha1)\s*\(|hashlib\.(md5|sha1)|crypto\.createHash\s*\(\s*[\'"](?:md5|sha1)'),
        "A02: Weak hash algorithm (MD5/SHA1)",
    ),
    "A02-hardcoded-key": (
        re.compile(r'(secret_key|encryption_key|signing_key|jwt_secret)\s*[=:]\s*["\'][A-Za-z0-9+/=]{8,}["\']', re.IGNORECASE),
        "A02: Hardcoded cryptographic key",
    ),

    # A03: Injection
    "A03-sql-injection": (
        re.compile(r'(cursor\.execute|\.query|\.exec)\s*\(\s*f["\']|\.execute\s*\(.*%\s'),
        "A03: Potential SQL injection (string formatting in query)",
    ),
    "A03-command-injection": (
        re.compile(r'(os\.system|subprocess\.(call|run|Popen).*shell\s*=\s*True|child_process\.exec)\s*\('),
        "A03: Potential command injection",
    ),
    "A03-xss-innerhtml": (
        re.compile(r'(innerHTML\s*=|dangerouslySetInnerHTML|document\.write\s*\()'),
        "A03: Potential XSS via innerHTML/document.write",
    ),

    # A07: Identification and Auth Failures
    "A07-password-in-code": (
        re.compile(r'password\s*[=:]\s*["\'][^"\']{4,}["\']', re.IGNORECASE),
        "A07: Hardcoded password",
    ),

    # A09: Security Logging and Monitoring Failures
    "A09-silent-auth-failure": (
        re.compile(r'except.*:\s*pass\s*(#.*)?$|catch\s*\(.*\)\s*\{\s*\}'),
        "A09: Silent exception handling (may hide auth failures)",
    ),
}

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

    for check_name, (pattern, message) in CHECKS.items():
        # Skip some checks in test files
        if is_test and check_name in ("A07-password-in-code", "A02-hardcoded-key", "A01-hardcoded-role-bypass"):
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                failures.append((str(f), i, check_name, message, line.strip()[:200]))

if failures:
    print(f"[validate-owasp-alignment] FAIL: OWASP alignment issues detected ({len(failures)})")
    # Group by check
    by_check = {}
    for f, line, check, msg, content in failures:
        by_check.setdefault(check, []).append((f, line, content))

    for check, items in sorted(by_check.items()):
        msg = CHECKS[check][1]
        print(f"\n  {msg} ({len(items)} occurrence(s)):")
        for f, line, content in items[:5]:
            print(f"    {f}:{line}: {content}")
        if len(items) > 5:
            print(f"    ... {len(items) - 5} more")
    sys.exit(1)

print("[validate-owasp-alignment] PASS: No OWASP alignment issues detected")
sys.exit(0)
PY
