# WO-157 acceptance contract

Deliver an opt-in VibeOS module that gives Codex-authored engineering work an
independent, provider-proven Claude review without repeating the entire audit after
each correction.

The delivered release must meet these requirements:

1. Default profile installation does not install or activate the module.
2. Explicit opt-in installs the audit CLI, cross-surface guidance and a blocking
   work-order close gate.
3. A full audit uses exact first-party `claude-fable-5-1` in a restricted, tool-free,
   non-persistent session with explicit spend, turn, time and prompt-size limits.
4. The full receipt binds the frozen work order, this acceptance contract, scope
   manifest, base and candidate commits, reviewed snapshot, diff and evidence.
5. Correction verification covers every original finding ID and only the correction
   diff, immediate affected behavior and supplied evidence. A changed acceptance
   contract or expanded correction scope requires a new full audit.
6. Work-order closure fails when the enabled receipt is missing, unresolved, stale,
   drifted, or lacks exact model and provider provenance.
7. Automated tests must cover default-off installation, explicit opt-in, the full to
   targeted-verification path, provider mismatch and drift refusal.
8. The exact release candidate must receive a real first-party Claude audit, all
   material findings must be closed, repository tests and gates must pass, and the
   published source must be read back before adoption.

Operational work-order status, evidence links and completion checkboxes may change
after the audit. Those administrative updates do not change this contract.
