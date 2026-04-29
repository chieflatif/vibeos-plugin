# WO-099: Autonomy Scheduler Profiles

## Status

`Complete`

## Phase

Phase 26: Autonomy Scheduler Profiles

## Objective

Generate reviewed shell, cron, launchd, and GitHub Actions scheduler profiles for long-run VibeOS autonomy without installing system or CI scheduler jobs automatically.

## Scope

### In Scope
- [x] Add `autonomy-scheduler-profile.py`
- [x] Generate `.vibeos/autonomy/scheduler-profile.json`
- [x] Generate shell, cron, launchd, and GitHub Actions profile files
- [x] Keep runtime launching disabled by default
- [x] Add scheduler profile reference guidance
- [x] Install profile generator through bootstrap and upgrade surfaces

### Out of Scope
- Installing cron jobs
- Loading launchd plists
- Creating GitHub Actions workflows directly in `.github/workflows/`
- Launching Codex or Claude by default

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-097 | Long-Run Loop Entrypoint | Complete |
| WO-098 | Runtime Handoff Adapter | Complete |

## Findings

1. The harness has a scheduler-safe tick, but external schedulers still need reviewed profile files with the right commands.
2. Scheduler profile generation must not silently install background jobs.
3. Runtime launch mode needs to be explicit because Codex/Claude invocations can spend tokens, edit files, and run tools.

## Acceptance Criteria

- [x] AC-1: Profile generator writes scheduler artifacts under `.vibeos/autonomy/scheduler/`
- [x] AC-2: Profile generator writes `.vibeos/autonomy/scheduler-profile.json`
- [x] AC-3: Generated profiles include `autonomy-loop.py`
- [x] AC-4: Generated profiles include `autonomy-runtime-adapter.py`
- [x] AC-5: Runtime adapter `--execute` appears only when `--launch-runtime` is requested

## Evidence

- [x] `plugins/vibeos/scripts/autonomy-scheduler-profile.py`
- [x] `plugins/vibeos/reference/autonomy/SCHEDULER-PROFILES.md.ref`
- [x] `tests/test_long_run_autonomy.py`
- [x] Full repository validation run
