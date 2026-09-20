# Install and customize VibeOS

Use one reviewed release from `chieflatif/vibeos-plugin`. The older
`codex-vibeos-plugin` and `vibeos-bootstrap` repositories are legacy entrypoints.
This release's measured target is macOS with Codex; it does not claim Windows
or Linux qualification.

## Requirements

- Python 3.12 or later, Bash 3.2 or later, Git and jq.
- Codex available on PATH for local runtime detection and native evaluation.
- pytest and Ruff in the Python/tool environment when using controlled evaluation.

Run version commands on the destination Mac. The release evidence names versions
actually exercised; a different runtime needs its own capability readback. No
installer copies login sessions, credentials, global settings or private projects.

## Clone an exact release

```bash
git clone --branch v2.4.0 --single-branch https://github.com/chieflatif/vibeos-plugin.git
cd vibeos-plugin
git rev-parse HEAD
```

Compare that commit with the GitHub release. Keep this source directory separate
from your application. The application should have its own Git repository and a
README or product document explaining what you are building.

## Configure the project

Place a project-owned JSON file in your application, for example
`vibeos-profile.json`. A starting profile can be:

```json
{
  "project_name": "My Application",
  "project_slug": "my-application",
  "mode": "product-engineering",
  "lead_runtime": "codex",
  "phase_audit_runtime": "codex",
  "canon_paths": ["README.md"],
  "protected_files": ["README.md"],
  "enabled_modules": [],
  "disabled_modules": [],
  "primary_gates": []
}
```

Set canon paths to the project's actual requirements, architecture and working
rules. `primary_gates` and auto-detected validators are copied into
`documented_primary_gates` and `documented_validators` for review. They are
informational: the profile installer does not execute them, they do not block, and
they cannot establish application acceptance. Empty documented gates likewise do
not make the application tested or ready to ship. The generated framework surface
audit checks the install surface only.

Configure a real required check as a gate row in the project's
`.claude/quality-gate-manifest.json`, backed by an installed repository-relative
script, with the required phase and blocking policy. Execute that phase with
`.vibeos/scripts/gate-runner.sh`. The installer deliberately does not turn arbitrary
command strings from `primary_gates` or validator detection into executable gates.
Review and preserve project-owned manifest customizations during later profile
upgrades.

From the VibeOS source directory:

```bash
./vibeos analyze --source . --target /absolute/path/to/application \
  --profile /absolute/path/to/application/vibeos-profile.json
./vibeos verify --plan /absolute/path/to/application/.vibeos/install-plan.json
./vibeos apply --plan /absolute/path/to/application/.vibeos/install-plan.json
```

Read the plan before apply. Check that `source_worktree_dirty` is false for a
reviewed release clone; the Git reference and generated-byte hashes are distinct
provenance fields. The plan lists generated files, existing files that will be
preserved, and any merge candidates. Source, profile or target changes invalidate
the analyzed plan; analyze again deliberately instead of forcing a stale plan.

From the application, detect the actual runtime:

```bash
bash .vibeos/scripts/detect-runtime-capabilities.sh --project-dir .
cat .vibeos/runtime-capabilities.json
python3 .vibeos/scripts/vibeos-active-surface-audit.py
```

The detector is evidence of available tools, not a guarantee that every edit route
is blocked. If commit-boundary enforcement is wanted, inspect existing Git hooks
and run the supplied hook setup without overwriting unrelated hooks. Commit-message
enforcement is installed only when `commit-msg-enforcement` is enabled and its
validator is present:

```bash
bash .vibeos/scripts/setup-git-hooks.sh --project-dir .
```

Open the application in Codex and describe its purpose, intended users and first
useful result. The generated instructions point to your project-owned documents.
Use [controlled evaluation](CONTROLLED-EVALUATION.md) to bind engineering results
to protected specifications and exact required checks. Pick agent models from the
models available on that Mac; use smaller models for bounded work and independent
review for consequential changes.

For Codex-led projects that require a separate Claude audit, explicitly enable the
disabled-by-default `claude-companion-audit` module and set
`phase_audit_runtime` to `claude`. The project must have an authenticated first-party
Claude Code CLI available to the backend process. VibeOS does not install or copy that
login. The module runs one frozen full audit and then targeted verification of the
original findings; see [Claude companion audit](CLAUDE-COMPANION-AUDIT.md).

## Upgrade and recover

Clone the next reviewed release separately and repeat analyze, verify and apply
against the existing application and its project-owned profile. Keep the prior
source revision until the upgrade is accepted. Customized or unmanaged files are
preserved and receive separate generated candidates for review. Resolve those
candidates deliberately; an install receipt is not permission to discard local rules.

After deliberately merging a candidate, deleting a resolved candidate, or changing
an installed project-owned file, `verify` will report installed target drift. Run
`analyze` again against the same source, target and profile, review the fresh plan,
then verify and apply it. Do not rewrite the install lock to bless the changed bytes.

`apply --skip-post-checks` writes an `applied-unverified` receipt and exits nonzero.
That state is not an accepted installation and cannot be finalized with the old plan.
Run `analyze` again against the same source, target and profile, review and verify the
fresh plan, then apply it without `--skip-post-checks`.

If apply is interrupted, inspect its recovery status and use:

```bash
./vibeos recover --plan /absolute/path/to/application/.vibeos/install-plan.json
```

Recovery must finish before a new apply. If a target changed after the interruption,
retain its evidence and reconcile it rather than overwriting concurrent work.
After successful recovery, analyze a fresh plan and rerun the checks. See the
release evidence for the exact interruption cases exercised.

Do not run the legacy bootstrap upgrade over a customized profile installation.
The legacy runtime replacement behavior does not provide the profile installer's
preservation and recovery contract.

The legacy entrypoints now refuse any target containing a profile install lock,
including with `--force` or `--uninstall`. Use the profile route above.

If you ran the optional hook setup with 2.3.0 on a default profile, inspect
`.git/hooks/commit-msg`. The 2.3.1 setup refuses a leftover VibeOS-owned hook when
commit-message enforcement is disabled. Preserve a copy and deliberately remove
that owned hook, or explicitly enable the module and install its validator, then
rerun setup, the surface audit and verification. Do not remove unrelated hooks.

Recovery covers the journaled interruption cases in the release evidence. An
interruption before the journal is written can leave backup or temporary files;
the transaction lock file is persistent. Inspect these artifacts before cleanup.
Changing modes does not automatically prune retired generated surfaces. Review
those surfaces explicitly and rerun the audit; a downgrade is not an automatic
reversal of every prior installation action.
