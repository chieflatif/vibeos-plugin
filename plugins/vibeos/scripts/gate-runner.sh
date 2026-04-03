#!/usr/bin/env bash
# VibeOS Plugin — Quality Gate Runner (Orchestrator)
# Reads quality-gate-manifest.json, runs gates by phase, handles baselines + tiers.
#
# Usage:
#   bash scripts/gate-runner.sh <phase> [options]
#
# Phases:
#   session_start, pre_commit, wo_exit, wo_exit_backend, wo_exit_frontend,
#   wo_exit_crosscutting, wo_exit_governance, post_deploy, full_audit, session_end
#
# Options:
#   --continue-on-failure   Don't stop on first blocking gate failure
#   --json                  Output results as JSON
#   --manifest PATH         Custom manifest path (default: auto-discover .claude/ then project root)
#   --wo NUMBER             Work order number (substitutes $WO_NUMBER in gate env)
#   --evidence-dir PATH     Evidence directory (substitutes $EVIDENCE_DIR in gate env)
#   --timeout SECONDS       Per-gate timeout (default: 120)
#   --lock                  Acquire runner lock (prevent concurrent runs)
#   --dry-run               Show which gates would run without executing them
#   -h, --help              Show usage
#
# Environment:
#   MANIFEST_PATH   — path to quality-gate-manifest.json
#   PROJECT_ROOT    — project root (default: $CLAUDE_PROJECT_DIR or cwd)
#   VIBEOS_FRAMEWORK_DIR — framework root where gate scripts live (auto-detected from .vibeos/)
#   GATE_TIMEOUT    — per-gate timeout in seconds (default: 120)
#   WO_NUMBER       — work order number for variable substitution
#   EVIDENCE_DIR    — evidence directory for variable substitution
#
# Exit codes:
#   0 = All gates passed (or within baselines)
#   1 = One or more blocking gates failed
#   2 = Configuration error
#   3 = Lock held by another runner
set -euo pipefail

FRAMEWORK_VERSION="2.1.0"
RUNNER_NAME="gate-runner"

# ─── Usage ───────────────────────────────────────────────────────
usage() {
  cat <<'EOF'
Usage:
  bash scripts/gate-runner.sh <phase> [options]

Phases:
  session_start    pre_commit       wo_exit
  wo_exit_backend  wo_exit_frontend wo_exit_crosscutting
  wo_exit_governance  post_deploy   full_audit   session_end

Options:
  --continue-on-failure   Don't stop on first blocking gate failure
  --json                  Output results as JSON
  --manifest PATH         Custom manifest path
  --wo NUMBER             Work order number
  --evidence-dir PATH     Evidence directory
  --timeout SECONDS       Per-gate timeout (default: 120)
  --lock                  Acquire runner lock
  --dry-run               Show gates without executing
  --framework-dir PATH    Plugin/framework root (where scripts/ lives)
  --project-dir PATH      Target project root
  -h, --help              Show usage

Examples:
  bash scripts/gate-runner.sh pre_commit
  bash scripts/gate-runner.sh wo_exit --continue-on-failure --wo 42
  bash scripts/gate-runner.sh full_audit --json
EOF
}

# ─── Logging ─────────────────────────────────────────────────────
log()  { echo "[$RUNNER_NAME] $*"; }
warn() { echo "[$RUNNER_NAME] WARN: $*"; }
err()  { echo "[$RUNNER_NAME] ERROR: $*" >&2; }
die()  { err "$*"; exit 2; }

# ─── Defaults ────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Auto-detect framework dir: .vibeos/ in project, or parent of scripts/ dir
if [ -d "${CLAUDE_PROJECT_DIR:-.}/.vibeos/scripts" ]; then
  FRAMEWORK_DIR="${CLAUDE_PROJECT_DIR:-.}/.vibeos"
elif [ -n "${VIBEOS_FRAMEWORK_DIR:-}" ]; then
  FRAMEWORK_DIR="$VIBEOS_FRAMEWORK_DIR"
else
  FRAMEWORK_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
fi
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-${PROJECT_ROOT:-$(pwd)}}"
DEFAULT_CLAUDE_MANIFEST="$PROJECT_ROOT/.claude/quality-gate-manifest.json"
DEFAULT_ROOT_MANIFEST="$PROJECT_ROOT/quality-gate-manifest.json"
if [[ -n "${MANIFEST_PATH:-}" ]]; then
  MANIFEST_EXPLICIT=true
