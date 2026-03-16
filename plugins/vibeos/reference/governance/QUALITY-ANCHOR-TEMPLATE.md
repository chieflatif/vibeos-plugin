# Quality Anchor — {{PROJECT_NAME}}

**Status:** Draft (human review required before freezing)
**Version:** 1.0
**Last reviewed:** {{DATE}}

This document defines what "quality" means for this project. It is the immutable standard that agents cannot modify. Changes require explicit human approval.

---

## 1. What "Complete" Actually Means

A work order is only `Complete` when ALL of these are true:

- [ ] The intended behavior works through its real execution path (route, handler, job, CLI, webhook, scheduler)
- [ ] Tests verify the behavior, not just that code exists
- [ ] The real path has been exercised — not just unit tests against mocks
- [ ] Evidence exists proving the verification (logs, screenshots, test output, curl responses)
- [ ] The repo is in a clean, resumable state

**Ground truth test:** Could a new developer clone this repo, follow the setup instructions, and see the feature working within 10 minutes? If no, the WO is not Complete.

### Completion Checklist

| Question | Required Answer |
|---|---|
| Does the feature work when you actually use it? | Yes |
| Do tests verify real behavior, not mock behavior? | Yes |
| Is there evidence beyond "tests pass"? | Yes |
| Could someone else verify this independently? | Yes |
| Is the status in WO-INDEX accurate? | Yes |

---

## 2. Verification Integrity

### Independent Verification
- Audit agents must run on current code, not stale worktrees
- Findings must include commit SHA for traceability
- Stale findings (from worktrees >1 commit behind HEAD) must be discarded

### Grounded Evidence
- "Tests pass" alone is not evidence of correctness
- Evidence must be anchored to observable reality (HTTP responses, database state, UI behavior)
- Self-referencing evidence loops (tests validate code, gates validate tests, audits validate gates) must be broken with ground truth checkpoints

### Worktree Integrity
- Audit agents verify worktree freshness before producing findings
- Build orchestrator discards findings from stale worktrees
- Commit SHA is tagged on every finding

---

## 3. Forbidden Testing Patterns

These patterns MUST NOT appear in test code. Their presence blocks WO completion.

| Pattern | Description | Why It's Forbidden |
|---|---|---|
| Silent pass guard | `if (element) { expect(...) }` with no else/fail | Test passes with zero assertions when condition is false |
| Vacuous assertion | `expect(true).toBe(true)` or `assert True` | Proves nothing about the code |
| Mock-only integration | API mocks without any contract validation test | Mock shape may not match real API |
| Fallback masking | Test passes via default/error path instead of intended path | Hides broken primary behavior |
| Verify-after-delete fallback | `id = response.id or "fallback-id"` in delete verification | Uses literal string instead of actual ID |
| Status inflation | Marking WO "Complete" when only mocks pass | Misleading status erodes trust |

---

## 4. Agent Alignment Rules

All agents (tester, backend, frontend, auditors) must:

1. **Optimize for correctness, not completion** — A WO stuck at "Awaiting Real-Path Verification" is better than a falsely-marked "Complete"
2. **Escalate uncertainty** — When unsure whether something works, say so instead of assuming success
3. **Cannot lower the quality bar** — No agent may modify this Quality Anchor, skip a blocking gate, or suppress findings without human approval
4. **Must challenge own claims** — Before marking a WO Complete, review whether the evidence would satisfy a skeptical external reviewer

---

## 5. Anti-Corruption Detection

The following automated checks exist to detect quality system corruption:

| Check | Trigger | Action |
|---|---|---|
| Red team audit | Phase boundary, on-demand | Adversarial review of test quality and status integrity |
| Contract drift detection | WO exit (cross-boundary WOs) | Frontend-backend contract comparison |
| Status integrity gate | WO exit | Cross-check claimed status against evidence |
| Baseline expiry | Phase boundary | Expire baseline entries older than 2 phases |
| Worktree freshness | Every audit dispatch | Verify worktree is within 1 commit of HEAD |

---

## 6. Escalation Triggers

These conditions require immediate human attention:

- Corruption score increases between phases
- Any cross-boundary contract mismatch (frontend 404s against backend)
- 2+ audit agents disagree on the same finding
- Real-path verification fails after WO was marked Complete
- False positive rate exceeds 30% of total findings
- A baseline entry has been suppressing findings for 3+ phases

---

## 7. The Human's Quality Vision

_This section is project-specific. Fill in during discovery based on user interview._

**What does "done well" mean for this project?**

{{QUALITY_VISION}}

**What shortcuts are never acceptable?**

{{UNACCEPTABLE_SHORTCUTS}}

**What would make you lose trust in the build system?**

{{TRUST_BREAKERS}}

**What's more important: shipping fast or shipping correctly?**

{{SPEED_VS_CORRECTNESS}}
