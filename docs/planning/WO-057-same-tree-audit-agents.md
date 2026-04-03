# WO-057: Same-Tree Audit Agents

## Status

`Complete`

## Phase

Phase 11: Advanced Governance (v2.1)

## Objective

Create same-tree variants of all audit agents that can audit uncommitted code in the active working directory without creating isolated worktrees. This enables auditing mid-WO during autonomous builds — a critical gap in the current system where audits only see committed code.

## Context

The current audit system requires isolated worktrees (`isolation: worktree`), which means auditors only see committed code. During autonomous builds, significant implementation happens between commits. Joan solved this by creating "same-tree" agent variants that read the active working directory directly, with visibility mode metadata in their output headers.

Same-tree agents follow the same audit prompts but:
1. Read `.vibeos/session-state.json` to check `audit_visibility_mode`
2. Require mode to be `same-tree` or `snapshot`
3. Audit current working tree directly (no worktree isolation)
4. Include visibility metadata in output headers

## Joan Sources

- `/Users/latifhorst/Joan/.claude/agents/security-auditor-same-tree.md`
- `/Users/latifhorst/Joan/.claude/agents/architecture-auditor-same-tree.md`
- `/Users/latifhorst/Joan/.claude/agents/correctness-auditor-same-tree.md`
- `/Users/latifhorst/Joan/.claude/agents/test-auditor-same-tree.md`
- `/Users/latifhorst/Joan/.claude/agents/evidence-auditor-same-tree.md`
- `/Users/latifhorst/Joan/.claude/agents/product-drift-auditor-same-tree.md`
- `/Users/latifhorst/Joan/.claude/agents/red-team-auditor-same-tree.md`
- `/Users/latifhorst/Joan/.claude/agents/contract-validator-same-tree.md`

## Scope

### In Scope

1. **7 same-tree audit agent variants** — one for each existing audit agent plus contract validator (8 total):
   - `security-auditor-same-tree.md`
   - `architecture-auditor-same-tree.md`
   - `correctness-auditor-same-tree.md`
   - `test-auditor-same-tree.md`
   - `evidence-auditor-same-tree.md`
   - `product-drift-auditor-same-tree.md`
   - `red-team-auditor-same-tree.md`

2. **Contract validator same-tree** — `contract-validator-same-tree.md`
   - Cross-boundary frontend-backend contract verification
   - Same-tree variant for uncommitted code

3. Each same-tree agent must:
   - Read `.vibeos/session-state.json` for visibility mode
   - Validate visibility mode before producing findings
   - Include `audit_visibility_mode` and `audit_snapshot_ref` in output header
   - Use `disallowedTools: Write, Edit, Agent` (read-only)
   - NOT use `isolation: worktree`

### Out of Scope

- Joan-specific agents (evidence-auditor-joan, plan-auditor-joan, product-drift-auditor-joan, runtime-rebuild-auditor)
- Modifying existing worktree-isolated agents (they remain as-is)
- Audit dispatch logic (that's WO-058/WO-064)

## Acceptance Criteria

1. All 8 same-tree agent .md files created with correct YAML frontmatter
2. Each agent reads session-state.json and validates visibility mode
3. Each agent includes visibility metadata in output header
4. All agents are read-only (disallowedTools enforced)
5. No Joan-specific references (no kernel, NWO, canon index, Microsoft boundary)
6. Agent prompts match their worktree counterparts except for visibility handling

## Dependencies

- WO-056 — session state schema must exist for visibility mode checking

## Files Created

- `plugins/vibeos/agents/security-auditor-same-tree.md`
- `plugins/vibeos/agents/architecture-auditor-same-tree.md`
- `plugins/vibeos/agents/correctness-auditor-same-tree.md`
- `plugins/vibeos/agents/test-auditor-same-tree.md`
- `plugins/vibeos/agents/evidence-auditor-same-tree.md`
- `plugins/vibeos/agents/product-drift-auditor-same-tree.md`
- `plugins/vibeos/agents/red-team-auditor-same-tree.md`
- `plugins/vibeos/agents/contract-validator-same-tree.md`
