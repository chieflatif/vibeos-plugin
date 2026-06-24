#!/usr/bin/env bash
# VibeOS Plugin — Lane Loop Stop Hook
# Hook type: Stop
# Enforces bounded lane loops from active WO frontmatter.

FRAMEWORK_VERSION="2.2.0"

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
CWD_VALUE=$(echo "$INPUT" | jq -r '.cwd // ""' 2>/dev/null || echo "")
PROJECT_ROOT="${CLAUDE_PROJECT_DIR:-$CWD_VALUE}"
if [ -z "$PROJECT_ROOT" ]; then
  PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
fi

export VIBEOS_STOP_INPUT="$INPUT"
export VIBEOS_PROJECT_ROOT="$PROJECT_ROOT"

python3 - <<'PY'
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.2.0"


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\n")


def parse_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        return {}
    data: dict[str, Any] = {}
    for raw_line in text[4:end].splitlines():
        if not raw_line or raw_line.startswith(" ") or ":" not in raw_line:
            continue
        key, raw_value = raw_line.split(":", 1)
        value = raw_value.strip().strip("'\"")
        if value == "null":
            data[key.strip()] = None
        elif re.fullmatch(r"-?\d+", value):
            data[key.strip()] = int(value)
        elif re.fullmatch(r"-?\d+(?:\.\d+)?", value):
            data[key.strip()] = float(value)
        else:
            data[key.strip()] = value
    return data


def resolve_wo_path(root: Path, ref: str) -> Path | None:
    if not ref:
        return None
    candidates = [Path(ref), root / ref]
    if ref.startswith("WO-"):
        candidates.extend(sorted((root / "docs/planning").glob(f"{ref}*.md")))
        candidates.append(root / "docs/planning" / f"{ref}.md")
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def gate_events(path: Path) -> list[dict[str, Any]]:
    events = []
    if not path.exists():
        return events
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def command_satisfies_goal(command: str, goal: str) -> bool:
    command = command.lower()
    goal = goal.lower()
    if "pre_commit" in goal or "pre-commit" in goal:
        return "pre_commit" in command or "pre-commit" in command
    if "wo_entry" in goal:
        return "wo_entry" in command
    if "wo_exit" in goal:
        return "wo_exit" in command
    if "pytest" in goal:
        return "pytest" in command
    if "test" in goal:
        return "pytest" in command or "validate-tests-pass" in command or "npm test" in command or "pnpm test" in command
    if "gate" in goal:
        return "gate-runner.sh" in command or "validate-" in command
    return False


def verify_goal(root: Path, goal: str) -> dict[str, Any]:
    gate_path = root / ".vibeos/hook-events/gate-results.jsonl"
    for event in reversed(gate_events(gate_path)):
        command = str(event.get("command") or "")
        status = str(event.get("status") or "").lower()
        if status == "pass" and command_satisfies_goal(command, goal):
            return {
                "verified": True,
                "source": str(gate_path.relative_to(root)),
                "command": command,
                "status": status,
            }
    return {
        "verified": False,
        "source": str(gate_path.relative_to(root)),
        "reason": "No passing gate/test evidence matched loop_goal.",
    }


def emit(decision: str, reason: str, lane_loop: dict[str, Any], code: int) -> None:
    payload = {
        "decision": decision,
        "reason": reason,
        "lane_loop": lane_loop,
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    raise SystemExit(code)


def main() -> int:
    root = Path(os.environ["VIBEOS_PROJECT_ROOT"]).resolve()
    try:
        hook_input = json.loads(os.environ.get("VIBEOS_STOP_INPUT") or "{}")
    except json.JSONDecodeError:
        hook_input = {}

    session_path = root / ".vibeos/session-state.json"
    session = load_json(session_path, {})
    active_wo = str(hook_input.get("active_wo") or session.get("active_wo") or "")
    wo_path = resolve_wo_path(root, active_wo)
    if not wo_path:
        return 0

    fm = parse_frontmatter(wo_path)
    goal = str(fm.get("loop_goal") or "").strip()
    ceiling = fm.get("loop_ceiling_turns")
    if not goal or not isinstance(ceiling, int):
        return 0

    wo_id = str(fm.get("wo") or wo_path.stem.split("-", 2)[0])
    previous = session.get("lane_loop") if isinstance(session.get("lane_loop"), dict) else {}
    prior_count = int(previous.get("turn_count") or 0) if previous.get("wo") == wo_id else 0
    turn_count = prior_count + 1
    evidence = verify_goal(root, goal)
    now = iso_now()

    if evidence["verified"]:
        status = "GOAL_VERIFIED"
        active = False
        decision = "allow"
        reason = "Loop goal verified from gate/test evidence."
        code = 0
    elif turn_count >= ceiling:
        status = "STALLED_AT_CEILING"
        active = False
        decision = "allow"
        reason = f"Loop ceiling reached without gate/test evidence for loop_goal: {goal}"
        code = 0
    else:
        status = "RUNNING"
        active = True
        decision = "block"
        reason = f"Loop goal not yet verified by gate/test evidence; turn {turn_count}/{ceiling}."
        code = 2

    lane_loop = {
        "framework_version": FRAMEWORK_VERSION,
        "wo": wo_id,
        "active_wo": str(wo_path.relative_to(root)),
        "goal": goal,
        "ceiling_turns": ceiling,
        "turn_count": turn_count,
        "status": status,
        "active": active,
        "goal_verified": bool(evidence["verified"]),
        "evidence": evidence,
        "last_updated": now,
    }
    session["lane_loop"] = lane_loop
    if status == "STALLED_AT_CEILING":
        session["loop_status"] = "STALLED_AT_CEILING"
        session["current_wo_status"] = "STALLED_AT_CEILING"
    elif status == "GOAL_VERIFIED":
        session["loop_status"] = "GOAL_VERIFIED"
        session["current_wo_status"] = "GOAL_VERIFIED"
    session["last_updated"] = now
    write_json(session_path, session)

    append_jsonl(
        root / ".vibeos/hook-events/lane-loop-stop.jsonl",
        {
            "timestamp": now,
            "event": "Stop",
            "decision": decision,
            "reason": reason,
            "lane_loop": lane_loop,
        },
    )
    emit(decision, reason, lane_loop, code)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
PY
