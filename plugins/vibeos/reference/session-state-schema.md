# Session State Schema

## File Location

`.vibeos/session-state.json` — created by `activate-session.sh` at WO entry, read by hooks and gates for context-aware enforcement.

## Schema

```json
{
  "session_id": "string — unique session identifier (ISO timestamp or CLAUDE_SESSION_ID)",
  "mode": "string — 'autonomous' | 'supervised'",
  "active": "boolean — true when session is running, false after ended_at set",
  "started_at": "string — ISO-8601 timestamp of session start",
  "last_updated": "string — ISO-8601 timestamp of last update",
  "active_wo": "string — relative path to the current work order file",
  "completed_wos": [
    {
      "wo": "string — WO number (e.g., 'WO-056')",
      "title": "string — WO title",
      "completed_at": "string — ISO-8601 timestamp",
      "summary": "string — 1-line summary of what was built"
    }
  ],
  "phase_checkpoints": [
    {
      "phase": "number — phase number",
      "completed_at": "string — ISO-8601 timestamp",
      "result": "string — 'passed' | 'failed' | 'skipped'"
    }
  ],
  "last_audit_report": "string | null — path to most recent WO audit report",
  "last_session_audit_report": "string | null — path to most recent session audit report",
  "last_audited_at": "string | null — ISO-8601 timestamp of last audit",
  "audit_visibility_mode": "string | null — 'same-tree' | 'snapshot' | 'committed-tree'",
  "audit_snapshot_ref": "string | null — git ref for snapshot mode auditing",
  "audit_dispatch_profile": "string | null — 'same-tree' | 'worktree'",
  "long_run": {
    "run_id": "string — durable id for a 24-48 hour autonomy run",
    "active": "boolean — true while the long-run control plane is active",
    "target_hours": "number — intended run duration, usually 24",
    "max_hours": "number — hard maximum, usually 48",
    "heartbeat_interval_minutes": "number — heartbeat cadence",
    "checkpoint_interval_minutes": "number — checkpoint cadence",
    "audit_interval_minutes": "number — audit cadence",
    "loop_iteration": "number — current long-run loop iteration",
    "last_heartbeat_at": "string | null — latest heartbeat timestamp",
    "last_heartbeat_file": "string | null — latest heartbeat artifact path",
    "last_checkpoint_at": "string | null — latest checkpoint timestamp",
    "last_audit_at": "string | null — latest audit timestamp",
    "status": "string — running | checkpoint | audit | blocked | paused | complete",
    "stop_reason": "string | null — terminal reason when blocked, paused, or complete"
  }
}
```

## Field Details

### Core Session Fields

| Field | Type | Set By | Read By |
|---|---|---|---|
| `session_id` | string | `activate-session.sh` | Audit reports, build log |
| `mode` | string | `activate-session.sh`, `/vibeos:autonomous` | Build skill, check-in logic |
| `active` | boolean | `activate-session.sh` (true), build skill (false on stop) | All hooks |
| `started_at` | string | `activate-session.sh` (first call only) | Session duration tracking |
| `last_updated` | string | Every session state write | Staleness detection |
| `active_wo` | string | `activate-session.sh` at WO entry | Hooks, gates, audit registration |

### Audit Visibility Fields

| Field | Type | Set By | Read By |
|---|---|---|---|
| `audit_visibility_mode` | string/null | `select-audit-visibility-mode.sh` | Same-tree auditors, `validate-audit-visibility.sh` |
| `audit_snapshot_ref` | string/null | `select-audit-visibility-mode.sh` | Snapshot-mode auditors |
| `audit_dispatch_profile` | string/null | `select-audit-visibility-mode.sh` | Build/audit skills (agent dispatch) |

### Long-Run Autonomy Fields

These fields are present when the project is running a deliberate 24-48 hour autonomous session.

| Field | Type | Set By | Read By |
|---|---|---|---|
| `long_run.run_id` | string | `autonomy-heartbeat.py`, `/vibeos:autonomous` | Status, session audit, validators |
| `long_run.active` | boolean | `autonomy-heartbeat.py` | Build, status, validators |
| `long_run.target_hours` | number | `autonomy-heartbeat.py`, `/vibeos:autonomous` | Validators |
| `long_run.max_hours` | number | `autonomy-heartbeat.py`, `/vibeos:autonomous` | Validators |
| `long_run.last_heartbeat_at` | string/null | `autonomy-heartbeat.py` | Status, stale-run detection |
| `long_run.last_checkpoint_at` | string/null | `autonomy-heartbeat.py`, checkpoint flow | Validators |
| `long_run.last_audit_at` | string/null | `autonomy-heartbeat.py`, session audit | Validators |

### Audit Visibility Modes

- **`same-tree`** — Audit uncommitted code in the active working directory. Use same-tree agent variants.
- **`snapshot`** — Audit code at a specific git ref. Use same-tree agents with `AUDIT_SNAPSHOT_REF`.
- **`committed-tree`** — Audit only committed code. Use standard worktree-isolated agents.

### Lifecycle

1. **Created** — `activate-session.sh` called at WO entry
2. **Updated** — Each WO completion appends to `completed_wos`, updates `last_updated`
3. **Ended** — Build skill sets `active: false` and adds `ended_at` timestamp on session stop
4. **Next session** — `activate-session.sh` preserves `completed_wos` history if file already exists

## Example

```json
{
  "session_id": "20260403T120000Z",
  "mode": "autonomous",
  "active": true,
  "started_at": "2026-04-03T12:00:00Z",
  "last_updated": "2026-04-03T14:30:00Z",
  "active_wo": "docs/planning/WO-058-audit-visibility-registration.md",
  "completed_wos": [
    {
      "wo": "WO-056",
      "title": "Session State & Gate Manifest Infrastructure",
      "completed_at": "2026-04-03T12:45:00Z",
      "summary": "Created session state tracking, gate manifest, and hook manifest"
    },
    {
      "wo": "WO-057",
      "title": "Same-Tree Audit Agents",
      "completed_at": "2026-04-03T13:30:00Z",
      "summary": "Created 8 same-tree audit agent variants for uncommitted code auditing"
    }
  ],
  "phase_checkpoints": [],
  "last_audit_report": ".vibeos/audit-reports/WO-057-20260403T133000Z.md",
  "last_session_audit_report": null,
  "last_audited_at": "2026-04-03T13:25:00Z",
  "audit_visibility_mode": "same-tree",
  "audit_snapshot_ref": null,
  "audit_dispatch_profile": "same-tree"
}
```
