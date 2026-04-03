#!/usr/bin/env bash
# VibeOS Plugin — Session Start Prerequisite Check
# Warns if required tools (bash, python3, jq, git) are not available.
#
# Hook type: SessionStart
# Framework version: 2.1.0
FRAMEWORK_VERSION="2.1.0"
set -euo pipefail

sanitize_json_text() {
  printf '%s' "$1" | tr '\n' ' ' | sed -e 's/[[:space:]][[:space:]]*/ /g' -e 's/^ //' -e 's/ $//' -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

summarize_branch() {
  local branch
  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "git unavailable"
    return
  fi

  branch=$(git branch --show-current 2>/dev/null || true)
  if [ -z "$branch" ]; then
    branch=$(git rev-parse --short HEAD 2>/dev/null || echo "detached")
  fi
  echo "$branch"
}

summarize_git_status() {
  local porcelain staged unstaged untracked

  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "git unavailable"
    return
  fi

  porcelain=$(git status --porcelain 2>/dev/null || true)
  if [ -z "$porcelain" ]; then
    echo "clean"
    return
  fi

  staged=$(printf '%s\n' "$porcelain" | awk 'substr($0,1,2) != "??" && substr($0,1,1) != " " { count++ } END { print count + 0 }')
  unstaged=$(printf '%s\n' "$porcelain" | awk 'substr($0,1,2) != "??" && substr($0,2,1) != " " { count++ } END { print count + 0 }')
  untracked=$(printf '%s\n' "$porcelain" | awk 'substr($0,1,2) == "??" { count++ } END { print count + 0 }')

  echo "${staged} staged, ${unstaged} unstaged, ${untracked} untracked"
}

summarize_recent_commits() {
  local commits

  if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "none"
    return
  fi

  commits=$(git log --oneline --no-decorate -3 2>/dev/null | awk 'BEGIN { ORS="" } { if (NR > 1) printf "; "; printf "%s", $0 }' || true)
  if [ -n "$commits" ]; then
    echo "$commits"
  else
    echo "none"
  fi
}

summarize_planning_state() {
  python3 - <<'PYEOF'
from pathlib import Path

root = Path(".")
plan_path = root / "docs/planning/DEVELOPMENT-PLAN.md"
index_path = root / "docs/planning/WO-INDEX.md"

def parse_plan_statuses(path: Path):
    statuses = {}
    if not path.exists():
        return statuses
    for line in path.read_text().splitlines():
        if not line.startswith("| WO-"):
            continue
        cols = [c.strip() for c in line.strip().split("|")[1:-1]]
        if len(cols) >= 4:
            statuses[cols[0]] = cols[3]
    return statuses

def parse_index(path: Path):
    statuses = {}
    next_wo = "none"
    section = ""
    if not path.exists():
        return statuses, next_wo
    for line in path.read_text().splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if not line.startswith("| WO-"):
            continue
        cols = [c.strip() for c in line.strip().split("|")[1:-1]]
        if len(cols) < 3:
            continue
        wo = cols[0]
        title = cols[1]
        status = cols[2]
        if section != "Completed":
            statuses[wo] = status
            if next_wo == "none" and status not in {"Complete", "Deferred"}:
                next_wo = f"{wo} — {title} [{status}]"
    return statuses, next_wo

plan_statuses = parse_plan_statuses(plan_path)
index_statuses, next_wo = parse_index(index_path)

mismatches = []
for wo in sorted(set(plan_statuses) & set(index_statuses)):
    if plan_statuses[wo] != index_statuses[wo]:
        mismatches.append(f"{wo}: plan={plan_statuses[wo]}, index={index_statuses[wo]}")

if not mismatches:
    mismatch_summary = "none"
elif len(mismatches) <= 3:
    mismatch_summary = "; ".join(mismatches)
else:
    mismatch_summary = "; ".join(mismatches[:3]) + f"; +{len(mismatches) - 3} more"

print(f"NEXT_WO={next_wo}")
print(f"MISMATCHES={mismatch_summary}")
PYEOF
}

summarize_checkpoint_state() {
  local checkpoint_file wo step total agents

  checkpoint_file=$(find ".vibeos/checkpoints" -name "*.json" -type f 2>/dev/null | sort | head -1 || true)
  if [ -z "$checkpoint_file" ]; then
    echo "none"
    return
  fi

  wo=$(jq -r '.wo // "unknown WO"' "$checkpoint_file" 2>/dev/null || echo "unknown WO")
  step=$(jq -r '.current_step // "?"' "$checkpoint_file" 2>/dev/null || echo "?")
  total=$(jq -r '.total_steps // "?"' "$checkpoint_file" 2>/dev/null || echo "?")
  agents=$(jq -r '[(.completed_agents // [])[].agent] | join(", ")' "$checkpoint_file" 2>/dev/null || echo "")
  if [ -z "$agents" ]; then
    agents="none"
  fi

  echo "${wo} at step ${step}/${total}; completed: ${agents}"
}

summarize_gate_signal() {
  local last_gate_line

  if [ ! -f ".vibeos/build-log.md" ]; then
    echo "unknown"
    return
  fi

  last_gate_line=$(grep 'gate-runner ' ".vibeos/build-log.md" 2>/dev/null | tail -1 || true)
  if [ -n "$last_gate_line" ]; then
    echo "$last_gate_line"
  else
    echo "unknown"
  fi
}

MISSING=()

for tool in bash python3 jq git; do
  if ! command -v "$tool" &> /dev/null; then
    MISSING+=("$tool")
  fi
done

# Check git repo
GIT_WARNING=""
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  GIT_WARNING=" Git repository not detected — convergence features (state tracking, baselines) require git. Run 'git init' to initialize."
fi

if [ ${#MISSING[@]} -gt 0 ]; then
  MISSING_LIST=$(printf ', %s' "${MISSING[@]}")
  MISSING_LIST="${MISSING_LIST:2}"
  cat << EOF
{
  "systemMessage": "WARNING: Missing tools: $MISSING_LIST. Some VibeOS gates may not work correctly.${GIT_WARNING}",
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "VibeOS Plugin prerequisite check: missing tools: $MISSING_LIST.${GIT_WARNING}"
  }
}
EOF
elif [ -n "$GIT_WARNING" ]; then
  cat << EOF
{
  "systemMessage": "VibeOS Plugin: All prerequisites available.${GIT_WARNING} Just describe what you want to build, or ask me anything about how the system works.",
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "VibeOS Plugin prerequisites satisfied but git not detected.${GIT_WARNING} Voice-led routing is active — the user can speak naturally and the intent router will suggest the right skill."
  }
}
EOF
else
  # Detect lifecycle state for context-aware welcome
  BRANCH_SUMMARY=$(summarize_branch)
  GIT_STATUS_SUMMARY=$(summarize_git_status)
  RECENT_COMMITS_SUMMARY=$(summarize_recent_commits)
  PLAN_STATE=$(summarize_planning_state)
  NEXT_WO_SUMMARY=$(printf '%s\n' "$PLAN_STATE" | awk -F= '/^NEXT_WO=/{sub(/^NEXT_WO=/, ""); print}')
  MISMATCH_SUMMARY=$(printf '%s\n' "$PLAN_STATE" | awk -F= '/^MISMATCHES=/{sub(/^MISMATCHES=/, ""); print}')
  CHECKPOINT_SUMMARY=$(summarize_checkpoint_state)
  GATE_STATUS_SUMMARY=$(summarize_gate_signal)

  if [ "$CHECKPOINT_SUMMARY" != "none" ]; then
    RESUME_SUMMARY="Resume ${CHECKPOINT_SUMMARY}."
  elif [ "$NEXT_WO_SUMMARY" != "none" ]; then
    RESUME_SUMMARY="No interrupted work. Recommended resume point: ${NEXT_WO_SUMMARY}."
  else
    RESUME_SUMMARY="No interrupted work. Review overall project status before resuming."
  fi

  RECOVERY_HINT=" Recovery summary: branch ${BRANCH_SUMMARY}; working tree ${GIT_STATUS_SUMMARY}; recent commits: ${RECENT_COMMITS_SUMMARY}; next WO: ${NEXT_WO_SUMMARY}; plan/index mismatches: ${MISMATCH_SUMMARY}; latest gate signal: ${GATE_STATUS_SUMMARY}; ${RESUME_SUMMARY}"
  LIFECYCLE_HINT="new project"
  ANCHOR_HINT=""
  if [ -f "project-definition.json" ] && [ -f "docs/planning/DEVELOPMENT-PLAN.md" ]; then
    LIFECYCLE_HINT="existing project with a development plan — ready to build"
  elif [ -f "project-definition.json" ]; then
    LIFECYCLE_HINT="discovered project — ready for planning"
  elif [ -d ".vibeos" ]; then
    LIFECYCLE_HINT="project with VibeOS state"
  fi

  if [ -f "project-definition.json" ]; then
    MISSING_ANCHORS=()
    for f in "docs/product/PRODUCT-ANCHOR.md" "docs/ENGINEERING-PRINCIPLES.md" "docs/research/RESEARCH-REGISTRY.md" "docs/decisions/DEVIATIONS.md"; do
      if [ ! -f "$f" ]; then
        MISSING_ANCHORS+=("$f")
      fi
    done
    if [ ${#MISSING_ANCHORS[@]} -gt 0 ]; then
      ANCHOR_LIST=$(printf ', %s' "${MISSING_ANCHORS[@]}")
      ANCHOR_LIST="${ANCHOR_LIST:2}"
      ANCHOR_HINT=" Anchor docs missing: $ANCHOR_LIST."
    else
      ANCHOR_HINT=" Product, engineering, research, and deviation anchors are present."
    fi
  fi

  SYSTEM_MESSAGE=$(sanitize_json_text "VibeOS Plugin ready (${LIFECYCLE_HINT}).${ANCHOR_HINT}${RECOVERY_HINT} Just tell me what you want to do — describe your idea, ask about progress, or say 'continue' to keep building. No commands needed.")
  ADDITIONAL_CONTEXT=$(sanitize_json_text "VibeOS Plugin prerequisites satisfied. Lifecycle: ${LIFECYCLE_HINT}.${ANCHOR_HINT}${RECOVERY_HINT} Voice-led routing is active — the user can speak naturally and the intent router will suggest the right skill. Follow the routing instructions in CLAUDE.md. Use the Product Anchor, Engineering Principles, Research Registry, and Deviation Log as the anti-drift memory of the project. Treat the recovery summary as the authoritative session-start handoff unless newer evidence appears during the turn.")

  cat << EOF
{
  "systemMessage": "$SYSTEM_MESSAGE",
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "$ADDITIONAL_CONTEXT"
  }
}
EOF
fi
