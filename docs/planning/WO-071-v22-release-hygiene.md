# WO-071: v2.2 Release Hygiene

## Status

`Complete`

## Phase

Phase 13: Evidence Memory Research

## Objective

Align README, install metadata, manifests, bootstrap output, and framework version constants with the v2.2 evidence recall release.

## Scope

### In Scope
- [x] Bump live framework metadata to `2.2.0`
- [x] Update README and presentation collateral with the evidence recall release note and install inventory
- [x] Add evidence recall to the quality-gate utility manifest
- [x] Update bootstrap-generated version metadata and script counts
- [x] Update marketplace/plugin metadata
- [x] Add generated evidence recall cache to project gitignore setup

### Out of Scope
- Rewriting historical Work Order evidence that correctly refers to older releases
- Adding new runtime behavior beyond WO-070
- Publishing package artifacts outside git push

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-070 | Evidence recall implementation | Complete |

## Findings

1. WO-070 added a runtime utility but README, plugin metadata, bootstrap output, and manifest utility listings still described the older framework surface.
2. The generated `.vibeos/cache/evidence-recall-index.json` should be treated as derived state and ignored by bootstrapped projects.
3. Historical planning docs should keep their original version references because those are evidence, not live metadata.

## Anchor Alignment

This keeps the installed framework truthful: users see the actual version and installed capability surface before upgrading or bootstrapping.

## Research & Freshness

- Current evidence required: local repository metadata and script inventory.
- Last verified on: 2026-04-24.
- Sources to verify: README, plugin manifest, marketplace manifest, bootstrap scripts, runtime manifests.
- Prompt engineering profile: N/A — release metadata only.

## Approved Deviations

None.

## Impact Analysis

- **Files created:** this WO
- **Files modified:** README, presentation collateral, bootstrap scripts, plugin/marketplace metadata, runtime manifests, file inventory, planning index and plan
- **Systems affected:** release/version reporting and install documentation only

## Acceptance Criteria

- [x] AC-1: Live plugin metadata reports `2.2.0`
- [x] AC-2: Bootstrap scripts write `2.2.0`
- [x] AC-3: README includes the v2.2 evidence recall release note
- [x] AC-4: Install inventory lists the current script count and generated recall cache
- [x] AC-5: Quality-gate manifest lists `scripts/evidence-recall.py` as a utility script
- [x] AC-6: Bootstrapped `.gitignore` includes `.vibeos/cache/`

## Test Strategy

- **Syntax tests:** `bash -n vibeos-init.sh vibeos-init-codex.sh plugins/vibeos/scripts/plugin-upgrade.sh`
- **JSON tests:** parse plugin, marketplace, hook, and quality manifest JSON
- **Version scan:** verify live metadata surfaces contain `2.2.0` and older version references are limited to historical release notes or migration guards
- **Verification command:** `rg -n "2\\.2\\.0" README.md vibeos-init.sh vibeos-init-codex.sh plugins/vibeos .claude-plugin`

## Implementation Plan

### Step 1: Update Version Surfaces
- Bump live runtime constants and manifests to `2.2.0`
- Expected outcome: bootstrap and metadata agree on the current release

### Step 2: Update User-Facing Docs
- Add README release note and inventory updates
- Expected outcome: users understand evidence recall and generated cache behavior

### Step 3: Verify
- Run syntax, JSON, unit, and diff hygiene checks
- Expected outcome: release hygiene is complete and commit-ready

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Findings: Release metadata must be updated before commit/push so WO-070 is not shipped as an invisible capability.
- Test status: Targeted checks defined.

### Pre-Implementation Audit
- Status: `complete`
- Findings: Restrict edits to live version surfaces and user-facing release docs; preserve historical evidence.
- Test status: Syntax and JSON checks selected.

### Pre-Commit Audit
- Status: `complete`
- Findings: Live metadata and install docs now align with v2.2. Historical older-version references remain where they document earlier WOs/releases.
- Test status: Syntax, JSON, unit, real-path query, and diff hygiene checks passed.

## Evidence

- [x] Implementation complete
- [x] Tests pass
- [x] Metadata updated
- [x] Documentation updated
- [x] No runtime dependency introduced

Verification commands run:
- `bash -n vibeos-init.sh vibeos-init-codex.sh plugins/vibeos/scripts/plugin-upgrade.sh`
- `python3 -m py_compile plugins/vibeos/scripts/evidence-recall.py plugins/vibeos/scripts/audit_aggregate.py tests/test_evidence_recall.py`
- `for f in plugins/vibeos/.claude-plugin/plugin.json .claude-plugin/marketplace.json plugins/vibeos/hook-manifest.json plugins/vibeos/quality-gate-manifest.json plugins/vibeos/reference/manifests/quality-gate-manifest.json.ref plugins/vibeos/reference/claude/settings.json.ref; do python3 -m json.tool "$f" >/dev/null; done`
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests`
- `PYTHONDONTWRITEBYTECODE=1 python3 plugins/vibeos/scripts/evidence-recall.py query "evidence memory token" --repo . --fresh --limit 3`
- `git diff --check`
