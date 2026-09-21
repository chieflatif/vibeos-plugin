# WO-157 automated verification

- Evidence recorded: 2026-09-21T01:40:47Z
- Tested implementation commit: `9d6ae01c9c6f33fae8be7baca04479b1b9013ed9`
- Tested tree: `8b7c76080fda3299e48429094664d9e4f646445d`

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

Result: **78 tests and 32 subtests passed in 50.58 seconds**.

This covers the companion CLI, provider/receipt refusal paths, full-to-targeted
verification, profile installation, release handoff, canonical closeout, enabled and
disabled close-gate behavior, large files, Unicode paths, and post-audit drift.

## Full repository suite

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests
```

Result: **388 tests and 78 subtests passed in 235.42 seconds**.

The run used permission only for the repository's in-process loopback HTTP fixtures;
no product service was contacted.

## Static and governance checks

- Ruff passed for the audit CLI, profile installer, and relevant tests.
- Bash syntax validation passed for `validate-independent-audit.sh`.
- WO frontmatter lint and generated-index validation passed.
- All repository JSON parsed successfully.
- Generated inventory matched source after excluding its volatile `generated_at` field.
- `git diff --check` passed.
- The configured pre-commit phase passed 9 gates, failed 0, and skipped the existing
  non-blocking dependency gate (10 total). Its embedded test gate passed in 111 seconds.

## Live review boundary

The first-party Fable full audit `claude-audit-892a4340-f578-4cd2-863a-ef7fb410ca31`
reviewed candidate `54c0080fdbd557ab31d0b7e71ed8b0aa6bba357b` and returned 17 named findings.
The implementation commit above resolves those findings. A targeted provider check of
those exact finding IDs is required before release; the earlier full audit is not rerun.
