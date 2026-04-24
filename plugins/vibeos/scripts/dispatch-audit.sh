#!/usr/bin/env bash
# VibeOS audit dispatcher.
#
# Creates audit dispatch directories and manifests, then aggregates
# populated findings files into summary.json and findings.md.

set -euo pipefail

FRAMEWORK_VERSION="2.2.0"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

usage() {
  cat <<'EOF'
usage:
  dispatch-audit.sh <trigger> [--tier N] [--wo WO-id] [--phase phase-id]
  dispatch-audit.sh --aggregate <dispatch-id>

triggers: wo-draft | wo-exit | phase-exit | canon-revision | security-change | live-fire
EOF
  exit 2
}

AGGREGATE_ID=""
TRIGGER=""
TIER=""
WO_ID=""
PHASE_ID=""

while [ $# -gt 0 ]; do
  case "$1" in
    --aggregate) AGGREGATE_ID="$2"; shift 2 ;;
    --tier) TIER="$2"; shift 2 ;;
    --wo) WO_ID="$2"; shift 2 ;;
    --phase) PHASE_ID="$2"; shift 2 ;;
    -h|--help) usage ;;
    wo-draft|wo-exit|phase-exit|canon-revision|security-change|live-fire)
      TRIGGER="$1"; shift ;;
    *) printf 'unknown arg: %s\n' "$1" >&2; usage ;;
  esac
done

required_auditors() {
  local trigger="$1" tier="$2"
  case "$trigger" in
    wo-draft) echo "plan" ;;
    wo-exit)
      case "$tier" in
        1) echo "evidence" ;;
        2) echo "evidence correctness test" ;;
        3) echo "evidence correctness test security architecture" ;;
        4) echo "evidence correctness test security architecture product_drift" ;;
        *) echo "evidence correctness test" ;;
      esac
      ;;
    phase-exit|live-fire) echo "evidence correctness test security architecture product_drift" ;;
    canon-revision) echo "evidence product_drift" ;;
    security-change) echo "security architecture test" ;;
    *) echo "" ;;
  esac
}

companion_required() {
  local trigger="$1" tier="$2"
  case "$trigger" in
    wo-exit)
      case "$tier" in
        3|4) echo "mandatory" ;;
        *) echo "none" ;;
      esac
      ;;
    phase-exit|live-fire|security-change) echo "mandatory" ;;
    canon-revision) echo "recommended" ;;
    *) echo "none" ;;
  esac
}

if [ -n "$AGGREGATE_ID" ]; then
  audit_dir="$REPO_ROOT/docs/audits/$AGGREGATE_ID"
  if [ ! -d "$audit_dir" ]; then
    printf 'error: audit dir not found: %s\n' "$audit_dir" >&2
    exit 1
  fi
  exec python3 "$REPO_ROOT/scripts/audit_aggregate.py" "$audit_dir"
fi

if [ -z "$TRIGGER" ]; then
  usage
fi

case "$TRIGGER" in
  wo-exit)
    if [ -z "$TIER" ] || [ -z "$WO_ID" ]; then
      printf 'wo-exit requires --tier N and --wo WO-id\n' >&2
      exit 2
    fi
    ;;
  phase-exit)
    if [ -z "$PHASE_ID" ]; then
      printf 'phase-exit requires --phase phase-id\n' >&2
      exit 2
    fi
    ;;
esac

iso="$(date -u +%Y-%m-%d)"
slug=""
if [ -n "$WO_ID" ]; then slug="-${WO_ID}"; fi
if [ -n "$PHASE_ID" ]; then slug="-${PHASE_ID}"; fi
dispatch_id="${TRIGGER}${slug}-${iso}"
audit_dir="$REPO_ROOT/docs/audits/$dispatch_id"
mkdir -p "$audit_dir"

auditors="$(required_auditors "$TRIGGER" "$TIER")"
companion="$(companion_required "$TRIGGER" "$TIER")"
manifest_out="$audit_dir/dispatch-manifest.json"

DISPATCH_ID_ENV="$dispatch_id" \
TRIGGER_ENV="$TRIGGER" \
TIER_ENV="$TIER" \
WO_ID_ENV="$WO_ID" \
PHASE_ENV="$PHASE_ID" \
AUDITORS_ENV="$auditors" \
COMPANION_ENV="$companion" \
ISO_ENV="$iso" \
MANIFEST_OUT_ENV="$manifest_out" \
python3 - <<'PY'
import json
import os
from pathlib import Path

data = {
    "dispatch_id": os.environ["DISPATCH_ID_ENV"],
    "trigger": os.environ["TRIGGER_ENV"],
    "tier": os.environ["TIER_ENV"],
    "wo_id": os.environ["WO_ID_ENV"],
    "phase": os.environ["PHASE_ENV"],
    "required_auditors": [a for a in os.environ["AUDITORS_ENV"].split() if a],
    "companion_required": os.environ["COMPANION_ENV"],
    "iso_date": os.environ["ISO_ENV"],
}
Path(os.environ["MANIFEST_OUT_ENV"]).write_text(
    json.dumps(data, indent=2) + "\n",
    encoding="utf-8",
)
PY

cat <<EOF

dispatch created: $dispatch_id
manifest: $manifest_out

required L2 auditors: $auditors
companion audit: $companion

next steps:
  1. invoke the required auditors
  2. write findings to $audit_dir/<auditor>-findings.md
  3. if companion audit is required, write its output to $audit_dir/companion-findings.md
  4. aggregate:
       bash scripts/dispatch-audit.sh --aggregate $dispatch_id
EOF