else
  MANIFEST_PATH=""
  MANIFEST_EXPLICIT=false
fi
GATE_TIMEOUT="${GATE_TIMEOUT:-120}"
WO_NUMBER="${WO_NUMBER:-}"
EVIDENCE_DIR="${EVIDENCE_DIR:-}"
CONTINUE_ON_FAILURE=false
JSON_OUTPUT=false
USE_LOCK=false
DRY_RUN=false
PHASE=""
LOCK_FILE="$PROJECT_ROOT/.claude/.gate-runner.lock"
STALE_LOCK_SECONDS=600

# ─── Parse Arguments ─────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --continue-on-failure) CONTINUE_ON_FAILURE=true; shift ;;
    --json) JSON_OUTPUT=true; shift ;;
    --manifest) MANIFEST_PATH="$2"; MANIFEST_EXPLICIT=true; shift 2 ;;
    --wo) WO_NUMBER="$2"; shift 2 ;;
    --evidence-dir) EVIDENCE_DIR="$2"; shift 2 ;;
    --timeout) GATE_TIMEOUT="$2"; shift 2 ;;
    --lock) USE_LOCK=true; shift ;;
    --dry-run) DRY_RUN=true; shift ;;
    --framework-dir) FRAMEWORK_DIR="$2"; shift 2 ;;
    --project-dir) PROJECT_ROOT="$2"; shift 2 ;;
    -*) die "Unknown option: $1" ;;
    *)
      if [[ -z "$PHASE" ]]; then
        PHASE="$1"
      else
        die "Unexpected argument: $1"
      fi
      shift ;;
  esac
done

if [[ -z "$PHASE" ]]; then
  usage
  die "Phase argument required"
fi

resolve_manifest_path() {
  if [[ "$MANIFEST_EXPLICIT" == "true" ]]; then
    printf '%s' "$MANIFEST_PATH"
    return 0
  fi

  if [[ -f "$DEFAULT_CLAUDE_MANIFEST" ]]; then
    printf '%s' "$DEFAULT_CLAUDE_MANIFEST"
  elif [[ -f "$DEFAULT_ROOT_MANIFEST" ]]; then
    printf '%s' "$DEFAULT_ROOT_MANIFEST"
  else
    printf '%s' "$DEFAULT_CLAUDE_MANIFEST"
  fi
}

MANIFEST_PATH="$(resolve_manifest_path)"

# ─── Validate Manifest ──────────────────────────────────────────
if [[ ! -f "$MANIFEST_PATH" ]]; then
  die "Manifest not found: $MANIFEST_PATH (looked for .claude/quality-gate-manifest.json then quality-gate-manifest.json)"
fi

if ! command -v jq >/dev/null 2>&1; then
  die "jq is required but not installed"
fi

if ! jq empty "$MANIFEST_PATH" 2>/dev/null; then
  die "Invalid JSON in manifest: $MANIFEST_PATH"
fi

if ! command -v python3 >/dev/null 2>&1; then
  die "python3 is required but not installed"
fi

# ─── Lock Management ────────────────────────────────────────────
acquire_lock() {
  if [[ "$USE_LOCK" != "true" ]]; then
    return 0
  fi

  mkdir -p "$(dirname "$LOCK_FILE")"

  if [[ -f "$LOCK_FILE" ]]; then
    local lock_pid lock_time now_time age
    lock_pid=$(head -1 "$LOCK_FILE" 2>/dev/null || echo "0")
    lock_time=$(tail -1 "$LOCK_FILE" 2>/dev/null || echo "0")
    now_time=$(date +%s)
    age=$((now_time - lock_time))

    # Check if stale
    if [[ $age -gt $STALE_LOCK_SECONDS ]]; then
      warn "Removing stale lock (age: ${age}s, PID: $lock_pid)"
      rm -f "$LOCK_FILE"
    elif kill -0 "$lock_pid" 2>/dev/null; then
      err "Runner already active (PID: $lock_pid, age: ${age}s)"
      exit 3
    else
      warn "Removing orphaned lock (PID $lock_pid not running)"
      rm -f "$LOCK_FILE"
    fi
  fi

  echo "$$" > "$LOCK_FILE"
  echo "$(date +%s)" >> "$LOCK_FILE"
}

release_lock() {
  if [[ "$USE_LOCK" == "true" && -f "$LOCK_FILE" ]]; then
    rm -f "$LOCK_FILE"
  fi
}

