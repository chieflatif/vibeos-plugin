#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BREWFILE="$SCRIPT_DIR/Brewfile"
FORMULA_BREWFILE="$SCRIPT_DIR/Brewfile.formulae"
OPTIONAL_NPM_GLOBALS="$SCRIPT_DIR/optional-npm-globals.txt"

APPLY=false
WITH_NPM_GLOBALS=false
FORCE_CASK_OWNERSHIP=false

usage() {
  cat <<'EOF'
Usage:
  ./install-macos.sh [--apply] [--with-npm-globals] [--force-cask-ownership]

Default mode is dry-run. Pass --apply to install tools.

Options:
  --apply             Run install commands instead of printing them.
  --with-npm-globals  Install optional npm globals from optional-npm-globals.txt.
  --force-cask-ownership
                      Try to install Homebrew casks even when an equivalent
                      unmanaged app or binary already exists.
  -h, --help          Show this help.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply)
      APPLY=true
      shift
      ;;
    --with-npm-globals)
      WITH_NPM_GLOBALS=true
      shift
      ;;
    --force-cask-ownership)
      FORCE_CASK_OWNERSHIP=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[install-macos] FAIL: unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

run() {
  echo "+ $*"
  if [[ "$APPLY" == "true" ]]; then
    "$@"
  fi
}

run_shell() {
  echo "+ $*"
  if [[ "$APPLY" == "true" ]]; then
    eval "$*"
  fi
}

require_macos() {
  if [[ "$(uname -s)" != "Darwin" ]]; then
    echo "[install-macos] FAIL: this bootstrap is macOS-only." >&2
    exit 2
  fi
}

ensure_xcode_cli_tools() {
  if xcode-select -p >/dev/null 2>&1; then
    echo "[install-macos] PASS: Xcode Command Line Tools found"
    return
  fi

  echo "[install-macos] WARN: Xcode Command Line Tools are not installed"
  run xcode-select --install
  if [[ "$APPLY" == "true" ]]; then
    echo "[install-macos] Re-run this script after the Apple installer finishes."
    exit 2
  fi
}

ensure_homebrew() {
  if command -v brew >/dev/null 2>&1; then
    echo "[install-macos] PASS: Homebrew found at $(command -v brew)"
    return
  fi

  echo "[install-macos] WARN: Homebrew is not installed"
  run_shell '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'

  if [[ -x "/opt/homebrew/bin/brew" ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  elif [[ -x "/usr/local/bin/brew" ]]; then
    eval "$(/usr/local/bin/brew shellenv)"
  fi
}

install_brew_bundle() {
  if [[ ! -f "$BREWFILE" ]]; then
    echo "[install-macos] FAIL: Brewfile missing at $BREWFILE" >&2
    exit 2
  fi
  if [[ ! -f "$FORMULA_BREWFILE" ]]; then
    echo "[install-macos] FAIL: formula Brewfile missing at $FORMULA_BREWFILE" >&2
    exit 2
  fi

  run brew update
  run brew bundle --file "$FORMULA_BREWFILE"
}

cask_app_path() {
  case "$1" in
    codex-app) echo "/Applications/Codex.app" ;;
    cursor) echo "/Applications/Cursor.app" ;;
    docker-desktop) echo "/Applications/Docker.app" ;;
    gcloud-cli) echo "/opt/homebrew/share/google-cloud-sdk/bin/gcloud" ;;
    *) echo "" ;;
  esac
}

cask_command() {
  case "$1" in
    claude-code) echo "claude" ;;
    codex) echo "codex" ;;
    cursor) echo "cursor" ;;
    docker-desktop) echo "docker" ;;
    gcloud-cli) echo "gcloud" ;;
    *) echo "" ;;
  esac
}

cask_equivalent_exists() {
  local cask="$1"
  local app_path command_name
  app_path="$(cask_app_path "$cask")"
  command_name="$(cask_command "$cask")"

  if [[ -n "$app_path" && -e "$app_path" ]]; then
    return 0
  fi
  if [[ -n "$command_name" ]] && command -v "$command_name" >/dev/null 2>&1; then
    return 0
  fi
  return 1
}

install_casks_safely() {
  local casks=(
    "claude-code"
    "codex"
    "codex-app"
    "cursor"
    "docker-desktop"
    "gcloud-cli"
  )

  local cask
  for cask in "${casks[@]}"; do
    if brew list --cask "$cask" >/dev/null 2>&1; then
      run brew upgrade --cask "$cask"
      continue
    fi

    if cask_equivalent_exists "$cask" && [[ "$FORCE_CASK_OWNERSHIP" != "true" ]]; then
      echo "[install-macos] WARN: $cask equivalent already exists but is not Homebrew-managed; skipping cask."
      echo "[install-macos] NOTE: rerun with --force-cask-ownership if you intentionally want Homebrew to try managing it."
      continue
    fi

    run brew install --cask "$cask"
  done
}

configure_node_tools() {
  if command -v corepack >/dev/null 2>&1 || [[ "$APPLY" != "true" ]]; then
    run corepack enable
    run corepack enable pnpm
  else
    echo "[install-macos] WARN: corepack is not available yet"
  fi
}

install_python_versions() {
  if command -v uv >/dev/null 2>&1 || [[ "$APPLY" != "true" ]]; then
    run uv python install 3.10 3.11 3.12
  else
    echo "[install-macos] WARN: uv is not available yet"
  fi
}

install_optional_npm_globals() {
  if [[ "$WITH_NPM_GLOBALS" != "true" ]]; then
    echo "[install-macos] SKIP: optional npm globals disabled"
    return
  fi

  if [[ ! -f "$OPTIONAL_NPM_GLOBALS" ]]; then
    echo "[install-macos] FAIL: optional npm globals file missing at $OPTIONAL_NPM_GLOBALS" >&2
    exit 2
  fi

  while IFS= read -r package_name; do
    [[ -z "$package_name" || "$package_name" =~ ^# ]] && continue
    run npm install -g "$package_name"
  done < "$OPTIONAL_NPM_GLOBALS"
}

print_next_steps() {
  cat <<'EOF'

[install-macos] Next manual steps:
  1. Open Docker Desktop and complete first-run setup.
  2. Run: gh auth login
  3. Run: az login
  4. Run: claude
  5. Run: codex
  6. Run: ./verify.sh

For each project that should use VibeOS:
  bash /path/to/vibeos-plugin/vibeos-init.sh
  bash /path/to/vibeos-plugin/vibeos-init-codex.sh
  bash .vibeos/scripts/detect-runtime-capabilities.sh --project-dir .
EOF
}

main() {
  if [[ "$APPLY" != "true" ]]; then
    echo "[install-macos] DRY RUN: pass --apply to install."
  fi

  require_macos
  ensure_xcode_cli_tools
  ensure_homebrew
  install_brew_bundle
  install_casks_safely
  configure_node_tools
  install_python_versions
  install_optional_npm_globals
  print_next_steps
}

main "$@"
