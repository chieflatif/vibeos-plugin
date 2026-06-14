#!/usr/bin/env bash
# VibeOS Plugin — Lane Readiness Check

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/lane-readiness.py" "$@"
