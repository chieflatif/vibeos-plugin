#!/usr/bin/env bash
# VibeOS — Git Pre-Commit Hook Installer
# Installs a git pre-commit hook that runs VibeOS pre_commit quality gates
# before each commit. This ensures local commits bypass no gates.
#
# Usage:
#   bash scripts/setup-git-hooks.sh
#   bash scripts/setup-git-hooks.sh --project-dir /path/to/project
#   bash scripts/setup-git-hooks.sh --force   # Overwrite existing hook
#   bash scripts/setup-git-hooks.sh --remove  # Remove the VibeOS hook
#
# Exit codes:
#   0 = Hook installed/removed successfully
#   1 = Error (not a git repo, hook exists without --force)
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="2.0.0"
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

echo "[$SCRIPT_NAME] Git Pre-Commit Hook Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verify git repo
if ! git -C "$PROJECT_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
  echo "[$SCRIPT_NAME] FAIL: $PROJECT_ROOT is not a git repository"
  exit 1
fi

GIT_DIR=$(git -C "$PROJECT_ROOT" rev-parse --git-dir)
HOOK_FILE="$GIT_DIR/hooks/pre-commit"
VIBEOS_MARKER="# VibeOS pre-commit gate runner"

# ─── Remove Mode ────────────────────────────────────────────────
if [[ "$REMOVE" == "true" ]]; then
  if [[ -f "$HOOK_FILE" ]] && grep -q "$VIBEOS_MARKER" "$HOOK_FILE" 2>/dev/null; then
    rm -f "$HOOK_FILE"
    echo "[$SCRIPT_NAME] Removed VibeOS pre-commit hook"
    exit 0
  else
    echo "[$SCRIPT_NAME] No VibeOS pre-commit hook found"
    exit 0
  fi
fi

# ─── Check for Existing Hook ───────────────────────────────────
if [[ -f "$HOOK_FILE" ]]; then
  # Check if it's a VibeOS hook (safe to overwrite)
  if grep -q "$VIBEOS_MARKER" "$HOOK_FILE" 2>/dev/null; then
    echo "[$SCRIPT_NAME] Updating existing VibeOS pre-commit hook"
  elif [[ "$FORCE" == "true" ]]; then
    echo "[$SCRIPT_NAME] WARN: Overwriting existing pre-commit hook (--force)"
    # Back up the existing hook
    cp "$HOOK_FILE" "${HOOK_FILE}.bak"
    echo "[$SCRIPT_NAME] Backup saved to ${HOOK_FILE}.bak"
  else
    # Check if it's just the sample template
    if grep -q "^# An example hook" "$HOOK_FILE" 2>/dev/null || grep -q "sample" "$HOOK_FILE" 2>/dev/null; then
      echo "[$SCRIPT_NAME] Replacing default sample hook"
    else
      echo "[$SCRIPT_NAME] FAIL: Pre-commit hook already exists"
      echo "[$SCRIPT_NAME] Use --force to overwrite (existing hook will be backed up)"
      exit 1
    fi
  fi
fi

# ─── Install Hook ──────────────────────────────────────────────
mkdir -p "$(dirname "$HOOK_FILE")"

# Detect gate runner location
GATE_RUNNER=""
if [[ -f "$PROJECT_ROOT/.vibeos/scripts/gate-runner.sh" ]]; then
  GATE_RUNNER=".vibeos/scripts/gate-runner.sh"
elif [[ -f "$PROJECT_ROOT/scripts/gate-runner.sh" ]]; then
  GATE_RUNNER="scripts/gate-runner.sh"
fi

cat > "$HOOK_FILE" << HOOKEOF
#!/usr/bin/env bash
$VIBEOS_MARKER
# Installed by VibeOS setup-git-hooks.sh
# Runs pre_commit quality gates before each commit
# Remove with: bash scripts/setup-git-hooks.sh --remove

set -euo pipefail

PROJECT_DIR="\$(git rev-parse --show-toplevel)"

# Locate gate runner
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

echo "[pre-commit] Running VibeOS quality gates..."
if bash "\$GATE_RUNNER" pre_commit --project-dir "\$PROJECT_DIR" --timeout 60; then
  echo "[pre-commit] Quality gates passed"
  exit 0
else
  echo ""
  echo "[pre-commit] Quality gates FAILED — commit blocked"
  echo "[pre-commit] Fix the issues above, then try committing again"
  echo "[pre-commit] To bypass (not recommended): git commit --no-verify"
  exit 1
fi
HOOKEOF

chmod +x "$HOOK_FILE"

echo "[$SCRIPT_NAME] Pre-commit hook installed at $HOOK_FILE"
if [[ -n "$GATE_RUNNER" ]]; then
  echo "[$SCRIPT_NAME] Gate runner: $GATE_RUNNER"
else
  echo "[$SCRIPT_NAME] NOTE: gate-runner.sh not yet present — hook will auto-detect on commit"
fi
echo "[$SCRIPT_NAME] PASS: Git pre-commit hook ready"
