#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FORMULA_BREWFILE="$SCRIPT_DIR/Brewfile.formulae"

FAILURES=0
WARNINGS=0

require_command() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    printf '[verify] PASS: %-14s %s\n' "$name" "$(command -v "$name")"
  else
    printf '[verify] FAIL: %-14s missing\n' "$name"
    FAILURES=$((FAILURES + 1))
  fi
}

warn_command() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    printf '[verify] PASS: %-14s %s\n' "$name" "$(command -v "$name")"
  else
    printf '[verify] WARN: %-14s missing\n' "$name"
    WARNINGS=$((WARNINGS + 1))
  fi
}

print_version() {
  local name="$1"
  shift
  if command -v "$name" >/dev/null 2>&1; then
    printf '\n[%s]\n' "$name"
    "$@" 2>&1 | sed -n '1,4p'
  fi
}

check_node_floor() {
  if ! command -v node >/dev/null 2>&1; then
    return
  fi
  if node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 24 ? 0 : 1)' >/dev/null 2>&1; then
    echo "[verify] PASS: node major version is >= 24"
  else
    echo "[verify] WARN: node major version is below 24; latifhorstweb currently declares node >=24"
    WARNINGS=$((WARNINGS + 1))
  fi
}

check_uv_python() {
  if ! command -v uv >/dev/null 2>&1; then
    return
  fi

  for version in 3.10 3.11 3.12; do
    if uv python find "$version" >/dev/null 2>&1; then
      echo "[verify] PASS: uv Python $version available"
    else
      echo "[verify] WARN: uv Python $version not found"
      WARNINGS=$((WARNINGS + 1))
    fi
  done
}

check_docker_running() {
  if ! command -v docker >/dev/null 2>&1; then
    return
  fi

  if docker info >/dev/null 2>&1; then
    echo "[verify] PASS: Docker daemon is running"
  else
    echo "[verify] WARN: Docker CLI exists but daemon is not running; open Docker Desktop"
    WARNINGS=$((WARNINGS + 1))
  fi
}

check_brew_bundle() {
  if ! command -v brew >/dev/null 2>&1; then
    return
  fi

  if brew bundle check --file "$FORMULA_BREWFILE" >/dev/null 2>&1; then
    echo "[verify] PASS: formula Brewfile dependencies are installed"
  else
    echo "[verify] WARN: formula Brewfile check reports missing dependencies"
    WARNINGS=$((WARNINGS + 1))
  fi
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

check_cask_or_equivalent() {
  local cask="$1"
  local app_path command_name
  app_path="$(cask_app_path "$cask")"
  command_name="$(cask_command "$cask")"

  if brew list --cask "$cask" >/dev/null 2>&1; then
    echo "[verify] PASS: cask $cask is Homebrew-managed"
    return
  fi

  if [[ -n "$app_path" && -e "$app_path" ]]; then
    echo "[verify] PASS: cask $cask equivalent exists unmanaged at $app_path"
    return
  fi

  if [[ -n "$command_name" ]] && command -v "$command_name" >/dev/null 2>&1; then
    echo "[verify] PASS: cask $cask equivalent command exists unmanaged at $(command -v "$command_name")"
    return
  fi

  echo "[verify] WARN: cask $cask is missing and no equivalent was found"
  WARNINGS=$((WARNINGS + 1))
}

check_cask_state() {
  check_cask_or_equivalent claude-code
  check_cask_or_equivalent codex
  check_cask_or_equivalent codex-app
  check_cask_or_equivalent cursor
  check_cask_or_equivalent docker-desktop
  check_cask_or_equivalent gcloud-cli
}

check_vibeos_runtime_detection() {
  local detector="$REPO_ROOT/plugins/vibeos/scripts/detect-runtime-capabilities.sh"
  if [[ ! -x "$detector" && ! -f "$detector" ]]; then
    echo "[verify] WARN: VibeOS runtime detector not found in this checkout"
    WARNINGS=$((WARNINGS + 1))
    return
  fi

  echo "[verify] INFO: Running VibeOS runtime capability detection"
  if bash "$detector" --project-dir "$REPO_ROOT"; then
    echo "[verify] PASS: VibeOS runtime capability detection completed"
  else
    echo "[verify] WARN: VibeOS runtime capability detection failed"
    WARNINGS=$((WARNINGS + 1))
  fi
}

main() {
  echo "[verify] macOS workstation bootstrap verification"

  require_command brew
  require_command git
  require_command gh
  require_command jq
  require_command rg
  require_command node
  require_command npm
  require_command corepack
  require_command python3
  require_command uv
  require_command docker
  require_command az
  require_command func
  require_command claude
  require_command codex
  warn_command cursor

  check_node_floor
  check_uv_python
  check_docker_running
  check_brew_bundle
  check_cask_state
  check_vibeos_runtime_detection

  print_version brew brew --version
  print_version node node --version
  print_version npm npm --version
  print_version python3 python3 --version
  print_version uv uv --version
  print_version docker docker --version
  print_version az az version
  print_version func func --version
  print_version claude claude --version
  print_version codex codex --version

  echo
  echo "[verify] Summary: failures=$FAILURES warnings=$WARNINGS"
  if [[ "$FAILURES" -gt 0 ]]; then
    exit 1
  fi
}

main "$@"