trap release_lock EXIT

# ─── Gate Collection ─────────────────────────────────────────────
# Uses Python to parse manifest and resolve phase includes + deduplication
collect_gates() {
  python3 - "$MANIFEST_PATH" "$PHASE" <<'PYEOF'
import json
import sys
from pathlib import Path

manifest_path = sys.argv[1]
target_phase = sys.argv[2]

with open(manifest_path) as f:
    manifest = json.load(f)

phases = manifest.get("phases", {})

def resolve_phase(phase_name, visited=None):
    """Resolve a phase's gates, including inherited gates from 'includes'."""
    if visited is None:
        visited = set()
    if phase_name in visited:
        return []
    visited.add(phase_name)

    phase = phases.get(phase_name, {})
    gates = []

    # First, resolve included phases
    includes = phase.get("includes", [])
    for inc in includes:
        gates.extend(resolve_phase(inc, visited))

    # Then add this phase's own gates
    for gate in phase.get("gates", []):
        gates.append(gate)

    return gates

if target_phase in phases:
    raw_gates = resolve_phase(target_phase)
elif target_phase == "wo_exit":
    fallback_phases = [
        name for name in (
            "wo_exit_backend",
            "wo_exit_frontend",
            "wo_exit_crosscutting",
            "wo_exit_governance",
        )
        if name in phases
    ]
    if not fallback_phases:
        print(f"ERROR:Phase '{target_phase}' not found in manifest", file=sys.stderr)
        print(f"ERROR:Available phases: {', '.join(sorted(phases.keys()))}", file=sys.stderr)
        sys.exit(1)

    raw_gates = []
    for phase_name in fallback_phases:
        raw_gates.extend(resolve_phase(phase_name))
else:
    print(f"ERROR:Phase '{target_phase}' not found in manifest", file=sys.stderr)
    print(f"ERROR:Available phases: {', '.join(sorted(phases.keys()))}", file=sys.stderr)
    sys.exit(1)

# Deduplicate by script path, keeping the LAST occurrence (most specific config wins)
seen = {}
for gate in raw_gates:
    script = gate.get("script", "")
    seen[script] = gate

# Preserve order: iterate raw_gates, emit each script only on its last occurrence
final = []
last_index = {}
for i, gate in enumerate(raw_gates):
    last_index[gate.get("script", "")] = i

emitted = set()
for i, gate in enumerate(raw_gates):
    script = gate.get("script", "")
    if last_index[script] == i and script not in emitted:
        final.append(seen[script])
        emitted.add(script)

# Output as JSON array
print(json.dumps(final))
PYEOF
}

# ─── Tier Info ───────────────────────────────────────────────────
get_tier_info() {
  local tier="$1"
  python3 - "$MANIFEST_PATH" "$tier" <<'PYEOF'
import json, sys
with open(sys.argv[1]) as f:
    manifest = json.load(f)
tier = int(sys.argv[2])
tiers = manifest.get("tiers", {})
tier_def = tiers.get(str(tier), {})
blocking = tier_def.get("blocking", tier <= 1)
label = tier_def.get("label", f"tier-{tier}")
print(f"{blocking}|{label}")
PYEOF
}

# ─── Baseline Check ─────────────────────────────────────────────
check_baseline() {
  local gate_name="$1"
  local exit_code="$2"
  local output="$3"

  python3 - "$MANIFEST_PATH" "$gate_name" "$exit_code" "$output" <<'PYEOF'
import json, re, sys

manifest_path = sys.argv[1]
gate_name = sys.argv[2]
exit_code = int(sys.argv[3])
output = sys.argv[4]

with open(manifest_path) as f:
    manifest = json.load(f)

baselines = manifest.get("known_baselines", {})

if gate_name not in baselines:
    # No baseline — failure is real
    print("no_baseline")
    sys.exit(0)

baseline = baselines[gate_name]
max_allowed = baseline.get("max_allowed_failures", 0)
pattern_str = baseline.get("fail_count_pattern", "")

if not pattern_str:
    # Baseline exists but no pattern — any failure within max is OK
    if exit_code != 0 and max_allowed > 0:
        print(f"within_baseline|0|{max_allowed}")
    else:
        print("exceeded_baseline")
    sys.exit(0)

# Extract failure count from output using pattern
match = re.search(pattern_str, output)
if match:
    try:
        fail_count = int(match.group(1))
    except (IndexError, ValueError):
        fail_count = 1
else:
    fail_count = 1 if exit_code != 0 else 0

if fail_count <= max_allowed:
    print(f"within_baseline|{fail_count}|{max_allowed}")
else:
    print(f"exceeded_baseline|{fail_count}|{max_allowed}")
PYEOF
}

