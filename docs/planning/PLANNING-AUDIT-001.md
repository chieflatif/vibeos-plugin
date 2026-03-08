# Planning Audit #001 — Development Plan Review

**Date:** 2026-03-07
**Auditor:** Fresh-context agent (isolated worktree, no prior project context)
**Scope:** Full development plan (40 WOs, 6 phases), plugin manifest, CLAUDE.md
**Checkpoint:** Planning

## Summary

| Severity | Count |
|----------|-------|
| P0 (Blocking) | 3 |
| P1 (High) | 5 |
| P2 (Medium) | 7 |
| P3 (Low) | 3 |
| **Total** | **18** |

## Findings & Resolutions

### P0 — Blocking

| # | Finding | Resolution | Status |
|---|---|---|---|
| F-01 | Plugin manifest schema (`agents`, `hooks` fields) unverified — may not be valid in Claude Code | **Add WO-000: Technical Spike** — create minimal plugin, test `claude plugin install`, document actual schema | Resolved: WO-000 added |
| F-02 | Skills vs Commands confusion — slash-invoked workflows should be `commands/`, not `skills/` | **Defer to WO-000 spike** — verify whether Claude Code uses `skills/` or `commands/` for explicit invocation. Rename all directories and references based on spike findings | Resolved: WO-000 covers this |
| F-03 | Subagent dispatch/return mechanism unverified — no evidence it works as assumed | **Include in WO-000 spike** — dispatch trivial agent, verify structured return, document mechanism | Resolved: WO-000 covers this |

### P1 — High

| # | Finding | Resolution | Status |
|---|---|---|---|
| F-04 | Script count mismatch — plan says 21 but source has 23+ | **Update WO-002** — inventory actual scripts during implementation, update all references | Accepted: fix during WO-002 |
| F-05 | `/vibeos:checkpoint` skill listed in plugin.json but not created until Phase 5 | **Fix plugin.json** — build manifest incrementally, only reference components that exist | Resolved: plugin.json updated |
| F-06 | Plugin.json references 12 agents and 8 skills that don't exist yet | **Fix plugin.json** — same as F-05, evolve manifest per-WO | Resolved: plugin.json updated |
| F-07 | Hook exit code semantics (0=allow, 2=block) unverified | **Include in WO-000 spike** — verify actual exit code contract | Resolved: WO-000 covers this |
| F-08 | No rollback/contingency plan if Phase 1 post-audit fails | **Add contingency section to DEVELOPMENT-PLAN.md** | Resolved: contingency added |

### P2 — Medium

| # | Finding | Resolution | Status |
|---|---|---|---|
| F-09 | Hook .ref files more complex than WO-006 assumes (8 files, only 4 addressed) | **Document in WO-006** — inventory all 8 .ref files, map to WOs | Accepted: inventory during WO-006 |
| F-10 | Phase 1 test strategy is entirely manual, no automated tests | **Add test runner script to WO-001** — bash test runner for static validation. Move WO-007a earlier | Resolved: WO-001 updated, WO-007a resequenced |
| F-11 | Dependency chains overly serial — limited parallelization | **Update dependency graph** — WO-024-027 parallel, WO-016/017 parallel | Resolved: dependencies updated |
| F-12 | Consensus logic (2+ agents = true positive) is naive | **Document consensus model in WO-028** — define overlap zones, single-auditor sufficiency | Accepted: document during WO-028 |
| F-13 | DEVELOPMENT-PLAN.md has hardcoded local paths | **Accepted risk** — these are development-time references, removed in production | Accepted |
| F-14 | No versioning/compatibility strategy | **Accepted** — defer to Phase 6 design, add note to WO-039 | Accepted |
| F-15 | Token/cost tracking deferred to Phase 5, risky from Phase 3 | **Add basic dispatch counting to WO-019** | Resolved: added to WO-019 scope |

### P3 — Low

| # | Finding | Resolution | Status |
|---|---|---|---|
| F-16 | WO-007a has Phase 4 acceptance criteria that can't be verified in Phase 1 | **Split ACs** — mark AC-5, AC-6 as deferred to Phase 4 | Resolved |
| F-17 | WO template format not validated by any gate | **Defer** — add template validation gate in later phase | Accepted |
| F-18 | No error budget or acceptable failure rate defined | **Add thresholds to WO-030** | Accepted: added to convergence scope |

## TDD Assessment

The test strategy for Phase 1 is inadequate by the plan's own standards. Resolution:
1. Add `tests/` directory and bash test runner to WO-001
2. Define test categories: static validation (automatable), integration (semi-automatable), runtime (requires Claude Code)
3. Move WO-007a (test fixture) to right after WO-001 in sequence

## Recommendation

**Complete WO-000 (Technical Spike) before approving the plan for implementation.** The spike validates:
1. Plugin manifest schema — what fields does `claude plugin install` actually accept?
2. Skills vs Commands — which directory convention is used for slash invocation?
3. Agent dispatch — can a skill/command dispatch an agent and receive structured output?
4. Hook exit codes — what code blocks an operation?

Once spike results are documented, re-audit against revised plan.

## Audit Status: Complete (with conditions)

Plan is not approved for implementation until WO-000 spike resolves the 3 P0 findings.
