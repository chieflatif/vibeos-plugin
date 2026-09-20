# Profile-Driven Install Architecture

Status: draft implementation note

## Problem

The current project bootstrap copies a broad generic VibeOS operating system into
target repositories. That makes generic instructions, dormant reference payload,
and aggressive hook policy look like target-project truth before the project has
defined its own canon, risk model, validators, or runtime split.

The IIN install cleanup showed the right boundary: target repos need a small
active harness generated from the target profile, not the full framework source
tree copied into `.vibeos/`.

## Architecture

Profile-driven install separates three layers:

1. Framework primitives stay in the VibeOS source repo: scripts, role templates,
   optional reference packs, and install generators.
2. A required project profile describes target truth: project name, canon paths,
   protected files, validators, avoided generic surfaces, enabled modules, and
   selected install mode.
3. Active target surfaces are generated from that profile: Codex skills,
   Codex Markdown role contracts, Codex TOML agents, hooks, gate manifests, and
   active-surface audit configuration.

Install is plan-first:

```bash
./vibeos analyze --target /path/to/repo --source /path/to/vibeos-plugin
./vibeos apply --plan /path/to/repo/.vibeos/install-plan.json
```

The analyze step writes an install plan with detected canon, protected files,
existing validators, enabled/skipped modules, active gates, dormant payload,
overwrite actions, and post-install checks. The apply step executes only that
plan.

## Modes

- `minimal`: runtime detector, gate runner, profile, Codex core surfaces,
  conservative hooks, active-surface audit.
- `product-engineering`: minimal plus implementation/test/review roles and
  product-engineering gates.
- `regulated/evidence-heavy`: product-engineering plus evidence and audit
  controls.
- `comp`: product-engineering plus competition-grade MVP modules.
- `autonomy`: product-engineering plus resumable long-run autonomy modules.
- `full`: all framework payload, including dormant reference material. This is
  opt-in only.

Minimal and product-engineering modes do not copy `.vibeos/reference`,
`.vibeos/decision-engine`, or `.vibeos/convergence`.

## Optional Local Engineering Intake

`local-engineering-intake` is an additive profile module and is not included by any
mode automatically. An opted-in profile must also set
`local_engineering_intake.enabled` to `true`; mismatched configuration fails analysis.

The module installs one loopback-only, stdlib CLI plus a narrowly triggered skill for
each supported runtime surface. The CLI accepts bounded artifacts on standard input,
requests closed JSON from an OpenAI-compatible local endpoint, validates exact evidence
quotes, retries once, and emits either `accepted` or `fallback_required`. It has no
file-input, shell, Git, deployment, approval, or automatic cloud-fallback path. See
`docs/LOCAL-ENGINEERING-INTAKE.md` for the profile contract and operator flow.

## Upgrade Safety

Generated files are tracked in `.vibeos/install-lock.json` with template IDs,
profile hash, source hash, and content hash. On upgrade, unchanged generated
files are replaced. Locally customized generated files are preserved, and the new
candidate is written under `.vibeos/merge-conflicts/` for review.

## Built-In Audit

The generated active-surface audit fails if active instructions:

- do not mention the target project,
- reference rejected generic paths,
- reference dormant payload that was not installed,
- make read-only auditor roles writable,
- activate generic prompt scanning or commit-message enforcement without opt-in.

Codex TOML agents are audited as first-class runtime surfaces.
