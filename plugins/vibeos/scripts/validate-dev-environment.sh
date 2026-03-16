#!/usr/bin/env bash
set -euo pipefail

# validate-dev-environment.sh — Reproducible dev setup, README instructions, Makefile/scripts
# VC Audit Dimension: D13 (Team & Process Maturity)
# Validates that a new engineer can go from git clone to running the system in <30 minutes.
#
# Exit codes:
#   0 — All checks pass
#   1 — Violations found (blocking)
#   2 — Configuration error (skip)
#
# Environment:
#   PROJECT_ROOT      — Project root directory (default: pwd)
#   EXCLUDE_DIRS      — Colon-separated directories to exclude

FRAMEWORK_VERSION="2.0.0"
GATE_NAME="validate-dev-environment"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
EXCLUDE_DIRS="${EXCLUDE_DIRS:-}"

VIOLATIONS=0
WARNINGS=0

# -------------------------------------------------------------------
# Check for containerized development environment
# -------------------------------------------------------------------
check_container_env() {
    local container_found=false

    if [ -f "$PROJECT_ROOT/Dockerfile" ]; then
        echo "[${GATE_NAME}] PASS: Dockerfile found"
        container_found=true
    fi

    if [ -f "$PROJECT_ROOT/docker-compose.yml" ] || [ -f "$PROJECT_ROOT/docker-compose.yaml" ] || [ -f "$PROJECT_ROOT/compose.yml" ] || [ -f "$PROJECT_ROOT/compose.yaml" ]; then
        echo "[${GATE_NAME}] PASS: Docker Compose configuration found"
        container_found=true
    fi

    if [ -d "$PROJECT_ROOT/.devcontainer" ] || [ -f "$PROJECT_ROOT/.devcontainer/devcontainer.json" ] || [ -f "$PROJECT_ROOT/.devcontainer.json" ]; then
        echo "[${GATE_NAME}] PASS: VS Code devcontainer configuration found"
        container_found=true
    fi

    # Nix flake
    if [ -f "$PROJECT_ROOT/flake.nix" ] || [ -f "$PROJECT_ROOT/shell.nix" ] || [ -f "$PROJECT_ROOT/default.nix" ]; then
        echo "[${GATE_NAME}] PASS: Nix environment definition found"
        container_found=true
    fi

    if [ "$container_found" = "false" ]; then
        echo "[${GATE_NAME}] WARN: No containerized/reproducible development environment (Dockerfile, docker-compose, devcontainer, Nix)"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# -------------------------------------------------------------------
# Check for README with setup instructions
# -------------------------------------------------------------------
check_readme() {
    local readme_found=false
    local has_setup=false

    # Find README
    local readme_file=""
    for f in README.md README.rst README.txt README readme.md; do
        if [ -f "$PROJECT_ROOT/$f" ]; then
            readme_file="$PROJECT_ROOT/$f"
            readme_found=true
            break
        fi
    done

    if [ "$readme_found" = "false" ]; then
        echo "[${GATE_NAME}] FAIL: No README file — new engineers have no starting point"
        VIOLATIONS=$((VIOLATIONS + 1))
        return
    fi

    echo "[${GATE_NAME}] PASS: README file found"

    # Check for setup/installation section
    local setup_keywords="install\|setup\|getting started\|quickstart\|quick start\|prerequisites\|requirements\|development\|how to run\|running locally\|local development"
    if grep -qi "$setup_keywords" "$readme_file" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: README contains setup/installation instructions"
        has_setup=true
    fi

    if [ "$has_setup" = "false" ]; then
        echo "[${GATE_NAME}] WARN: README exists but no setup/installation section detected"
        WARNINGS=$((WARNINGS + 1))
    fi

    # Check for common run commands in README
    if grep -q 'npm\|yarn\|pip\|poetry\|go run\|cargo\|make\|docker' "$readme_file" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: README includes executable commands"
    else
        echo "[${GATE_NAME}] WARN: README does not contain executable commands — setup may be unclear"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# -------------------------------------------------------------------
# Check for environment variable documentation
# -------------------------------------------------------------------
check_env_documentation() {
    local env_doc_found=false

    # .env.example / .env.template / .env.sample
    for f in .env.example .env.template .env.sample .env.local.example; do
        if [ -f "$PROJECT_ROOT/$f" ]; then
            local var_count
            var_count=$(grep -cE '^[A-Z_]+=.' "$PROJECT_ROOT/$f" 2>/dev/null || true)
            var_count="${var_count:-0}"
            echo "[${GATE_NAME}] PASS: $f found ($var_count variables defined)"
            env_doc_found=true
            break
        fi
    done

    if [ "$env_doc_found" = "false" ]; then
        # Check if env vars are referenced in code
        local env_usage
        env_usage=$(grep -rn 'os\.environ\|process\.env\|os\.Getenv\|env::var\|std::env' \
            "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" --include="*.rs" 2>/dev/null | \
            grep -v 'test\|node_modules\|venv\|__pycache__' | head -1 || true)

        if [ -n "$env_usage" ]; then
            echo "[${GATE_NAME}] WARN: Code references environment variables but no .env.example — new engineers won't know what to configure"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Check for task runner / common scripts
# -------------------------------------------------------------------
check_task_runner() {
    local runner_found=false

    # Makefile
    if [ -f "$PROJECT_ROOT/Makefile" ]; then
        local targets
        targets=$(grep -cE '^[a-zA-Z_-]+:' "$PROJECT_ROOT/Makefile" 2>/dev/null || true)
        targets="${targets:-0}"
        echo "[${GATE_NAME}] PASS: Makefile found ($targets targets)"
        runner_found=true
    fi

    # package.json scripts
    if [ -f "$PROJECT_ROOT/package.json" ]; then
        local script_count
        script_count=$(python3 -c "
import json
try:
    with open('$PROJECT_ROOT/package.json') as f:
        data = json.load(f)
    scripts = data.get('scripts', {})
    print(len(scripts))
except: print(0)
" 2>/dev/null || echo "0")
        if [ "$script_count" -gt 0 ]; then
            echo "[${GATE_NAME}] PASS: package.json has $script_count npm scripts"
            runner_found=true

            # Check for essential scripts
            local has_dev=false has_test=false has_build=false has_lint=false
            if python3 -c "
import json
with open('$PROJECT_ROOT/package.json') as f:
    scripts = json.load(f).get('scripts', {})
essentials = ['dev', 'start', 'test', 'build', 'lint']
found = [s for s in essentials if s in scripts]
missing = [s for s in essentials if s not in scripts]
if missing: print('MISSING:' + ','.join(missing))
else: print('COMPLETE')
" 2>/dev/null | grep -q "MISSING"; then
                local missing
                missing=$(python3 -c "
import json
with open('$PROJECT_ROOT/package.json') as f:
    scripts = json.load(f).get('scripts', {})
missing = [s for s in ['dev', 'start', 'test', 'build', 'lint'] if s not in scripts]
print(','.join(missing))
" 2>/dev/null || echo "unknown")
                echo "[${GATE_NAME}] WARN: package.json missing common scripts: $missing"
                WARNINGS=$((WARNINGS + 1))
            fi
        fi
    fi

    # pyproject.toml scripts
    if [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
        if grep -q '\[tool\.poetry\.scripts\]\|\[project\.scripts\]\|\[tool\.taskipy\.tasks\]' "$PROJECT_ROOT/pyproject.toml" 2>/dev/null; then
            echo "[${GATE_NAME}] PASS: pyproject.toml has script definitions"
            runner_found=true
        fi
    fi

    # Just (justfile)
    if [ -f "$PROJECT_ROOT/justfile" ] || [ -f "$PROJECT_ROOT/Justfile" ]; then
        echo "[${GATE_NAME}] PASS: Justfile found"
        runner_found=true
    fi

    # Taskfile (go-task)
    if [ -f "$PROJECT_ROOT/Taskfile.yml" ] || [ -f "$PROJECT_ROOT/Taskfile.yaml" ]; then
        echo "[${GATE_NAME}] PASS: Taskfile found"
        runner_found=true
    fi

    if [ "$runner_found" = "false" ]; then
        echo "[${GATE_NAME}] WARN: No task runner (Makefile, npm scripts, justfile, Taskfile) — common operations not standardized"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# -------------------------------------------------------------------
# Check for dependency lockfile
# -------------------------------------------------------------------
check_lockfile() {
    local lockfile_found=false

    for f in package-lock.json yarn.lock pnpm-lock.yaml bun.lockb poetry.lock Pipfile.lock requirements.txt go.sum Cargo.lock Gemfile.lock composer.lock; do
        if [ -f "$PROJECT_ROOT/$f" ]; then
            echo "[${GATE_NAME}] PASS: Dependency lockfile found ($f)"
            lockfile_found=true
            break
        fi
    done

    if [ "$lockfile_found" = "false" ]; then
        echo "[${GATE_NAME}] WARN: No dependency lockfile — builds may not be reproducible"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# -------------------------------------------------------------------
# Check for CI configuration
# -------------------------------------------------------------------
check_ci_config() {
    local ci_found=false

    if [ -d "$PROJECT_ROOT/.github/workflows" ]; then
        local workflow_count
        workflow_count=$(find "$PROJECT_ROOT/.github/workflows" -name "*.yml" -o -name "*.yaml" 2>/dev/null | wc -l | tr -d ' ')
        workflow_count="${workflow_count:-0}"
        echo "[${GATE_NAME}] PASS: GitHub Actions configured ($workflow_count workflows)"
        ci_found=true
    fi

    if [ -f "$PROJECT_ROOT/.gitlab-ci.yml" ]; then
        echo "[${GATE_NAME}] PASS: GitLab CI configured"
        ci_found=true
    fi

    if [ -f "$PROJECT_ROOT/Jenkinsfile" ]; then
        echo "[${GATE_NAME}] PASS: Jenkins pipeline configured"
        ci_found=true
    fi

    if [ -f "$PROJECT_ROOT/.circleci/config.yml" ]; then
        echo "[${GATE_NAME}] PASS: CircleCI configured"
        ci_found=true
    fi

    if [ -f "$PROJECT_ROOT/azure-pipelines.yml" ]; then
        echo "[${GATE_NAME}] PASS: Azure Pipelines configured"
        ci_found=true
    fi

    if [ -f "$PROJECT_ROOT/bitbucket-pipelines.yml" ]; then
        echo "[${GATE_NAME}] PASS: Bitbucket Pipelines configured"
        ci_found=true
    fi

    if [ "$ci_found" = "false" ]; then
        echo "[${GATE_NAME}] WARN: No CI/CD configuration — builds, tests, and deploys are manual"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# -------------------------------------------------------------------
# Check for code formatting/linting config
# -------------------------------------------------------------------
check_code_standards() {
    local standards_found=false

    # Check for linter/formatter configs
    for f in .eslintrc .eslintrc.js .eslintrc.json .eslintrc.yml eslint.config.js eslint.config.mjs \
             .prettierrc .prettierrc.js .prettierrc.json prettier.config.js \
             ruff.toml .ruff.toml \
             setup.cfg .flake8 \
             .editorconfig \
             biome.json biome.jsonc \
             .stylelintrc .stylelintrc.json; do
        if [ -f "$PROJECT_ROOT/$f" ]; then
            standards_found=true
            break
        fi
    done

    # Check pyproject.toml for tool configs
    if [ -f "$PROJECT_ROOT/pyproject.toml" ]; then
        if grep -q '\[tool\.ruff\]\|\[tool\.black\]\|\[tool\.isort\]\|\[tool\.mypy\]\|\[tool\.flake8\]' "$PROJECT_ROOT/pyproject.toml" 2>/dev/null; then
            standards_found=true
        fi
    fi

    if [ "$standards_found" = "true" ]; then
        echo "[${GATE_NAME}] PASS: Code formatting/linting configuration found"
    else
        echo "[${GATE_NAME}] WARN: No linter/formatter configuration — code style will diverge with team growth"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
main() {
    echo "[${GATE_NAME}] INFO: Starting development environment validation (v${FRAMEWORK_VERSION})"

    check_container_env
    check_readme
    check_env_documentation
    check_task_runner
    check_lockfile
    check_ci_config
    check_code_standards

    echo ""
    echo "[${GATE_NAME}] INFO: Dev environment validation complete — $VIOLATIONS violations, $WARNINGS warnings"

    if [ "$VIOLATIONS" -gt 0 ]; then
        echo "[${GATE_NAME}] FAIL: $VIOLATIONS dev environment violations found"
        exit 1
    fi

    if [ "$WARNINGS" -gt 0 ]; then
        echo "[${GATE_NAME}] WARN: $WARNINGS dev environment gaps (non-blocking)"
    fi

    echo "[${GATE_NAME}] PASS: Development environment checks passed"
    exit 0
}

main "$@"
