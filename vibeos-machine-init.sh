#!/usr/bin/env bash
set -euo pipefail

# VibeOS machine bootstrap wrapper.
# This prepares the Mac workstation baseline. It is separate from vibeos-init.sh,
# which installs VibeOS governance into an individual project repository.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MACOS_BOOTSTRAP="$SCRIPT_DIR/workstation-bootstrap/macos/install-macos.sh"

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

if [[ ! -x "$MACOS_BOOTSTRAP" ]]; then
  echo "[vibeos-machine-init] FAIL: macOS bootstrap missing or not executable: $MACOS_BOOTSTRAP" >&2
  exit 2
fi

exec "$MACOS_BOOTSTRAP" "$@"
