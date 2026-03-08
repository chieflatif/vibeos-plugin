# WO-053: Validation & Safety Hardening

## Status

`Complete`

## Phase

Phase 8: Resilience & Transparency

## Objective

Close remaining validation gaps: verify git repo exists before running convergence scripts, log test file protection events for transparency, and define the precise merge algorithm for midstream PRD collisions so re-running discover doesn't lose user edits.

## Scope

### In Scope
- [x] Add git repo validation to prereq-check.sh: check if current directory is a git repo
- [x] If not a git repo: warn user that convergence features (state hashing, baselines) require git
- [x] Add git repo check to build skill prerequisites
- [x] Test file protection logging: when hook blocks an agent, log incident to `.vibeos/build-log.md`
- [x] Test file protection fail-open alert: when agent identity is missing, log warning
- [x] Test file protection metrics in WO completion summary: "TDD enforcement: [N] modification attempts blocked"
- [x] Define PRD merge algorithm for midstream re-discovery
- [x] PRD merge: section-level merge — user-authored sections preserved, inferred sections updated
- [x] PRD merge: metadata tagging — each section tagged with `source: user|inferred` and `last_updated`
- [x] PRD merge: conflict resolution — if both user and inference touch same section, keep user version with note

### Out of Scope
- Creating new hooks (only enhancing existing ones)
- Changing test file protection enforcement model (fail-open remains for user direct editing)
- Changing git requirements (just adding detection and warning)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Phase 7 | All Phase 7 WOs | Complete |

## Impact Analysis

- **Files modified:** `hooks/scripts/prereq-check.sh` (git repo check), `hooks/scripts/test-file-protection.sh` (logging), `skills/build/SKILL.md` (git check in prerequisites, TDD metrics in WO summary), `skills/discover/SKILL.md` (PRD merge algorithm in Step M3c)
- **Files created:** None
- **Systems affected:** Prerequisites validation, test file protection, midstream discovery

## Acceptance Criteria

- [x] AC-1: prereq-check.sh detects if current directory is a git repo and warns if not
- [x] AC-2: Build skill prerequisites check includes git repo validation
- [x] AC-3: Test file protection hook logs block events to build-log.md
- [x] AC-4: Test file protection hook logs warning when agent identity missing (fail-open triggered)
- [x] AC-5: WO completion summary includes TDD enforcement metric
- [x] AC-6: PRD merge algorithm defined with section-level granularity
- [x] AC-7: User-authored PRD sections preserved during re-discovery
- [x] AC-8: Inferred PRD sections updated with new analysis results
- [x] AC-9: PRD sections tagged with source metadata (user vs inferred)

## Test Strategy

- **Git check:** Run prereq-check.sh in git repo (pass) and non-git directory (warn)
- **Test protection logging:** Trigger a block event, verify build-log.md entry
- **Fail-open alert:** Remove current-agent.txt, trigger hook, verify warning logged
- **PRD merge:** Run discover twice on same midstream project, verify user edits preserved

## Implementation Plan

### Step 1: Add Git Repo Check to prereq-check.sh
After existing tool checks, add:
```bash
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  # Add warning to system message
  WARNINGS="${WARNINGS}Git repository not detected. "
  WARNINGS="${WARNINGS}Convergence features (state tracking, baselines) require git. "
  WARNINGS="${WARNINGS}Run 'git init' to initialize. "
fi
```

### Step 2: Add Git Check to Build Skill Prerequisites
In build skill prerequisites section, add:
- Check: current directory is a git repo
- If not: warn user that state tracking and baselines won't work
- Suggest: "Initialize git with `git init` before building. This enables quality tracking across work orders."
- Non-blocking: build can proceed but with degraded convergence features

### Step 3: Add Logging to Test File Protection Hook
In `hooks/scripts/test-file-protection.sh`:
- When blocking an agent: append to `.vibeos/build-log.md`:
  ```
  | [timestamp] | test-file-protection | BLOCKED: [agent] attempted to modify [file] | TDD enforced |
  ```
- When fail-open triggered (missing identity): append warning:
  ```
  | [timestamp] | test-file-protection | WARNING: Agent identity unknown, allowing write to [file] | Fail-open |
  ```
- Track block count in a simple counter for WO summary

### Step 4: Add TDD Metrics to WO Summary
In build skill Step 10 (WO completion), add to summary:
> "TDD enforcement: [N] test file modification attempts blocked during this WO"
Read count from build-log.md entries for this WO.

### Step 5: Define PRD Merge Algorithm
In discover skill Step M3c, specify the merge strategy:

**Section identification:**
- Each major section (## heading) is a merge unit
- Sections tagged with HTML comment metadata: `<!-- source: user|inferred, updated: ISO-8601 -->`

**Merge rules:**
1. If section exists in old PRD with `source: user` → KEEP user version
2. If section exists in old PRD with `source: inferred` → REPLACE with new inference
3. If section is new (not in old PRD) → ADD with `source: inferred`
4. If section exists in old PRD but not in new analysis → KEEP (user may have added it)

**Conflict handling:**
- If both user-edited and new inference differ: keep user version, add note:
  > "<!-- Note: VibeOS inferred updated content for this section but preserved your edits. Run `/vibeos:discover --refresh` to see the new inference. -->"

### Step 6: Implement PRD Metadata Tagging
When discover skill generates PRD.md (Step M3/Step 5):
- Tag each section with source metadata
- On re-run: read existing PRD, identify tagged sections, apply merge rules

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Test status: Validate all three areas independently
- Risk: PRD merge adds complexity to discover skill; keep merge logic simple and well-documented

## Evidence

- [x] Git repo check warns when not in git repo
- [x] Build skill checks git status
- [x] Test file protection logs block events
- [x] Fail-open scenarios logged with warning
- [x] TDD metrics in WO completion summary
- [x] PRD merge preserves user edits
- [x] PRD sections tagged with source metadata
