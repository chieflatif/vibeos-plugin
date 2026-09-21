# WO-157 research record

## Existing implementations inspected

- VibeOS already declares cross-identity companion review, but its dispatcher creates
  a manifest and waits for an external reviewer; it does not call Claude or prove
  provider/model provenance.
- The Claude Enterprise OS prototype directly invokes the Claude Code CLI, disables
  tools and persistence, and checks `modelUsage`. It does not bind acceptance-contract
  bytes, commits or correction scope, and it repeats broad completion review.
- The IIN phase-audit wrapper invokes several broad Claude reviewers each run. It is
  project-specific and has no targeted correction-verification mode.
- The BOE review bridge proves exact `claude-fable-5-1` and first-party provider
  metadata outside the Codex Keychain sandbox. Its fixed bounded request and
  provenance checks were reused conceptually; BOE-specific queue/account policy was
  not copied into the reusable project module.

## Primary documentation refreshed

- Anthropic Claude Code CLI reference confirms non-interactive `--print`, exact
  `--model`, `--json-schema`, `--restricted`, `--tools`, `--permission-prompts none`,
  `--max-budget-usd`, `--max-turns`, `--safe-mode` and
  `--no-session-persistence` behavior.
- Anthropic's Fable 5.1 model page provides the exact `claude-fable-5-1` identifier.

Sources:

- <https://code.claude.com/docs/en/cli-usage>
- <https://platform.claude.com/docs/en/models/fable-5-1/overview>

## Decision

Reuse the existing CLI and provider-provenance pattern as an opt-in VibeOS module.
Add immutable input bindings and a separate correction-verification contract rather
than building a new orchestration service. Keep provider calls disabled until a
project profile opts in, and require a real receipt before release acceptance.
