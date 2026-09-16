# Claude release audit resolution

The original review examined immutable 2.3.0, not this patch. Its verdict was
PASS_WITH_LIMITS, with handoff held for INST-01. Findings are retained below so
corrections and accepted operating limits remain distinguishable.

| Finding | Resolution in 2.3.1 |
|---|---|
| INST-01 P1 | Profile-aware optional commit-message hook, copied validator, unrelated-hook preservation; default real-commit and explicit enforcement regressions. |
| CE-01 P2 | Graceful signal forwarding and bounded process-group cleanup; nested process timeout/interruption regressions. |
| BOOT-01 P2 | Profile install-lock guard in both legacy entrypoints, all mutation modes; unchanged-target regression. |
| GATE-01 P2 | Detected validators moved out of executable gate rows into explicitly informational metadata. |
| GATE-02 P2 | Primary checks removed from claimed blocking active gates; docs require project-owned executable manifest configuration. |
| GATE-03 P2 | Missing required tools return nonzero SKIP; Python complexity uses installed radon or Ruff C901 and fails malformed results. |
| INST-02 P3 | Intentional customization drift remains detected; error and guide explain reanalysis. |
| INST-03 P3 | Skipped post-checks exit nonzero and document reanalysis; no success claim. |
| INST-04 P3 | Remaining limit: persistent lock and possible interruption residue; inspection and preservation required. |
| INST-05 P3 | Remaining limit: mode downgrades do not prune retired surfaces automatically. |
| INST-06 P3 | Python prerequisite is checked before installer import. |
| INST-07 P3 | Generated project-owner language; neutralized machine-specific examples in the two reported planning documents. |
| CE-02 P3 | One total execution deadline; bounded cleanup grace is separate. |
| CE-03 P3 | Strict stdout/stderr, source admission, line budget and isolated pytest requirements documented. |

The primary team executed regressions and native proofs. Claude's independent
review is static and must not be described as executing those tests.

## Measured cleanup boundary

Native macOS Codex proof exercised a three-second total execution deadline with
an adapter and grandchild both ignoring SIGTERM. Both recorded processes stopped,
no admitted result appeared, and candidate bytes remained unchanged. The measured
run finished in 3.60 seconds including cleanup. Normal completion with a child
that closes inherited pipes and timeout with an early-exiting parent are also
covered by real subprocess regressions.

The initial integrated run found a stub-detector false positive in a helper's
`except ProcessLookupError: pass`. The helper now returns false for an absent
group and true for a delivered signal. Callers ignore the return; cleanup behavior
is unchanged. This small correction followed the frozen Claude delta snapshot
and passed the stub gate and all five process regressions. The snapshot and final
source hashes are retained separately.

## Targeted Claude re-review

`claude-fable-5-1` returned PASS_WITH_LIMITS and explicitly closed all six material
findings. It reviewed the frozen correction snapshot statically; runtime evidence
was measured separately. Its new P3 concerning nested quotes in a Python parse-
error message was corrected by computing the relative path before formatting.
The actual macOS Python 3.9.6 compatibility probe and seven gate regressions passed.
This does not lower the installer's Python 3.12 requirement.

The review's remaining native-interruption evidence gap was then closed by a real
Codex sandbox proof: send SIGTERM directly to the evaluator after both child PIDs
exist, with a 30-second configured deadline. The record says interrupted=true,
timed_out=false and reaped=true. Both child PIDs were absent; candidate bytes were
unchanged and no result was admitted. The earlier deadline proof also passed.

Ruff's reusable complexity fallback honors project configuration; owners must
review exclusions and C901 ignores when defining their gate. Explicit separate-
session escapes and the narrow signal-during-spawn race remain outside a claim
of hostile same-user isolation. TypeScript projects need a usable compiler
configuration; its absence fails instead of receiving an implicit pass.

Final canonical pre-commit: nine PASS, zero FAIL, one nonblocking dependency SKIP,
including a passing full pytest gate. The small parse-format compatibility fix
followed that integrated run and passed the targeted gate tests and native older-
interpreter probe. No broad audit or suite was repeated for that isolated fix.