# ─── Run Single Gate ─────────────────────────────────────────────
run_single_gate() {
  local script="$1"
  local gate_name="$2"
  local tier="$3"
  local env_json="$4"
  local timeout="$5"

  local script_path="$FRAMEWORK_DIR/$script"

  if [[ ! -f "$script_path" ]]; then
    warn "Script not found: $script"
    echo "SKIP|$gate_name|script_not_found|0"
    return 0
  fi

  if [[ ! -x "$script_path" && ! "$script_path" == *.py ]]; then
    chmod +x "$script_path" 2>/dev/null || true
  fi

  # Build environment export commands from gate config
  local env_exports=""
  if [[ "$env_json" != "{}" && "$env_json" != "null" && -n "$env_json" ]]; then
    env_exports=$(python3 -c "
import json, sys
env = json.loads(sys.argv[1])
wo = sys.argv[2]
ev = sys.argv[3]
pr = sys.argv[4]
for k, v in env.items():
    if k.startswith('_comment'):
        continue
    v = str(v)
    v = v.replace('\$WO_NUMBER', wo)
    v = v.replace('\$EVIDENCE_DIR', ev)
    v = v.replace('\$PROJECT_ROOT', pr)
    # Export as env var
    print(f'export {k}={v!r}')
" "$env_json" "$WO_NUMBER" "$EVIDENCE_DIR" "$PROJECT_ROOT" 2>/dev/null || echo "")
  fi

  # Determine runner command
  local runner
  if [[ "$script_path" == *.py ]]; then
    runner="python3"
  else
    runner="bash"
  fi

  # Run with timeout (portable: gtimeout on macOS, timeout on Linux)
  local output exit_code start_time end_time duration
  start_time=$(date +%s)

  # Build the full command
  local full_cmd=""
  if [[ -n "$env_exports" ]]; then
    full_cmd="$env_exports"$'\n'
  fi
  full_cmd+="\"$runner\" \"$script_path\""

  if command -v gtimeout >/dev/null 2>&1; then
    output=$(gtimeout "$timeout" bash -c "$full_cmd" 2>&1) && exit_code=0 || exit_code=$?
  elif command -v timeout >/dev/null 2>&1; then
    output=$(timeout "$timeout" bash -c "$full_cmd" 2>&1) && exit_code=0 || exit_code=$?
  else
    output=$(bash -c "$full_cmd" 2>&1) && exit_code=0 || exit_code=$?
  fi

  end_time=$(date +%s)
  duration=$((end_time - start_time))

  # Timeout detection (exit code 124 from GNU timeout)
  if [[ $exit_code -eq 124 ]]; then
    echo "TIMEOUT|$gate_name|timeout_${timeout}s|$duration"
    return 0
  fi

  if [[ $exit_code -eq 0 ]]; then
    if printf '%s\n' "$output" | grep -q 'SKIP:'; then
      echo "SKIP|$gate_name|$exit_code|$duration"
      printf '%s\n' "$output"
    else
      echo "PASS|$gate_name|$exit_code|$duration"
    fi
  else
    echo "FAIL|$gate_name|$exit_code|$duration"
    printf '%s\n' "$output"
  fi

  return 0
}

# ─── Main Execution ─────────────────────────────────────────────
acquire_lock

if [[ "$JSON_OUTPUT" != "true" ]]; then
  log "Quality Gate Runner v$FRAMEWORK_VERSION"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  log "Phase: $PHASE"
  log "Manifest: $MANIFEST_PATH"
  log "Project: $PROJECT_ROOT"
  log "Framework: $FRAMEWORK_DIR"
  [[ -n "$WO_NUMBER" ]] && log "Work Order: $WO_NUMBER"
  echo ""
fi

# Collect gates for this phase
gates_json=$(collect_gates)
if [[ $? -ne 0 || -z "$gates_json" ]]; then
  die "Failed to collect gates for phase: $PHASE"
fi

gate_count=$(echo "$gates_json" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))")

