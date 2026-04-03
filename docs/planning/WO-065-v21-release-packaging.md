# WO-065: v2.1 Release Packaging

## Status

`Complete`

## Phase

Phase 11: Advanced Governance (v2.1)

## Objective

Finalize v2.1.0 release: version bump all scripts, update CLAUDE.md with new capabilities, update README, update upgrade script, validate all JSON and scripts, run full quality gate sweep.

## Context

Phase 11 adds 20 enhancement items extracted from Joan. This WO packages everything for release: consistent version numbers, updated documentation, working upgrade path, and a clean quality gate run.

## Scope

### In Scope

1. **Version bump** — `FRAMEWORK_VERSION="2.1.0"` in all scripts
2. **CLAUDE.md updates**:
   - Architecture section: add same-tree agents, Codex audit skill, new hooks
   - File counts: update agent count, script count, hook count, skill count
   - Key constraints: add audit visibility modes, parallel worktree support
   - Technology: add Codex CLI as optional dependency
3. **README updates** — New capabilities section for v2.1
4. **Upgrade script** — `scripts/plugin-upgrade.sh`:
   - Handle 2.0.0 → 2.1.0 migration
   - Add new scripts, agents, hooks
   - Preserve user customizations in gate manifest and session state
5. **CHANGELOG** — v2.1.0 entry with all 20 enhancements listed
6. **Full validation sweep**:
   - `bash -n` on all .sh files
   - `jq .` on all .json files
   - No placeholder patterns (`{{.*}}`)
   - No stubs, TODOs, or incomplete implementations
7. **Gate manifest** — Ensure all new gates are registered
8. **Hook manifest** — Ensure all new hooks are documented
9. **vibeos-init.sh** — Update to install new files

### Out of Scope

- New features beyond what was built in WO-056-064
- Distribution mechanism changes (that's WO-055)

## Acceptance Criteria

1. All scripts have `FRAMEWORK_VERSION="2.1.0"`
2. CLAUDE.md accurately reflects new file counts and capabilities
3. README documents v2.1 enhancements
4. Upgrade script handles 2.0.0 → 2.1.0 cleanly
5. All .sh files pass `bash -n`
6. All .json files pass `jq .`
7. No `{{.*}}` placeholders anywhere
8. No stubs, TODOs, or incomplete implementations
9. Full gate sweep passes
10. vibeos-init.sh installs all new files
11. WO-INDEX.md updated with final statuses for all Phase 11 WOs

## Dependencies

- WO-056 through WO-064 — all implementation WOs must be complete

## Files Modified

- All scripts (version bump)
- `CLAUDE.md`
- `README.md`
- `plugins/vibeos/scripts/plugin-upgrade.sh`
- `vibeos-init.sh`

## Files Created

- `CHANGELOG.md` (or update if exists)
