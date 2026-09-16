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
git clone --branch v2.3.0 --single-branch https://github.com/chieflatif/vibeos-plugin.git
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
rules. Add the project's own validation commands and security constraints as they
become known. Empty project gates mean project acceptance checks are not configured;
they do not make the application tested or ready to ship. The generated framework
surface audit checks the install, not the application.

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
and run the supplied hook setup without overwriting unrelated hooks:

```bash
bash .vibeos/scripts/setup-git-hooks.sh --project-dir .
```

Open the application in Codex and describe its purpose, intended users and first
useful result. The generated instructions point to your project-owned documents.
Use [controlled evaluation](CONTROLLED-EVALUATION.md) to bind engineering results
to protected specifications and exact required checks. Pick agent models from the
models available on that Mac; use smaller models for bounded work and independent
review for consequential changes.

## Upgrade and recover

Clone the next reviewed release separately and repeat analyze, verify and apply
against the existing application and its project-owned profile. Keep the prior
source revision until the upgrade is accepted. Customized or unmanaged files are
preserved and receive separate generated candidates for review. Resolve those
candidates deliberately; an install receipt is not permission to discard local rules.

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
