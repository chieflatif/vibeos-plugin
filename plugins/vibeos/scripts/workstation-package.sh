#!/usr/bin/env bash
# FILE-SIZE-EXCEPTION: WO-148 — optional macOS workstation package checker/installer is intentionally self-contained so fresh clones can dry-run before auxiliary package files exist.
set -euo pipefail

FRAMEWORK_VERSION="2.3.0"
TOOL_NAME="workstation-package"

MODE="${WORKSTATION_PACKAGE_MODE:-check}"
APPLY=false
WITH_NPM_GLOBALS=false
FORCE_CASK_OWNERSHIP=false
INCLUDE_AUTH=false
FAILURES=0
WARNINGS=0

TAPS=("azure/functions" "stripe/stripe-cli")
FORMULAE=(
  "git" "gh" "jq" "yq" "ripgrep" "fd" "tree" "wget"
  "node" "uv" "ruff" "mise" "go" "cmake"
  "azure-cli" "azure/functions/azure-functions-core-tools@4"
  "render" "stripe/stripe-cli/stripe" "opentofu" "cloudflared" "rclone"
  "redis" "postgresql@16" "ffmpeg" "imagemagick" "poppler" "pandoc"
)
CASKS=("claude-code" "codex" "codex-app" "cursor" "docker-desktop" "gcloud-cli")
OPTIONAL_NPM_GLOBALS=(
  "typescript" "tsx" "@azure/static-web-apps-cli" "@pnp/cli-microsoft365"
  "airtable-mcp-server" "exa-mcp-server" "firecrawl-mcp" "mcp-sqlite"
)
COMMAND_SPINE=(
  "brew" "git" "gh" "jq" "yq" "rg" "fd" "tree" "wget" "node" "npm"
  "corepack" "pnpm" "python3" "uv" "ruff" "docker" "az" "func"
  "claude" "codex" "cursor" "gcloud" "render" "stripe" "tofu"
  "redis-server" "postgres" "ffmpeg" "magick" "pdftotext" "pandoc"
)
VERIFY_REQUIRED=(
  "brew" "git" "gh" "jq" "rg" "node" "npm" "corepack" "python3"
  "uv" "docker" "az" "func" "claude" "codex"
)

usage() {
  cat <<'EOF'
Usage:
  bash .vibeos/scripts/workstation-package.sh [check|install|verify] [options]

Modes:
  check     Audit workstation package state without changing anything (default)
  install   Dry-run the macOS package installer; pass --apply to install
  verify    Verify the baseline command spine after installation/manual sign-in

Options:
  --apply                  Execute install commands. Without this, install is dry-run.
  --with-npm-globals       Install optional npm globals during install mode.
  --force-cask-ownership   Try Homebrew cask ownership even if an equivalent app exists.
  --include-auth           Include gh/az auth status in check mode.
  -h, --help               Show this help.

The workstation package is optional harness support. It never copies secrets or
account sessions, and it does not replace per-project VibeOS install.
EOF
}

log() { echo "[$TOOL_NAME] $*"; }

section() {
  printf '\n## %s\n' "$1"
}

run_cmd() {
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

is_macos() {
  [[ "$(uname -s)" == "Darwin" ]]
}

parse_args() {
  if [[ $# -gt 0 && ! "${1:-}" =~ ^- ]]; then
    MODE="$1"
    shift
  fi
  case "$MODE" in
    doctor) MODE="check" ;;
    dry-run) MODE="install" ;;
    check|install|verify) ;;
    *) echo "[$TOOL_NAME] FAIL: unknown mode: $MODE" >&2; usage >&2; exit 2 ;;
  esac
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --apply) APPLY=true; shift ;;
      --with-npm-globals) WITH_NPM_GLOBALS=true; shift ;;
      --force-cask-ownership) FORCE_CASK_OWNERSHIP=true; shift ;;
      --include-auth) INCLUDE_AUTH=true; shift ;;
      -h|--help) usage; exit 0 ;;
      *) echo "[$TOOL_NAME] FAIL: unknown argument: $1" >&2; usage >&2; exit 2 ;;
    esac
  done
}

write_brewfile() {
  local path="$1" item
  : > "$path"
  for item in "${TAPS[@]}"; do
    printf 'tap "%s"\n' "$item" >> "$path"
  done
  for item in "${FORMULAE[@]}"; do
    printf 'brew "%s"\n' "$item" >> "$path"
  done
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
  local cask="$1" app_path command_name
  app_path="$(cask_app_path "$cask")"
  command_name="$(cask_command "$cask")"
  [[ -n "$app_path" && -e "$app_path" ]] && return 0
  [[ -n "$command_name" ]] && command -v "$command_name" >/dev/null 2>&1 && return 0
  return 1
}

