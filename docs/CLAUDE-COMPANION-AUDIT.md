# Claude companion audit

This optional VibeOS module gives Codex-authored engineering work a genuinely
separate Claude review without paying for the same broad audit after every fix.

The operating rule is simple:

1. Finish and commit one bounded work unit.
2. Run one full Claude audit against that exact commit, work order and acceptance
   contract.
3. Fix the named findings.
4. Ask Claude to check those findings and the correction diff only.

A new full audit is required only when the acceptance contract changes, a correction
escapes the original review scope, or the targeted check exposes a new material
blocker.

## What is enforced

The CLI records the exact base and candidate commits, reviewed paths and byte
snapshot, acceptance-contract digest, scope-manifest digest, diff digest, evidence
digests, prompt digest, raw provider-result digest, Claude CLI version and binary
digest, requested and observed model, requested and observed provider, findings and
closure state.

The provider call is pinned to `claude-fable-5-1` through the first-party Claude Code
CLI. It runs in safe, restricted, tool-free mode with no MCP servers, no permission
prompts, no browser, no session persistence, a maximum budget and a turn ceiling.
The model receives a frozen packet; it cannot read or change the repository.

The work-order close gate fails when the receipt is missing, still has open findings,
uses the wrong model/provider, or no longer matches the current reviewed bytes and
acceptance contract.

## Enable it for one project

Add the module explicitly to the project profile:

```json
{
  "phase_audit_runtime": "claude",
  "enabled_modules": ["claude-companion-audit"],
  "claude_companion_audit": {
    "enabled": true,
    "model": "claude-fable-5-1",
    "provider": "firstParty",
    "max_budget_usd": 20,
    "max_turns": 20,
    "timeout_seconds": 2700,
    "max_prompt_bytes": 240000
  }
}
```

The module is disabled by default. Enabling it authorizes this audit lane for that
project; it does not authorize deployment, acceptance or unrelated provider use.

## Scope manifests

A full-audit manifest names the exact work order, acceptance files, reviewed paths and
evidence. Its `finding_ids` list is empty:

```json
{
  "schema_version": 1,
  "work_order": "WO-157",
  "acceptance_contract": ["docs/evidence/WO-157/acceptance-contract.md"],
  "review_paths": ["src/feature.py", "tests/test_feature.py"],
  "evidence_paths": ["docs/evidence/WO-157/tests.txt"],
  "finding_ids": []
}
```

Keep the acceptance contract stable and limited to the objective, constraints and
acceptance criteria. The work order is always included in the frozen full-audit packet
and its reviewed SHA is retained in the receipt, but later status and evidence-checkbox
updates do not invalidate an otherwise closed audit. Changing the normative acceptance
contract still requires a new full audit.

The correction manifest keeps the same acceptance contract, narrows `review_paths` to
the corrected files and lists every finding from the full receipt. Both manifests and
all audited inputs must be committed before the provider call.

## Commands

```bash
python3 .vibeos/scripts/claude-companion-audit.py full \
  --project-dir . \
  --work-order docs/planning/WO-157-example.md \
  --scope-manifest docs/evidence/WO-157/full-scope.json \
  --base-ref origin/main \
  --candidate-ref HEAD \
  --out .vibeos/audit-reports/WO-157-full.json
```

After the corrections are committed:

```bash
python3 .vibeos/scripts/claude-companion-audit.py verification \
  --project-dir . \
  --work-order docs/planning/WO-157-example.md \
  --scope-manifest docs/evidence/WO-157/correction-scope.json \
  --candidate-ref HEAD \
  --parent-receipt .vibeos/audit-reports/WO-157-full.json \
  --out .vibeos/audit-reports/WO-157-verification.json
```

The CLI registers its Markdown report and JSON receipt in session state. The normal
work-order exit gate then validates them:

```bash
bash .vibeos/scripts/validate-independent-audit.sh \
  docs/planning/WO-157-example.md \
  .vibeos/audit-reports/WO-157-verification.md
```

## Authentication boundary

The process must be able to prove a logged-in first-party Claude account through
`claude auth status`. If a sandbox cannot access that login, run the bounded CLI from
an authenticated backend process or provide the supported unattended Claude
authentication outside the repository. Never place credentials in a profile, scope
manifest, work order or audit packet.

The CLI reference used for this implementation is Anthropic's current Claude Code
command-line documentation: <https://code.claude.com/docs/en/cli-usage>. The exact
model identity is documented at
<https://platform.claude.com/docs/en/models/fable-5-1/overview>.
