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

Final corrected-candidate result: 73 tests and 32 subtests passed in 45.38 seconds
after the remaining default-branch-authority finding and legacy-receipt upgrade were
covered.

The selection now includes the companion CLI, profile installation, release handoff,
canonical closeout and generated-inventory coverage.

## Full repository suite

Command:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -q tests
```

Final corrected-candidate result: 380 tests and 78 subtests passed in 226.95 seconds.

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
verification, provider mismatch refusal and drift invalidation. The real first-party
full audit returned findings against candidate `999f1d5`; release remains held until
those exact findings pass targeted verification.

The first live invocation stopped before a provider call because the roughly 290 KB
release packet exceeded its 240 KB project ceiling. The committed audit configuration
raises that one ceiling to 320 KB, within the CLI's enforced 500 KB maximum; model,
provider, spend, turn and time limits are unchanged.
