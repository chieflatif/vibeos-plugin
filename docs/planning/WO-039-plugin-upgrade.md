# WO-039: Plugin Upgrade Mechanism

## Status

`Complete`

## Phase

Phase 6: Midstream Embedding & Production Readiness

## Objective

Implement a plugin upgrade mechanism that updates VibeOS plugin components without losing project-specific configuration, merges new gates, preserves baselines, and provides a "what's new" summary.

## Scope

### In Scope
- [x] Detect when a newer version of the plugin is available
- [x] Upgrade plugin files without overwriting project config (.vibeos/config.json, baselines)
- [x] Merge new gate scripts: add new gates, update existing gates, preserve custom gates
- [x] Preserve baselines: midstream and phase baselines are never overwritten
- [x] Preserve hook customizations
- [x] Generate "what's new" summary: new gates, updated scripts, new features
- [x] Rollback capability: snapshot current state before upgrade
- [x] Version tracking in .vibeos/version.json

### Out of Scope
- Auto-update (upgrade is user-initiated)
- Breaking changes migration (requires manual intervention)
- Plugin distribution mechanism (separate concern)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-035 | Midstream embedding | Complete |

## Impact Analysis

- **Files created:** Upgrade logic, .vibeos/version.json
- **Systems affected:** Plugin management, gate scripts, configuration

## Acceptance Criteria

- [x] AC-1: Plugin files updated to new version
- [x] AC-2: .vibeos/config.json preserved (not overwritten)
- [x] AC-3: Baseline files preserved (not overwritten)
- [x] AC-4: New gates added, existing gates updated, custom gates preserved
- [x] AC-5: "What's new" summary generated in plain English
- [x] AC-6: Pre-upgrade snapshot created for rollback
- [x] AC-7: .vibeos/version.json tracks current and previous versions

## Test Strategy

- **Integration:** Upgrade from version A to version B, verify preservation
- **Merge:** Add custom gate, upgrade, verify custom gate preserved
- **Rollback:** Upgrade, rollback, verify original state restored
- **What's new:** Verify summary accurately describes changes

## Implementation Plan

### Step 1: Implement Version Detection
- Read current version from .vibeos/version.json
- Compare against available version (from plugin source)
- Determine if upgrade is needed

### Step 2: Implement Pre-Upgrade Snapshot
- Snapshot current gate scripts, hooks, manifests
- Store in .vibeos/upgrade-backup/
- Record snapshot timestamp

### Step 3: Implement Upgrade Logic
- Copy new plugin files (gates, hooks, reference files)
- Merge strategy: new files added, existing files updated, custom files preserved
- Detect custom files: files not in plugin manifest = custom
- Update .vibeos/version.json

### Step 4: Implement "What's New" Summary
- Compare old manifest against new manifest
- List: new gates, updated gates, new features, removed items
- Present in plain English

### Step 5: Implement Rollback
- On request: restore from .vibeos/upgrade-backup/
- Revert .vibeos/version.json
- Confirm rollback complete

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Test status: Integration test — upgrade with custom config, verify preservation
- Risk: Merge logic complexity; must handle edge cases (renamed files, moved files)

## Evidence

- [x] Upgrade completes without losing config
- [x] Baselines preserved
- [x] New gates added, custom gates preserved
- [x] "What's new" summary accurate
- [x] Rollback works
- [x] Version tracking updated
