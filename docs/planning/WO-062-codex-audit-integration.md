# WO-062: Codex Audit Integration

## Status

`Complete`

## Phase

Phase 11: Advanced Governance (v2.1)

## Objective

Add Codex as an independent complementary auditor. When Claude implements, Codex audits. When Codex implements, Claude audits. Includes significance detection (auto-trigger on important events), an audit broker, and the `/vibeos:codex-audit` skill.

## Context

Joan pioneered dual-model auditing: Claude and Codex (GPT-5.4) audit each other's work. This is the single most impactful governance enhancement — independent verification catches issues that same-model self-auditing misses. The system includes:
1. **Significance detection** — Automatically determines if an event warrants a complementary audit
2. **Audit broker** — Dispatches audits to Codex via the codex-companion CLI
3. **Forced reconciliation** — Claude must fix all critical/high Codex findings before WO closure
4. **Stop hook** — Auto-triggers on plan finalization, WO completion, session closeout

## Joan Sources

- `/Users/latifhorst/Joan/.claude/skills/codex-audit/SKILL.md`
- `/Users/latifhorst/Joan/.vibeos/audit/adapters/codex.sh`
- `/Users/latifhorst/Joan/.vibeos/scripts/detect-significance.sh`
- `/Users/latifhorst/Joan/.claude/settings.json` (Stop hook with detect-significance)

## Scope

### In Scope

1. **`/vibeos:codex-audit` skill** — User-invocable skill:
   - Argument hints: `[plan|complete|session|manual] [--both] [--wo <path>] [--wait|--background] [--explicit]`
   - Audit types: plan_audit, completion_audit, session_audit, manual_audit
   - Dispatches via audit broker
   - Mandatory reconciliation: critical/high → fix now, medium → fix or create WO, low → fix if trivial
   - Evidence bundling in docs/evidence/

2. **`scripts/detect-significance.sh`** — Significance threshold detection:
   - Checks if recent event warrants complementary audit
   - Significant events: WO closure, plan finalization, session closeout
   - Returns JSON: `{"significant": true/false, "reason": "...", "audit_type": "..."}`

3. **Audit broker** — `scripts/codex-audit-broker.sh`:
   - Dispatches audit to Codex via codex-companion CLI
   - Passes context: git diff, WO file, evidence bundles, build logs
   - Collects and returns Codex findings
   - Handles Codex unavailability gracefully (falls back to Claude-only audit)

4. **Codex adapter** — `scripts/codex-audit-adapter.sh`:
   - Wraps codex-companion invocation
   - Handles timeout, retry, output parsing
   - Supports plan_audit, completion_audit, session_audit, manual_audit

5. **Stop hook integration** — Auto-trigger on significant events:
   - Check significance after every agent stop
   - If significant and autonomous mode: invoke codex-audit immediately
   - If significant and supervised: surface recommendation

### Out of Scope

- Codex CLI installation (assumes codex-companion is available)
- Modifying existing Claude-only audit flow (complementary, not replacement)
- Joan-specific audit types (NWO-specific)

## Acceptance Criteria

1. `/vibeos:codex-audit` skill has valid SKILL.md with YAML frontmatter
2. `detect-significance.sh` correctly identifies significant events from git log and session state
3. Audit broker dispatches to Codex and returns structured findings
4. Broker handles Codex unavailability with graceful fallback
5. Reconciliation protocol documented and enforced in skill
6. Stop hook correctly triggers significance detection
7. All scripts pass `bash -n` syntax validation
8. All scripts have `FRAMEWORK_VERSION="2.1.0"`
9. Skill registered in intent router for natural language invocation

## Dependencies

- WO-058 — audit visibility and registration system
- Codex CLI (codex-companion) must be installed in target environment

## Files Created

- `plugins/vibeos/skills/codex-audit/SKILL.md`
- `plugins/vibeos/scripts/detect-significance.sh`
- `plugins/vibeos/scripts/codex-audit-broker.sh`
- `plugins/vibeos/scripts/codex-audit-adapter.sh`

## Files Modified

- `plugins/vibeos/hooks/hooks.json` — add Stop hook for significance detection
- Intent router — add codex-audit routing
