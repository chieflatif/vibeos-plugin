# WO-157 automated verification

- Evidence recorded: 2026-09-21T01:57:11Z
- Tested implementation commit: `0e6697367b72ec9a0ce7ededc4602f1a261e168e`
- Tested tree: `afb2a09c410c200d22fbe46313cda3eb9c8b3135`

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

Result: **79 tests and 32 subtests passed in 52.80 seconds**.

This covers the companion CLI, provider/receipt refusal paths, full-to-targeted
verification, profile installation, release handoff, canonical closeout, enabled and
disabled close-gate behavior, large files, Unicode paths, and post-audit drift.

## Full repository suite

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests
```

Result: **389 tests and 78 subtests passed in 238.68 seconds**.

The run used permission only for the repository's in-process loopback HTTP fixtures;
no product service was contacted.

## Static and governance checks

- Ruff passed for the audit CLI, profile installer, and relevant tests.
- Bash syntax validation passed for `validate-independent-audit.sh`.
- WO frontmatter lint and generated-index validation passed.
- All repository JSON parsed successfully.
- Generated inventory matched source after excluding its volatile `generated_at` field.
- `git diff --check` passed.
- The first configured pre-commit run reached the wrapper's default 120-second ceiling
  while rerunning the already-green suite; it reported a timeout, not a test failure.
  The documented `--timeout 300` override then passed 9 gates, failed 0, and skipped
  the existing non-blocking dependency gate (10 total). Its test gate passed in 119
  seconds.

## Live review boundary

The targeted first-party receipt `claude-audit-909ed4d9-ba46-4776-bef7-0b63ef3e7bd2`
closed all 17 findings from the preceding full audit and exposed one new medium blocker:
profile activation could fail open when `jq` and the generated gate entry were absent.
The implementation commit above fixes that new blocker. Under the frozen audit rule, a
new material blocker requires one fresh full audit before release.

The final full packet is approximately 345 KB after adding the correction history.
Its committed prompt ceiling is therefore 400 KB, still below the CLI's enforced
500 KB maximum; model, provider, spend, turn and time limits are unchanged.
