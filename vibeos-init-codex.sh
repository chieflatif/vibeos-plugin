#!/usr/bin/env bash
set -euo pipefail

FRAMEWORK_VERSION="2.0.0"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "$SCRIPT_DIR/plugins/vibeos/skills" ]; then
  SOURCE_DIR="$SCRIPT_DIR/plugins/vibeos"
else
  SOURCE_DIR="$SCRIPT_DIR"
fi
TARGET_DIR="$(pwd)"
UPGRADE_MODE=false
UNINSTALL_MODE=false
FORCE=false

usage() {
  sed -n '1,28p' "$0"
}

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
      usage
      exit 0
      ;;
    *)
      echo "[vibeos-init-codex] ERROR: Unknown option: $1"
      exit 1
      ;;
  esac
done

canonicalize_paths() {
  SOURCE_DIR="$(cd "$SOURCE_DIR" && pwd)"
  TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

  if [ "$SOURCE_DIR" = "$TARGET_DIR" ]; then
    echo "[vibeos-init-codex] FAIL: Source and target are the same directory."
    exit 1
  fi

  case "$TARGET_DIR" in
    /|/usr|/usr/*|/etc|/etc/*|/var|/bin|/sbin|/System|/Library)
      echo "[vibeos-init-codex] FAIL: Target is a system directory: $TARGET_DIR"
      exit 1
      ;;
  esac
}

check_symlinks() {
  local dir="$1"
  if [ -L "$dir/.codex" ]; then
    echo "[vibeos-init-codex] FAIL: $dir/.codex is a symlink. Refusing to write through symlinks."
    exit 1
  fi
  if [ -L "$dir/.vibeos" ]; then
    echo "[vibeos-init-codex] FAIL: $dir/.vibeos is a symlink. Refusing to write through symlinks."
    exit 1
  fi
}

validate_source() {
  local required_paths=(
    "reference/codex/AGENTS.md.ref"
    "reference/codex/skills"
    "agents"
    "scripts"
    "decision-engine"
    "reference"
    "convergence"
    "docs/USER-COMMUNICATION-CONTRACT.md"
  )

  local path
  for path in "${required_paths[@]}"; do
    if [ ! -e "$SOURCE_DIR/$path" ]; then
      echo "[vibeos-init-codex] FAIL: Source missing '$path': $SOURCE_DIR"
      exit 1
    fi
  done

  echo "[vibeos-init-codex] PASS: Source validated: $SOURCE_DIR"
}

validate_target() {
  if [ ! -d "$TARGET_DIR" ]; then
    echo "[vibeos-init-codex] FAIL: Target directory does not exist: $TARGET_DIR"
    exit 1
  fi

  echo "[vibeos-init-codex] PASS: Target validated: $TARGET_DIR"
}

check_existing() {
  if [ -d "$TARGET_DIR/.codex/skills" ] || [ -d "$TARGET_DIR/.codex/agents" ] || [ -f "$TARGET_DIR/AGENTS.md" ]; then
    if [ "$UPGRADE_MODE" = true ] || [ "$FORCE" = true ]; then
      echo "[vibeos-init-codex] Upgrading existing Codex installation..."
      return 0
    fi

    echo "[vibeos-init-codex] Codex VibeOS appears to already be installed in $TARGET_DIR"
    echo "[vibeos-init-codex] Use --upgrade to refresh the framework, or --force to overwrite."
    exit 2
  fi
}

copy_codex_skills() {
  echo "[vibeos-init-codex] Installing Codex skills..."
  mkdir -p "$TARGET_DIR/.codex/skills"

  local skill_dir name count
  count=0
  for skill_dir in "$SOURCE_DIR/reference/codex/skills"/*; do
    [ -d "$skill_dir" ] || continue
    name="$(basename "$skill_dir")"
    rm -rf "$TARGET_DIR/.codex/skills/$name"
    mkdir -p "$TARGET_DIR/.codex/skills/$name"
    cp "$skill_dir/SKILL.md" "$TARGET_DIR/.codex/skills/$name/SKILL.md"
    count=$((count + 1))
  done

  echo "[vibeos-init-codex] PASS: $count Codex skills installed"
}

copy_codex_agents() {
  echo "[vibeos-init-codex] Installing Codex agent templates..."
  mkdir -p "$TARGET_DIR/.codex/agents"
  find "$TARGET_DIR/.codex/agents" -type f -name "*.md" -delete

  local count
  count=0
  while IFS= read -r agent_file; do
    cp "$agent_file" "$TARGET_DIR/.codex/agents/$(basename "$agent_file")"
    count=$((count + 1))
  done < <(find "$SOURCE_DIR/agents" -type f -name "*.md" | sort)

  echo "[vibeos-init-codex] PASS: $count agent templates installed"
}

copy_runtime() {
  echo "[vibeos-init-codex] Installing shared .vibeos runtime..."
  mkdir -p "$TARGET_DIR/.vibeos"

  rm -rf "$TARGET_DIR/.vibeos/scripts"
  rm -rf "$TARGET_DIR/.vibeos/decision-engine"
  rm -rf "$TARGET_DIR/.vibeos/reference"
  rm -rf "$TARGET_DIR/.vibeos/convergence"

  cp -R "$SOURCE_DIR/scripts" "$TARGET_DIR/.vibeos/scripts"
  cp -R "$SOURCE_DIR/decision-engine" "$TARGET_DIR/.vibeos/decision-engine"
  cp -R "$SOURCE_DIR/reference" "$TARGET_DIR/.vibeos/reference"
  cp -R "$SOURCE_DIR/convergence" "$TARGET_DIR/.vibeos/convergence"

  printf '%s\n' "$FRAMEWORK_VERSION" > "$TARGET_DIR/.vibeos/version.txt"
  cat > "$TARGET_DIR/.vibeos/version.json" <<EOF
{
  "current": "$FRAMEWORK_VERSION",
  "surface": "codex",
  "installed_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
}
EOF
  printf '%s\n' "codex" > "$TARGET_DIR/.vibeos/runtime.txt"

  echo "[vibeos-init-codex] PASS: Shared runtime installed"
}

copy_docs() {
  mkdir -p "$TARGET_DIR/docs"
  cp "$SOURCE_DIR/docs/USER-COMMUNICATION-CONTRACT.md" "$TARGET_DIR/docs/USER-COMMUNICATION-CONTRACT.md"
  echo "[vibeos-init-codex] PASS: Communication contract installed"
}

generate_agents_md() {
  local agents_file project_name template
  agents_file="$TARGET_DIR/AGENTS.md"
  template="$SOURCE_DIR/reference/codex/AGENTS.md.ref"
  project_name="$(basename "$TARGET_DIR")"

  if [ -f "$agents_file" ] && [ "$FORCE" != true ] && [ "$UPGRADE_MODE" = false ]; then
    echo "[vibeos-init-codex] SKIP: AGENTS.md already exists (use --force to overwrite)"
    return
  fi

  if [ -f "$agents_file" ] && [ "$UPGRADE_MODE" = true ] && [ "$FORCE" != true ]; then
    echo "[vibeos-init-codex] SKIP: Preserving existing AGENTS.md during upgrade"
    return
  fi

  sed "s/\\\$PROJECT_NAME/$project_name/g" "$template" > "$agents_file"
  echo "[vibeos-init-codex] PASS: AGENTS.md generated"
}

update_gitignore() {
  local gitignore
  gitignore="$TARGET_DIR/.gitignore"

  touch "$gitignore"

  while IFS= read -r entry; do
    [ -n "$entry" ] || continue
    if ! grep -Fqx "$entry" "$gitignore"; then
      printf '%s\n' "$entry" >> "$gitignore"
    fi
  done <<'EOF'
.vibeos/checkpoints/
.vibeos/current-agent.txt
.vibeos/build-log.md
.vibeos/session-state.json
.vibeos/session-audits/
.vibeos/audit-reports/
EOF

  echo "[vibeos-init-codex] PASS: .gitignore updated"
}

uninstall() {
  echo "[vibeos-init-codex] Removing Codex VibeOS from $TARGET_DIR..."

  rm -rf "$TARGET_DIR/.codex/skills/vibeos-discover"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-plan"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-build"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-audit"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-gate"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-status"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-project-status"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-session-audit"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-checkpoint"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-wo"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-help"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-autonomous"

  rm -rf "$TARGET_DIR/.codex/agents"
  rm -f "$TARGET_DIR/.vibeos/runtime.txt"
  rm -f "$TARGET_DIR/.vibeos/version.txt"
  rm -f "$TARGET_DIR/.vibeos/version.json"

  echo "[vibeos-init-codex] PASS: Codex skills and templates removed"
  echo "[vibeos-init-codex] NOTE: Shared .vibeos runtime, docs, and AGENTS.md were preserved."
  echo "[vibeos-init-codex] NOTE: Claude/Cursor assets were untouched."
  exit 0
}

print_welcome() {
  cat <<EOF

[vibeos-init-codex] PASS: Codex VibeOS installed into $TARGET_DIR (experimental)

What was installed:
- AGENTS.md                         (Codex instructions)
- .codex/skills/                   (12 VibeOS Codex skills — instruction-based)
- .codex/agents/                   (role contracts — read by agent, not spawned)
- .vibeos/                         (shared VibeOS runtime: gate scripts, decision engine, references)
- docs/USER-COMMUNICATION-CONTRACT.md

What Codex gets:
- Structured build instructions and quality gate scripts (run manually)
- Decision engine, reference materials, and convergence logic
- Shared project state (plans, checkpoints, baselines, logs)

What Codex does NOT get:
- No hooks (no intent routing, secrets scanning, or test file protection)
- No subagent spawning (role contracts are read, not executed as isolated agents)
- No automatic enforcement (gates must be run manually)

For full enforcement, use Claude Code or Cursor:
  bash /path/to/vibeos-plugin/vibeos-init.sh

Existing .claude/, CLAUDE.md, and Cursor rules were preserved.

Next steps:
1. Open the project in Codex
2. Start naturally: "help me understand this codebase", "make a plan", or "continue building"
EOF
}

main() {
  canonicalize_paths
  check_symlinks "$TARGET_DIR"
  validate_source
  validate_target

  if [ "$UNINSTALL_MODE" = true ]; then
    uninstall
  fi

  check_existing
  copy_codex_skills
  copy_codex_agents
  copy_runtime
  copy_docs
  generate_agents_md
  update_gitignore
  print_welcome
}

main "$@"
