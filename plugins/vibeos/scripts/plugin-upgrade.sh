#!/usr/bin/env bash
set -euo pipefail

# plugin-upgrade.sh — VibeOS plugin upgrade mechanism
# Upgrades plugin files while preserving project configuration, baselines,
# and custom gates. Supports rollback via pre-upgrade snapshot.
# Exit 0 = success, 1 = error

FRAMEWORK_VERSION="2.1.0"

usage() {
  echo "Usage:"
  echo "  $0 check --plugin-dir <path> --project-dir <path>"
  echo "  $0 upgrade --plugin-dir <path> --project-dir <path>"
  echo "  $0 rollback --project-dir <path>"
  echo "  $0 whats-new --plugin-dir <path> --project-dir <path>"
  echo ""
  echo "Commands:"
  echo "  check      Check if an upgrade is available"
  echo "  upgrade    Perform the upgrade (creates backup first)"
  echo "  rollback   Restore from pre-upgrade backup"
  echo "  whats-new  Show what changed in the new version"
  exit 1
}

COMMAND="${1:-}"
shift || true

PLUGIN_DIR=""
PROJECT_DIR=""

while [ $# -gt 0 ]; do
  case "$1" in
    --plugin-dir) PLUGIN_DIR="$2"; shift 2 ;;
    --project-dir) PROJECT_DIR="$2"; shift 2 ;;
    --help|-h) usage ;;
    *) echo "[plugin-upgrade] ERROR: Unknown argument: $1" >&2; exit 1 ;;
  esac
done

VIBEOS_DIR="${PROJECT_DIR:-.}/.vibeos"
VERSION_FILE="${VIBEOS_DIR}/version.json"
LEGACY_VERSION_FILE="${VIBEOS_DIR}/version.txt"
BACKUP_DIR="${VIBEOS_DIR}/upgrade-backup"

# Preserved paths (never overwritten during upgrade)
PRESERVED_PATHS=(
  ".vibeos/config.json"
  ".vibeos/baselines"
  ".vibeos/token-usage.json"
  ".vibeos/build-log.md"
  ".vibeos/audit-reports"
  ".vibeos/session-state.json"
  ".claude/quality-gate-manifest.json"
)

# New files added in 2.1.0 that must be copied on upgrade
V21_NEW_GATE_SCRIPTS=(
  "activate-session.sh"
  "audit-ratchet.sh"
  "audit_aggregate.py"
  "codex-audit-adapter.sh"
  "codex-audit-broker.sh"
  "detect-significance.sh"
  "dispatch-audit.sh"
  "register-audit-report.sh"
  "register-session-audit-report.sh"
  "select-audit-visibility-mode.sh"
  "session-commit.sh"
  "validate-audit-visibility.sh"
  "validate-commit-msg.sh"
  "validate-independent-audit.sh"
  "validate-file-size.sh"
  "validate-model-versions.sh"
  "validate-scope-discipline.sh"
  "validate-session-start.sh"
  "validate-worktree-freshness.sh"
)

V21_NEW_HOOK_SCRIPTS=(
  "governance-guard.sh"
  "proof-protection.sh"
  "file-budget.sh"
  "worktree-scope-guard.sh"
  "worktree-bash-guard.sh"
)

V21_NEW_AGENT_FILES=(
  "security-auditor-same-tree.md"
  "architecture-auditor-same-tree.md"
  "correctness-auditor-same-tree.md"
  "test-auditor-same-tree.md"
  "evidence-auditor-same-tree.md"
  "product-drift-auditor-same-tree.md"
  "contract-validator-same-tree.md"
  "red-team-auditor-same-tree.md"
)

V21_NEW_SKILLS=(
  "codex-audit"
)

get_plugin_version() {
  local dir="$1"
  if [ -f "$dir/.claude-plugin/plugin.json" ] && command -v jq >/dev/null 2>&1; then
    jq -r '.version // "0.0.0"' "$dir/.claude-plugin/plugin.json" 2>/dev/null || echo "0.0.0"
  else
    echo "0.0.0"
  fi
}

get_installed_version() {
  if [ -f "$VERSION_FILE" ] && command -v jq >/dev/null 2>&1; then
    jq -r '.current // "0.0.0"' "$VERSION_FILE" 2>/dev/null || echo "0.0.0"
  elif [ -f "$LEGACY_VERSION_FILE" ]; then
    cat "$LEGACY_VERSION_FILE" 2>/dev/null || echo "0.0.0"
  else
    echo "0.0.0"
  fi
}

