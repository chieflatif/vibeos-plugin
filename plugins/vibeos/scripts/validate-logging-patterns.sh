#!/usr/bin/env bash
# VibeOS Plugin — Logging Pattern Validation Gate
# Checks for structured logging and request/correlation ID usage.
#
# Usage:
#   bash scripts/validate-logging-patterns.sh
#
# Environment:
#   SCAN_DIR  — directory to scan (default: auto-detect source dir)
#   LANGUAGE  — python|typescript|javascript|go|rust|java (default: auto-detect)
#
# Exit codes:
#   0 = Logging patterns found
#   1 = Missing structured logging patterns
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="2.1.0"
GATE_NAME="validate-logging-patterns"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate-logging-patterns.sh

Environment:
  SCAN_DIR   Directory to scan (default: auto-detect source dir)
  LANGUAGE   python|typescript|javascript|go|rust|java (default: auto-detect)

Checks:
  - Structured logging is used (not bare print/console.log for logging)
  - request_id / correlation_id / trace_id patterns exist
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] Logging Pattern Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Auto-detect source directory
if [[ -z "${SCAN_DIR:-}" ]]; then
  for candidate in src lib app; do
    if [[ -d "$repo_root/$candidate" ]]; then
      SCAN_DIR="$candidate"
      break
    fi
  done
fi

if [[ -z "${SCAN_DIR:-}" ]]; then
  echo "[$GATE_NAME] WARN: No source directory found. Set SCAN_DIR env var."
  echo "[$GATE_NAME] SKIP: Cannot validate logging without source directory"
  exit 0
fi

scan_path="$repo_root/$SCAN_DIR"
if [[ ! -d "$scan_path" ]]; then
  echo "[$GATE_NAME] WARN: Directory not found: $scan_path"
  echo "[$GATE_NAME] SKIP: SCAN_DIR does not exist"
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

python3 - "$scan_path" "$LANGUAGE" <<'PY'
import sys
from pathlib import Path

scan_dir = Path(sys.argv[1])
language = sys.argv[2]

def read_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

# Select file extensions based on language
ext_map = {
    "python": ["*.py"],
    "javascript": ["*.js", "*.jsx", "*.ts", "*.tsx", "*.mjs"],
    "typescript": ["*.ts", "*.tsx", "*.js", "*.jsx"],
    "go": ["*.go"],
    "rust": ["*.rs"],
    "java": ["*.java", "*.kt"],
}
extensions = ext_map.get(language, ["*.py", "*.js", "*.ts", "*.go", "*.rs", "*.java"])

files = []
for ext in extensions:
    files.extend(scan_dir.rglob(ext))

if not files:
    print(f"[validate-logging-patterns] WARN: No source files found in {scan_dir}")
    sys.exit(0)

blob = "\n".join(read_text(p) for p in files)

# Language-specific logging checks
logging_checks = {
    "python": [
        ("structured logging module", [
            "import logging", "import structlog", "getLogger",
            "structlog.get_logger", "logging.getLogger",
        ]),
    ],
    "javascript": [
        ("structured logging module", [
            "winston", "pino", "bunyan", "log4js", "morgan",
            "import.*logger", "require.*logger", "createLogger",
        ]),
    ],
    "typescript": [
        ("structured logging module", [
            "winston", "pino", "bunyan", "log4js", "morgan",
            "import.*logger", "require.*logger", "createLogger",
        ]),
    ],
    "go": [
        ("structured logging module", [
            "log/slog", "go.uber.org/zap", "logrus", "zerolog",
            "slog.New", "zap.New",
        ]),
    ],
    "rust": [
        ("structured logging module", [
            "tracing", "log::", "env_logger", "slog",
            "tracing::info", "log::info",
        ]),
    ],
    "java": [
        ("structured logging module", [
            "org.slf4j", "log4j", "java.util.logging",
            "LoggerFactory", "Logger.getLogger",
        ]),
    ],
}

# Correlation ID patterns (universal)
correlation_patterns = ["request_id", "correlation_id", "trace_id", "requestId", "correlationId", "traceId", "x-request-id"]

checks = []

# Logging module check
lang_checks = logging_checks.get(language, logging_checks.get("python", []))
for name, patterns in lang_checks:
    found = any(p in blob for p in patterns)
    checks.append((name, found))

# Correlation ID check
correlation_found = any(p in blob for p in correlation_patterns)
checks.append(("request_id or correlation_id referenced", correlation_found))

fail = False
for name, ok in checks:
    if ok:
        print(f"[validate-logging-patterns] PASS: {name}")
    else:
        print(f"[validate-logging-patterns] FAIL: {name}")
        fail = True

sys.exit(1 if fail else 0)
PY

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[$GATE_NAME] Logging pattern validation complete"
