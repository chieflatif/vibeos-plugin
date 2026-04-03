#!/usr/bin/env bash
# VibeOS Plugin — Voice-Led Intent Router
# Hook type: UserPromptSubmit
# Fires on every user message. Reads project lifecycle state and classifies
# the user's intent to inject routing context for the model.
#
# Framework version: 2.1.0
FRAMEWORK_VERSION="2.1.0"

# Note: no pipefail — stdin/jq patterns need lenient error handling (documented exception)
set -eu

# --- Read hook input from stdin ---
INPUT=$(cat)
PROMPT=$(printf '%s' "$INPUT" | jq -r '.prompt // ""' 2>/dev/null || echo "")

# If no prompt, exit silently (nothing to route)
if [[ -z "$PROMPT" ]]; then
  exit 0
fi

# --- Determine project root ---
# Use CWD from hook input, fall back to current directory
PROJECT_ROOT=$(printf '%s' "$INPUT" | jq -r '.cwd // ""' 2>/dev/null || echo "")
if [[ -z "$PROJECT_ROOT" ]]; then
  PROJECT_ROOT="$(pwd)"
fi

# ============================================================
# LIFECYCLE STATE DETECTION
# ============================================================
# Determines project stage from file existence checks.
# Returns one of: virgin, discovered, planned, building, checkpoint, phase-boundary, complete

detect_lifecycle_state() {
  local project_root="$1"

  # Check for .vibeos/config.json
  local has_config=false
  if [[ -f "$project_root/.vibeos/config.json" ]]; then
    has_config=true
  fi

  # Check for project-definition.json
  local has_definition=false
  if [[ -f "$project_root/project-definition.json" ]]; then
    has_definition=true
  fi

  # Check for development plan
  local has_plan=false
  if [[ -f "$project_root/docs/planning/DEVELOPMENT-PLAN.md" ]]; then
    has_plan=true
  fi

  # Check for WO index
  local has_wo_index=false
  if [[ -f "$project_root/docs/planning/WO-INDEX.md" ]]; then
    has_wo_index=true
  fi

  # Check for checkpoint (resume state)
  local has_checkpoint=false
  if [[ -d "$project_root/.vibeos/checkpoints" ]]; then
    local checkpoint_count
    checkpoint_count=$(find "$project_root/.vibeos/checkpoints" -name "*.json" -type f 2>/dev/null | wc -l | tr -d ' ')
    if [[ "$checkpoint_count" -gt 0 ]]; then
      has_checkpoint=true
    fi
  fi

  # Parse WO statuses if index exists
  local active_wos=0
  local complete_wos=0
  local total_wos=0
  if [[ "$has_wo_index" == true ]]; then
    # Count WOs with different statuses from the index
    active_wos=$(grep -cE '\|\s*(In Progress|Active|Implemented Locally|Awaiting Gate Cleanup|Awaiting Real-Path Verification|Dev-Mode Complete|Awaiting Checkpoint|Awaiting Evidence|Pre-Commit Audit)' "$project_root/docs/planning/WO-INDEX.md" 2>/dev/null || echo "0")
    complete_wos=$(grep -cE '\|\s*Complete\s*\|' "$project_root/docs/planning/WO-INDEX.md" 2>/dev/null || echo "0")
    total_wos=$(grep -cE '\|\s*WO-[0-9]' "$project_root/docs/planning/WO-INDEX.md" 2>/dev/null || echo "0")
  fi

  # --- State determination ---

  # No config at all — brand new
  if [[ "$has_config" == false && "$has_definition" == false ]]; then
    echo "virgin"
    return
  fi

  # Config exists but lifecycle_state explicitly set to virgin (freshly bootstrapped)
  if [[ "$has_config" == true && "$has_definition" == false ]]; then
    local stored_state=""
    if command -v jq &>/dev/null; then
      stored_state=$(jq -r '.lifecycle_state // ""' "$project_root/.vibeos/config.json" 2>/dev/null || echo "")
    fi
    if [[ "$stored_state" == "virgin" ]]; then
      echo "virgin"
      return
    fi
  fi

  # Has definition but no plan — discovery done, needs planning
  if [[ "$has_definition" == true && "$has_plan" == false ]]; then
    echo "discovered"
    return
  fi

  # Has checkpoint — interrupted build, should resume
  if [[ "$has_checkpoint" == true ]]; then
    echo "checkpoint"
    return
  fi

  # Has plan but no WOs started
  if [[ "$has_plan" == true && "$active_wos" -eq 0 && "$complete_wos" -eq 0 ]]; then
    echo "planned"
    return
  fi

  # All WOs complete — check if all phases done
  if [[ "$has_plan" == true && "$total_wos" -gt 0 && "$active_wos" -eq 0 ]]; then
    # All WOs accounted for and none active — could be phase boundary or complete
    # Check if there are pending/draft WOs remaining
    local pending_wos
    pending_wos=$(grep -cE '\|\s*(Draft|Pending|Blocked|Implementation Ready|In Progress|Active|Implemented Locally|Awaiting Gate Cleanup|Awaiting Real-Path Verification|Dev-Mode Complete|Awaiting Checkpoint|Awaiting Evidence|Pre-Commit Audit)' "$project_root/docs/planning/WO-INDEX.md" 2>/dev/null || echo "0")
    if [[ "$pending_wos" -eq 0 ]]; then
      echo "complete"
    else
      echo "phase-boundary"
    fi
    return
  fi

  # Active WOs exist — building
  if [[ "$active_wos" -gt 0 ]]; then
    echo "building"
    return
  fi

  # Fallback — has some state but unclear
  echo "building"
}

