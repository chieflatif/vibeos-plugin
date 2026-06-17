#!/usr/bin/env bash
set -euo pipefail

# VibeOS optional workstation package wrapper.
# The implementation lives in the shared harness at plugins/vibeos/scripts.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSTATION_PACKAGE="$SCRIPT_DIR/plugins/vibeos/scripts/workstation-package.sh"

usage() {
  cat <<'EOF'
Usage:
  ./vibeos-machine-init.sh [--apply] [--with-npm-globals] [--force-cask-ownership]

Default mode is dry-run. Pass --apply to install workstation tools.

This script prepares a new or partially configured Mac with the baseline tools
needed for Latif's VibeOS, Claude Code, Codex, Python, Node, Docker, Azure,
media, and deployment workflows.

Per-project VibeOS install remains separate:
  ./vibeos-init.sh
  ./vibeos-init-codex.sh
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "[vibeos-machine-init] FAIL: this machine bootstrap is currently macOS-only." >&2
  exit 2
fi

if [[ ! -x "$WORKSTATION_PACKAGE" ]]; then
  echo "[vibeos-machine-init] FAIL: workstation package missing or not executable: $WORKSTATION_PACKAGE" >&2
  exit 2
fi

exec "$WORKSTATION_PACKAGE" install "$@"
