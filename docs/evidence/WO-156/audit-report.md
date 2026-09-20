# WO-156 Pre-Commit Audit

## Scope and Freshness

- Base commit: `5165e86628badd3875add55ce2445e1e1c3a7032` (`origin/main` at
  implementation start).
- Candidate: the uncommitted WO-156 diff in the isolated
  `codex/local-engineering-intake` worktree.
- Review contracts applied sequentially: `correctness-auditor`,
  `security-auditor`, and `test-auditor`.

Codex-native delegation was not authorized for this task, so these contracts were
applied sequentially in the implementation context as the repository's documented
fallback. This is a role-contract review, not a claim of fresh-context independent
model review.

## Outcome

No blocking finding remains. The review found four material boundary gaps while the
candidate was still mutable; each was corrected and covered before closeout:

| Finding | Impact a user would notice | Resolution | Evidence |
|---|---|---|---|
| The free-text objective appeared outside the untrusted-data fence. | A hostile objective could steer classification even though the worker has no tools. | Objective text is now injection-scanned and placed inside the randomized untrusted-data fence. | `test_request_bounds_and_untrusted_context_fail_closed` |
| Standard input was decoded before a raw-size ceiling. | A very large request could consume unnecessary memory before the configured artifact limit applied. | The CLI reads only a bounded JSON envelope derived from the configured artifact ceiling and returns `request_too_large`. | `test_raw_request_is_bounded_before_json_parsing` |
| Malformed or deeply nested JSON could escape as a parser exception on uncommon inputs. | A broken local response could print a traceback instead of the promised parent-owned fallback receipt. | Provider, model-result, and request decoding now convert decode, Unicode, and recursion failures into bounded reason codes. | `test_malformed_model_json_retries_once_then_returns_to_parent`; `test_deeply_nested_non_object_request_returns_bounded_error` |
| Ambiguous installer inputs could defer failure until runtime. | An invalid port or simultaneous enable/disable selection could leave a project with an unusable lane. | Profile analysis rejects invalid ports, remote hosts, unknown fields, missing source, and contradictory module selection before apply. | `test_local_engineering_intake_rejects_mismatched_or_remote_profile` |

## Correctness Review

- **Critical:** 0
- **High:** 0 open
- **Medium:** 0 open
- **Low:** 0 open

The default path remains unchanged. Opt-in requires both the module and the explicit
enable flag. Accepted results require the exact task type, closed keys, bounded fields,
artifact-grounded quotes, and escalation for high uncertainty. Every provider or
validation failure is limited to two local attempts and returns control to the parent;
there is no third call or automatic cloud path.

## Security Review

- **Critical:** 0
- **High:** 0
- **Medium:** 0 open
- **Low:** 0 open

The endpoint must be `localhost` or a numeric loopback address and must resolve only to
loopback addresses. URL credentials, proxies, redirects, remote hosts, query strings,
and fragments are rejected. The API key can come only from the environment and header
breaks are rejected. The worker receives no file, shell, Git, deployment, or other
action tool. No credential or private key was added to the candidate diff.

The residual risk is explicit: a local model can still produce misleading advisory
prose, and a loopback service can retain material sent to it. The parent must verify
the exact evidence quotes and must not route secrets or material outside the task's
existing privacy authority.

## Test Quality Review

- **Feature test methods:** 16 (13 runtime, 3 installer)
- **Acceptance criteria covered:** 6 of 6
- **Mocked transports:** 0
- **Fallback-masked tests:** 0 identified
- **Over-mocked files:** 0

Transport behavior uses an ephemeral real loopback HTTP server rather than mocking the
function under test. Assertions distinguish `accepted`, `ready`, and
`fallback_required`, check exit codes and exact call counts, and prove that injection
and oversize failures occur before a network call. The disposable install and live
local-model receipt exercise the public installed path separately from the fixture.

Test-first commit ordering cannot be proven because the work order, tests, and
implementation are one candidate commit. The acceptance contract was written before
closeout, every criterion has explicit coverage, and the full product suite passed.

## Disposition

All review findings were fixed in scope. There is no deferred code, security, or test
finding for WO-156.
