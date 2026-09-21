# WO-157 independent-audit corrections

The real first-party `claude-fable-5-1` full audit of candidate `999f1d5` returned
18 findings: nine medium, seven low and two informational. This correction set stays
inside the original reviewed paths and addresses those finding IDs only.

- `F-001`: the provider prompt now travels over standard input, never a positional
  argument; OS launch errors fail cleanly and a test sends more than 131,072 bytes.
- `F-002`: current-byte validation now snapshots only Git-tracked paths and preserves
  Git-compatible symlink bytes; ignored bytecode no longer invalidates a receipt.
- `F-003`: acceptance-contract files are always included as frozen audit and
  verification material, independent of whether they appear in the diff.
- `F-004`: the close gate fails when its configured module cannot be parsed, is not
  active, uses the wrong phase runtime, or lacks `jq`; installer output and negative
  gate cases are tested.
- `F-005`: reports truthfully identify one companion reviewer and its review coverage;
  the fabricated “Auditors dispatched” statement was removed.
- `F-006`: permission mode is now `default`, avoiding the unrelated plan-workflow
  system instructions while retaining restricted, tool-free execution.
- `F-007`: validation re-parses the stored provider result, rechecks model/provider,
  auth and closure, and requires exact equality with the receipt result. Claude-side
  proof protection now covers companion receipts; Codex's hook limitation is explicit.
- `F-008`: a full audit base must equal the candidate's merge base with the recorded
  default branch. Changed paths must also fit work-order `write_scope` and the declared
  review/evidence classification. Both refusal paths are tested.
- `F-009`: negative tests now cover finding-ID mismatch, review/correction expansion,
  blocking-pass inconsistency, verification inconsistency, canonical-model mismatch,
  unauthenticated use, empty diffs, open verification, and unknown CLI flags.
- `F-010`: release notes now point to this evidence bundle instead of duplicating test
  counts. The corrected focused and full results are recorded in `automated-tests.md`.
- `F-011`: observed model and provider now come from `modelUsage`, with numeric token,
  context and cost fields retained as provider evidence.
- `F-012`: non-passing full results without finding IDs require a new full audit;
  later targeted rounds may use another same-work-order scope manifest and are tested.
- `F-013`: explicit config is now a recorded, explicit plugin-self-audit override;
  normal installed projects must authorize the call through their active profile.
- `F-014`: the reversible email hash was removed and the CLI hash is accurately named
  as an entrypoint-file digest.
- `F-015`: malformed nested receipts and OS/runtime errors return the documented
  controlled failure rather than a traceback; exit meanings are documented.
- `F-016`: reports and session state record `audit_visibility_mode: committed-tree`
  and the exact candidate commit.
- `F-017`: CLI 2.1.277 is the minimum enforced version, standard proxy/CA variables
  pass through, and model policy now explains the exact-provenance pinning exception.
- `F-018`: generated inventory records a portable project root (`.`), not the
  temporary release checkout path.

Verification evidence before the targeted provider check:

- Final focused release slice after correction round 2: 72 tests and 32 subtests passed.
- Final full repository suite after correction round 2: 379 tests and 78 subtests passed.
- Ruff, Bash syntax, JSON parsing and whitespace checks passed.
