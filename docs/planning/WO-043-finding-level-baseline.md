# WO-043: Finding-Level Baseline Model

## Status

`Complete`

## Phase

Phase 7: Informed Onboarding & User Comprehension

## Objective

Replace the count-based baseline model (`"critical": 10`) with a finding-level model where each baselined finding has a unique ID, file location, description, and user-decided disposition. This prevents new issues from hiding behind fixed old ones and enables precise tracking of what was acknowledged vs what is new.

## Scope

### In Scope
- [x] New baseline schema: per-finding entries with IDs, not aggregate counts
- [x] Each finding in baseline linked to its entry in findings-registry.json
- [x] Baseline comparison: match by finding ID + file + pattern, not by count
- [x] New finding detection: if a finding doesn't match any baselined entry, it's NEW (blocks)
- [x] Fixed finding detection: if a baselined finding no longer appears, it's FIXED (ratchet)
- [x] Swapped finding detection: if count stays same but specific findings differ, flag it
- [x] Update `convergence/baseline-check.sh` to support finding-level comparison
- [x] Backward compatibility: count-based baselines still work (graceful migration)
- [x] Baseline migration script: convert old count-based to finding-level format
- [x] Update `skills/build/SKILL.md` Step 7 to use finding-level baseline
- [x] Update `skills/checkpoint/SKILL.md` to use finding-level ratcheting

### Out of Scope
- Creating the findings (WO-042)
- User decision flow (WO-042)
- Remediation execution

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-042 | Guided codebase audit | Complete |

## Impact Analysis

- **Files modified:** `convergence/baseline-check.sh` (finding-level support with new CLI interface), `skills/build/SKILL.md` (Step 7 — finding-level check), `skills/checkpoint/SKILL.md` (finding-level ratcheting — runs in parallel with existing phase-level count-based ratchet; phase baselines retain aggregate counts, finding-level provides precision)
- **Files created:** `convergence/migrate-baseline.sh` (converts count-based baselines to finding-level format)
- **Systems affected:** Baseline system, gate evaluation, checkpoint ratcheting
- **Note:** SHA-256 fingerprinting uses `shasum -a 256` (available on macOS by default) with jq for JSON processing — no new dependencies required beyond what gate-runner.sh already uses.

## Acceptance Criteria

- [x] AC-1: Baseline stores individual findings with IDs, not just counts
- [x] AC-2: New finding (not in baseline) correctly detected and blocks
- [x] AC-3: Pre-existing finding (in baseline) correctly tracked and doesn't block
- [x] AC-4: Fixed finding (was in baseline, now gone) triggers ratchet (removed from baseline)
- [x] AC-5: Swapped finding (old fixed, new introduced, count unchanged) correctly detected as NEW
- [x] AC-6: Count-based baselines still work (backward compatibility)
- [x] AC-7: Migration script converts count-based to finding-level format
- [x] AC-8: Build skill uses finding-level comparison in gate evaluation
- [x] AC-9: Checkpoint skill uses finding-level ratcheting

## Test Strategy

- **Unit:** Test finding-level comparison logic (match, new, fixed, swapped scenarios)
- **Migration:** Test conversion of count-based baseline to finding-level
- **Integration:** Run gates with finding-level baseline, verify correct blocking/tracking
- **Swap detection:** Fix one issue, introduce another, verify system detects the swap

## Implementation Plan

### Step 1: Define Finding-Level Baseline Schema
```json
{
  "type": "midstream",
  "version": "2.0",
  "date": "ISO-8601",
  "source_files": 150,
  "findings": [
    {
      "id": "SEC-001",
      "category": "security",
      "severity": "critical",
      "fingerprint": "sha256-of-file+line+pattern",
      "file": "src/config.py",
      "line": 42,
      "pattern": "hardcoded-secret",
      "description": "AWS API key hardcoded",
      "disposition": "fix-now",
      "baselined_at": "ISO-8601",
      "status": "open"
    }
  ],
  "summary": {
    "critical": 3, "high": 8, "medium": 15, "low": 22,
    "fix_now": 5, "fix_later": 12, "accepted_risk": 9, "total": 48
  }
}
```

