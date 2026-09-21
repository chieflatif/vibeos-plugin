# Correction verification evidence

- Tested implementation commit: `6d2c0ea5efc10304b90272f7bbf9a65b4d01826f`
- Tested tree: `7340c235ca148a265ccd8297f76b7a4187acb4a8`

The same canonical pre-commit command in automated-tests.md passed after F-001
through F-007 corrections: nine gates passed, zero failed, one optional dependency
check skipped. Full test gate passed in145seconds. Combined companion regressions:
66tests and25subtests passed. All production and changed-test Ruff, compilation
and scoped diff checks passed. The helper remains299physical lines without a new
size exception. Existing large core size exception remains unchanged.

Specific added proof: status-only work-order edits remain valid; write-scope
edits and new unreviewed files inside that scope fail; genuinely unrelated work
remains allowed; provider-schema optional fields validate; legacy v1 medium
findings cannot be deferred; wrong-model/malformed Claude output cannot generate
fallback permission; both mixed-route directions validate; reports preserve the
actual broad-review route; non-Latif operator records are supported without any
claim of identity authentication.

## Real native transport qualification, not fallback authorization

A separate synthetic prompt requested only `{"status":"synthetic-pass"}` through
installed codex-cli0.147.0, requesting gpt-5.6-luna/high. It used stdin, a new empty
temporary cwd, ephemeral mode, ignore-user-config, skip-git-repo-check, a read-only
sandbox request, output-schema, JSON events and output-last-message. No project
source or prior conversation was supplied. No user-approval record was made, no
Claude failure was fabricated, and this was not the candidate's fallback review.

Actual CLI exit0; thread01a0c246-64f4-75d2-a059-b549093b8934. Observed events:
thread.started, turn.started, one completed agent_message containing the exact
structured result, and turn.completed. The helper's event/final-message validator
accepted the captured transcript and native final-message file. No tool events.
The serving model/provider were not reported, so this proves requested-model CLI
transport behavior, not provider-observed model identity.

Telemetry:16648input tokens,35output tokens (including16reasoning), zero reported
cached input. Do not claim cost savings from this one test: the fixed request
overhead is a reason not to delegate trivial work. A model-cache parsing warning
appeared on stderr before successful completion; no cache or global configuration
was repaired. Local probe artifacts are retained at
`/private/tmp/vibeos-codex-transport.ZraPrB/`; observed-events.jsonl is a transcription
of tool-returned stdout, while final-message.json was written by the native CLI.

This corrects the earlier evidence's limitation: there is now a real native
transport proof, but still no live user-approved fallback audit of this candidate.
The next independent call is targeted Claude verification of F-001 through F-007.
