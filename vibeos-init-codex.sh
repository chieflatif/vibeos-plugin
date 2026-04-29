#!/usr/bin/env bash
set -euo pipefail

FRAMEWORK_VERSION="2.2.0"

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
GIT_HOOK_STATUS="not-attempted"

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
  if [ -L "$dir/.agents" ]; then
    echo "[vibeos-init-codex] FAIL: $dir/.agents is a symlink. Refusing to write through symlinks."
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
    "reference/codex/config.toml.ref"
    "reference/codex/hooks.json.ref"
    "reference/codex/hooks"
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
  if [ -d "$TARGET_DIR/.agents/skills" ] || [ -d "$TARGET_DIR/.codex/skills" ] || [ -d "$TARGET_DIR/.codex/agents" ] || [ -f "$TARGET_DIR/AGENTS.md" ]; then
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
  mkdir -p "$TARGET_DIR/.agents/skills"
  mkdir -p "$TARGET_DIR/.codex/skills"

  local skill_dir name count
  count=0
  for skill_dir in "$SOURCE_DIR/reference/codex/skills"/*; do
    [ -d "$skill_dir" ] || continue
    name="$(basename "$skill_dir")"
    rm -rf "$TARGET_DIR/.agents/skills/$name"
    mkdir -p "$TARGET_DIR/.agents/skills/$name"
    cp "$skill_dir/SKILL.md" "$TARGET_DIR/.agents/skills/$name/SKILL.md"
    rm -rf "$TARGET_DIR/.codex/skills/$name"
    mkdir -p "$TARGET_DIR/.codex/skills/$name"
    cp "$skill_dir/SKILL.md" "$TARGET_DIR/.codex/skills/$name/SKILL.md"
    count=$((count + 1))
  done

  echo "[vibeos-init-codex] PASS: $count Codex skills installed (.agents/skills + legacy .codex/skills)"
}

copy_codex_agents() {
  echo "[vibeos-init-codex] Installing Codex-native agents and legacy role contracts..."
  mkdir -p "$TARGET_DIR/.codex/agents"
  mkdir -p "$TARGET_DIR/.codex/agent-contracts"
  find "$TARGET_DIR/.codex/agents" -type f \( -name "*.md" -o -name "*.toml" \) -delete
  find "$TARGET_DIR/.codex/agent-contracts" -type f -name "*.md" -delete

  local count
  count=0
  while IFS= read -r agent_file; do
    cp "$agent_file" "$TARGET_DIR/.codex/agent-contracts/$(basename "$agent_file")"
    count=$((count + 1))
  done < <(find "$SOURCE_DIR/agents" -type f -name "*.md" | sort)

  SOURCE_DIR="$SOURCE_DIR" TARGET_DIR="$TARGET_DIR" python3 - <<'PYEOF'
import json
import os
import re
from pathlib import Path

source = Path(os.environ["SOURCE_DIR"]) / "agents"
target = Path(os.environ["TARGET_DIR"]) / ".codex" / "agents"
target.mkdir(parents=True, exist_ok=True)

model_map = {
    "opus": ("gpt-5.5", "high"),
    "sonnet": ("gpt-5.5", "medium"),
    "haiku": ("gpt-5.4-mini", "low"),
}

def parse_frontmatter(text: str):
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return {}, text
    raw = parts[1]
    body = parts[2]
    data = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data, body

def snake(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]+", "_", name).strip("_").lower()

for path in sorted(source.glob("*.md")):
    text = path.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    base_name = meta.get("name") or path.stem
    codex_name = f"vibeos_{snake(base_name)}"
    model_key = (meta.get("model") or "sonnet").lower()
    model, effort = model_map.get(model_key, ("gpt-5.5", "medium"))
    tools = meta.get("tools", "")
    disallowed = meta.get("disallowedTools", "")
    read_only = "Write" not in tools and "Edit" not in tools
    if "Write" in disallowed or "Edit" in disallowed:
        read_only = True
    sandbox = "read-only" if read_only else "workspace-write"
    instructions = (
        "You are a Codex-native VibeOS agent generated from the canonical VibeOS role contract. "
        "You are not alone in the codebase; do not revert or overwrite work by other agents. "
        "Respect VibeOS Work Orders, evidence discipline, gate requirements, and truthful completion states.\n\n"
        f"Canonical source: plugins/vibeos/agents/{path.name}\n\n"
        f"{body.strip()}\n"
    )
    out = target / f"{path.stem}.toml"
    out.write_text(
        "\n".join([
            f"name = {json.dumps(codex_name)}",
            f"description = {json.dumps(meta.get('description', f'VibeOS {base_name} agent.'))}",
            f"model = {json.dumps(model)}",
            f"model_reasoning_effort = {json.dumps(effort)}",
            f"sandbox_mode = {json.dumps(sandbox)}",
            f"developer_instructions = {json.dumps(instructions)}",
            "",
        ]),
        encoding="utf-8",
    )
PYEOF

  echo "[vibeos-init-codex] PASS: $count role contracts and Codex-native TOML agents installed"
}

copy_codex_config_and_hooks() {
  echo "[vibeos-init-codex] Installing Codex config and hooks..."
  mkdir -p "$TARGET_DIR/.codex/hooks"

  if [ -f "$TARGET_DIR/.codex/config.toml" ] && [ "$FORCE" != true ]; then
    echo "[vibeos-init-codex] SKIP: Preserving existing .codex/config.toml"
  else
    cp "$SOURCE_DIR/reference/codex/config.toml.ref" "$TARGET_DIR/.codex/config.toml"
  fi

  if [ -f "$TARGET_DIR/.codex/hooks.json" ] && [ "$FORCE" != true ]; then
    echo "[vibeos-init-codex] SKIP: Preserving existing .codex/hooks.json"
  else
    cp "$SOURCE_DIR/reference/codex/hooks.json.ref" "$TARGET_DIR/.codex/hooks.json"
  fi

  cp "$SOURCE_DIR/reference/codex/hooks/"*.sh "$TARGET_DIR/.codex/hooks/"
  cp "$SOURCE_DIR/hooks/scripts/worktree-bash-guard.sh" "$TARGET_DIR/.codex/hooks/worktree-bash-guard.sh"
  cp "$SOURCE_DIR/hooks/scripts/worktree-scope-guard.sh" "$TARGET_DIR/.codex/hooks/worktree-scope-guard.sh"
  chmod +x "$TARGET_DIR/.codex/hooks/"*.sh 2>/dev/null || true

  echo "[vibeos-init-codex] PASS: Codex config and hooks installed"
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
  find "$TARGET_DIR/.vibeos/scripts" -type f -name "*.sh" -exec chmod +x {} + 2>/dev/null || true
  find "$TARGET_DIR/.vibeos/scripts" -type f -name "*.py" -exec chmod +x {} + 2>/dev/null || true
  find "$TARGET_DIR/.vibeos/convergence" -type f -name "*.sh" -exec chmod +x {} + 2>/dev/null || true

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
.vibeos/runtime-capabilities.json
.vibeos/session-audits/
.vibeos/audit-reports/
.vibeos/cache/
.vibeos/autonomy/
EOF

  echo "[vibeos-init-codex] PASS: .gitignore updated"
}

install_git_hooks() {
  if ! command -v git >/dev/null 2>&1; then
    GIT_HOOK_STATUS="git-unavailable"
    echo "[vibeos-init-codex] NOTE: git not found; skipped VibeOS git hook installation"
    return 0
  fi

  if ! git -C "$TARGET_DIR" rev-parse --git-dir >/dev/null 2>&1; then
    GIT_HOOK_STATUS="not-a-git-repo"
    echo "[vibeos-init-codex] NOTE: Target is not a git repository; skipped VibeOS git hook installation"
    return 0
  fi

  local -a hook_args
  hook_args=(--project-dir "$TARGET_DIR")
  if [ "$FORCE" = true ]; then
    hook_args+=(--force)
  fi

  if bash "$TARGET_DIR/.vibeos/scripts/setup-git-hooks.sh" "${hook_args[@]}"; then
    GIT_HOOK_STATUS="installed"
    return 0
  fi

  GIT_HOOK_STATUS="manual-follow-up"
  echo "[vibeos-init-codex] WARN: VibeOS git hooks were not installed automatically"
  echo "[vibeos-init-codex] WARN: Resolve existing hook ownership, then run:"
  echo "[vibeos-init-codex] WARN:   bash \"$TARGET_DIR/.vibeos/scripts/setup-git-hooks.sh\" --project-dir \"$TARGET_DIR\""
}

uninstall() {
  echo "[vibeos-init-codex] Removing Codex VibeOS from $TARGET_DIR..."

  rm -rf "$TARGET_DIR/.codex/skills/vibeos-discover"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-plan"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-build"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-comp"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-audit"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-gate"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-status"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-project-status"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-session-audit"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-checkpoint"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-wo"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-help"
  rm -rf "$TARGET_DIR/.codex/skills/vibeos-autonomous"

  rm -rf "$TARGET_DIR/.agents/skills/vibeos-discover"
  rm -rf "$TARGET_DIR/.agents/skills/vibeos-plan"
  rm -rf "$TARGET_DIR/.agents/skills/vibeos-build"
  rm -rf "$TARGET_DIR/.agents/skills/vibeos-comp"
  rm -rf "$TARGET_DIR/.agents/skills/vibeos-audit"
  rm -rf "$TARGET_DIR/.agents/skills/vibeos-gate"
  rm -rf "$TARGET_DIR/.agents/skills/vibeos-status"
  rm -rf "$TARGET_DIR/.agents/skills/vibeos-project-status"
  rm -rf "$TARGET_DIR/.agents/skills/vibeos-session-audit"
  rm -rf "$TARGET_DIR/.agents/skills/vibeos-checkpoint"
  rm -rf "$TARGET_DIR/.agents/skills/vibeos-wo"
  rm -rf "$TARGET_DIR/.agents/skills/vibeos-help"
  rm -rf "$TARGET_DIR/.agents/skills/vibeos-autonomous"

  rm -rf "$TARGET_DIR/.codex/agents"
  rm -rf "$TARGET_DIR/.codex/agent-contracts"
  rm -rf "$TARGET_DIR/.codex/hooks"
  rm -f "$TARGET_DIR/.codex/hooks.json"
  if [ -f "$TARGET_DIR/.codex/config.toml" ] && grep -q "VibeOS Codex project config" "$TARGET_DIR/.codex/config.toml" 2>/dev/null; then
    rm -f "$TARGET_DIR/.codex/config.toml"
  fi
  rm -f "$TARGET_DIR/.vibeos/runtime.txt"
  rm -f "$TARGET_DIR/.vibeos/version.txt"
  rm -f "$TARGET_DIR/.vibeos/version.json"

  echo "[vibeos-init-codex] PASS: Codex skills, agents, hooks, and templates removed"
  echo "[vibeos-init-codex] NOTE: Shared .vibeos runtime, docs, and AGENTS.md were preserved."
  echo "[vibeos-init-codex] NOTE: Claude/Cursor assets were untouched."
  exit 0
}

print_welcome() {
  local hook_summary
  case "$GIT_HOOK_STATUS" in
    installed) hook_summary="- Installed: VibeOS pre-commit and commit-msg hooks are active" ;;
    not-a-git-repo) hook_summary="- Skipped: target is not a git repository yet" ;;
    git-unavailable) hook_summary="- Skipped: git was not available during installation" ;;
    manual-follow-up) hook_summary="- Manual follow-up required: an existing non-VibeOS hook layout was preserved" ;;
    *) hook_summary="- Not attempted" ;;
  esac

  cat <<EOF

[vibeos-init-codex] PASS: Codex VibeOS installed into $TARGET_DIR (experimental)

What was installed:
- AGENTS.md                         (Codex instructions)
- .agents/skills/                  (13 VibeOS Codex skills — current repo-scoped location)
- .codex/skills/                   (legacy mirror for older Codex surfaces)
- .codex/agents/                   (Codex-native TOML subagents)
- .codex/agent-contracts/          (legacy Markdown role contracts)
- .codex/config.toml               (project agent concurrency and hook feature flag)
- .codex/hooks.json + hooks/       (Codex-compatible guardrail hooks)
- .vibeos/                         (shared VibeOS runtime: gate scripts, decision engine, references)
- docs/USER-COMMUNICATION-CONTRACT.md

What Codex gets:
- Structured build instructions, repo skills, and Codex-native agent definitions
- Runtime capability detection via .vibeos/runtime-capabilities.json
- Long-run autonomy heartbeat, checkpoint, and closeout validation support for 24-48 hour resumable runs
- Codex hooks where the local Codex runtime supports them
- Decision engine, reference materials, and convergence logic
- Shared project state (plans, checkpoints, baselines, logs)
- Commit-boundary Git hooks when the target repo can install them

What remains true:
- Codex hooks are guardrails, not Claude Code hook parity
- Codex feature support is runtime/version dependent; read .vibeos/runtime-capabilities.json
- Git hooks and explicit VibeOS gates remain the cross-runtime enforcement baseline

Git hook status:
$hook_summary

For full enforcement, use Claude Code or Cursor:
  bash /path/to/vibeos-plugin/vibeos-init.sh

Existing .claude/, CLAUDE.md, and Cursor rules were preserved.

Next steps:
1. Open the project in Codex
2. Run planning so the project generates .claude/quality-gate-manifest.json
3. Start naturally: "build this as a competition-grade enterprise MVP", "make a plan", or "continue building"
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
  copy_codex_config_and_hooks
  copy_runtime
  copy_docs
  generate_agents_md
  update_gitignore
  install_git_hooks
  print_welcome
}

main "$@"
