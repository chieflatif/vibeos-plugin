# WO-157 automated verification

Date: 2026-09-20 (America/Los_Angeles)

## Focused audit and installer path

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q \
  tests/test_claude_companion_audit.py \
  tests/test_profile_install.py \
  tests/test_profile_install_release.py \
  tests/test_release_handoff.py \
  tests/test_canonical_closeout.py
```

Result: 52 tests and 24 subtests passed in 24.86 seconds after release metadata
and governance checks were included.

The narrower new-module/profile selection passed 23 tests and 7 subtests after the
stable acceptance-contract behavior was added.

## Full repository suite

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests
```

Final post-version-bump result: 362 tests and 70 subtests passed in 174.05 seconds.

The first sandboxed run denied seven pre-existing localhost HTTP fixtures and also
found one invalid WO model-policy value. The metadata was corrected. The exact suite
was then rerun with localhost test-server permission and passed. The network permission
was used only for the repository's in-process loopback fixtures.

## Static and governance checks

- `ruff check` passed for the new audit CLI, profile installer and relevant tests.
- `bash -n plugins/vibeos/scripts/validate-independent-audit.sh` passed.
- `wo-frontmatter-lint.py lint` and `validate-index` passed after the WO contract was
  corrected.
- JSON parsing and `git diff --check` passed.
- The pre-commit quality-gate run passed 9 blocking gates with 0 failures; one
  dependency gate was skipped under its existing non-blocking policy.

## Evidence limit

The fake Claude CLI proves exact command flags, schema handling, full-to-targeted
verification, provider mismatch refusal and drift invalidation. It does not prove a
provider call. The release remains held until a real first-party Fable receipt exists.

The first live invocation stopped before a provider call because the roughly 290 KB
release packet exceeded its 240 KB project ceiling. The committed audit configuration
raises that one ceiling to 320 KB, within the CLI's enforced 500 KB maximum; model,
provider, spend, turn and time limits are unchanged.
