#!/usr/bin/env bash
set -euo pipefail

FRAMEWORK_VERSION="2.0.0"

# ─── VibeOS Bootstrap ────────────────────────────────────────────────────────
# Installs VibeOS governance framework into a target project's .claude/ and
# .vibeos/ directories. Works with Claude Code's project-level config system.
#
# Usage:
#   bash vibeos-init.sh [OPTIONS]
#
# Options:
#   --source PATH     Path to VibeOS framework (default: directory containing this script)
#   --target PATH     Target project directory (default: current working directory)
#   --upgrade         Update existing installation to latest framework
#   --uninstall       Remove VibeOS from project
#   --force           Overwrite without confirmation
#   -h, --help        Show this help
#
# Modes (auto-detected):
#   Fresh install     No .vibeos/ directory exists in target
#   Upgrade           .vibeos/ exists + --upgrade flag
#   Midstream         Source files detected in target (existing code)
#   Greenfield        No source files detected (new project)
# ─────────────────────────────────────────────────────────────────────────────

# ─── Defaults ────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Auto-detect: if this script is at repo root and plugins/vibeos/ exists, use that as source
if [ -d "$SCRIPT_DIR/plugins/vibeos/skills" ]; then
    SOURCE_DIR="$SCRIPT_DIR/plugins/vibeos"
else
    SOURCE_DIR="$SCRIPT_DIR"
fi
TARGET_DIR="$(pwd)"
UPGRADE_MODE=false
UNINSTALL_MODE=false
FORCE=false

# ─── Parse Arguments ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case "$1" in
        --source)
            SOURCE_DIR="$2"
            shift 2
            ;;
        --target)
            TARGET_DIR="$2"
            shift 2
            ;;
        --upgrade)
            UPGRADE_MODE=true
            shift
            ;;
        --uninstall)
            UNINSTALL_MODE=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            head -28 "$0" | tail -25
            exit 0
            ;;
        *)
            echo "[vibeos-init] ERROR: Unknown option: $1"
            exit 1
            ;;
    esac
done