command_status() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    printf '[%s] present %-14s %s\n' "$TOOL_NAME" "$name" "$(command -v "$name")"
  else
    printf '[%s] missing %-14s\n' "$TOOL_NAME" "$name"
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

require_command() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    printf '[%s] PASS: %-14s %s\n' "$TOOL_NAME" "$name" "$(command -v "$name")"
  else
    printf '[%s] FAIL: %-14s missing\n' "$TOOL_NAME" "$name"
    FAILURES=$((FAILURES + 1))
  fi
}

warn_command() {
  local name="$1"
  if command -v "$name" >/dev/null 2>&1; then
    printf '[%s] PASS: %-14s %s\n' "$TOOL_NAME" "$name" "$(command -v "$name")"
  else
    printf '[%s] WARN: %-14s missing\n' "$TOOL_NAME" "$name"
    WARNINGS=$((WARNINGS + 1))
  fi
}

brew_bundle_check() {
  command -v brew >/dev/null 2>&1 || return 0
  local brewfile status
  brewfile="$(mktemp)"
  write_brewfile "$brewfile"
  set +e
  brew bundle check --verbose --file "$brewfile"
  status=$?
  set -e
  rm -f "$brewfile"
  return "$status"
}

cask_state() {
  local cask="$1"
  if brew list --cask "$cask" >/dev/null 2>&1; then
    echo "[$TOOL_NAME] cask-managed $cask"
  elif cask_equivalent_exists "$cask"; then
    echo "[$TOOL_NAME] unmanaged-present $cask"
  else
    echo "[$TOOL_NAME] missing-cask $cask"
  fi
}

check_cask_or_equivalent() {
  local cask="$1"
  if brew list --cask "$cask" >/dev/null 2>&1; then
    echo "[$TOOL_NAME] PASS: cask $cask is Homebrew-managed"
  elif cask_equivalent_exists "$cask"; then
    echo "[$TOOL_NAME] PASS: cask $cask equivalent exists unmanaged"
  else
    echo "[$TOOL_NAME] WARN: cask $cask is missing and no equivalent was found"
    WARNINGS=$((WARNINGS + 1))
  fi
}

mode_check() {
  if ! is_macos; then
    log "SKIP: workstation package check is currently macOS-only"
    return 0
  fi
  section "System"
  sw_vers 2>/dev/null || true
  uname -m
  section "Command Spine"
  for tool in "${COMMAND_SPINE[@]}"; do command_status "$tool"; done
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
    section "Homebrew Bundle Formula Check"; brew_bundle_check || true
    section "Homebrew Outdated"; brew outdated --verbose || true
    section "Cask Ownership"; for cask in "${CASKS[@]}"; do cask_state "$cask"; done
  fi
  section "npm Global Outdated"
  if command -v npm >/dev/null 2>&1; then
    npm outdated -g --depth=0 || true
  else
    echo "[$TOOL_NAME] npm missing"
  fi
  section "uv Python Versions"
  if command -v uv >/dev/null 2>&1; then
    uv python list --only-installed || true
  else
    echo "[$TOOL_NAME] uv missing"
  fi
  section "Docker Daemon"
  command -v docker >/dev/null 2>&1 && { docker info >/dev/null 2>&1 && echo "[$TOOL_NAME] Docker daemon running" || echo "[$TOOL_NAME] Docker daemon not running"; } || echo "[$TOOL_NAME] docker missing"
  if [[ "$INCLUDE_AUTH" == "true" ]]; then
    section "Auth Status"
    command -v gh >/dev/null 2>&1 && gh auth status 2>&1 | sed -n '1,80p' || true
    command -v az >/dev/null 2>&1 && az account show --query '{name:name, user:user.name, tenantId:tenantId}' -o json 2>/dev/null || true
  fi
}

ensure_xcode_cli_tools() {
  xcode-select -p >/dev/null 2>&1 && { log "PASS: Xcode Command Line Tools found"; return; }
  log "WARN: Xcode Command Line Tools are not installed"
  run_cmd xcode-select --install
  [[ "$APPLY" == "true" ]] && { log "Re-run after the Apple installer finishes."; exit 2; }
}

ensure_homebrew() {
  command -v brew >/dev/null 2>&1 && { log "PASS: Homebrew found at $(command -v brew)"; return; }
  log "WARN: Homebrew is not installed"
  run_shell '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  [[ -x "/opt/homebrew/bin/brew" ]] && eval "$(/opt/homebrew/bin/brew shellenv)"
  [[ -x "/usr/local/bin/brew" ]] && eval "$(/usr/local/bin/brew shellenv)"
}

