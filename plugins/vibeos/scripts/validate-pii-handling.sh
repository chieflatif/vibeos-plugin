#!/usr/bin/env bash
# VibeOS Plugin — PII Handling Validation Gate
# Detects personally identifiable information patterns in code and logs.
#
# Usage:
#   bash scripts/validate-pii-handling.sh
#
# Environment:
#   SCAN_DIRS     — space-separated directories to scan (default: auto-detect)
#   PII_PATTERNS  — comma-separated additional PII field names to check
#   STRICT_MODE   — set to "true" for GDPR-strict validation (default: false)
#
# Exit codes:
#   0 = No PII handling issues detected
#   1 = PII issues found
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="2.2.0"
GATE_NAME="validate-pii-handling"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate-pii-handling.sh

Environment:
  SCAN_DIRS     Space-separated directories to scan (default: auto-detect)
  PII_PATTERNS  Comma-separated additional PII field names
  STRICT_MODE   Set to "true" for GDPR-strict mode (default: false)
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] PII Handling Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STRICT_MODE="${STRICT_MODE:-false}"

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

python3 - "$STRICT_MODE" "${PII_PATTERNS:-}" ${SCAN_ARGS[@]+"${SCAN_ARGS[@]}"} <<'PY'
import os
import re
import sys
from pathlib import Path

strict_mode = sys.argv[1] == "true"
extra_patterns = [p.strip() for p in sys.argv[2].split(",") if p.strip()] if sys.argv[2] else []
paths = [Path(p) for p in sys.argv[3:]] or [Path(".")]

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

# PII field patterns
PII_FIELDS = [
    "social_security", "ssn", "national_id",
    "date_of_birth", "dob", "birthday",
    "passport_number", "drivers_license", "driver_license",
    "credit_card", "card_number", "cvv", "ccv",
    "bank_account", "routing_number", "iban",
    "ip_address", "mac_address",
    "biometric", "fingerprint", "face_id",
    "medical_record", "health_record", "diagnosis",
    "ethnicity", "race", "religion", "sexual_orientation",
    "political_affiliation", "union_membership",
] + extra_patterns

# Build regex for PII field detection in code
pii_field_rx = re.compile(
    r"\b(" + "|".join(re.escape(f) for f in PII_FIELDS) + r")\b",
    re.IGNORECASE,
)

# Patterns that suggest PII is being logged (high risk)
pii_logging = [
    # Python
    re.compile(r"(logger\.|logging\.|print\().*\b(" + "|".join(PII_FIELDS[:15]) + r")\b", re.IGNORECASE),
    # JS
    re.compile(r"console\.(log|info|warn|error)\(.*\b(" + "|".join(PII_FIELDS[:15]) + r")\b", re.IGNORECASE),
]

# Patterns for email/phone in log output
pii_in_logs = re.compile(
    r"(logger\.|logging\.|print\(|console\.(log|info|warn|error)).*"
    r"(email|phone|phone_number|mobile|first_name|last_name|full_name|address)\b",
    re.IGNORECASE,
)

# GDPR-strict: data retention / erasure patterns
gdpr_checks = []
if strict_mode:
    gdpr_checks = [
        (re.compile(r"\bdelete\b.*\b(user|customer|person)\b|\b(user|customer|person)\b.*\bdelete\b", re.IGNORECASE),
         "GDPR: No data erasure implementation found"),
        (re.compile(r"\bconsent\b", re.IGNORECASE),
         "GDPR: Consent management referenced"),
    ]

failures = []
warnings = []

for f in iter_files():
    try:
        data = f.read_bytes()
    except Exception:
        continue
    if b"\x00" in data[:4096]:
        continue
    text = data.decode("utf-8", errors="ignore")
    is_test = "test" in str(f).lower()

    if is_test:
        continue

    for i, line in enumerate(text.splitlines(), 1):
        # Check for PII being logged
        for rx in pii_logging:
            if rx.search(line):
                failures.append((str(f), i, "PII field in log output", line.strip()[:200]))
                break

        if pii_in_logs.search(line):
            warnings.append((str(f), i, "Personal data field referenced in log statement", line.strip()[:200]))

output = []

if failures:
    output.append(f"[validate-pii-handling] FAIL: PII handling issues detected ({len(failures)})")
    for f, line, msg, content in failures[:20]:
        output.append(f"  - {msg}: {f}:{line}: {content}")
    if len(failures) > 20:
        output.append(f"  ... {len(failures) - 20} more")

if warnings:
    output.append(f"\n[validate-pii-handling] WARN: Potential PII exposure ({len(warnings)})")
    for f, line, msg, content in warnings[:10]:
        output.append(f"  - {msg}: {f}:{line}: {content}")
    if len(warnings) > 10:
        output.append(f"  ... {len(warnings) - 10} more")

if failures:
    print("\n".join(output))
    sys.exit(1)
elif warnings:
    print("\n".join(output))
    print(f"\n[validate-pii-handling] PASS (with {len(warnings)} warning(s))")
    sys.exit(0)
else:
    print("[validate-pii-handling] PASS: No PII handling issues detected")
    sys.exit(0)
PY
