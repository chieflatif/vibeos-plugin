# WO-156 Verification

## Environment

- Source: isolated worktree at canonical `origin/main` commit
  `5165e86628badd3875add55ce2445e1e1c3a7032`.
- Disposable install target: `/private/tmp/vibeos-local-intake-install-proof`.
- Configured local endpoint: `http://127.0.0.1:1234/v1`.
- Configured model: `gpt-oss-120b`.

## Install Proof

The normal profile workflow completed without a merge conflict:

```text
[vibeos] PASS: install plan written
[vibeos] mode=product-engineering enabled_modules=7 active_surfaces=135
[vibeos] PASS: applied profile-driven install plan
[vibeos] files=134 conflicts=0
[vibeos] PASS: install transaction verified: installed
plan_payload_hash=151cee19171cb235ea303fe4af883505c81f5effbf68438c67adb1296dc59672
```

The installed active-surface audit passed for the disposable project. The generated
`.agents/skills/vibeos-local-intake/SKILL.md` also passed the skill-creator
`quick_validate.py` check with valid first-line YAML frontmatter.

## Local Backend and Real Path

The installed `probe` command reached the configured loopback server, found the exact
model, and returned `status: ready` in 8 ms.

The installed `run` command processed one bounded pytest failure through the live local
model. The first result did not satisfy the deterministic contract; the permitted
second attempt returned `status: accepted` in 9,539 ms. The receipt reports 1,351
prompt tokens and 385 completion tokens. Both accepted evidence quotes occur verbatim
in the supplied artifact. The exact accepted receipt is preserved in
`real-path-receipt.json`.

This proves the intended path: install, skill discovery, endpoint/model probe, local
inference, validation, one retry, and accepted advisory output. It does not establish
implementation or acceptance authority for the local model.

## Automated Coverage

Focused suite before the full gate:

```text
python3 -m pytest -q tests/test_local_engineering_intake.py tests/test_profile_install.py
28 passed, 13 subtests passed
```

Covered behavior includes default-off installation, explicit opt-in, profile mismatch
and remote-host rejection, closed result schema, artifact-grounded evidence, successful
first-pass output, invalid-output retry, malformed-model fallback, raw-input bounds,
deeply nested input rejection, prompt-injection refusal before a network call, redirect
refusal, and high-uncertainty escalation.

The complete product regression suite also passed:

```text
python3 -m pytest -q tests
354 passed, 70 subtests passed
```

The canonical pre-commit gate passed after the final runtime, installer, tests,
documentation, and audit record were present:

```text
Total: 10 | Passed: 9 | Failed: 0 | Skipped: 1
Result: PASS
```

The one skipped advisory check was the repository's dependency command; every critical
and important gate ran and passed.

## Research-to-Test Trace

| Research or requirement | Implemented control | Decisive proof |
|---|---|---|
| Local open-weight model is useful for closed structured work, not frontier-equivalent coding | Allowed task-type set excludes implementation and acceptance | Installer and request-schema tests |
| OpenAI-compatible local serving already exists | Reuse `/v1/models` and `/v1/chat/completions` | Live probe and real-path run |
| Model prose is not trustworthy by itself | Closed JSON, no extra fields, exact artifact quotes | Invalid-grounding retry test |
| Local routing must not create hidden cloud spend | Loopback resolution, proxies and redirects disabled, no cloud fallback | Remote-host and redirect tests |
| A weak result must not become an action | Advisory authority label and parent-owned fallback | Receipt assertions and generated skill validation |
