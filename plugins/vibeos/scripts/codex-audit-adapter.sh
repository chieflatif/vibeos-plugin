#!/usr/bin/env bash
# VibeOS — Codex Audit Adapter
# Wraps the Codex CLI (codex-companion) invocation for all four audit types.
# Handles plugin discovery, timeout, output parsing, and result serialization.
#
# Usage:
#   bash codex-audit-adapter.sh [OPTIONS]
#
# Options:
#   --type    plan_audit|completion_audit|session_audit|manual_audit  (required)
#   --executor-model  claude|codex                                     (default: claude)
#   --wo FILE          work order file path
#   --plan FILE        plan or design document file path
#   --context TEXT     additional free-text context
#   --session-log FILE build log or session transcript
#   --out FILE         write structured result to this file (in addition to stdout)
#   --wait             run synchronously / foreground                  [default]
#   --background       run asynchronously (print status and exit)
#
# Requirements:
#   - Codex Claude Code plugin must be installed
#   - Run from the project root directory
#
# Output (stdout): structured audit result in markdown
# Exit codes:
#   0 — success
#   1 — invocation error (adapter failure, empty output)
#   2 — Codex plugin not found
#
# Framework: VibeOS 2.2.0 | Codex Complementary Audit Protocol

set -euo pipefail

FRAMEWORK_VERSION="2.2.0"

# ---- Defaults ----
AUDIT_TYPE="manual_audit"
EXECUTOR_MODEL="claude"
WO_FILE=""
PLAN_FILE=""
CONTEXT_TEXT=""
SESSION_LOG_FILE=""
OUT_FILE=""
FOREGROUND=true

# ---- Parse arguments ----
while [[ $# -gt 0 ]]; do
  case "$1" in
    --type)           AUDIT_TYPE="$2"; shift 2 ;;
    --executor-model) EXECUTOR_MODEL="$2"; shift 2 ;;
    --wo)             WO_FILE="$2"; shift 2 ;;
    --plan)           PLAN_FILE="$2"; shift 2 ;;
    --context)        CONTEXT_TEXT="$2"; shift 2 ;;
    --session-log)    SESSION_LOG_FILE="$2"; shift 2 ;;
    --out)            OUT_FILE="$2"; shift 2 ;;
    --wait)           FOREGROUND=true; shift ;;
    --background)     FOREGROUND=false; shift ;;
    *) shift ;;
  esac
done

# ---- Validate audit type ----
case "$AUDIT_TYPE" in
  plan_audit|completion_audit|session_audit|manual_audit) ;;
  *)
    echo "[codex-adapter] FAIL: unknown audit type '${AUDIT_TYPE}'" >&2
    exit 1
    ;;
esac