### Step 2: Update baseline-check.sh
Add finding-level mode with new CLI interface:

**Count-based mode (existing, version 1.0):**
```bash
baseline-check.sh check --baseline-file <path> --category <name> --current-count <N>
baseline-check.sh ratchet --baseline-file <path> --category <name> --current-count <N>
```

**Finding-level mode (new, version 2.0):**
```bash
baseline-check.sh check --mode finding-level --baseline-file <path> --current-findings-file <path>
baseline-check.sh ratchet --mode finding-level --baseline-file <path> --current-findings-file <path>
```

The `--current-findings-file` is a JSON file with the same schema as findings-registry.json (WO-042 schema contract). Mode detection:
- If `--mode finding-level` is passed, use finding-level comparison
- If `--mode` is omitted, detect from baseline version field (1.0 = count-based, 2.0 = finding-level)
- `check`: NEW (not in baseline) → FAIL with specific finding details, IN_BASELINE → TRACKED, NO_FINDINGS → PASS
- `ratchet`: Remove findings from baseline that no longer appear in current scan
- Preserve backward compatibility for version 1.0

### Step 3: Implement Fingerprinting
Finding fingerprint = SHA-256 of `category + file + pattern + severity` using `shasum -a 256` (macOS built-in, no external dependencies):
```bash
echo -n "${category}:${file}:${pattern}:${severity}" | shasum -a 256 | cut -d' ' -f1
```
Fingerprints are **pre-computed and stored** in the baseline file (as shown in Step 1 schema `fingerprint` field). At comparison time, compute fingerprints for current findings and match against stored fingerprints. This avoids recomputing on every check.
- Tolerates line number changes (file refactoring)
- Catches same-pattern-different-file as new finding
- Catches same-file-different-pattern as new finding

### Step 4: Implement Swap Detection
After gate/audit run:
1. Match current findings against baseline by fingerprint
2. Unmatched current findings = NEW (potential new issues)
3. Unmatched baseline findings = FIXED (improvements)
4. If NEW > 0: report specifically which findings are new, even if total count unchanged

### Step 4b: Update findings-registry.json
When a finding is first baselined, update the corresponding entry in `.vibeos/findings-registry.json` to set `baselined_at_wo` (the WO number at time of baselining). This cross-file update is required by WO-042's schema contract and consumed by WO-044 for aging reminders.

### Step 5: Migration Script
`convergence/migrate-baseline.sh`:
- Read old count-based baseline
- Convert to finding-level format with generic entries
- Preserve original counts in summary
- Mark all entries as `disposition: "pre-existing-unmigrated"` (user needs to review)

### Step 6: Update Skills
- `skills/build/SKILL.md` Step 7: use finding-level check (`--mode finding-level`), report specific new findings by ID and file
- `skills/checkpoint/SKILL.md`: add finding-level ratchet alongside existing phase-level count-based ratchet. Phase baselines (`phase-[N]-baseline.json`) retain aggregate counts for backward compatibility. Finding-level baselines (from findings-registry.json) provide precision tracking. The checkpoint runs both: count-based ratchet ensures aggregate quality only improves, finding-level ratchet ensures specific findings are tracked and swaps are detected.

## Audit Checkpoints

### Planning Audit
- Status: `complete`
- Test status: Unit tests for all comparison scenarios
- Risk: Fingerprinting must be stable across minor code changes; too sensitive = false positives, too loose = missed swaps

## Evidence

- [x] Finding-level comparison works
- [x] New findings correctly detected
- [x] Fixed findings correctly ratcheted
- [x] Swapped findings detected (count unchanged but findings differ)
- [x] Backward compatibility with count-based baselines
- [x] Migration script works
