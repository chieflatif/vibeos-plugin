#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FORMULA_BREWFILE="$SCRIPT_DIR/Brewfile.formulae"

INCLUDE_AUTH=false

usage() {
  cat <<'EOF'
Usage:
  ./doctor.sh [--include-auth]

Audits the current machine without installing anything. Use this before running
the bootstrap on a partially configured Mac or before deciding what to upgrade
on the current Mac.

Options:
  --include-auth  Include GitHub and Azure auth status. Tokens are masked by
                  the upstream tools, but account names may be printed.
  -h, --help      Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --include-auth)
      INCLUDE_AUTH=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[doctor] FAIL: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

section() {
  printf '\n## %s\n' "$1"
}

command_status() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    printf '[doctor] present %-14s %s\n' "$name" "$(command -v "$name")"
  else
    printf '[doctor] missing %-14s\n' "$name"
  fi
}

version_if_present() {
  local name="$1"
  shift
  if command -v "$name" >/dev/null 2>&1; then
    printf '\n[%s]\n' "$name"
    "$@" 2>&1 | sed -n '1,8p'
  fi
}

cask_state() {
  local cask="$1"
  local equivalent="$2"
  if brew list --cask "$cask" >/dev/null 2>&1; then
    echo "[doctor] cask-managed $cask"
  elif [[ -n "$equivalent" && ( -e "$equivalent" || "$(command -v "$equivalent" 2>/dev/null || true)" != "" ) ]]; then
    echo "[doctor] unmanaged-present $cask via $equivalent"
  else
    echo "[doctor] missing-cask $cask"
  fi
}

section "System"
sw_vers 2>/dev/null || true
uname -m

section "Command Spine"
for tool in brew git gh jq yq rg fd tree wget node npm corepack pnpm python3 uv ruff docker az func claude codex cursor gcloud render stripe tofu redis-server postgres ffmpeg magick pdftotext pandoc; do
  command_status "$tool"
done

section "Versions"
version_if_present brew brew --version
version_if_present gh gh --version
version_if_present node node --version
version_if_present npm npm --version
version_if_present pnpm pnpm --version
version_if_present python3 python3 --version
version_if_present uv uv --version
version_if_present docker docker --version
version_if_present az az version
version_if_present func func --version
version_if_present claude claude --version
version_if_present codex codex --version

if command -v brew >/dev/null 2>&1; then
  section "Homebrew Bundle Formula Check"
  brew bundle check --verbose --file "$FORMULA_BREWFILE" || true

  section "Homebrew Outdated"
  brew outdated --verbose || true

  section "Cask Ownership"
  cask_state claude-code claude
  cask_state codex codex
  cask_state codex-app /Applications/Codex.app
  cask_state cursor /Applications/Cursor.app
  cask_state docker-desktop /Applications/Docker.app
  cask_state gcloud-cli gcloud
fi

section "npm Global Outdated"
if command -v npm >/dev/null 2>&1; then
  npm outdated -g --depth=0 || true
else
  echo "[doctor] npm missing"
fi

section "uv Python Versions"
if command -v uv >/dev/null 2>&1; then
  uv python list --only-installed || true
else
  echo "[doctor] uv missing"
fi

section "Docker Daemon"
if command -v docker >/dev/null 2>&1; then
  docker info >/dev/null 2>&1 && echo "[doctor] Docker daemon running" || echo "[doctor] Docker daemon not running"
else
  echo "[doctor] docker missing"
fi

if [[ "$INCLUDE_AUTH" == "true" ]]; then
  section "Auth Status"
  if command -v gh >/dev/null 2>&1; then
    gh auth status 2>&1 | sed -n '1,80p' || true
  fi
  if command -v az >/dev/null 2>&1; then
    az account show --query '{name:name, user:user.name, tenantId:tenantId}' -o json 2>/dev/null || true
  fi
fi