case "$COMMAND" in
  check)
    if [ -z "$PLUGIN_DIR" ]; then
      echo "[plugin-upgrade] ERROR: --plugin-dir is required" >&2
      exit 1
    fi

    AVAILABLE=$(get_plugin_version "$PLUGIN_DIR")
    INSTALLED=$(get_installed_version)

    if [ "$AVAILABLE" = "$INSTALLED" ]; then
      echo "{\"upgrade_available\": false, \"installed\": \"$INSTALLED\", \"available\": \"$AVAILABLE\"}"
    else
      echo "{\"upgrade_available\": true, \"installed\": \"$INSTALLED\", \"available\": \"$AVAILABLE\"}"
    fi
    ;;

  upgrade)
    if [ -z "$PLUGIN_DIR" ] || [ -z "$PROJECT_DIR" ]; then
      echo "[plugin-upgrade] ERROR: --plugin-dir and --project-dir are required" >&2
      exit 1
    fi

    AVAILABLE=$(get_plugin_version "$PLUGIN_DIR")
    INSTALLED=$(get_installed_version)

    echo "[plugin-upgrade] Upgrading from $INSTALLED to $AVAILABLE"

    # Step 1: Create pre-upgrade backup
    echo "[plugin-upgrade] Creating pre-upgrade backup..."
    mkdir -p "$BACKUP_DIR"
    TIMESTAMP=$(date -u +"%Y%m%dT%H%M%SZ")
    SNAPSHOT_DIR="${BACKUP_DIR}/${TIMESTAMP}"
    mkdir -p "$SNAPSHOT_DIR"

    # Backup current scripts, hooks, and version info
    if [ -d "$PLUGIN_DIR/scripts" ]; then
      cp -r "$PLUGIN_DIR/scripts" "$SNAPSHOT_DIR/scripts" 2>/dev/null || true
    fi
    if [ -d "$PLUGIN_DIR/hooks" ]; then
      cp -r "$PLUGIN_DIR/hooks" "$SNAPSHOT_DIR/hooks" 2>/dev/null || true
    fi
    if [ -f "$VERSION_FILE" ]; then
      cp "$VERSION_FILE" "$SNAPSHOT_DIR/version.json" 2>/dev/null || true
    elif [ -f "$LEGACY_VERSION_FILE" ]; then
      cp "$LEGACY_VERSION_FILE" "$SNAPSHOT_DIR/version.txt" 2>/dev/null || true
    fi

    echo "[plugin-upgrade] Backup created at $SNAPSHOT_DIR"

    # Step 2: Detect custom files (files in project not in plugin manifest)
    CUSTOM_GATES=()
    if [ -d "$PROJECT_DIR/scripts" ]; then
      for f in "$PROJECT_DIR/scripts"/*.sh; do
        [ -f "$f" ] || continue
        BASENAME=$(basename "$f")
        if [ ! -f "$PLUGIN_DIR/scripts/$BASENAME" ]; then
          CUSTOM_GATES+=("$BASENAME")
          echo "[plugin-upgrade] Preserving custom gate: $BASENAME"
        fi
      done
    fi

    # Step 2b: Run version-specific migration tasks
    if [ "$INSTALLED" = "2.0.0" ] && [ "$AVAILABLE" = "2.1.0" ]; then
      echo "[plugin-upgrade] Running 2.0.0 → 2.1.0 migration..."

      # Install new gate scripts
      VIBEOS_SCRIPTS_DIR="${PROJECT_DIR:-.}/.vibeos/scripts"
      if [ -d "$PLUGIN_DIR/scripts" ] && [ -d "$VIBEOS_SCRIPTS_DIR" ]; then
        for script in "${V21_NEW_GATE_SCRIPTS[@]}"; do
          if [ -f "$PLUGIN_DIR/scripts/$script" ]; then
            cp "$PLUGIN_DIR/scripts/$script" "$VIBEOS_SCRIPTS_DIR/$script"
            chmod +x "$VIBEOS_SCRIPTS_DIR/$script"
            echo "[plugin-upgrade] Installed new gate script: $script"
          fi
        done
      fi

      # Install new hook scripts
      CLAUDE_HOOKS_DIR="${PROJECT_DIR:-.}/.claude/hooks"
      if [ -d "$PLUGIN_DIR/hooks/scripts" ] && [ -d "$CLAUDE_HOOKS_DIR" ]; then
        for hook in "${V21_NEW_HOOK_SCRIPTS[@]}"; do
          if [ -f "$PLUGIN_DIR/hooks/scripts/$hook" ]; then
            cp "$PLUGIN_DIR/hooks/scripts/$hook" "$CLAUDE_HOOKS_DIR/$hook"
            chmod +x "$CLAUDE_HOOKS_DIR/$hook"
            echo "[plugin-upgrade] Installed new hook: $hook"
          fi
        done
      fi

      # Install same-tree agent variants
      CLAUDE_AGENTS_DIR="${PROJECT_DIR:-.}/.claude/agents"
      if [ -d "$PLUGIN_DIR/agents" ] && [ -d "$CLAUDE_AGENTS_DIR" ]; then
        for agent in "${V21_NEW_AGENT_FILES[@]}"; do
          if [ -f "$PLUGIN_DIR/agents/$agent" ]; then
            cp "$PLUGIN_DIR/agents/$agent" "$CLAUDE_AGENTS_DIR/$agent"
            echo "[plugin-upgrade] Installed same-tree agent: $agent"
          fi
        done
      fi

      # Install new skills
      CLAUDE_SKILLS_DIR="${PROJECT_DIR:-.}/.claude/skills"
      if [ -d "$PLUGIN_DIR/skills" ] && [ -d "$CLAUDE_SKILLS_DIR" ]; then
        for skill in "${V21_NEW_SKILLS[@]}"; do
          if [ -f "$PLUGIN_DIR/skills/$skill/SKILL.md" ]; then
            mkdir -p "$CLAUDE_SKILLS_DIR/$skill"
            cp "$PLUGIN_DIR/skills/$skill/SKILL.md" "$CLAUDE_SKILLS_DIR/$skill/SKILL.md"
            echo "[plugin-upgrade] Installed new skill: $skill"
          fi
        done
      fi

      echo "[plugin-upgrade] PASS: 2.0.0 → 2.1.0 migration complete"
      echo "[plugin-upgrade] NOTE: Review .claude/settings.json to add new hooks if needed"
      echo "[plugin-upgrade] NOTE: New hooks: governance-guard.sh, proof-protection.sh, file-budget.sh, worktree-scope-guard.sh, worktree-bash-guard.sh"
    fi

    # Step 3: Update version tracking
    mkdir -p "$VIBEOS_DIR"
    if command -v jq >/dev/null 2>&1; then
      echo "{\"current\": \"$AVAILABLE\", \"previous\": \"$INSTALLED\", \"upgraded_at\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\", \"backup_path\": \"$SNAPSHOT_DIR\"}" | jq . > "$VERSION_FILE"
    else
      echo "{\"current\": \"$AVAILABLE\", \"previous\": \"$INSTALLED\", \"upgraded_at\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\", \"backup_path\": \"$SNAPSHOT_DIR\"}" > "$VERSION_FILE"
    fi
    printf '%s\n' "$AVAILABLE" > "$LEGACY_VERSION_FILE"

    echo "[plugin-upgrade] Upgrade complete: $INSTALLED → $AVAILABLE"
    echo "[plugin-upgrade] Preserved: ${#CUSTOM_GATES[@]} custom gates, all baselines and config"
    echo "{\"status\": \"upgraded\", \"from\": \"$INSTALLED\", \"to\": \"$AVAILABLE\", \"backup\": \"$SNAPSHOT_DIR\", \"custom_gates_preserved\": ${#CUSTOM_GATES[@]}}"
    ;;

  rollback)
    if [ -z "$PROJECT_DIR" ]; then
      echo "[plugin-upgrade] ERROR: --project-dir is required" >&2
      exit 1
    fi

    if [ ! -d "$BACKUP_DIR" ]; then
      echo "[plugin-upgrade] ERROR: No backup directory found at $BACKUP_DIR" >&2
      exit 1
    fi

    # Find most recent backup
    LATEST_BACKUP=$(ls -1d "$BACKUP_DIR"/*/ 2>/dev/null | sort -r | head -1 || true)
    if [ -z "$LATEST_BACKUP" ]; then
      echo "[plugin-upgrade] ERROR: No backups found" >&2
      exit 1
    fi

    echo "[plugin-upgrade] Rolling back from backup: $LATEST_BACKUP"

    # Restore scripts directory
    if [ -d "$LATEST_BACKUP/scripts" ]; then
      cp -r "$LATEST_BACKUP/scripts/"* "$PLUGIN_DIR/scripts/" 2>/dev/null || true
      echo "[plugin-upgrade] Restored scripts from backup"
    fi

    # Restore hooks directory
    if [ -d "$LATEST_BACKUP/hooks" ]; then
      cp -r "$LATEST_BACKUP/hooks/"* "$PLUGIN_DIR/hooks/" 2>/dev/null || true
      echo "[plugin-upgrade] Restored hooks from backup"
    fi

    # Restore version file
    if [ -f "$LATEST_BACKUP/version.json" ]; then
      cp "$LATEST_BACKUP/version.json" "$VERSION_FILE"
      printf '%s\n' "$(jq -r '.current // "0.0.0"' "$LATEST_BACKUP/version.json" 2>/dev/null || echo "0.0.0")" > "$LEGACY_VERSION_FILE"
      echo "[plugin-upgrade] Restored version tracking"
    elif [ -f "$LATEST_BACKUP/version.txt" ]; then
      cp "$LATEST_BACKUP/version.txt" "$LEGACY_VERSION_FILE"
      echo "[plugin-upgrade] Restored version tracking"
    fi

    echo "[plugin-upgrade] Rollback complete: scripts, hooks, and version restored"
    echo "{\"status\": \"rolled_back\", \"backup_used\": \"$LATEST_BACKUP\"}"
    ;;

  whats-new)
    if [ -z "$PLUGIN_DIR" ]; then
      echo "[plugin-upgrade] ERROR: --plugin-dir is required" >&2
      exit 1
    fi

    AVAILABLE=$(get_plugin_version "$PLUGIN_DIR")
    INSTALLED=$(get_installed_version)

    echo "## What's New in VibeOS Plugin $AVAILABLE"
    echo ""
    echo "**Previous version:** $INSTALLED"
    echo "**New version:** $AVAILABLE"
    echo ""

    # Compare script counts
    if [ -d "$PLUGIN_DIR/scripts" ]; then
      NEW_SCRIPTS=$(ls -1 "$PLUGIN_DIR/scripts/"*.sh 2>/dev/null | wc -l | tr -d ' ')
      echo "**Gate scripts:** $NEW_SCRIPTS"
    fi

    # List agents
    if [ -d "$PLUGIN_DIR/agents" ]; then
      NEW_AGENTS=$(ls -1 "$PLUGIN_DIR/agents/"*.md 2>/dev/null | wc -l | tr -d ' ')
      echo "**Agents:** $NEW_AGENTS"
    fi

    # List skills
    if [ -d "$PLUGIN_DIR/skills" ]; then
      NEW_SKILLS=$(find "$PLUGIN_DIR/skills" -name "SKILL.md" 2>/dev/null | wc -l | tr -d ' ')
      echo "**Skills:** $NEW_SKILLS"
    fi

    # List hooks
    if [ -d "$PLUGIN_DIR/hooks/scripts" ]; then
      NEW_HOOKS=$(ls -1 "$PLUGIN_DIR/hooks/scripts/"*.sh 2>/dev/null | wc -l | tr -d ' ')
      echo "**Hook scripts:** $NEW_HOOKS"
    fi

    # Version-specific changelog
    if [ "$AVAILABLE" = "2.1.0" ]; then
      echo ""
      echo "## v2.1.0 — Advanced Governance (Phase 11)"
      echo ""
      echo "**New capabilities:**"
      echo "  - Same-tree audit agents (8 variants): run in current context without worktree isolation"
      echo "  - Audit visibility modes: inline, isolated (worktree), or codex (external CLI)"
      echo "  - Codex audit integration: /codex-audit skill + broker/adapter scripts"
      echo "  - Session state infrastructure: session-state.json + quality-gate-manifest.json"
      echo "  - Scope discipline gate: validate-scope-discipline.sh blocks WO scope creep"
      echo "  - Proof protection hook: blocks writes to audit evidence artifacts"
      echo "  - Governance guard hook: enforces WO-driven session discipline at prompt time"
      echo "  - File budget hook: blocks sessions exceeding file-change budget"
      echo "  - Parallel worktree scope guard: blocks cross-scope writes in parallel agents"
      echo "  - Worktree bash guard: enforces bash command boundaries in worktree context"
      echo "  - Enhanced investigator agent: CLI-vs-MCP reference awareness"
      echo "  - Build and audit skill enhancements: significance detection, audit report registration"
      echo ""
      echo "**File counts (2.1.0):**"
      echo "  - Gate scripts: 53 (up from 41)"
      echo "  - Agents: 23 (15 base + 8 same-tree)"
      echo "  - Skills: 14 (added codex-audit)"
      echo "  - Hook scripts: 11 (added governance-guard, proof-protection, file-budget, worktree-scope-guard, worktree-bash-guard)"
    fi
    ;;

  *)
    usage
    ;;
esac
