# Independent release review

Scope: the new controlled-evaluation CLI and six modules, profile installation
integrity/recovery changes, gate result handling and macOS timeout helper.
The reviewer inspected implementation independently of its authors and ran
concrete failure probes. The primary owner separately ran native macOS/Codex
installation/evaluation proofs and retained responsibility for release acceptance.

## Findings and required corrections

1. A fabricated complete install lock with an empty installed-state list could
   pass verify before outputs existed. Verification must derive the exact expected
   file inventory, hashes, modes and actions from the analyzed plan rather than
   accepting the lock's own claims.
2. A fresh post-install audit could run before the new generated-file inventory
   existed, auditing zero instruction surfaces. Audit must consume the pending
   exact inventory, and completion must follow a successful audit.
3. Interrupted recovery left newly created empty parent directories. The journal
   must record those parents and remove only the installer-created empty ones
   after restoring files. Concurrent nonempty directories must remain intact.
4. Source HEAD alone could look like exact byte provenance for a modified checkout.
   Source worktree state and byte hashes must be explicit alongside the Git
   reference. Published-clone proof must use a clean checkout.
5. A normally completed gate returning 124 could be mislabeled as a deadline.
   Actual timeout evidence must distinguish helper-enforced deadlines from a
   child's ordinary nonzero status and preserve output.

The primary review also found that the legacy Python complexity validator could
print violations but return success because counters were updated in a subshell.
Its required-check configuration used the wrong exclusion delimiter. Regression
coverage must prove real violation propagation and refusal of an empty source
scope; the release gate's measured source scope must be explicit.

## Controlled-evaluation conclusion

No further release-impact defect was found in the bounded review of exact schemas,
required test identity/exit accounting, protected input bindings, native sandbox
command, timeout/SIGTERM handling, current-run binding, single-writer locking or
immutable publication. This is not a hostile same-user isolation assessment.
Native proof and launch-emulator tests are distinct. A `PRE_REVIEW` result remains
separate from project acceptance or deployment authority.

## Correction review

Independent re-review found no open release blocker in the bounded scope.
The review replay passed 41 installer/gate tests and 27 controlled-evaluation,
project-scope and autonomy regressions. The additional real SIGTERM test proves
recovery between provisional and final lock publication. Original failing probes
now reject forged/empty locks, expose new instruction surfaces to the audit,
restore the complete pre-apply tree, disclose dirty source provenance and classify
ordinary exit 124 accurately.

The primary owner also corrected child command environment propagation so an
explicitly selected project remains authoritative over inherited PROJECT_ROOT.
The two existing heartbeat tests now exercise a conflicting inherited path and
prove that the wrong target is not created. Independent review accepted this
bounded correction.

Primary acceptance: the final integrated suite, strict/default lint and two
native fresh-installed project proofs pass. Clean-clone and published-ref readback
are the remaining distribution steps; their receipts accompany the release.
