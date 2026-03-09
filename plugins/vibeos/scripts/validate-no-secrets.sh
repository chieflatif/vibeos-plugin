#!/usr/bin/env bash
# VibeOS Plugin — Secrets Detection Gate
# Scans text files for common secret patterns (API keys, tokens, PEM keys, JWTs).
#
# Usage:
#   bash scripts/validate-no-secrets.sh [path ...]
#
# Environment:
#   SCAN_DIRS — space-separated directories to scan (default: git-tracked files)
#
# Exit codes:
#   0 = No secrets detected
#   1 = Potential secrets found
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="1.0.0"
GATE_NAME="validate-no-secrets"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate-no-secrets.sh [path ...]

Environment:
  SCAN_DIRS  Space-separated directories to scan (default: git-tracked files)

Notes:
  - Scans text-like files for common secret patterns.
  - Lines containing [REDACTED] are ignored.
  - Placeholder examples (XXXX, xxxxxxxx) are ignored.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] Secrets Detection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Build scan path arguments
SCAN_ARGS=()
if [[ $# -gt 0 ]]; then
  SCAN_ARGS=("$@")
elif [[ -n "${SCAN_DIRS:-}" ]]; then
  read -ra SCAN_ARGS <<< "$SCAN_DIRS"
fi

python3 - ${SCAN_ARGS[@]+"${SCAN_ARGS[@]}"} <<'PY'
import os
import re
import subprocess
import sys
from pathlib import Path

paths = [Path(p) for p in sys.argv[1:]]

EXCLUDE_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "venv",
    ".venv",
    "dist",
    "build",
    ".mypy_cache",
    ".tox",
    ".eggs",
    "vendor",
    "target",       # Rust, Java
}

def is_excluded_dir(p: Path) -> bool:
    for part in p.parts:
        if part in EXCLUDE_DIR_NAMES:
            return True
        if part.startswith(".venv"):
            return True
    return False

def is_texty_file(p: Path) -> bool:
    return p.suffix.lower() in {
        # Python
        ".py",
        # JavaScript / TypeScript
        ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
        # Go
        ".go",
        # Rust
        ".rs",
        # Java
        ".java", ".kt", ".kts", ".gradle",
        # Shell
        ".sh", ".bash", ".zsh",
        # Config / Data
        ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
        ".env", ".env.local", ".env.example",
        # Docs
        ".md", ".txt", ".rst",
        # Web
        ".html", ".htm", ".xml", ".svg",
        # Other
        ".dockerfile",
    }

PATTERNS = [
    # AWS access keys
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "aws_access_key_id"),
    (re.compile(r"\bASIA[0-9A-Z]{16}\b"), "aws_temp_access_key_id"),
    # GitHub PATs
    (re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"), "github_pat"),
    (re.compile(r"\bgho_[A-Za-z0-9]{20,}\b"), "github_oauth_token"),
    (re.compile(r"\bghs_[A-Za-z0-9]{20,}\b"), "github_app_token"),
    (re.compile(r"\bghr_[A-Za-z0-9]{20,}\b"), "github_refresh_token"),
    # PEM private keys
    (re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |)PRIVATE KEY-----"), "private_key_pem"),
    # JWT-like: three base64url segments separated by dots
    (re.compile(r"\beyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\b"), "jwt_like"),
    # Stripe
    (re.compile(r"\bsk_(?:live|test)_[A-Za-z0-9]{16,}\b"), "stripe_secret_key"),
    (re.compile(r"\brk_(?:live|test)_[A-Za-z0-9]{16,}\b"), "stripe_restricted_key"),
    # OpenAI-style keys
    (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "openai_like_key"),
    # Slack tokens
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "slack_token"),
    # Google API keys
    (re.compile(r"\bAIza[A-Za-z0-9_\\-]{35}\b"), "google_api_key"),
    # Azure / Microsoft
    (re.compile(r"\b[A-Za-z0-9+/]{40,}==?\b"), "possible_base64_secret"),
    # Generic high-entropy strings assigned to secret-like variable names
    (re.compile(r"(?:secret|password|api_key|apikey|access_token|auth_token|private_key)\s*[=:]\s*['\"][A-Za-z0-9+/=_\-]{20,}['\"]", re.IGNORECASE), "hardcoded_credential"),
]

def iter_files():
    """Scan git-tracked files by default, fall back to filesystem walk."""
    try:
        cmd = ["git", "ls-files"]
        if paths:
            cmd += ["--", *[str(p) for p in paths]]
        out = subprocess.check_output(cmd, text=True)
        for rel in out.splitlines():
            if not rel:
                continue
            p = Path(rel)
            if is_excluded_dir(p):
                continue
            if not is_texty_file(p):
                continue
            if p.exists() and p.is_file():
                yield p
        return
    except Exception:
        scan_roots = paths or [Path(".")]

    seen = set()
    for base in scan_roots:
        base = base.resolve()
        if base.is_file():
            if base not in seen and is_texty_file(base) and not is_excluded_dir(base):
                seen.add(base)
                yield base
            continue
        if not base.exists():
            continue
        for root, dirs, files in os.walk(base):
            rp = Path(root)
            if is_excluded_dir(rp):
                dirs[:] = []
                continue
            dirs[:] = [d for d in dirs if not is_excluded_dir(rp / d)]
            for f in files:
                p = rp / f
                if p in seen:
                    continue
                seen.add(p)
                if not is_texty_file(p):
                    continue
                yield p

hits = []
for f in iter_files():
    try:
        data = f.read_bytes()
    except Exception:
        continue
    # Skip binary files
    if b"\x00" in data[:4096]:
        continue
    text = data.decode("utf-8", errors="ignore")
    for i, line in enumerate(text.splitlines(), start=1):
        if "[REDACTED]" in line:
            continue
        # Allow obvious placeholder examples (docs/templates)
        if "XXXX" in line or "xxxxxxxx" in line:
            continue
        for rx, label in PATTERNS:
            if rx.search(line):
                hits.append(f"{f}:{i}: {label}: {line.strip()[:240]}")
                break

if hits:
    print(f"[validate-no-secrets] FAIL: Potential secrets detected ({len(hits)})")
    for h in hits[:50]:
        print(f"  - {h}")
    if len(hits) > 50:
        print(f"  ... {len(hits) - 50} more")
    sys.exit(1)

print("[validate-no-secrets] PASS: No secrets detected")
sys.exit(0)
PY