# ─── Path Safety ─────────────────────────────────────────────────────────────
canonicalize_paths() {
    # Resolve to absolute paths
    SOURCE_DIR="$(cd "$SOURCE_DIR" && pwd)"
    TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

    # Prevent self-overwrite
    if [ "$SOURCE_DIR" = "$TARGET_DIR" ]; then
        echo "[vibeos-init] FAIL: Source and target are the same directory."
        echo "[vibeos-init] Run from your project directory, not the VibeOS framework directory."
        exit 1
    fi

    # Reject obvious system paths
    case "$TARGET_DIR" in
        /|/usr|/usr/*|/etc|/etc/*|/var|/bin|/sbin|/System|/Library)
            echo "[vibeos-init] FAIL: Target is a system directory: $TARGET_DIR"
            exit 1
            ;;
    esac
}

check_symlinks() {
    local dir="$1"
    if [ -L "$dir/.claude" ]; then
        echo "[vibeos-init] FAIL: $dir/.claude is a symlink. Refusing to write through symlinks."
        exit 1
    fi
    if [ -L "$dir/.vibeos" ]; then
        echo "[vibeos-init] FAIL: $dir/.vibeos is a symlink. Refusing to write through symlinks."
        exit 1
    fi
}

# ─── Validation ──────────────────────────────────────────────────────────────
validate_source() {
    local required_dirs=("skills" "agents" "hooks" "scripts" "decision-engine" "reference" "convergence")
    for dir in "${required_dirs[@]}"; do
        if [ ! -d "$SOURCE_DIR/$dir" ]; then
            echo "[vibeos-init] FAIL: Source directory missing '$dir/': $SOURCE_DIR"
            echo "[vibeos-init] Is $SOURCE_DIR the VibeOS framework directory?"
            exit 1
        fi
    done
    echo "[vibeos-init] PASS: Source validated: $SOURCE_DIR"
}

validate_target() {
    if [ ! -d "$TARGET_DIR" ]; then
        echo "[vibeos-init] FAIL: Target directory does not exist: $TARGET_DIR"
        exit 1
    fi
    echo "[vibeos-init] PASS: Target validated: $TARGET_DIR"
}

# ─── Uninstall ───────────────────────────────────────────────────────────────
uninstall() {
    echo "[vibeos-init] Removing VibeOS from $TARGET_DIR..."

    # Remove framework directories
    rm -rf "$TARGET_DIR/.vibeos/scripts"
    rm -rf "$TARGET_DIR/.vibeos/decision-engine"
    rm -rf "$TARGET_DIR/.vibeos/reference"
    rm -rf "$TARGET_DIR/.vibeos/convergence"
    rm -f "$TARGET_DIR/.vibeos/version.txt"

    # Remove .claude components (skills, agents, hooks)
    rm -rf "$TARGET_DIR/.claude/skills/discover"
    rm -rf "$TARGET_DIR/.claude/skills/plan"
    rm -rf "$TARGET_DIR/.claude/skills/build"
    rm -rf "$TARGET_DIR/.claude/skills/audit"
    rm -rf "$TARGET_DIR/.claude/skills/gate"
    rm -rf "$TARGET_DIR/.claude/skills/status"
    rm -rf "$TARGET_DIR/.claude/skills/checkpoint"
    rm -rf "$TARGET_DIR/.claude/skills/wo"
    rm -rf "$TARGET_DIR/.claude/skills/help"
    rm -rf "$TARGET_DIR/.claude/skills/upgrade"
    rm -rf "$TARGET_DIR/.claude/skills/autonomous"
    rm -rf "$TARGET_DIR/.claude/skills/project-status"
    rm -rf "$TARGET_DIR/.claude/skills/session-audit"

    rm -f "$TARGET_DIR/.claude/agents/plan-auditor.md"
    rm -f "$TARGET_DIR/.claude/agents/investigator.md"
    rm -f "$TARGET_DIR/.claude/agents/tester.md"
    rm -f "$TARGET_DIR/.claude/agents/backend.md"
    rm -f "$TARGET_DIR/.claude/agents/frontend.md"
    rm -f "$TARGET_DIR/.claude/agents/doc-writer.md"
    rm -f "$TARGET_DIR/.claude/agents/security-auditor.md"
    rm -f "$TARGET_DIR/.claude/agents/architecture-auditor.md"
    rm -f "$TARGET_DIR/.claude/agents/correctness-auditor.md"
    rm -f "$TARGET_DIR/.claude/agents/test-auditor.md"
    rm -f "$TARGET_DIR/.claude/agents/evidence-auditor.md"
    rm -f "$TARGET_DIR/.claude/agents/product-drift-auditor.md"
    rm -f "$TARGET_DIR/.claude/agents/contract-validator.md"
    rm -f "$TARGET_DIR/.claude/agents/red-team-auditor.md"
    rm -f "$TARGET_DIR/.claude/agents/prompt-engineer.md"

    rm -f "$TARGET_DIR/.claude/hooks/intent-router.sh"
    rm -f "$TARGET_DIR/.claude/hooks/secrets-scan.sh"
    rm -f "$TARGET_DIR/.claude/hooks/frozen-files.sh"
    rm -f "$TARGET_DIR/.claude/hooks/test-file-protection.sh"
    rm -f "$TARGET_DIR/.claude/hooks/test-diff-audit.sh"
    rm -f "$TARGET_DIR/.claude/hooks/prereq-check.sh"

    # Clean up empty directories
    rmdir "$TARGET_DIR/.claude/skills" 2>/dev/null || true
    rmdir "$TARGET_DIR/.claude/agents" 2>/dev/null || true
    rmdir "$TARGET_DIR/.claude/hooks" 2>/dev/null || true

    echo "[vibeos-init] PASS: VibeOS removed from $TARGET_DIR"
    echo "[vibeos-init] NOTE: .claude/settings.json, .claude/CLAUDE.md, and docs/ were preserved."
    echo "[vibeos-init] NOTE: .vibeos/config.json and .vibeos/baselines/ were preserved."
    exit 0
}

# ─── Detect Project Mode ────────────────────────────────────────────────────
detect_project_mode() {
    local has_code=false
    local code_dirs=("src" "lib" "app" "packages" "cmd" "internal")

    for dir in "${code_dirs[@]}"; do
        if [ -d "$TARGET_DIR/$dir" ]; then
            has_code=true
            break
        fi
    done

    if [ "$has_code" = false ]; then
        # Check for source files in root
        local count
        count=$(find "$TARGET_DIR" -maxdepth 1 -type f \( -name "*.py" -o -name "*.ts" -o -name "*.js" -o -name "*.go" -o -name "*.rs" -o -name "*.java" -o -name "*.tsx" -o -name "*.jsx" \) 2>/dev/null | head -1 | wc -l)
        if [ "$count" -gt 0 ]; then
            has_code=true
        fi
    fi

    if [ "$has_code" = true ]; then
        echo "midstream"
    else
        echo "greenfield"
    fi
}

# ─── Check Existing Installation ────────────────────────────────────────────
check_existing() {
    if [ -d "$TARGET_DIR/.vibeos/scripts" ]; then
        if [ "$UPGRADE_MODE" = true ] || [ "$FORCE" = true ]; then
            echo "[vibeos-init] Upgrading existing installation..."
            return 0
        fi
        echo "[vibeos-init] VibeOS is already installed in $TARGET_DIR"
        echo "[vibeos-init] Use --upgrade to update framework files, or --force to overwrite."
        exit 2
    fi
}

# ─── Copy Framework Files ───────────────────────────────────────────────────
copy_skills() {
    echo "[vibeos-init] Installing skills..."
    mkdir -p "$TARGET_DIR/.claude/skills"

    local skills=("discover" "plan" "build" "audit" "gate" "status" "checkpoint" "wo" "help" "upgrade" "autonomous" "project-status" "session-audit")
    for skill in "${skills[@]}"; do
        mkdir -p "$TARGET_DIR/.claude/skills/$skill"
        cp "$SOURCE_DIR/skills/$skill/SKILL.md" "$TARGET_DIR/.claude/skills/$skill/SKILL.md"
    done

    echo "[vibeos-init] PASS: ${#skills[@]} skills installed"
}

copy_agents() {
    echo "[vibeos-init] Installing agents..."
    mkdir -p "$TARGET_DIR/.claude/agents"

    local agents
    agents=$(find "$SOURCE_DIR/agents" -name "*.md" -type f)
    local count=0
    while IFS= read -r agent_file; do
        local name
        name=$(basename "$agent_file")
        cp "$agent_file" "$TARGET_DIR/.claude/agents/$name"
        count=$((count + 1))
    done <<< "$agents"

    echo "[vibeos-init] PASS: $count agents installed"
}

copy_hooks() {
    echo "[vibeos-init] Installing hook scripts..."
    mkdir -p "$TARGET_DIR/.claude/hooks"

    local hooks=("intent-router.sh" "secrets-scan.sh" "frozen-files.sh" "test-file-protection.sh" "test-diff-audit.sh" "prereq-check.sh")
    for hook in "${hooks[@]}"; do
        cp "$SOURCE_DIR/hooks/scripts/$hook" "$TARGET_DIR/.claude/hooks/$hook"
        chmod +x "$TARGET_DIR/.claude/hooks/$hook"
    done

    echo "[vibeos-init] PASS: ${#hooks[@]} hook scripts installed"
}

copy_framework_runtime() {
    echo "[vibeos-init] Installing framework runtime..."

    # Gate scripts
    mkdir -p "$TARGET_DIR/.vibeos/scripts"
    cp "$SOURCE_DIR"/scripts/*.sh "$TARGET_DIR/.vibeos/scripts/" 2>/dev/null || true
    cp "$SOURCE_DIR"/scripts/*.py "$TARGET_DIR/.vibeos/scripts/" 2>/dev/null || true
    cp "$SOURCE_DIR"/scripts/*.json "$TARGET_DIR/.vibeos/scripts/" 2>/dev/null || true
    chmod +x "$TARGET_DIR"/.vibeos/scripts/*.sh 2>/dev/null || true

    # Decision engine
    mkdir -p "$TARGET_DIR/.vibeos/decision-engine"
    cp "$SOURCE_DIR"/decision-engine/*.md "$TARGET_DIR/.vibeos/decision-engine/"

    # Reference materials
    if [ -d "$SOURCE_DIR/reference" ]; then
        mkdir -p "$TARGET_DIR/.vibeos/reference"
        cp -R "$SOURCE_DIR/reference/"* "$TARGET_DIR/.vibeos/reference/"
    fi

    # Convergence scripts
    if [ -d "$SOURCE_DIR/convergence" ]; then
        mkdir -p "$TARGET_DIR/.vibeos/convergence"
        cp "$SOURCE_DIR"/convergence/*.sh "$TARGET_DIR/.vibeos/convergence/"
        chmod +x "$TARGET_DIR"/.vibeos/convergence/*.sh 2>/dev/null || true
    fi

    # Version marker
    echo "$FRAMEWORK_VERSION" > "$TARGET_DIR/.vibeos/version.txt"

    echo "[vibeos-init] PASS: Framework runtime installed"
}

copy_docs() {
    echo "[vibeos-init] Installing documentation..."
    mkdir -p "$TARGET_DIR/docs"

    # Communication contract (always copy — it's framework, not project-specific)
    if [ -f "$SOURCE_DIR/docs/USER-COMMUNICATION-CONTRACT.md" ]; then
        cp "$SOURCE_DIR/docs/USER-COMMUNICATION-CONTRACT.md" "$TARGET_DIR/docs/USER-COMMUNICATION-CONTRACT.md"
    fi

    echo "[vibeos-init] PASS: Documentation installed"
}

# ─── Generate Configuration ─────────────────────────────────────────────────
generate_settings() {
    local settings_file="$TARGET_DIR/.claude/settings.json"

    if [ -f "$settings_file" ] && [ "$FORCE" != true ] && [ "$UPGRADE_MODE" != true ]; then
        echo "[vibeos-init] SKIP: .claude/settings.json exists (use --force to overwrite)"
        return
    fi

    # If upgrading and settings exist, only update the hooks section
    if [ -f "$settings_file" ] && [ "$UPGRADE_MODE" = true ]; then
        echo "[vibeos-init] SKIP: Preserving existing .claude/settings.json during upgrade"
        echo "[vibeos-init] NOTE: If hooks have changed, manually update .claude/settings.json"
        return
    fi

    mkdir -p "$TARGET_DIR/.claude"
    cat > "$settings_file" << 'SETTINGS_EOF'
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "./.claude/hooks/prereq-check.sh"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "./.claude/hooks/intent-router.sh"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "./.claude/hooks/secrets-scan.sh"
          },
          {
            "type": "command",
            "command": "./.claude/hooks/frozen-files.sh"
          },
          {
            "type": "command",
            "command": "./.claude/hooks/test-file-protection.sh"
          },
          {
            "type": "command",
            "command": "./.claude/hooks/test-diff-audit.sh"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Review the response you just gave. Check for any of the following quality issues:\n1. Stubs: raise NotImplementedError, def func(): pass, def func(): ...\n2. Placeholders: TODO, FIXME, HACK, XXX comments\n3. Incomplete code: 'implement later', 'add here', 'placeholder'\n4. Swallowed errors: bare except: pass\n\nIf you find ANY of these issues, immediately flag them to the user and offer to fix them. Do not let incomplete code pass without acknowledgment."
          }
        ]
      }
    ]
  }
}
SETTINGS_EOF

    echo "[vibeos-init] PASS: .claude/settings.json generated with hooks"
}

generate_claude_md() {
    local claude_md="$TARGET_DIR/.claude/CLAUDE.md"

    if [ -f "$claude_md" ] && [ "$FORCE" != true ] && [ "$UPGRADE_MODE" != true ]; then
        echo "[vibeos-init] SKIP: .claude/CLAUDE.md exists (use --force to overwrite)"
        return
    fi

    if [ -f "$claude_md" ] && [ "$UPGRADE_MODE" = true ]; then
        echo "[vibeos-init] SKIP: Preserving existing .claude/CLAUDE.md during upgrade"
        return
    fi

    mkdir -p "$TARGET_DIR/.claude"
    cat > "$claude_md" << 'CLAUDEMD_EOF'
# VibeOS — Agent Instructions

## What Is VibeOS

An autonomous, self-governing development engine. You guide users through product discovery, create development plans, then autonomously build with layered quality audits enforcing zero technical debt.

## Architecture

```
.claude/skills/          ← 13 user-invocable skills (/discover, /plan, /build, /upgrade, etc.)
.claude/agents/          ← 15 specialized subagents (auditors, tester, implementation, red-team, etc.)
.claude/hooks/           ← Event-driven enforcement (intent routing, secrets, stubs, frozen files)
.vibeos/scripts/         ← 41 deterministic gate scripts + gate-runner.sh
.vibeos/decision-engine/ ← 10 decision tree files
.vibeos/reference/       ← 45+ annotated reference files
.vibeos/convergence/     ← Loop control scripts (state hashing, convergence checks)
docs/planning/           ← Development plan, WO index, individual WO files
```

## Key Constraints

1. **Subagents cannot spawn subagents** — only the main thread dispatches agents
2. **Audit agents are read-only** — `disallowedTools: Write, Edit, Agent` + `isolation: worktree`
3. **Tests are written from spec, not code** — tester agent never sees implementation
4. **Implementation agents cannot modify test files** — enforced by PreToolUse hook
5. **All scripts are bash 3.2+ compatible** — macOS default, no external dependencies

## Voice-Led Intent Routing

VibeOS is conversational. Users should NEVER need to type slash commands. When a user speaks naturally, the `UserPromptSubmit` hook (`intent-router.sh`) analyzes their message and injects a routing hint into your context as `[VibeOS Intent Router]`.

### How to Handle Routing Hints

1. **High confidence** — Invoke the suggested skill immediately using the Skill tool. Do not ask the user to confirm. Example: user says "I want to build a task management app" → invoke `/discover`.

2. **Medium confidence** — Briefly confirm before invoking. One sentence, not an interrogation. Example: "It sounds like you want to run a code review. Should I start the audit?"

3. **Low confidence** — Ask a brief clarifying question. Do not guess. Example: "I can help with that — are you looking to check project status, or would you like me to continue building?"

4. **No hint (explicit slash command or direct help)** — The router stays silent. If the user typed a slash command, invoke it normally. If the user is asking about specific code/errors, help them directly without invoking a skill.

### Conflict Resolution: Skill vs. Direct Help

Not every message should trigger a skill. Use these rules:

- **File paths, line numbers, error messages, code snippets** → Help directly. Do not invoke a skill.
- **Conceptual questions** ("what is ratcheting?", "how do phases work?") → Invoke `/help`.
- **Product ideas or feature requests** → Invoke `/discover` (new project) or `/wo` (existing project with plan).
- **"Continue", "next", "keep going"** → Invoke `/build`.
- **"Upgrade", "update the framework", "pulled the latest"** → Invoke `/upgrade`.
- **Vague messages with no clear intent** → Check lifecycle state from the routing hint. At `virgin` stage, suggest discovery. At `building` stage, show status.

### Slash Commands Are Power-User Shortcuts

Slash commands (`/discover`, `/build`, etc.) still work and always take precedence. But never instruct users to type them. Instead of "Run `/discover`", say "Just tell me what you want to build."

## Development Governance

- **DEVELOPMENT-PLAN.md** defines phases and ordered Work Orders
- Agent determines next WO from the plan, never asks "what next?"
- Every WO has a file in `docs/planning/` with status, scope, acceptance criteria
- WO-INDEX.md tracks all WOs and their status

## Conventions

- Shell scripts: `#!/usr/bin/env bash`, `set -euo pipefail`
- Exit codes: 0 = pass, 1 = fail, 2 = skip/block
- Logging: `echo "[COMPONENT] PASS|FAIL|WARN|SKIP: message"`
- No stubs, no placeholders, no TODOs in any file
CLAUDEMD_EOF

    echo "[vibeos-init] PASS: .claude/CLAUDE.md generated"
}

# ─── Gitignore Setup ────────────────────────────────────────────────────────
setup_gitignore() {
    local gitignore="$TARGET_DIR/.gitignore"
    local vibeos_entries=(
        ""
        "# VibeOS runtime state (not checked in)"
        ".vibeos/baselines/"
        ".vibeos/current-agent.txt"
        ".claude/settings.local.json"
    )

    if [ -f "$gitignore" ]; then
        # Check if already has vibeos entries
        if grep -q "vibeos/baselines" "$gitignore" 2>/dev/null; then
            return
        fi
    fi

    for entry in "${vibeos_entries[@]}"; do
        echo "$entry" >> "$gitignore"
    done

    echo "[vibeos-init] PASS: .gitignore updated"
}

# ─── Initialize Project Config ──────────────────────────────────────────────
init_project_config() {
    local config_file="$TARGET_DIR/.vibeos/config.json"

    if [ -f "$config_file" ]; then
        echo "[vibeos-init] SKIP: .vibeos/config.json exists (preserving)"
        return
    fi

    mkdir -p "$TARGET_DIR/.vibeos"
    cat > "$config_file" << 'CONFIG_EOF'
{
  "framework_version": "2.0.0",
  "autonomy_level": "wo",
  "project_mode": "pending",
  "lifecycle_state": "virgin"
}
CONFIG_EOF

    echo "[vibeos-init] PASS: Project config initialized"
}

# ─── Main ────────────────────────────────────────────────────────────────────
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║  VibeOS — Autonomous Development Engine v$FRAMEWORK_VERSION     ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo ""

    validate_source
    validate_target
    canonicalize_paths

    # Handle uninstall
    if [ "$UNINSTALL_MODE" = true ]; then
        uninstall
    fi

    # Safety checks
    check_symlinks "$TARGET_DIR"
    check_existing

    # Detect project mode
    local project_mode
    project_mode=$(detect_project_mode)
    echo "[vibeos-init] Project mode: $project_mode"

    # Install framework
    copy_skills
    copy_agents
    copy_hooks
    copy_framework_runtime
    copy_docs

    # Generate configuration
    generate_settings
    generate_claude_md

    # Setup
    setup_gitignore
    init_project_config

    # Update config with detected mode
    if command -v jq &>/dev/null && [ -f "$TARGET_DIR/.vibeos/config.json" ]; then
        local config_tmp="$TARGET_DIR/.vibeos/config.json.tmp"
        if jq --arg mode "$project_mode" '.project_mode = $mode' "$TARGET_DIR/.vibeos/config.json" > "$config_tmp" 2>/dev/null; then
            mv "$config_tmp" "$TARGET_DIR/.vibeos/config.json"
        else
            rm -f "$config_tmp"
        fi
    fi

    echo ""
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║  VibeOS installed successfully!                     ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo ""
    echo "  Project: $TARGET_DIR"
    echo "  Mode:    $project_mode"
    echo ""
    echo "  Open this project in Claude Code or Cursor and say:"
    echo ""
    if [ "$project_mode" = "greenfield" ]; then
        echo '    "I want to build [describe your idea]"'
    else
        echo '    "Help me understand this codebase"'
        echo '    or "Set up governance for this project"'
    fi
    echo ""
    echo "  VibeOS will take it from there."
    echo ""
}

main
