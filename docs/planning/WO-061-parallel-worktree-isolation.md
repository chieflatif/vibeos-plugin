# WO-061: Enhanced Parallel Worktree Isolation

## Status

`Complete`

## Phase

Phase 11: Advanced Governance (v2.1)

## Objective

Enhance the existing worktree guard hooks with Joan's improvements: worktree-scopes.json-driven exclusive path enforcement, additional blocking patterns (destructive DB ops, cross-worktree merges), and reference documentation for parallel WO execution setup.

## Context

VibeOS already has `worktree-scope-guard.sh` (83 lines) and `worktree-bash-guard.sh` (76 lines). Joan evolved these hooks significantly (114 and 121 lines respectively) with:
1. **Scopes JSON support** — `worktree-scopes.json` maps branches to exclusive paths, enabling declarative territory enforcement
2. **Additional blocking patterns** — Destructive DB ops, cross-worktree branch merges, configurable feature branch patterns
3. **Better error messages** — Clear explanations of why operations are blocked

## Joan Sources

- `/Users/latifhorst/Joan/.claude/hooks/worktree-scope-guard.sh` (114 lines vs existing 83)
- `/Users/latifhorst/Joan/.claude/hooks/worktree-bash-guard.sh` (121 lines vs existing 76)
- `/Users/latifhorst/Joan/.vibeos/worktree-scopes.json`

## Scope

### In Scope

1. **Enhance `hooks/worktree-scope-guard.sh`** — Diff Joan vs existing, merge improvements:
   - Add `.vibeos/worktree-scopes.json` support for declarative path mapping
   - Add shared paths concept
   - Improve error messages with territory ownership info

2. **Enhance `hooks/worktree-bash-guard.sh`** — Diff Joan vs existing, merge improvements:
   - Add destructive DB operation blocking (DROP, TRUNCATE, DELETE WHERE 1=1)
   - Add cross-worktree branch merge blocking
   - Generalize branch pattern from `feat/p37-*` to configurable `feat/*`

3. **Worktree scopes schema** — Document `.vibeos/worktree-scopes.json`:
   - Schema: branches → {wo_ids, exclusive_paths}
   - Shared paths list

4. **Reference documentation** — `reference/parallel-worktree-guide.md`:
   - How to set up parallel WO execution
   - How to configure worktree-scopes.json
   - Safety guarantees and limitations

### Out of Scope

- Automatic worktree creation/management (manual setup)
- Joan-specific branch naming patterns

## Acceptance Criteria

1. Enhanced scope guard supports worktree-scopes.json declarative territories
2. Enhanced scope guard allows shared paths across worktrees
3. Enhanced bash guard blocks destructive DB operations
4. Enhanced bash guard blocks cross-worktree merges
5. Both hooks retain all existing functionality (no regression)
6. Scopes JSON schema documented with examples
7. Both hooks pass `bash -n` syntax validation
8. All scripts have `FRAMEWORK_VERSION="2.1.0"`

## Dependencies

- WO-056 — session state infrastructure

## Files Modified

- `plugins/vibeos/hooks/scripts/worktree-scope-guard.sh`
- `plugins/vibeos/hooks/scripts/worktree-bash-guard.sh`

## Files Created

- `plugins/vibeos/reference/parallel-worktree-guide.md`