# ============================================================
# INTENT CLASSIFICATION
# ============================================================
# Pattern-matches user prompt to determine likely skill.
# Returns: intent_category, suggested_skill, confidence

classify_intent() {
  local prompt="$1"
  local lifecycle="$2"

  # Lowercase the prompt for matching
  local lower
  lower=$(printf '%s' "$prompt" | tr '[:upper:]' '[:lower:]')

  # --- Check for explicit slash commands first ---
  if printf '%s' "$lower" | grep -qE '/vibeos:'; then
    echo "explicit|none|high"
    return
  fi

  # --- Direct help signals: file paths, error messages, code references ---
  # If the message looks like it's about specific code, don't route to a skill
  if printf '%s' "$prompt" | grep -qE '(\.[a-z]{1,4}:[0-9]+|line [0-9]+|error:|traceback|exception|stack trace|TypeError|ValueError|SyntaxError|ImportError|ModuleNotFoundError)'; then
    echo "direct|none|high"
    return
  fi

  # --- Intent patterns (ordered by specificity) ---

  # Full autonomous mode override
  if printf '%s' "$lower" | grep -qE '\b(go autonomous|stay autonomous|full autonomous|autonomous mode|run autonomously|work autonomously|stop checking in|no more check.ins|dont check in|don.t check in)\b'; then
    echo "autonomy|autonomous|high"
    return
  fi

  # Upgrade / Update framework
  if printf '%s' "$lower" | grep -qE '\b(upgrade vibeos|update vibeos|upgrade the framework|update the framework|run the upgrade|apply the upgrade|pulled the latest|new version of vibeos|framework upgrade|vibeos upgrade)\b'; then
    echo "upgrade|upgrade|high"
    return
  fi

  # Codex / complementary / dual-model audit
  if printf '%s' "$lower" | grep -qE '\b(codex audit|audit with codex|independent audit|dual audit|dual-audit|complementary audit|audit this with codex)\b'; then
    echo "codex-review|codex-audit|high"
    return
  fi

  # Session audit / session closeout review
  if printf '%s' "$lower" | grep -qE '\b(session audit|audit this session|audit the session|review this session|review the session|close out this session|session review)\b'; then
    echo "session-review|session-audit|high"
    return
  fi

  # Continue / Resume — highest priority when building
  if printf '%s' "$lower" | grep -qE '\b(continue|keep going|resume|carry on|pick up where|next one|go ahead)\b'; then
    echo "continue|build|high"
    return
  fi

  # Executive / overall project status
  if printf '%s' "$lower" | grep -qE '\b(project status|overall project status|overall status|big picture|big picture status|executive briefing|executive update|founder update|program status|strategic status|reorient me overall|re-orient me overall|reorientate me overall)\b' || printf '%s' "$lower" | grep -qE 'where .* overall|where .* in the project|where .* on the project|where do we stand overall|reorient .* overall'; then
    echo "project-progress|project-status|high"
    return
  fi

  # Progress / Status — check BEFORE explain, because "what is the status" should be status, not explain
  if printf '%s' "$lower" | grep -qE '\b(status|progress|where are we|what.s done|what.s left|dashboard|overview|how far|reorient me|re-orient me|orient me|reorientate me)\b' || printf '%s' "$lower" | grep -qE 'how.*(going|doing|coming along|looking)|update me|what is the status|where .* right now|remind me where we are'; then
    echo "progress|status|high"
    return
  fi

  # Explain / Help — conceptual questions
  if printf '%s' "$lower" | grep -qE '\b(what is|what are|what does|explain|help me understand|how does|tell me about|what.s a|define)\b'; then
    echo "explain|help|high"
    return
  fi

  # Plan / Organize
  if printf '%s' "$lower" | grep -qE '\b(plan|break down|break it down|organize|roadmap|phases|work orders|structure the|map out)\b'; then
    echo "plan|plan|high"
    return
  fi

  # Quality / Gates — "check" + quality/code/passing context
  if printf '%s' "$lower" | grep -qE '\b(quality gate|run the gate|pre.commit|lint)\b' || printf '%s' "$lower" | grep -qE 'check.*(quality|code)|run.*(check|gate)|are we passing|validate (the |this )?(code|build)'; then
    echo "quality|gate|medium"
    return
  fi

  # Review / Audit
  if printf '%s' "$lower" | grep -qE '\b(audit|review the code|security review|code review|look over|inspect|check for (issues|bugs|vulnerabilities))\b'; then
    echo "review|audit|medium"
    return
  fi

  # Work Order management
  if printf '%s' "$lower" | grep -qE '\b(work order|create a wo|wo status|new wo|add a task|create task)\b'; then
    echo "manage|wo|high"
    return
  fi

  # Milestone / Checkpoint
  if printf '%s' "$lower" | grep -qE '\b(milestone|checkpoint)\b' || printf '%s' "$lower" | grep -qE 'phase.*(done|complete|finished|boundary)|wrap.*(up|phase)'; then
    echo "milestone|checkpoint|medium"
    return
  fi

  # Create / Build / Idea — context-dependent
  if printf '%s' "$lower" | grep -qE '\b(i want to build|i want to create|i want to make|build me|create a|make a|my idea|i.m thinking of|i have an idea|new (app|project|product|feature|system|platform|tool|service|website|api))\b'; then
    # At virgin/discovered stage, this means discover. At planned+, this means build.
    case "$lifecycle" in
      virgin|discovered)
        echo "create|discover|high"
        ;;
      planned|building|checkpoint)
        echo "create|build|high"
        ;;
      *)
        echo "create|discover|medium"
        ;;
    esac
    return
  fi

  # Generic "build" / "start" — depends on lifecycle
  if printf '%s' "$lower" | grep -qE '\b(build|start|begin|let.s go|get started|kick off|launch)\b'; then
    case "$lifecycle" in
      virgin)
        echo "start|discover|high"
        ;;
      discovered)
        echo "start|plan|high"
        ;;
      planned)
        echo "start|build|high"
        ;;
      building|checkpoint)
        echo "start|build|high"
        ;;
      phase-boundary)
        echo "start|checkpoint|medium"
        ;;
      complete)
        echo "start|status|medium"
        ;;
      *)
        echo "start|discover|low"
        ;;
    esac
    return
  fi

  # --- No strong match ---
  # Fall back to lifecycle-based default suggestion
  case "$lifecycle" in
    virgin)
      echo "ambiguous|discover|low"
      ;;
    discovered)
      echo "ambiguous|plan|low"
      ;;
    planned|building|checkpoint)
      echo "ambiguous|status|low"
      ;;
    *)
      echo "ambiguous|status|low"
      ;;
  esac
}

