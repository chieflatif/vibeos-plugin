#!/usr/bin/env bash
# VibeOS Plugin — Model Policy Guard
# Hook type: ConfigChange
# Blocks silent model/effort downgrades for active non-downgrade policy tiers.

FRAMEWORK_VERSION="2.3.2"

# --- VibeOS project-scope guard (auto-inserted) ------------------------------
# Stay inert outside VibeOS-managed projects. The plugin is user-scoped, so
# without this every hook would fire in every project on the machine.
# Override with VIBEOS_FORCE_HOOKS=1. Definition: is-vibeos-project.sh
__VIBEOS_GUARD_LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)/is-vibeos-project.sh"
if [ -f "$__VIBEOS_GUARD_LIB" ]; then
  # shellcheck source=/dev/null
  . "$__VIBEOS_GUARD_LIB"
  is_vibeos_project || exit 0
fi
# -----------------------------------------------------------------------------


INPUT=$(cat)
EVENT_NAME=$(echo "$INPUT" | jq -r '.hook_event_name // .hookEventName // .event // "ConfigChange"' 2>/dev/null || echo "ConfigChange")
SOURCE=$(echo "$INPUT" | jq -r '.source // ""' 2>/dev/null || echo "")
CWD_VALUE=$(echo "$INPUT" | jq -r '.cwd // ""' 2>/dev/null || echo "")
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$CWD_VALUE}"
if [ -z "$PROJECT_ROOT" ]; then
  PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
fi

FRAMEWORK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SESSION_STATE="$PROJECT_ROOT/.vibeos/session-state.json"
EVENT_DIR="$PROJECT_ROOT/.vibeos/hook-events"

first_existing() {
  for candidate in "$@"; do
    if [ -f "$candidate" ]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

POLICY_FILE=$(first_existing \
  "$PROJECT_ROOT/plugins/vibeos/reference/model-policy.json" \
  "$PROJECT_ROOT/.vibeos/reference/model-policy.json" \
  "$FRAMEWORK_ROOT/reference/model-policy.json" \
  2>/dev/null || true)

timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ"
}

record_event() {
  local decision="$1"
  local reason="$2"
  local policy="$3"
  local model="$4"
  local fallback_model="$5"
  local teammate_model="$6"
  local effort="$7"

  mkdir -p "$EVENT_DIR" 2>/dev/null || true
  jq -nc \
    --arg timestamp "$(timestamp)" \
    --arg event "$EVENT_NAME" \
    --arg source "$SOURCE" \
    --arg decision "$decision" \
    --arg reason "$reason" \
    --arg policy "$policy" \
    --arg model "$model" \
    --arg fallback_model "$fallback_model" \
    --arg teammate_model "$teammate_model" \
    --arg effort "$effort" \
    '{
      timestamp: $timestamp,
      event: $event,
      source: $source,
      decision: $decision,
      reason: $reason,
      active_model_policy: $policy,
      model: $model,
      fallback_model: $fallback_model,
      teammate_model: $teammate_model,
      effort: $effort
    }' >> "$EVENT_DIR/model-policy-guard.jsonl" 2>/dev/null || true
}

allow() {
  local reason="$1"
  local policy="${2:-}"
  local model="${3:-}"
  local fallback_model="${4:-}"
  local teammate_model="${5:-}"
  local effort="${6:-}"
  record_event "allow" "$reason" "$policy" "$model" "$fallback_model" "$teammate_model" "$effort"
  jq -n \
    --arg event "$EVENT_NAME" \
    --arg reason "$reason" \
    --arg policy "$policy" \
    '{"decision": "allow", "event": $event, "reason": $reason, "active_model_policy": $policy}'
  exit 0
}

block() {
  local reason="$1"
  local policy="$2"
  local model="$3"
  local fallback_model="$4"
  local teammate_model="$5"
  local effort="$6"
  record_event "block" "$reason" "$policy" "$model" "$fallback_model" "$teammate_model" "$effort"
  jq -n \
    --arg event "$EVENT_NAME" \
    --arg reason "$reason" \
    --arg policy "$policy" \
    '{"decision": "block", "event": $event, "reason": $reason, "active_model_policy": $policy}'
  exit 2
}

payload_value() {
  local expression="$1"
  echo "$INPUT" | jq -r "$expression // empty" 2>/dev/null || true
}

