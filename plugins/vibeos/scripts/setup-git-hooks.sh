#!/usr/bin/env bash
# VibeOS git hook installer.
#
# Installs:
# - a pre-commit hook that runs the VibeOS pre_commit gate phase
# - a commit-msg hook that validates commit message structure

set -euo pipefail

FRAMEWORK_VERSION="2.2.0"
SCRIPT_NAME="setup-git-hooks"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
FORCE=false
REMOVE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-dir) PROJECT_ROOT="$2"; shift 2 ;;
    --force) FORCE=true; shift ;;
    --remove) REMOVE=true; shift ;;
    -h|--help)
      echo "Usage: bash $0 [--project-dir PATH] [--force] [--remove]"
      exit 0
      ;;
    *) shift ;;
  esac
done

echo "[$SCRIPT_NAME] Git Hook Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

if ! git -C "$PROJECT_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  echo "[$SCRIPT_NAME] FAIL: $PROJECT_ROOT is not a git repository"
  exit 1
fi

RAW_GIT_DIR="$(git -C "$PROJECT_ROOT" rev-parse --git-dir)"
case "$RAW_GIT_DIR" in
  /*) GIT_DIR="$RAW_GIT_DIR" ;;
  *) GIT_DIR="$PROJECT_ROOT/$RAW_GIT_DIR" ;;
esac

resolve_hooks_dir() {
  local configured_path
  configured_path="$(git -C "$PROJECT_ROOT" config --path core.hooksPath 2>/dev/null || true)"

  if [[ -z "$configured_path" ]]; then
    printf '%s\n' "$GIT_DIR/hooks"
    return 0
  fi

  case "$configured_path" in
    /*) printf '%s\n' "$configured_path" ;;
    *) printf '%s\n' "$PROJECT_ROOT/$configured_path" ;;
  esac
}

HOOKS_DIR="$(resolve_hooks_dir)"
PRE_COMMIT_HOOK="$HOOKS_DIR/pre-commit"
COMMIT_MSG_HOOK="$HOOKS_DIR/commit-msg"
PRE_COMMIT_MARKER="# VibeOS pre-commit gate runner"
COMMIT_MSG_MARKER="# VibeOS commit-msg validator"

remove_hook_if_owned() {
  local path="$1"
  local marker="$2"
  if [[ -f "$path" ]] && grep -q "$marker" "$path" 2>/dev/null; then
    rm -f "$path"
    return 0
  fi
  return 1
}

check_existing_hook() {
  local path="$1"
  local marker="$2"
  local label="$3"

  if [[ ! -f "$path" ]]; then
    return 0
  fi

  if grep -q "$marker" "$path" 2>/dev/null; then
    echo "[$SCRIPT_NAME] Updating existing VibeOS $label hook"
    return 0
  fi

  if [[ "$FORCE" == "true" ]]; then
    echo "[$SCRIPT_NAME] WARN: Overwriting existing $label hook (--force)"
    cp "$path" "${path}.bak"
    echo "[$SCRIPT_NAME] Backup saved to ${path}.bak"
    return 0
  fi

  if grep -q "^# An example hook" "$path" 2>/dev/null || grep -q "sample" "$path" 2>/dev/null; then
    echo "[$SCRIPT_NAME] Replacing default sample $label hook"
    return 0
  fi

  echo "[$SCRIPT_NAME] FAIL: $label hook already exists"
  echo "[$SCRIPT_NAME] Use --force to overwrite (existing hook will be backed up)"
  exit 1
}

if [[ "$REMOVE" == "true" ]]; then
  removed_any=false
  if remove_hook_if_owned "$PRE_COMMIT_HOOK" "$PRE_COMMIT_MARKER"; then
    echo "[$SCRIPT_NAME] Removed VibeOS pre-commit hook"
    removed_any=true
  fi
  if remove_hook_if_owned "$COMMIT_MSG_HOOK" "$COMMIT_MSG_MARKER"; then
    echo "[$SCRIPT_NAME] Removed VibeOS commit-msg hook"
    removed_any=true
  fi
  if [[ "$removed_any" == "true" ]]; then
    exit 0
  fi
  echo "[$SCRIPT_NAME] No VibeOS git hooks found"
  exit 0
fi

check_existing_hook "$PRE_COMMIT_HOOK" "$PRE_COMMIT_MARKER" "pre-commit"
check_existing_hook "$COMMIT_MSG_HOOK" "$COMMIT_MSG_MARKER" "commit-msg"

mkdir -p "$HOOKS_DIR"

GATE_RUNNER=""
if [[ -f "$PROJECT_ROOT/.vibeos/scripts/gate-runner.sh" ]]; then
  GATE_RUNNER=".vibeos/scripts/gate-runner.sh"
elif [[ -f "$PROJECT_ROOT/scripts/gate-runner.sh" ]]; then
  GATE_RUNNER="scripts/gate-runner.sh"
fi

cat > "$PRE_COMMIT_HOOK" <<HOOKEOF
#!/usr/bin/env bash
$PRE_COMMIT_MARKER
# Installed by VibeOS setup-git-hooks.sh

set -euo pipefail

PROJECT_DIR="\$(git rev-parse --show-toplevel)"

GATE_RUNNER=""
if [[ -f "\$PROJECT_DIR/.vibeos/scripts/gate-runner.sh" ]]; then
  GATE_RUNNER="\$PROJECT_DIR/.vibeos/scripts/gate-runner.sh"
elif [[ -f "\$PROJECT_DIR/scripts/gate-runner.sh" ]]; then
  GATE_RUNNER="\$PROJECT_DIR/scripts/gate-runner.sh"
fi

if [[ -z "\$GATE_RUNNER" ]]; then
  echo "[pre-commit] WARN: gate-runner.sh not found — skipping quality gates"
  exit 0
fi

MANIFEST_PATH=""
if [[ -f "\$PROJECT_DIR/.claude/quality-gate-manifest.json" ]]; then
  MANIFEST_PATH="\$PROJECT_DIR/.claude/quality-gate-manifest.json"
elif [[ -f "\$PROJECT_DIR/quality-gate-manifest.json" ]]; then
  MANIFEST_PATH="\$PROJECT_DIR/quality-gate-manifest.json"
fi

if [[ -z "\$MANIFEST_PATH" ]]; then
  echo "[pre-commit] WARN: quality-gate-manifest.json not found — skipping VibeOS gates"
  echo "[pre-commit] NOTE: Generate the manifest during planning; commit-time gate enforcement starts after that"
  exit 0
fi

echo "[pre-commit] Running VibeOS quality gates..."
if bash "\$GATE_RUNNER" pre_commit --project-dir "\$PROJECT_DIR" --manifest "\$MANIFEST_PATH" --timeout 60; then
  echo "[pre-commit] Quality gates passed"
  exit 0
fi

echo ""
echo "[pre-commit] Quality gates FAILED — commit blocked"
echo "[pre-commit] Fix the issues above, then try committing again"
exit 1
HOOKEOF

cat > "$COMMIT_MSG_HOOK" <<'HOOKEOF'
#!/usr/bin/env bash
# VibeOS commit-msg validator
# Installed by VibeOS setup-git-hooks.sh

set -euo pipefail

PROJECT_DIR="$(git rev-parse --show-toplevel)"

VALIDATOR=""
if [[ -f "$PROJECT_DIR/scripts/validate-commit-msg.sh" ]]; then
  VALIDATOR="$PROJECT_DIR/scripts/validate-commit-msg.sh"
elif [[ -f "$PROJECT_DIR/.vibeos/scripts/validate-commit-msg.sh" ]]; then
  VALIDATOR="$PROJECT_DIR/.vibeos/scripts/validate-commit-msg.sh"
fi

if [[ -z "$VALIDATOR" ]]; then
  exit 0
fi

bash "$VALIDATOR" "$1"
HOOKEOF

chmod +x "$PRE_COMMIT_HOOK" "$COMMIT_MSG_HOOK"

echo "[$SCRIPT_NAME] Hooks directory: $HOOKS_DIR"
echo "[$SCRIPT_NAME] Pre-commit hook installed at $PRE_COMMIT_HOOK"
echo "[$SCRIPT_NAME] Commit-msg hook installed at $COMMIT_MSG_HOOK"
if [[ -n "$GATE_RUNNER" ]]; then
  echo "[$SCRIPT_NAME] Gate runner: $GATE_RUNNER"
else
  echo "[$SCRIPT_NAME] NOTE: gate-runner.sh not yet present — hook will auto-detect on commit"
fi
echo "[$SCRIPT_NAME] PASS: Git hooks ready"
