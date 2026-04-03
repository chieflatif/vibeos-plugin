# WO-058: Audit Visibility & Registration System

## Status

`Complete`

## Phase

Phase 11: Advanced Governance (v2.1)

## Objective

Create the audit lifecycle management system: automatic visibility mode selection, audit report registration, and validation that audits actually ran before WO closure. This ensures autonomous builds produce verifiable audit trails without interrupting execution flow.

## Context

Joan discovered that autonomous builds need three audit infrastructure pieces:
1. **Visibility mode selection** — Automatically choose whether to audit uncommitted code (same-tree) or committed code (worktree) based on session state
2. **Audit report registration** — Record which audit reports exist so closure gates can verify audits happened
3. **Independent audit validation** — Fail WO closure if no post-implementation audit was registered

Without this, autonomous builds either skip audits (because code isn't committed yet) or interrupt flow to commit before auditing.

## Joan Sources

- `/Users/latifhorst/Joan/.vibeos/scripts/select-audit-visibility-mode.sh`
- `/Users/latifhorst/Joan/.vibeos/scripts/validate-audit-visibility.sh`
- `/Users/latifhorst/Joan/.vibeos/scripts/validate-independent-audit.sh`
- `/Users/latifhorst/Joan/.vibeos/scripts/register-audit-report.sh`
- `/Users/latifhorst/Joan/.vibeos/scripts/register-session-audit-report.sh`

## Scope

### In Scope

1. **`scripts/select-audit-visibility-mode.sh`** — Chooses safest audit mode:
   - If uncommitted changes in WO write scope → `same-tree`
   - If all WO changes committed → `committed-tree`
   - Records selection in session-state.json
   - Never interrupts autonomy to ask user

2. **`scripts/validate-audit-visibility.sh`** — Closure gate:
   - Fails closed when audit couldn't see the code it validated
   - Checks audit visibility mode declaration exists
   - Validates audit report metadata against uncommitted changes

3. **`scripts/validate-independent-audit.sh`** — Closure gate:
   - Fails closed when WO reaches closeout without a post-implementation audit
   - Requires audit reports in `.vibeos/audit-reports/`
   - Validates auditor summaries target the active WO

4. **`scripts/register-audit-report.sh`** — Registers audit results:
   - Records audit report path and metadata in session-state.json
   - Infers WO number from report path or active WO
   - Tracks audit type (plan, completion, session, manual)

5. **`scripts/register-session-audit-report.sh`** — Session-level variant:
   - Simpler registration for end-of-session audits

### Out of Scope

- Same-tree agent creation (WO-057)
- Skill integration of visibility dispatch (WO-064)
- Codex-specific audit registration (WO-062)

## Acceptance Criteria

1. `select-audit-visibility-mode.sh` correctly identifies uncommitted WO changes and selects mode
2. `validate-audit-visibility.sh` fails when audit visibility mode is incompatible with code state
3. `validate-independent-audit.sh` fails when no audit report exists for active WO
4. `register-audit-report.sh` writes to session-state.json correctly
5. All scripts pass `bash -n` syntax validation
6. All scripts have `FRAMEWORK_VERSION="2.1.0"` and standard headers
7. No Joan-specific references (NWO, kernel, canon)

## Dependencies

- WO-056 — session state schema (visibility mode stored in session-state.json)

## Files Created

- `plugins/vibeos/scripts/select-audit-visibility-mode.sh`
- `plugins/vibeos/scripts/validate-audit-visibility.sh`
- `plugins/vibeos/scripts/validate-independent-audit.sh`
- `plugins/vibeos/scripts/register-audit-report.sh`
- `plugins/vibeos/scripts/register-session-audit-report.sh`
