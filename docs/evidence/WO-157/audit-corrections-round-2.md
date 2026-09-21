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
- Receipt validation now hashes and revalidates the committed config, then verifies
  the recorded and current remote histories both retain the audited base. Config drift,
  unrelated history or a historical merge-base mismatch invalidates closure; normal
  remote advancement does not.
- A full receipt missing any of these binding fields is rejected. There is no legacy
  schema-1 upgrade path because this is the first published companion-audit format.
- Tests prove that a local `HEAD~1` authority is refused, a safe remote advance remains
  valid, and an unrelated remote history invalidates the receipt.
- The Claude CLI minimum-version check now runs before the paid provider call.

This round changes only the remaining finding's immediate code, configuration,
documentation and tests. It does not reopen unrelated audited areas.

Verification evidence is recorded with its tested commit in `automated-tests.md`.
