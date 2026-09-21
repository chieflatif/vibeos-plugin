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
digests, prompt digest, raw provider-result digest, Claude CLI version and entrypoint
file digest, requested and observed model, requested and observed provider, usage,
findings and closure state.

The provider call is pinned to `claude-fable-5-1` through the first-party Claude Code
CLI. It runs in safe, restricted, tool-free mode with no MCP servers, no permission
prompts, no browser, no session persistence, project-only setting sources, a maximum
budget and a turn ceiling. Before any paid call, the wrapper checks the installed
CLI version and confirms every pinned flag appears in that CLI's help output.
The model receives the frozen packet over standard input, so source is not exposed in
the process argument list; it cannot read or change the repository.

The work-order close gate fails when the receipt is missing, still has open findings,
uses the wrong model/provider, or no longer matches the current reviewed bytes and
acceptance contract.

On Claude Code surfaces, the proof-protection hook also blocks implementation roles
from editing companion receipts. Codex does not have equivalent write-hook isolation;
validation therefore cross-checks the receipt result and observed provenance against
the stored raw provider payload, but this remains integrity evidence rather than a
hostile same-user security boundary.

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
    "max_prompt_bytes": 240000,
    "default_branch_ref": "origin/main"
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

The full-audit base must equal the candidate's merge base with the committed
`default_branch_ref` from the project profile. Only `origin/*` remote refs are accepted,
and receipt validation proves both the recorded and current remote histories still
descend from the audited base. The remote branch may advance or absorb the candidate
without invalidating the receipt. Every changed path must also be declared by the work
order and covered by the review or its explicit administrative evidence. This prevents
a late, artificially narrow CLI base from hiding earlier implementation commits.

Installed projects read authorization and limits from `.vibeos/project-profile.json`.
The plugin repository's own release audit may instead pass a committed `--config`
file only together with the explicit `--allow-unprofiled-project` flag; that override
is recorded in the receipt. It is not the normal project workflow.

Exit code `0` means a closed pass, `3` means valid review output still requires
correction or verification, and `2` means the audit input, provider result or receipt
failed validation. Further correction rounds may use new scope-manifest filenames in
the same work-order evidence directory; they remain targeted to the original findings.

## Authentication boundary

The process must be able to prove a logged-in first-party Claude account through
`claude auth status`. The accepted path is `authMethod=claude.ai` and
`apiProvider=firstParty`, using the normal account store under `HOME` or a credential
store selected by `CLAUDE_CONFIG_DIR`. API-key and OAuth-token environment variables
are deliberately removed and do not satisfy this lane. If a sandbox cannot see the
Claude account store, run the bounded CLI from an authenticated backend process with
the correct `CLAUDE_CONFIG_DIR`. Never place credentials in a profile, scope manifest,
work order or audit packet.

The auditor runs from an empty temporary directory with `--setting-sources project`.
That keeps user-level settings, hooks and plugins out of the run while retaining access
to the first-party account store. The effective CLI help digest and selected entrypoint
digest are retained as integrity evidence; they are not a hostile same-user trust
boundary.

The CLI reference used for this implementation is Anthropic's current Claude Code
command-line documentation: <https://code.claude.com/docs/en/cli-usage>. The exact
model identity is documented at
<https://platform.claude.com/docs/en/models/fable-5-1/overview>.
CLI version 2.1.277 or newer is required for the pinned flags. Standard proxy and CA
environment variables are passed through for authenticated enterprise backends.
