# WO-148 Verification Receipt

Date: 2026-06-17

## Commands Run

```bash
bash -n vibeos-machine-init.sh plugins/vibeos/scripts/workstation-package.sh
bash plugins/vibeos/scripts/workstation-package.sh install
bash plugins/vibeos/scripts/workstation-package.sh check
bash plugins/vibeos/scripts/workstation-package.sh verify
bash plugins/vibeos/scripts/gate-runner.sh workstation_check --framework-dir plugins/vibeos --project-dir . --manifest plugins/vibeos/quality-gate-manifest.json --dry-run
python3 -m pytest tests/test_gate_runner.py tests/test_codex_bootstrap.py
python3 plugins/vibeos/scripts/generate-inventory.py --project-dir . --out docs/evidence/vnext/generated-inventory.json
python3 plugins/vibeos/scripts/wo-frontmatter-lint.py generate-index --project-dir . --out docs/planning/WO-INDEX.md
python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .
git diff --check
```

## Results

- Shell syntax checks passed for the root wrapper and harness package script.
- `vibeos-machine-init.sh` now delegates to `plugins/vibeos/scripts/workstation-package.sh install`.
- `workstation-package.sh install` ran in dry-run mode and did not install packages.
- `workstation-package.sh check` ran successfully and reported current-machine state without installing anything.
- `workstation-package.sh verify` completed with `failures=0 warnings=4`.
- The optional `workstation_check` gate-runner phase dry-run resolved `scripts/workstation-package.sh`.
- Focused tests passed for gate-runner phase registration and Codex bootstrap installation of the utility.
- `generated-inventory.json` was refreshed so public script/gate/work-order counts include the optional workstation package.
- `wo-frontmatter-lint.py validate-index` passed after regenerating `WO-INDEX.md`.
- `git diff --check` passed.
- The top-level `workstation-bootstrap/` side package tree was removed from the intended published surface.

## Current-Machine Warnings

These are not harness integration failures:

- `uv` Python 3.10 was not installed.
- `uv` Python 3.11 was not installed.
- Docker CLI exists but Docker Desktop was not running.
- Baseline formula checks may report missing or outdated dependencies because this existing laptop was not installed from the new package and several installed formulae are behind the current Homebrew index.
- Several apps are present outside Homebrew cask management: Claude Code, Codex CLI/App, Cursor, and Docker Desktop.

## Current-Machine Upgrade Drift

Observed via workstation package check, `brew outdated --verbose`, and `npm outdated -g --depth=0`:

- Homebrew formulae with available updates include `azure-cli`, `gh`, `node`, `uv`, `render`, `ruff`, `go`, `cloudflared`, `opentofu`, `pandoc`, `poppler`, `redis`, PostgreSQL packages, and Python formulae.
- npm globals with available updates include `@anthropic-ai/claude-code`, `@openai/codex`, `azure-functions-core-tools`, `npm`, `pnpm`, `typescript`, `tsx`, and several MCP packages.
- Missing from the desired command spine on this machine: `yq`, `fd`, `tree`, `wget`, and ImageMagick's `magick`.
- Homebrew warned that `stripe/stripe-cli/stripe` is from an untrusted tap; the package should not auto-trust taps without explicit operator intent.

## Not Claimed

- Clean-machine `workstation-package.sh install --apply` has not been run.
- Docker Desktop first-run license acceptance has not been completed on the new Mac.
- Claude, Codex, GitHub, and Azure authentication have not been completed on the new Mac.
- Per-project VibeOS install has not been tested on the new Mac.
