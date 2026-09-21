# WO-157 automated verification

- Evidence recorded: 2026-09-21T02:52:34Z
- Tested implementation commit: `e0710e034e745b16f8eb363309c8b1237b501302`
- Tested tree: `cbf2d8ff6a04fc5fe56c2aa1839b91e0f4f48d5a`

The later evidence-only commit may add this record, the targeted scope manifest and
release-gate wording; it does not alter executable implementation bytes.

## Focused release slice

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/test_claude_companion_audit.py \
  tests/test_profile_install.py \
  tests/test_profile_install_release.py \
  tests/test_release_handoff.py \
  tests/test_canonical_closeout.py
```

Result: **85 tests and 39 subtests passed in 71.15 seconds**.

This covers the companion CLI, provider/receipt refusal paths, full-to-targeted
verification, profile installation, release handoff, canonical closeout, enabled and
disabled close-gate behavior, large files, Unicode paths, and post-audit drift.

## Full repository suite

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests
```

Result: **395 tests and 85 subtests passed in 274.67 seconds**.

The run used permission only for the repository's in-process loopback HTTP fixtures;
no product service was contacted.

## Static and governance checks

- Ruff passed for the audit CLI, profile installer, and relevant tests.
- Bash syntax validation passed for `validate-independent-audit.sh`.
- WO frontmatter lint and generated-index validation passed.
- All repository JSON parsed successfully.
- Generated inventory matched source after excluding its volatile `generated_at` field.
- `git diff --check` passed.
- A sandboxed full run reported the seven expected loopback-fixture permission
  failures and also exposed a real file-size breach after the close-gate hardening.
  The gate was reduced to the permitted 300-line ceiling without an exemption. The
  exact full suite then passed with localhost-only fixture permission.
- The documented `--timeout 300` pre-commit run passed 9 gates, failed 0, and skipped
  the existing non-blocking dependency gate (10 total). Its test gate passed in 135
  seconds.

## Live review boundary

The fresh first-party full receipt
`claude-audit-96e0e5ee-a663-4b2d-9a07-70be5112a0b0` reviewed candidate `40574d6`
and returned 12 findings. Commit `e0710e0` corrects those named findings; the next and
only provider step is targeted verification against that parent receipt. The final
candidate machine-checks that all changes after this tested implementation commit are
administrative evidence only.
