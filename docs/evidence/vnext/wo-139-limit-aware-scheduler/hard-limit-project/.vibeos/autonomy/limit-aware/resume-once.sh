#!/usr/bin/env bash
set -euo pipefail

# VibeOS provider/session-limit one-shot resume profile.
# This script is pure local control-plane logic until it reaches night-loop.sh.
ROOT='/Users/latifhorst/cursor projects/vibeos-plugin/docs/evidence/vnext/wo-139-limit-aware-scheduler/hard-limit-project'
SCRIPTS_DIR="${VIBEOS_SCRIPTS_DIR:-$ROOT/.vibeos/scripts}"
MARKER='/Users/latifhorst/cursor projects/vibeos-plugin/docs/evidence/vnext/wo-139-limit-aware-scheduler/hard-limit-project/.vibeos/autonomy/limit-aware/resume-once.done'
RESET_AT=2026-04-29T01:00:00Z
RESET_EPOCH=1777424400
NOW_EPOCH="$(date -u +%s)"
if [ "$NOW_EPOCH" -lt "$RESET_EPOCH" ]; then
  echo "[limit-aware-resume] waiting until $RESET_AT"
  exit 0
fi
if [ -f "$MARKER" ]; then
  echo "[limit-aware-resume] one-shot marker exists: $MARKER"
  exit 0
fi
mkdir -p "$(dirname "$MARKER")"
printf '{"resumed_at":"%s","reset_at":"%s"}\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$RESET_AT" > "$MARKER"
python3 "$SCRIPTS_DIR/autonomy-scheduler-guard.py" --project-dir "$ROOT" --json
bash "$SCRIPTS_DIR/night-loop.sh" --project-dir "$ROOT" --evidence-dir '/Users/latifhorst/cursor projects/vibeos-plugin/docs/evidence/vnext/wo-139-limit-aware-scheduler/hard-limit-project/.vibeos/evidence/limit-resume' --execute --json
