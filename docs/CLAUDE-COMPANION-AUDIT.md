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
findings and closure state. It also binds the latest tested implementation commit and
tree. Any later candidate changes must be limited to the named evidence, contract,
work-order, config and scope-manifest files; executable changes after that tested
commit fail before a provider call.

The provider call is pinned to `claude-fable-5-1` through the first-party Claude Code
CLI. It runs in safe, restricted, tool-free mode with no MCP servers, no permission
prompts, no browser, no session persistence, project-only setting sources, a maximum
budget and a turn ceiling. Before any paid call, the wrapper checks the installed
CLI version and confirms every advertised pinned flag appears in that CLI's help
output. Claude Code 2.1.277 accepts but does not advertise `--max-turns`, so the
wrapper also runs an isolated, credential-free parser probe for that flag and requires
the exact authentication stop before continuing. If a future supported CLI advertises
the flag, the probe is skipped. The receipt records which path was used.
The model receives the frozen packet over standard input, so source is not exposed in
the process argument list; it cannot read or change the repository.

The work-order close gate fails when the receipt is missing, still has open findings,
uses the wrong model/provider, or no longer matches the current reviewed bytes and
acceptance contract. Validation also requires a clean non-ignored worktree, rechecks
the work-order write scope and test binding, and requires the report supplied to the
gate to be the exact report path bound by the registered receipt.

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
  "evidence_paths": ["docs/evidence/WO-157/automated-tests.md"],
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

At least one evidence file must bind the deterministic checks to a real Git commit
and tree using these exact lines:

```text
- Tested implementation commit: `0123456789abcdef0123456789abcdef01234567`
- Tested tree: `89abcdef0123456789abcdef0123456789abcdef`
```

Run the checks on the implementation commit first, then add this evidence in a later
administrative-only commit. Multiple correction rounds may retain older bindings; the
CLI selects the unique latest tested commit and proves every newer change is
administrative only.

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
is recorded in the receipt. It is not the normal project workflow. Because the plugin
cannot use its not-yet-published installed gate to release itself, its release uses the
same validator and exact receipt/report checks manually in the work-order checklist;
installed projects receive the blocking `wo_exit` gate.

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
The pinned CLI's own `--help` states that `--safe-mode` disables `CLAUDE.md`, skills,
plugins, hooks, MCP servers, custom commands and agents, workflows and the other named
customizations; admin-managed policy may still apply. The receipt records safe mode,
the project-only setting-source argument, the effective help digest and the selected
entrypoint digest. These facts retain access to the first-party account store without
reading or copying personal Claude configuration. They are integrity evidence, not a
hostile same-user trust boundary.

The JSON receipt, Markdown report and raw provider response are local project
artifacts under `.vibeos/audit-reports/`. They are deliberately not published in the
plugin source distribution. Committed work-order evidence may name their audit IDs and
summarize the outcome, but a published-source reader cannot independently verify the
provider call without the local artifacts.

The CLI reference used for this implementation is Anthropic's current Claude Code
command-line documentation: <https://code.claude.com/docs/en/cli-usage>. The exact
model identity is documented at
<https://platform.claude.com/docs/en/models/fable-5-1/overview>.
CLI version 2.1.277 or newer is required for the pinned flags. Standard proxy and CA
environment variables are passed through for authenticated enterprise backends.