resolve_wo_path() {
  local ref="$1"
  local candidate
  if [ -z "$ref" ]; then
    return 1
  fi
  if [ -f "$ref" ]; then
    printf '%s' "$ref"
    return 0
  fi
  if [ -f "$PROJECT_ROOT/$ref" ]; then
    printf '%s' "$PROJECT_ROOT/$ref"
    return 0
  fi
  for candidate in \
    "$PROJECT_ROOT/docs/planning/${ref}.md" \
    "$PROJECT_ROOT/docs/planning/${ref}"*.md; do
    if [ -f "$candidate" ]; then
      printf '%s' "$candidate"
      return 0
    fi
  done
  return 1
}

frontmatter_model_policy() {
  local path="$1"
  awk -F: '
    /^---[[:space:]]*$/ && seen == 0 { seen=1; next }
    /^---[[:space:]]*$/ && seen == 1 { exit }
    seen == 1 && $1 == "model_policy" {
      value=$0
      sub(/^[^:]+:[[:space:]]*/, "", value)
      gsub(/["'\'']/, "", value)
      print value
      exit
    }
  ' "$path" 2>/dev/null
}

active_policy_from_session() {
  local active_policy=""
  local active_wo=""
  local wo_path=""
  if [ -f "$SESSION_STATE" ]; then
    active_policy=$(jq -r '
      .active_model_policy //
      .current_model_policy //
      .model_policy //
      .governance.model_policy //
      empty
    ' "$SESSION_STATE" 2>/dev/null || true)
    if [ -n "$active_policy" ]; then
      printf '%s' "$active_policy"
      return 0
    fi
    active_wo=$(jq -r '.active_wo // .current_wo // .wo // empty' "$SESSION_STATE" 2>/dev/null || true)
    wo_path=$(resolve_wo_path "$active_wo" || true)
    if [ -n "$wo_path" ]; then
      frontmatter_model_policy "$wo_path"
      return 0
    fi
  fi
  return 0
}

settings_file_path() {
  local path
  path=$(payload_value '.file_path // .path // .settings_path')
  if [ -z "$path" ]; then
    return 0
  fi
  if [ -f "$path" ]; then
    printf '%s' "$path"
    return 0
  fi
  if [ -f "$PROJECT_ROOT/$path" ]; then
    printf '%s' "$PROJECT_ROOT/$path"
    return 0
  fi
  return 0
}

json_file_value() {
  local path="$1"
  local expression="$2"
  if [ -n "$path" ] && [ -f "$path" ]; then
    jq -r "$expression // empty" "$path" 2>/dev/null || true
  fi
}

model_allowed() {
  local value="$1"
  local policy="$2"
  local lower
  local alias
  if [ -z "$value" ]; then
    return 0
  fi
  lower=$(printf '%s' "$value" | tr '[:upper:]' '[:lower:]')
  while IFS= read -r alias; do
    if [ -n "$alias" ] && { [ "$lower" = "$alias" ] || [[ "$lower" == *"$alias"* ]]; }; then
      return 0
    fi
  done < <(jq -r --arg policy "$policy" '.tiers[$policy].allowed_model_aliases[]? | ascii_downcase' "$POLICY_FILE" 2>/dev/null)
  return 1
}

effort_known() {
  local effort="$1"
  if [ -z "$effort" ]; then
    return 0
  fi
  [ "$(jq -r --arg effort "$effort" '(.effort_levels | index($effort)) != null' "$POLICY_FILE" 2>/dev/null || echo false)" = "true" ]
}

effort_too_low() {
  local effort="$1"
  local required="$2"
  if [ -z "$effort" ] || [ -z "$required" ]; then
    return 1
  fi
  [ "$(jq -r --arg actual "$effort" --arg required "$required" '
    def index_of($value): .effort_levels | index($value);
    ((index_of($actual) // -1) < (index_of($required) // 999))
  ' "$POLICY_FILE" 2>/dev/null || echo false)" = "true" ]
}

if [ "$SOURCE" = "policy_settings" ]; then
  allow "policy_settings changes are observed only; Claude Code does not allow ConfigChange hooks to block policy settings."
fi

if [ -z "$POLICY_FILE" ] || [ ! -f "$POLICY_FILE" ]; then
  allow "model-policy.json not found; downgrade guard cannot evaluate policy."
fi

ACTIVE_POLICY=$(payload_value '.active_model_policy // .model_policy')
if [ -z "$ACTIVE_POLICY" ]; then
  ACTIVE_POLICY=$(active_policy_from_session)
fi
ACTIVE_POLICY=$(printf '%s' "$ACTIVE_POLICY" | tr -d '[:space:]')
if [ -z "$ACTIVE_POLICY" ]; then
  allow "No active model_policy found in ConfigChange payload or session state."
fi

ALLOW_DOWNGRADE=$(jq -r --arg policy "$ACTIVE_POLICY" '
  if (.tiers[$policy] | type) == "object" then
    (.tiers[$policy].allow_downgrade | tostring)
  else
    empty
  end
' "$POLICY_FILE" 2>/dev/null || true)
if [ -z "$ALLOW_DOWNGRADE" ]; then
  allow "Active model_policy is custom or not declared in model-policy.json." "$ACTIVE_POLICY"
fi
if [ "$ALLOW_DOWNGRADE" = "true" ]; then
  allow "Active model_policy allows downgrades." "$ACTIVE_POLICY"
fi

SETTINGS_PATH=$(settings_file_path)
MODEL=$(payload_value '.model // .settings.model // .new_settings.model // .configuration.model')
FALLBACK_MODEL=$(payload_value '.fallbackModel // .settings.fallbackModel // .new_settings.fallbackModel // .configuration.fallbackModel')
TEAMMATE_MODEL=$(payload_value '.teammateDefaultModel // .settings.teammateDefaultModel // .new_settings.teammateDefaultModel // .configuration.teammateDefaultModel')
EFFORT=$(payload_value '.effortLevel // .effort // .settings.effortLevel // .new_settings.effortLevel // .configuration.effortLevel')

if [ -z "$MODEL" ]; then
  MODEL=$(json_file_value "$SETTINGS_PATH" '.model // .settings.model // .new_settings.model // .configuration.model')
fi
if [ -z "$FALLBACK_MODEL" ]; then
  FALLBACK_MODEL=$(json_file_value "$SETTINGS_PATH" '.fallbackModel // .settings.fallbackModel // .new_settings.fallbackModel // .configuration.fallbackModel')
fi
if [ -z "$TEAMMATE_MODEL" ]; then
  TEAMMATE_MODEL=$(json_file_value "$SETTINGS_PATH" '.teammateDefaultModel // .settings.teammateDefaultModel // .new_settings.teammateDefaultModel // .configuration.teammateDefaultModel')
fi
if [ -z "$EFFORT" ]; then
  EFFORT=$(json_file_value "$SETTINGS_PATH" '.effortLevel // .effort // .settings.effortLevel // .new_settings.effortLevel // .configuration.effortLevel')
fi

DEFAULT_EFFORT=$(jq -r --arg policy "$ACTIVE_POLICY" '.tiers[$policy].default_effort // empty' "$POLICY_FILE" 2>/dev/null || true)

if ! model_allowed "$MODEL" "$ACTIVE_POLICY"; then
  block "Configured model '$MODEL' is below or outside active policy '$ACTIVE_POLICY'." "$ACTIVE_POLICY" "$MODEL" "$FALLBACK_MODEL" "$TEAMMATE_MODEL" "$EFFORT"
fi
if ! model_allowed "$FALLBACK_MODEL" "$ACTIVE_POLICY"; then
  block "Configured fallbackModel '$FALLBACK_MODEL' is below or outside active policy '$ACTIVE_POLICY'." "$ACTIVE_POLICY" "$MODEL" "$FALLBACK_MODEL" "$TEAMMATE_MODEL" "$EFFORT"
fi
if ! model_allowed "$TEAMMATE_MODEL" "$ACTIVE_POLICY"; then
  block "Configured teammateDefaultModel '$TEAMMATE_MODEL' is below or outside active policy '$ACTIVE_POLICY'." "$ACTIVE_POLICY" "$MODEL" "$FALLBACK_MODEL" "$TEAMMATE_MODEL" "$EFFORT"
fi
if ! effort_known "$EFFORT"; then
  block "Configured effort '$EFFORT' is not declared in model-policy.json." "$ACTIVE_POLICY" "$MODEL" "$FALLBACK_MODEL" "$TEAMMATE_MODEL" "$EFFORT"
fi
if effort_too_low "$EFFORT" "$DEFAULT_EFFORT"; then
  block "Configured effort '$EFFORT' is below required effort '$DEFAULT_EFFORT' for active policy '$ACTIVE_POLICY'." "$ACTIVE_POLICY" "$MODEL" "$FALLBACK_MODEL" "$TEAMMATE_MODEL" "$EFFORT"
fi

allow "ConfigChange respects active model_policy." "$ACTIVE_POLICY" "$MODEL" "$FALLBACK_MODEL" "$TEAMMATE_MODEL" "$EFFORT"