if [[ "$gate_count" -eq 0 ]]; then
  if [[ "$JSON_OUTPUT" == "true" ]]; then
    echo '{"phase":"'"$PHASE"'","gates":[],"summary":{"total":0,"passed":0,"failed":0,"skipped":0,"result":"PASS"}}'
  else
    log "No gates configured for phase: $PHASE"
  fi
  exit 0
fi

if [[ "$JSON_OUTPUT" != "true" ]]; then
  log "Running $gate_count gate(s)..."
  echo ""
fi

# ─── Dry Run ─────────────────────────────────────────────────────
if [[ "$DRY_RUN" == "true" ]]; then
  echo "$gates_json" | python3 -c "
import json, sys
gates = json.load(sys.stdin)
for i, g in enumerate(gates, 1):
    name = g.get('name', g.get('script', 'unknown'))
    script = g.get('script', '?')
    tier = g.get('tier', 1)
    print(f'  {i}. [{name}] (tier {tier}) → {script}')
"
  log "Dry run complete — $gate_count gate(s) would execute"
  exit 0
fi

# ─── Execute Gates ───────────────────────────────────────────────
total=0
passed=0
failed=0
skipped=0
baselined=0
timed_out=0
blocking_failures=0
results_json="["

# Parse gates and run each one
while IFS= read -r gate_line; do
  gate_name=$(echo "$gate_line" | python3 -c "import json,sys; g=json.load(sys.stdin); print(g.get('name', g.get('script','unknown')))")
  gate_script=$(echo "$gate_line" | python3 -c "import json,sys; g=json.load(sys.stdin); print(g.get('script',''))")
  gate_tier=$(echo "$gate_line" | python3 -c "import json,sys; g=json.load(sys.stdin); print(g.get('tier', 1))")
  gate_env=$(echo "$gate_line" | python3 -c "import json,sys; g=json.load(sys.stdin); print(json.dumps(g.get('env', {})))")
  gate_timeout_override=$(echo "$gate_line" | python3 -c "import json,sys; g=json.load(sys.stdin); print(g.get('timeout', 0))")

  effective_timeout="$GATE_TIMEOUT"
  if [[ "$gate_timeout_override" -gt 0 ]] 2>/dev/null; then
    effective_timeout="$gate_timeout_override"
  fi

  total=$((total + 1))

  # Get tier info
  tier_info=$(get_tier_info "$gate_tier")
  tier_blocking=$(echo "$tier_info" | cut -d'|' -f1)
  tier_label=$(echo "$tier_info" | cut -d'|' -f2)

  if [[ "$JSON_OUTPUT" != "true" ]]; then
    echo -n "  [$gate_name] ($tier_label) ... "
  fi

  # Run the gate
  result=$(run_single_gate "$gate_script" "$gate_name" "$gate_tier" "$gate_env" "$effective_timeout")
  result_header=$(printf '%s\n' "$result" | awk 'NR==1 {print; exit}')
  gate_output=$(printf '%s\n' "$result" | awk 'NR>1 {print}')
  status=$(printf '%s\n' "$result_header" | cut -d'|' -f1)
  duration=$(printf '%s\n' "$result_header" | cut -d'|' -f4)

  gate_result="pass"

  case "$status" in
    PASS)
      passed=$((passed + 1))
      if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo "PASS (${duration}s)"
      fi
      ;;

    SKIP)
      skipped=$((skipped + 1))
      gate_result="skip"
      if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo "SKIP"
      fi
      ;;

    TIMEOUT)
      timed_out=$((timed_out + 1))
      gate_result="timeout"
      if [[ "$tier_blocking" == "true" || "$tier_blocking" == "True" ]]; then
        blocking_failures=$((blocking_failures + 1))
        failed=$((failed + 1))
      fi
      if [[ "$JSON_OUTPUT" != "true" ]]; then
        echo "TIMEOUT (${effective_timeout}s)"
      fi
      ;;

    FAIL)
      gate_exit_code=$(printf '%s\n' "$result_header" | cut -d'|' -f3)

      # Check baseline
      baseline_result=$(check_baseline "$gate_name" "$gate_exit_code" "$gate_output")
      baseline_status=$(echo "$baseline_result" | cut -d'|' -f1)

      case "$baseline_status" in
        within_baseline)
          baselined=$((baselined + 1))
          passed=$((passed + 1))
          gate_result="baselined"
          bl_count=$(echo "$baseline_result" | cut -d'|' -f2)
          bl_max=$(echo "$baseline_result" | cut -d'|' -f3)
          if [[ "$JSON_OUTPUT" != "true" ]]; then
            echo "PASS (baselined: $bl_count/$bl_max) (${duration}s)"
          fi
          ;;

        exceeded_baseline)
          failed=$((failed + 1))
          gate_result="fail"
          bl_count=$(echo "$baseline_result" | cut -d'|' -f2)
          bl_max=$(echo "$baseline_result" | cut -d'|' -f3)
          if [[ "$tier_blocking" == "true" || "$tier_blocking" == "True" ]]; then
            blocking_failures=$((blocking_failures + 1))
            if [[ "$JSON_OUTPUT" != "true" ]]; then
              echo "FAIL [BLOCKING] (exceeded baseline: $bl_count/$bl_max) (${duration}s)"
            fi
          else
            if [[ "$JSON_OUTPUT" != "true" ]]; then
              echo "FAIL (advisory, exceeded baseline: $bl_count/$bl_max) (${duration}s)"
            fi
          fi
          ;;

        no_baseline|*)
          failed=$((failed + 1))
          gate_result="fail"
          if [[ "$tier_blocking" == "true" || "$tier_blocking" == "True" ]]; then
            blocking_failures=$((blocking_failures + 1))
            if [[ "$JSON_OUTPUT" != "true" ]]; then
              echo "FAIL [BLOCKING] (${duration}s)"
            fi
          else
            if [[ "$JSON_OUTPUT" != "true" ]]; then
              echo "FAIL (advisory) (${duration}s)"
            fi
          fi
          ;;
      esac

      # Show failure details for non-JSON output
      if [[ "$JSON_OUTPUT" != "true" && "$gate_result" == "fail" ]]; then
        echo "$gate_output" | head -20 | sed 's/^/    /'
        output_lines=$(echo "$gate_output" | wc -l | tr -d ' ')
        if [[ "$output_lines" -gt 20 ]]; then
          echo "    ... ($((output_lines - 20)) more lines)"
        fi
      fi

      # Stop on blocking failure unless --continue-on-failure
      if [[ "$gate_result" == "fail" && "$tier_blocking" == "true" && "$CONTINUE_ON_FAILURE" != "true" ]]; then
        if [[ "$JSON_OUTPUT" != "true" ]]; then
          echo ""
          log "ABORT: Blocking gate failed. Use --continue-on-failure to run remaining gates."
        fi
        # Still output summary
        break
      fi
      ;;
  esac

  # Build JSON result entry
  if [[ "$JSON_OUTPUT" == "true" ]]; then
    if [[ $total -gt 1 ]]; then results_json+=","; fi
    results_json+="{\"name\":\"$gate_name\",\"script\":\"$gate_script\",\"tier\":$gate_tier,\"result\":\"$gate_result\",\"duration\":${duration:-0}}"
  fi