install_formulae() {
  local brewfile status
  brewfile="$(mktemp)"
  write_brewfile "$brewfile"
  run_cmd brew update
  set +e
  run_cmd brew bundle --file "$brewfile"
  status=$?
  set -e
  rm -f "$brewfile"
  return "$status"
}

install_casks() {
  local cask
  for cask in "${CASKS[@]}"; do
    if brew list --cask "$cask" >/dev/null 2>&1; then
      run_cmd brew upgrade --cask "$cask"
    elif cask_equivalent_exists "$cask" && [[ "$FORCE_CASK_OWNERSHIP" != "true" ]]; then
      log "WARN: $cask equivalent already exists unmanaged; skipping cask"
      log "NOTE: use --force-cask-ownership to let Homebrew try managing it"
    else
      run_cmd brew install --cask "$cask"
    fi
  done
}

install_optional_npm_globals() {
  [[ "$WITH_NPM_GLOBALS" == "true" ]] || { log "SKIP: optional npm globals disabled"; return; }
  local package_name
  for package_name in "${OPTIONAL_NPM_GLOBALS[@]}"; do
    run_cmd npm install -g "$package_name"
  done
}

mode_install() {
  is_macos || { log "FAIL: workstation install is currently macOS-only" >&2; exit 2; }
  [[ "$APPLY" == "true" ]] || log "DRY RUN: pass --apply to install workstation tools"
  ensure_xcode_cli_tools
  ensure_homebrew
  install_formulae
  install_casks
  run_cmd corepack enable
  run_cmd corepack enable pnpm
  run_cmd uv python install 3.10 3.11 3.12
  install_optional_npm_globals
  cat <<'EOF'

[workstation-package] Next manual steps:
  1. Open Docker Desktop and complete first-run setup.
  2. Run: gh auth login
  3. Run: az login
  4. Run: claude
  5. Run: codex
  6. Run: bash plugins/vibeos/scripts/workstation-package.sh verify
  7. Install VibeOS per project with vibeos-init.sh and vibeos-init-codex.sh
EOF
}

check_node_floor() {
  command -v node >/dev/null 2>&1 || return 0
  node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 24 ? 0 : 1)' >/dev/null 2>&1 \
    && log "PASS: node major version is >= 24" \
    || { log "WARN: node major version is below 24"; WARNINGS=$((WARNINGS + 1)); }
}

check_uv_python() {
  command -v uv >/dev/null 2>&1 || return 0
  local version
  for version in 3.10 3.11 3.12; do
    uv python find "$version" >/dev/null 2>&1 \
      && log "PASS: uv Python $version available" \
      || { log "WARN: uv Python $version not found"; WARNINGS=$((WARNINGS + 1)); }
  done
}

mode_verify() {
  is_macos || { log "SKIP: workstation verification is currently macOS-only"; return 0; }
  local command_name cask detector project_dir
  for command_name in "${VERIFY_REQUIRED[@]}"; do require_command "$command_name"; done
  warn_command cursor
  check_node_floor
  check_uv_python
  command -v docker >/dev/null 2>&1 && { docker info >/dev/null 2>&1 && log "PASS: Docker daemon is running" || { log "WARN: Docker CLI exists but daemon is not running"; WARNINGS=$((WARNINGS + 1)); }; }
  if command -v brew >/dev/null 2>&1; then
    brew_bundle_check >/dev/null 2>&1 && log "PASS: baseline formulae are installed" || { log "WARN: baseline formula check reports missing dependencies"; WARNINGS=$((WARNINGS + 1)); }
    for cask in "${CASKS[@]}"; do check_cask_or_equivalent "$cask"; done
  fi
  detector="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/detect-runtime-capabilities.sh"
  project_dir="${PROJECT_ROOT:-$(pwd)}"
  if [[ -f "$detector" ]]; then
    bash "$detector" --project-dir "$project_dir" && log "PASS: runtime capability detection completed" || { log "WARN: runtime capability detection failed"; WARNINGS=$((WARNINGS + 1)); }
  else
    log "WARN: runtime capability detector not found next to workstation-package.sh"
    WARNINGS=$((WARNINGS + 1))
  fi
  log "Summary: failures=$FAILURES warnings=$WARNINGS"
  [[ "$FAILURES" -eq 0 ]]
}

main() {
  parse_args "$@"
  case "$MODE" in
    check) mode_check ;;
    install) mode_install ;;
    verify) mode_verify ;;
  esac
}

main "$@"
