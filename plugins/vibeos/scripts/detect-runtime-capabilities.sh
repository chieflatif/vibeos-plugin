#!/usr/bin/env bash
# VibeOS Plugin — Runtime Capability Matrix
# Detects local Claude/Codex capabilities and writes .vibeos/runtime-capabilities.json.
#
# Usage:
#   bash scripts/detect-runtime-capabilities.sh [--project-dir DIR] [--out FILE] [--json] [--quiet]
set -euo pipefail

FRAMEWORK_VERSION="2.2.0"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY_SCRIPT="$SCRIPT_DIR/runtime-capabilities.py"

if [[ ! -f "$PY_SCRIPT" ]]; then
  echo "[runtime-capabilities] FAIL: runtime-capabilities.py not found at $PY_SCRIPT" >&2
  exit 1
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 "$PY_SCRIPT" "$@"
fi

echo "[runtime-capabilities] FAIL: python3 is required for runtime capability detection" >&2
exit 1