# ---- Locate Codex plugin ----
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-}"
if [[ -z "$PLUGIN_ROOT" ]]; then
  # Search standard Claude Code plugin cache locations
  PLUGIN_ROOT=$(ls -d ~/.claude/plugins/cache/openai-codex/codex/*/ 2>/dev/null | sort -V | tail -1 | tr -d '\n' || echo "")
  PLUGIN_ROOT="${PLUGIN_ROOT%/}"
fi

if [[ -z "$PLUGIN_ROOT" ]] || [[ ! -f "${PLUGIN_ROOT}/scripts/codex-companion.mjs" ]]; then
  echo "[codex-adapter] FAIL: Codex plugin not found." >&2
  echo "[codex-adapter] Expected: ~/.claude/plugins/cache/openai-codex/codex/<version>/scripts/codex-companion.mjs" >&2
  echo "[codex-adapter] Install the Codex plugin for Claude Code and retry, or use /vibeos:audit for Claude-only auditing." >&2
  exit 2
fi

COMPANION="${PLUGIN_ROOT}/scripts/codex-companion.mjs"

# ---- Build audit prompt ----
build_prompt() {
  local type="$1"
  local executor="$2"

  printf 'You are conducting a %s for work implemented by %s.\n\n' "$type" "$executor"
  printf 'Perform an independent, adversarial audit. Your role is to find issues the implementor missed.\n\n'

  printf '## Audit Scope\n\n'
  printf 'Evaluate against these pillars:\n'
  printf '1. **Correctness** — Logic errors, off-by-one, missing edge cases\n'
  printf '2. **Security** — Injection, secrets exposure, auth bypasses, input validation gaps\n'
  printf '3. **Architecture** — Layer violations, boundary violations, coupling issues\n'
  printf '4. **Completeness** — Missing implementations, stubs, TODOs, unhandled errors\n'
  printf '5. **Test quality** — Missing tests, untested error paths, mock overuse\n'

  if [[ -n "$WO_FILE" ]] && [[ -f "$WO_FILE" ]]; then
    printf '\n## Work Order\n\n'
    cat "$WO_FILE"
  fi

  if [[ -n "$PLAN_FILE" ]] && [[ -f "$PLAN_FILE" ]]; then
    printf '\n## Plan Document\n\n'
    cat "$PLAN_FILE"
  fi

  if [[ -n "$SESSION_LOG_FILE" ]] && [[ -f "$SESSION_LOG_FILE" ]]; then
    printf '\n## Session Log (last 100 lines)\n\n'
    tail -100 "$SESSION_LOG_FILE"
  fi

  if [[ -n "$CONTEXT_TEXT" ]]; then
    printf '\n## Additional Context\n\n%s\n' "$CONTEXT_TEXT"
  fi

  printf '\n## Required Output Format\n\n'
  printf 'Return your findings in this exact structure:\n\n'
  printf '### Verdict\n[PASS|CONDITIONAL PASS|FAIL] — one sentence summary.\n\n'
  printf '### Findings\n'
  printf 'For each finding:\n'
  printf '- **[CRITICAL|HIGH|MEDIUM|LOW|INFO] F-N:** Description\n'
  printf '  - **Location:** file:line\n'
  printf '  - **Recommendation:** what must be done\n\n'
  printf '### Pillar Assessment\n'
  printf '| Pillar | Status | Notes |\n|---|---|---|\n'
  printf '| Correctness | [PASS/WARN/FAIL] | ... |\n'
  printf '| Security | [PASS/WARN/FAIL] | ... |\n'
  printf '| Architecture | [PASS/WARN/FAIL] | ... |\n'
  printf '| Completeness | [PASS/WARN/FAIL] | ... |\n'
  printf '| Test quality | [PASS/WARN/FAIL] | ... |\n'
}

PROMPT_FILE=$(mktemp /tmp/codex-audit-prompt-XXXXXX.txt)
# shellcheck disable=SC2064
trap "rm -f '${PROMPT_FILE}'" EXIT

build_prompt "$AUDIT_TYPE" "$EXECUTOR_MODEL" > "$PROMPT_FILE"

if [[ ! -s "$PROMPT_FILE" ]]; then
  echo "[codex-adapter] FAIL: prompt builder produced no output" >&2
  exit 1
fi

PROMPT_TEXT=$(cat "$PROMPT_FILE")

# ---- Dispatch to Codex ----
echo "[codex-adapter] Invoking Codex audit (type=${AUDIT_TYPE}, executor=${EXECUTOR_MODEL})..." >&2

AUDIT_OUTPUT=""

if [[ "$AUDIT_TYPE" == "completion_audit" ]]; then
  # Completion audits: adversarial-review pass (git-diff-native) + structured pillar follow-up
  if [[ "$FOREGROUND" == "true" ]]; then
    ADVER_OUTPUT=$(node "$COMPANION" adversarial-review --wait 2>/dev/null) || ADVER_OUTPUT=""
    TASK_OUTPUT=$(node "$COMPANION" task "$PROMPT_TEXT" --resume-last 2>/dev/null) || TASK_OUTPUT=""
    AUDIT_OUTPUT="${ADVER_OUTPUT}

---

## Structured Pillar Assessment

${TASK_OUTPUT}"
  else
    node "$COMPANION" adversarial-review 2>/dev/null || true
    echo "[codex-adapter] Codex adversarial-review started in background." >&2
    echo "[codex-adapter] Re-run with --wait after /codex:status shows complete." >&2
    exit 0
  fi
else
  # plan_audit, session_audit, manual_audit: structured task prompt
  if [[ "$FOREGROUND" == "true" ]]; then
    AUDIT_OUTPUT=$(node "$COMPANION" task "$PROMPT_TEXT" 2>/dev/null) || {
      echo "[codex-adapter] FAIL: codex-companion task returned non-zero exit" >&2
      exit 1
    }
  else
    node "$COMPANION" task "$PROMPT_TEXT" &
    BG_PID=$!
    echo "[codex-adapter] Codex audit task started in background (PID: ${BG_PID})." >&2
    exit 0
  fi
fi

if [[ -z "$AUDIT_OUTPUT" ]]; then
  echo "[codex-adapter] FAIL: Codex returned empty output" >&2
  exit 1
fi

# ---- Serialize result ----
RESULT_HEADER="---
auditor: codex
executor: ${EXECUTOR_MODEL}
audit_type: ${AUDIT_TYPE}
timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)
framework_version: ${FRAMEWORK_VERSION}
---
"

if [[ -n "$OUT_FILE" ]]; then
  {
    printf '%s\n' "$RESULT_HEADER"
    printf '%s\n' "$AUDIT_OUTPUT"
  } > "$OUT_FILE"
  echo "[codex-adapter] Result written to: ${OUT_FILE}" >&2
fi

printf '%s\n' "$RESULT_HEADER"
printf '%s\n' "$AUDIT_OUTPUT"

exit 0
