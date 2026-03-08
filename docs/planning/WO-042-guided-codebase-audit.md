# WO-042: Guided Codebase Audit with User Decisions

## Status

`Draft`

## Phase

Phase 7: Informed Onboarding & User Comprehension

## Objective

Replace the blind baseline-everything approach with a guided category-by-category audit walkthrough. The user reviews findings by domain (security, architecture, code quality, dependencies, test coverage), understands each finding in plain English with its implications, and decides the disposition: fix now, fix later, or accept risk.

## Scope

### In Scope
- [ ] Run full audit suite after architecture document is validated (WO-041)
- [ ] Present findings category by category, not as aggregate counts
- [ ] Security findings walkthrough: each critical/high explained with risk and recommendation
- [ ] Architecture findings walkthrough: violations explained with impact on maintainability
- [ ] Code quality findings walkthrough: complexity, dead code, missing error handling
- [ ] Dependency audit: run language-specific tools (npm audit, pip-audit, etc.) for CVE detection
- [ ] Test coverage assessment: what's tested, what's not, what's the gap
- [ ] Per-finding user decision: `fix-now`, `fix-later`, `accepted-risk`
- [ ] `accepted-risk` requires brief justification from user (stored with finding)
- [ ] `fix-later` creates a tracked remediation item with priority
- [ ] `fix-now` items feed into Phase 0 remediation WOs
- [ ] Generate human-readable audit report: `.vibeos/midstream-report.md`
- [ ] Update `skills/plan/SKILL.md` Step 1b to use guided audit flow

### Out of Scope
- Fixing the findings (handled by remediation WOs)
- Baseline creation (WO-043 — happens after user decisions)
- Automated remediation

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-041 | Architecture-first discovery | Draft |

## Impact Analysis

- **Files modified:** `skills/plan/SKILL.md` (replace blanket baseline with guided audit)
- **Files created:** `.vibeos/midstream-report.md` (in target project), `.vibeos/findings-registry.json` (in target project)
- **Systems affected:** Plan skill, audit pipeline, remediation WO creation

## Acceptance Criteria

- [ ] AC-1: Full audit runs after architecture validation (5 agents + gates)
- [ ] AC-2: Findings presented category by category with plain English explanations
- [ ] AC-3: Each critical and high finding individually presented with risk context
- [ ] AC-4: User decides disposition per finding: fix-now, fix-later, accepted-risk
- [ ] AC-5: accepted-risk requires justification text from user
- [ ] AC-6: Dependency audit runs language-specific CVE tools
- [ ] AC-7: Test coverage gap identified and presented
- [ ] AC-8: Medium/low findings summarized by category (not individually walked through)
- [ ] AC-9: Human-readable report generated at `.vibeos/midstream-report.md`
- [ ] AC-10: Structured findings registry at `.vibeos/findings-registry.json` with per-finding dispositions

## Test Strategy

- **Integration:** Run guided audit on project with known issues, verify each category walkthrough
- **Decision loop:** Verify user can set different dispositions per finding
- **Report:** Verify report is human-readable and complete
- **Dependency audit:** Verify CVE detection for npm/pip/go projects

## Implementation Plan

### Step 1: Run Comprehensive Audit
After architecture validation (WO-041):
1. Run all gates via `gate-runner.sh pre_commit`
2. Dispatch all 5 audit agents
3. Run language-specific dependency audit:
   - Node.js: `npm audit --json` or `npx audit-ci`
   - Python: `pip-audit --format json` or `safety check`
   - Go: `govulncheck ./...`
   - Rust: `cargo audit`
   - Java: dependency-check or OWASP plugin
4. Assess test coverage (count test files, map to source files, identify gaps)

### Step 2: Categorize and Prioritize Findings
Organize all findings into categories:
1. **Security** — secrets, injection, auth gaps, CVEs in dependencies
2. **Architecture** — layer violations, circular deps, boundary violations
3. **Code Quality** — complexity, dead code, error handling gaps, type safety
4. **Dependencies** — outdated packages, known CVEs, unpinned versions
5. **Test Coverage** — untested modules, low coverage areas, missing edge cases

Within each category, sort by severity (critical → high → medium → low).

### Step 3: Guided Walkthrough
Present each category to the user:

> **Security Audit Results**
>
> I found [N] security-related issues in your codebase:
>
> **Critical (must address):**
> 1. **Hardcoded API key** in `src/config.py:42`
>    - Risk: Anyone with access to your code can use this key to access [service]
>    - Recommendation: Move to environment variable
>    - What do you want to do? [fix now / fix later / accept risk]
>
> 2. **SQL injection vulnerability** in `src/db/queries.py:118`
>    - Risk: An attacker could read or modify your entire database
>    - Recommendation: Use parameterized queries
>    - What do you want to do? [fix now / fix later / accept risk]
>
> **High:**
> 3. **Missing CSRF protection** on 4 POST endpoints
>    - Risk: ...
>
> **Medium (summarized):**
> - 5 instances of overly permissive CORS configuration
> - 3 instances of debug mode enabled in config files
> These are tracked but won't block your development.

For `accepted-risk`, ask for justification:
> "You chose to accept the risk of [finding]. Can you briefly explain why? This will be documented for audit trail purposes."

### Step 4: Store Decisions
Write `.vibeos/findings-registry.json`:
```json
{
  "audit_date": "ISO-8601",
  "architecture_doc": "docs/product/ARCHITECTURE-OUTLINE.md",
  "findings": [
    {
      "id": "SEC-001",
      "category": "security",
      "severity": "critical",
      "title": "Hardcoded API key",
      "file": "src/config.py",
      "line": 42,
      "description": "AWS API key hardcoded in source",
      "recommendation": "Move to environment variable",
      "disposition": "fix-now",
      "justification": null,
      "agents": ["security-auditor", "correctness-auditor"],
      "consensus": "true-positive"
    }
  ]
}
```

### Step 5: Generate Report
Write `.vibeos/midstream-report.md`:
- Executive summary (1 paragraph plain English)
- Category-by-category findings with dispositions
- Fix-now items (will become Phase 0 WOs)
- Fix-later items (tracked, prioritized)
- Accepted risks (with justifications)
- Test coverage gap summary

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test with known-issue project
- Risk: Large codebases may have hundreds of findings; walkthrough must be efficient (batch medium/low, walk through critical/high individually)

## Evidence

- [ ] Category-by-category walkthrough works
- [ ] User decisions captured per finding
- [ ] Dependency CVE audit runs
- [ ] Report generated and readable
- [ ] Findings registry stored with dispositions
