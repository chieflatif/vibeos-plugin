# WO-148 Investigation: New Machine Bootstrap Package

Date: 2026-06-17

## Verdict

Create a workstation bootstrap path in the VibeOS GitHub checkout before treating VibeOS as ready for a new computer. VibeOS should keep the per-project governance installer, but the repository should also expose a machine-level bootstrap wrapper so a new Mac can be prepared from the same checkout before installing VibeOS into individual projects.

## Repo Evidence

- `README.md` documents VibeOS as a project-level bootstrap that installs into a target project's `.claude/` and `.vibeos/` directories.
- `README.md` lists VibeOS requirements as Claude Code, OpenAI Codex, bash, python3, jq, and git.
- `CLAUDE.md` states the plugin itself uses pure Claude Code capabilities plus Bash, Python, jq, git, and optional Codex CLI. It explicitly says no external frameworks are part of the plugin architecture.
- `plugins/vibeos/reference/codex/AGENTS.md.ref` says Codex does not get Claude hook parity and must read `.vibeos/runtime-capabilities.json` before claiming orchestration capability.
- `docs/planning/WO-147-plugin-install-integrity-remediation.md` records that the local 2.2.0 development tree may be ahead of the public marketplace/install source. That is a migration risk for a new computer.

## Runtime Evidence From This Machine

Command:

```bash
bash plugins/vibeos/scripts/detect-runtime-capabilities.sh --project-dir .
```

Observed result:

```text
Codex: available version=0.125.0 subagents=unavailable hooks=unavailable
Claude: available version=2.1.177 subagents=available worktrees=available workflows=available
Strategy: claude / claude-subagents
```

This means the package should install both Claude and Codex, then rerun detection locally. It should not hardcode a universal orchestration strategy.

## Local Project Stack Sample

| Workspace | Evidence | Bootstrap implication |
|---|---|---|
| `/Users/latifhorst/Joan4U` | `pyproject.toml`, `requirements.txt`, `Dockerfile`, `Makefile`, `control_plane/web/package.json`, `package-lock.json` | Python 3.12, npm, Docker, make |
| `/Users/latifhorst/meeting-sidekick` | `pyproject.toml`, `requirements.txt`, `uv.lock`, `Dockerfile`, `docker-compose.yml`, `Makefile` | uv, Python 3.12, Docker Compose, Azure-adjacent dependencies |
| `/Users/latifhorst/pipeline-rebel-cowork` | service `pyproject.toml`, `uv.lock`, video `package.json`, `package-lock.json` | uv, Python, Node/npm, ffmpeg/media tooling |
| `/Users/latifhorst/latifhorstweb` | `docker-compose.yml`, backend `requirements.txt`, frontend `package.json`, `package-lock.json`, Dockerfiles | Docker, Python, Node/npm |
| `/Users/latifhorst/Fabriq` | `package.json`, `package-lock.json`, `render.yaml` | Node/npm, Render CLI |
| `/Users/latifhorst/Microsoft_Admin` | Azure Functions `package.json`, `package-lock.json` | Node >=20, Azure CLI, Azure Functions Core Tools |

No sampled repo made Go, Rust, Java, or Kubernetes mandatory for the first machine package. Go is included as a useful optional build/runtime tool because it is already installed on the current machine and some CLIs use it, but the package does not make Go project setup a completion criterion.

## Partial-Install Finding

The current machine already has several tools installed outside the Homebrew cask state:

- `/Applications/Claude.app` exists and `claude` is available, but the `claude-code` cask is not installed.
- `/Applications/Cursor.app` exists and `cursor` is available, but the `cursor` cask is not installed.
- `/Applications/Docker.app` exists and `docker` is available, but the `docker-desktop` cask is not installed.
- `/Applications/Codex.app` exists and `codex` is available, but the `codex` / `codex-app` casks are not installed.

The installer must treat this as an adoption/detection case, not a failure. The package now installs formulae separately and handles casks one by one, skipping unmanaged equivalents unless `--force-cask-ownership` is used.

## Current Machine Tool Inventory

Required spine observed locally:

- Homebrew, git, GitHub CLI, jq, ripgrep
- Node 24, npm, corepack, pnpm
- Python 3, uv, ruff
- Docker CLI / Docker Compose
- Azure CLI, Azure Functions Core Tools
- Claude Code, Codex CLI, Cursor

Upgrade drift observed locally:

- Homebrew reported outdated formulae including `azure-cli`, `gh`, `node`, `uv`, `render`, `ruff`, `go`, `cloudflared`, `opentofu`, `pandoc`, `poppler`, `redis`, and PostgreSQL packages.
- npm global packages reported updates for `@anthropic-ai/claude-code`, `@openai/codex`, `azure-functions-core-tools`, `npm`, `pnpm`, `typescript`, `tsx`, and several MCP packages.
- `uv python list --only-installed` showed Python 3.12 available through uv, plus Homebrew/user 3.13 and Homebrew 3.14, but not uv-managed 3.10 or 3.11.
- GitHub CLI auth and Azure account auth are configured on this current machine; the bootstrap intentionally does not copy credentials.

Useful installed extras:

- ffmpeg, poppler, pandoc for media/PDF/document workflows
- render, stripe CLI, gcloud CLI, cloudflared, rclone
- postgres and redis for local service work
- opentofu for infrastructure work

## Official Source Checks

- Homebrew official install command and Apple Silicon prefix behavior were checked at `https://brew.sh/`.
- Claude Code official quickstart was checked at `https://code.claude.com/docs/en/quickstart`.
- OpenAI Codex CLI setup was checked at `https://developers.openai.com/codex/cli`.
- OpenAI Codex app setup was checked at `https://developers.openai.com/codex/app`.
- Docker Desktop macOS installation and license requirements were checked at `https://docs.docker.com/desktop/setup/install/mac-install/`.
- uv install options were checked at `https://docs.astral.sh/uv/getting-started/installation/`.
- pnpm/Corepack guidance was checked at `https://pnpm.io/installation`.
- Azure CLI macOS install guidance was checked at `https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-macos`.
- Azure Functions Core Tools macOS install guidance was checked at `https://learn.microsoft.com/en-us/azure/azure-functions/functions-run-local`.

## Recommendation

Use `workstation-bootstrap/macos/` as the first package:

1. `vibeos-machine-init.sh` is the top-level GitHub-checkout entrypoint for Mac baseline setup.
2. `Brewfile` records full desired state.
3. `Brewfile.formulae` installs formulae separately from casks.
4. `install-macos.sh` defaults to dry-run and only installs with `--apply`.
5. `doctor.sh` audits current or partially configured machines without installing anything.
6. `verify.sh` checks the installed tool spine and reruns VibeOS runtime detection when available.
7. VibeOS itself stays per-project: run `vibeos-init.sh` and `vibeos-init-codex.sh` inside each cloned project.

## Known Risks

- WO-147 must be resolved before relying on marketplace/plugin install to reproduce the current 2.2.0 VibeOS runtime on a new computer.
- Docker Desktop requires a license acceptance and may require paid subscription depending on commercial context.
- Claude and Codex authentication should remain interactive; do not script credentials.
- Project dependencies should be installed per repo with `uv sync`, `pip`, or `npm ci` based on the repo lockfile, not globally in this bootstrap.