done < <(echo "$gates_json" | python3 -c "
import json, sys
gates = json.load(sys.stdin)
for g in gates:
    print(json.dumps(g))
")

# ─── Summary ─────────────────────────────────────────────────────
overall_result="PASS"
exit_code=0

if [[ $blocking_failures -gt 0 ]]; then
  overall_result="FAIL"
  exit_code=1
elif [[ $failed -gt 0 ]]; then
  overall_result="PASS (with advisory failures)"
fi

if [[ "$JSON_OUTPUT" == "true" ]]; then
  results_json+="]"
  cat <<JSONEOF
{
  "phase": "$PHASE",
  "manifest": "$MANIFEST_PATH",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "gates": $results_json,
  "summary": {
    "total": $total,
    "passed": $passed,
    "failed": $failed,
    "skipped": $skipped,
    "baselined": $baselined,
    "timed_out": $timed_out,
    "blocking_failures": $blocking_failures,
    "result": "$overall_result"
  }
}
JSONEOF
else
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  log "Phase: $PHASE"
  log "Total: $total | Passed: $passed | Failed: $failed | Skipped: $skipped"
  [[ $baselined -gt 0 ]] && log "Baselined: $baselined (pre-existing, within limits)"
  [[ $timed_out -gt 0 ]] && log "Timed out: $timed_out"

  if [[ "$overall_result" == "FAIL" ]]; then
    log "Result: FAIL ($blocking_failures blocking failure(s))"
  elif [[ $failed -gt 0 ]]; then
    log "Result: PASS (with $failed advisory failure(s))"
  else
    log "Result: PASS"
  fi
fi

exit $exit_code