# ============================================================
# MAIN
# ============================================================

LIFECYCLE=$(detect_lifecycle_state "$PROJECT_ROOT")
CLASSIFICATION=$(classify_intent "$PROMPT" "$LIFECYCLE")

# Parse classification
INTENT=$(echo "$CLASSIFICATION" | cut -d'|' -f1)
SKILL=$(echo "$CLASSIFICATION" | cut -d'|' -f2)
CONFIDENCE=$(echo "$CLASSIFICATION" | cut -d'|' -f3)

# --- Build routing context ---

# If explicit slash command or direct help, don't inject routing
if [[ "$INTENT" == "explicit" || "$INTENT" == "direct" ]]; then
  exit 0
fi

# Build the additionalContext message
CONTEXT=""

case "$CONFIDENCE" in
  high)
    CONTEXT="[VibeOS Intent Router] Project lifecycle: ${LIFECYCLE}. Detected intent: ${INTENT}. Suggested skill: /vibeos:${SKILL}. Confidence: high. Follow the routing instructions in CLAUDE.md to invoke this skill unless the user is clearly asking for direct code help."
    ;;
  medium)
    CONTEXT="[VibeOS Intent Router] Project lifecycle: ${LIFECYCLE}. Detected intent: ${INTENT}. Suggested skill: /vibeos:${SKILL}. Confidence: medium. Consider invoking this skill, but briefly confirm with the user if their intent is ambiguous. Example: 'It sounds like you want to [action]. Should I start that?'"
    ;;
  low)
    CONTEXT="[VibeOS Intent Router] Project lifecycle: ${LIFECYCLE}. Detected intent: ${INTENT}. Suggested skill: /vibeos:${SKILL}. Confidence: low. The user's intent is unclear. Ask a brief clarifying question before invoking any skill. Do not guess."
    ;;
esac

# Output routing context as JSON
cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "${CONTEXT}"
  }
}
EOF
