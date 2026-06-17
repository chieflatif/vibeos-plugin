# WO-148 Verification Receipt

Date: 2026-06-17

## Commands Run

```bash
bash -n vibeos-machine-init.sh
bash -n workstation-bootstrap/macos/install-macos.sh
bash -n workstation-bootstrap/macos/verify.sh
bash -n workstation-bootstrap/macos/doctor.sh
git diff --check -- docs/planning/WO-148-new-machine-bootstrap-package.md docs/planning/WO-INDEX.md docs/evidence/vnext/wo-148-new-machine-bootstrap-package/investigation.md docs/evidence/vnext/wo-148-new-machine-bootstrap-package/verification.md workstation-bootstrap/macos/Brewfile workstation-bootstrap/macos/Brewfile.formulae workstation-bootstrap/macos/Brewfile.casks workstation-bootstrap/macos/README.md workstation-bootstrap/macos/install-macos.sh workstation-bootstrap/macos/optional-npm-globals.txt workstation-bootstrap/macos/verify.sh workstation-bootstrap/macos/doctor.sh
workstation-bootstrap/macos/install-macos.sh
workstation-bootstrap/macos/verify.sh
workstation-bootstrap/macos/doctor.sh
python3 plugins/vibeos/scripts/wo-frontmatter-lint.py generate-index --project-dir . --out docs/planning/WO-INDEX.md
python3 plugins/vibeos/scripts/wo-frontmatter-lint.py validate-index --project-dir .
```

## Results

- Shell syntax checks passed.
- `vibeos-machine-init.sh` dry-run passed and delegated to the macOS bootstrap without installing packages.
- `git diff --check` passed for the WO-148 files and generated index.
- `install-macos.sh` dry-run passed and did not install packages.
- `verify.sh` completed with `failures=0 warnings=4`.
- Current-machine drift checks found meaningful Homebrew and npm global updates available.
- Several apps/binaries are present but not Homebrew cask-managed; the installer now treats these as unmanaged equivalents and skips cask ownership by default.
- `doctor.sh` ran successfully and reported current-machine state without installing anything.
- `wo-frontmatter-lint.py validate-index` passed after regenerating `WO-INDEX.md`.
- VibeOS runtime detection completed and reported Claude as the recommended primary runtime on this machine.

## Current-Machine Warnings

These are not scaffold failures:

- `uv` Python 3.10 was not installed.
- `uv` Python 3.11 was not installed.
- Docker CLI exists but Docker Desktop was not running.
- Formula Brewfile check reported missing or outdated dependencies because this existing laptop was not installed from the new Brewfile and several installed formulae are behind the current Homebrew index.
- Several apps are present outside Homebrew cask management: Claude Code, Codex CLI/App, Cursor, and Docker Desktop.

## Current-Machine Upgrade Drift

Observed via `doctor.sh`, `brew outdated --verbose`, and `npm outdated -g --depth=0`:

- Homebrew formulae with available updates include `azure-cli`, `gh`, `node`, `uv`, `render`, `ruff`, `go`, `cloudflared`, `opentofu`, `pandoc`, `poppler`, `redis`, PostgreSQL packages, and Python formulae.
- npm globals with available updates include `@anthropic-ai/claude-code`, `@openai/codex`, `azure-functions-core-tools`, `npm`, `pnpm`, `typescript`, `tsx`, and several MCP packages.
- Missing from the desired bootstrap command spine on this machine: `yq`, `fd`, `tree`, `wget`, and ImageMagick's `magick`.
- Homebrew warned that `stripe/stripe-cli/stripe` is from an untrusted tap; the package should not auto-trust taps without explicit operator intent.

## Not Yet Proven

- Clean-machine `./install-macos.sh --apply` has not been run.
- Docker Desktop first-run license acceptance has not been completed on the new Mac.
- Claude, Codex, GitHub, and Azure authentication have not been completed on the new Mac.
- Per-project VibeOS install has not been tested on the new Mac.
