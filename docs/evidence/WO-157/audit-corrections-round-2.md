# WO-157 targeted correction round 2

The first targeted verification closed 17 of 18 findings and left only `F-008`
open. It confirmed that merge-base and work-scope checks were present, but found that
the default-branch reference was still selectable through a CLI argument.

The follow-up correction makes the default branch part of committed project authority:

- `default_branch_ref` is now a required audit configuration field and installer
  default. It must name an `origin/*` remote-tracking ref; local expressions such as
  `HEAD~1` are rejected.
- The `--default-branch-ref` CLI argument has been removed, so a late command-line
  override cannot narrow the review range.
- Full receipts retain the configured ref, its exact commit, the computed merge base
  and audited base commit. Verification receipts carry that original base authority
  forward.
- Receipt validation now hashes and revalidates the committed config, resolves the
  recorded remote ref again, and recomputes the candidate merge base. Config drift,
  remote-ref drift or a merge-base mismatch invalidates closure.
- Original full-audit receipts created before these binding fields existed are upgraded
  only by deriving the ref from current committed configuration and proving that the
  recomputed merge base equals the original receipt's audited base commit.
- Tests prove that a local `HEAD~1` authority is refused and that moving the recorded
  remote ref after an otherwise passing audit invalidates the receipt.
- The Claude CLI minimum-version check now runs before the paid provider call.

This round changes only the remaining finding's immediate code, configuration,
documentation and tests. It does not reopen unrelated audited areas.

Verification evidence: the final focused slice passed 73 tests and 32 subtests; the
complete repository suite passed 380 tests and 78 subtests.
