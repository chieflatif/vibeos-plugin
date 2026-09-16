#!/usr/bin/env bash
# VibeOS Plugin — Code Quality Validation Gate
# Runs language-appropriate linting and compile checks.
#
# Usage:
#   bash scripts/validate-code-quality.sh
#
# Environment:
#   SOURCE_DIR  — primary source directory (default: auto-detect)
#   TEST_DIR    — test directory (default: tests/)
#   LANGUAGE    — python|typescript|javascript|go|rust|java (default: auto-detect)
#   LINTER      — override linter command (default: language-appropriate)
#
# Exit codes:
#   0 = Quality checks passed
#   1 = Quality checks failed
#   2 = Required source, configuration, or tool unavailable
set -euo pipefail

FRAMEWORK_VERSION="2.3.1"
GATE_NAME="validate-code-quality"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate-code-quality.sh

Environment:
  SOURCE_DIR  Primary source directory (default: auto-detect)
  TEST_DIR    Test directory (default: tests/)
  LANGUAGE    python|typescript|javascript|go|rust|java (default: auto-detect)
  LINTER      Override linter command (default: language-appropriate)
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] Code Quality Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
framework_root="$(cd "$script_dir/.." && pwd)"
if [[ -n "${PROJECT_ROOT:-}" ]]; then
  if [[ ! -d "$PROJECT_ROOT" ]]; then
    echo "[$GATE_NAME] FAIL: PROJECT_ROOT is not a directory: $PROJECT_ROOT"
    exit 2
  fi
  repo_root="$(cd "$PROJECT_ROOT" && pwd -P)"
else
  repo_root="$framework_root"
fi

# Auto-detect language if not set
detect_language() {
  if [[ -f "$repo_root/pyproject.toml" ]] || [[ -f "$repo_root/setup.py" ]] || [[ -f "$repo_root/requirements.txt" ]]; then
    echo "python"
  elif [[ -f "$repo_root/tsconfig.json" ]]; then
    echo "typescript"
  elif [[ -f "$repo_root/package.json" ]]; then
    echo "javascript"
  elif [[ -f "$repo_root/go.mod" ]]; then
    echo "go"
  elif [[ -f "$repo_root/Cargo.toml" ]]; then
    echo "rust"
  elif [[ -f "$repo_root/pom.xml" ]] || [[ -f "$repo_root/build.gradle" ]] || [[ -f "$repo_root/build.gradle.kts" ]]; then
    echo "java"
  else
    echo "unknown"
  fi
}

LANGUAGE="${LANGUAGE:-$(detect_language)}"
echo "Language: $LANGUAGE"

# Auto-detect source directory if not set
if [[ -z "${SOURCE_DIR:-}" ]]; then
  # Try common source directory conventions
  for candidate in src lib app "${repo_root##*/}"; do
    if [[ -d "$repo_root/$candidate" ]]; then
      SOURCE_DIR="$candidate"
      break
    fi
  done
  # Framework scripts are source only when the selected root is an actual
  # VibeOS plugin root. They must not be inferred for an arbitrary project.
  if [[ -z "${SOURCE_DIR:-}" && -f "$repo_root/.claude-plugin/plugin.json" && -d "$repo_root/scripts" ]]; then
    SOURCE_DIR="scripts"
  fi
fi

if [[ -z "${SOURCE_DIR:-}" ]]; then
  echo "[$GATE_NAME] WARN: No source directory detected. Set SOURCE_DIR env var."
  echo "[$GATE_NAME] SKIP: Cannot run quality checks without source directory"
  exit 2
fi

if [[ "$SOURCE_DIR" == /* ]]; then
  source_path="$SOURCE_DIR"
else
  source_path="$repo_root/$SOURCE_DIR"
fi
if [[ ! -d "$source_path" ]]; then
  echo "[$GATE_NAME] SKIP: Source directory not found: $source_path"
  exit 2
fi

echo "Source directory: $SOURCE_DIR"
TEST_DIR="${TEST_DIR:-tests}"

current_section=""
fail_with() {
  echo "[$GATE_NAME] FAIL ($current_section)"
  exit 1
}
trap 'fail_with' ERR

run_cmd() {
  echo "+ $*"
  "$@"
}

skip_unavailable() {
  echo "[$GATE_NAME] SKIP: $1"
  exit 2
}

# ============================================================================
# PYTHON
# ============================================================================
if [[ "$LANGUAGE" == "python" ]]; then
  python_cmd="python3"
  if ! command -v python3 >/dev/null 2>&1; then
    if command -v python >/dev/null 2>&1; then
      python_cmd="python"
    else
      skip_unavailable "Python not installed"
    fi
  fi

  # Compile check
  current_section="COMPILE_CHECK"
  echo "=== Python Compile Check ($SOURCE_DIR/) ==="
  run_cmd "$python_cmd" -m compileall "$source_path"

  # Linter
  current_section="LINT"
  echo ""
  echo "=== Python Lint ($SOURCE_DIR/) ==="

  if [[ -n "${LINTER:-}" ]]; then
    linter_command="${LINTER%%[[:space:]]*}"
    if ! command -v "$linter_command" >/dev/null 2>&1; then
      skip_unavailable "Required Python linter not available: $linter_command"
    fi
    run_cmd $LINTER "$source_path"
  elif command -v ruff >/dev/null 2>&1; then
    lint_targets=("$source_path")
    [[ -d "$repo_root/$TEST_DIR" ]] && lint_targets+=("$repo_root/$TEST_DIR")
    run_cmd ruff check "${lint_targets[@]}"
  elif "$python_cmd" -m ruff --version >/dev/null 2>&1; then
    lint_targets=("$source_path")
    [[ -d "$repo_root/$TEST_DIR" ]] && lint_targets+=("$repo_root/$TEST_DIR")
    run_cmd "$python_cmd" -m ruff check "${lint_targets[@]}"
  elif command -v flake8 >/dev/null 2>&1; then
    run_cmd flake8 "$source_path"
  elif "$python_cmd" -m flake8 --version >/dev/null 2>&1; then
    run_cmd "$python_cmd" -m flake8 "$source_path"
  else
    skip_unavailable "No Python linter installed (ruff or flake8)"
  fi

# ============================================================================
# TYPESCRIPT / JAVASCRIPT
# ============================================================================
elif [[ "$LANGUAGE" == "typescript" || "$LANGUAGE" == "javascript" ]]; then
  current_section="LINT"

  # TypeScript compile check
  if [[ "$LANGUAGE" == "typescript" ]]; then
    current_section="TYPE_CHECK"
    echo "=== TypeScript Type Check ==="
    if command -v tsc >/dev/null 2>&1; then
      run_cmd tsc --noEmit 2>&1
    elif command -v npx >/dev/null 2>&1 && npx --no-install tsc --version >/dev/null 2>&1; then
      run_cmd npx --no-install tsc --noEmit 2>&1
    else
      skip_unavailable "TypeScript compiler not available"
    fi
    echo ""
  fi

  current_section="LINT"
  echo "=== JavaScript/TypeScript Lint ==="

  if [[ -n "${LINTER:-}" ]]; then
    linter_command="${LINTER%%[[:space:]]*}"
    if ! command -v "$linter_command" >/dev/null 2>&1; then
      skip_unavailable "Required JS/TS linter not available: $linter_command"
    fi
    run_cmd $LINTER
  elif [[ -f "$repo_root/.eslintrc.js" ]] || [[ -f "$repo_root/.eslintrc.json" ]] || [[ -f "$repo_root/.eslintrc.yml" ]] || [[ -f "$repo_root/eslint.config.js" ]] || [[ -f "$repo_root/eslint.config.mjs" ]]; then
    if command -v eslint >/dev/null 2>&1; then
      run_cmd eslint "$source_path" 2>&1
    elif command -v npx >/dev/null 2>&1 && npx --no-install eslint --version >/dev/null 2>&1; then
      run_cmd npx --no-install eslint "$source_path" 2>&1
    else
      skip_unavailable "ESLint not available"
    fi
  elif [[ -f "$repo_root/biome.json" ]] || [[ -f "$repo_root/biome.jsonc" ]]; then
    if command -v biome >/dev/null 2>&1; then
      run_cmd biome check "$source_path" 2>&1
    elif command -v npx >/dev/null 2>&1 && npx --no-install biome --version >/dev/null 2>&1; then
      run_cmd npx --no-install biome check "$source_path" 2>&1
    else
      skip_unavailable "Biome not available"
    fi
  else
    skip_unavailable "No JS/TS linter configuration found"
  fi

# ============================================================================
# GO
# ============================================================================
elif [[ "$LANGUAGE" == "go" ]]; then
  current_section="BUILD_CHECK"
  echo "=== Go Build Check ==="
  if command -v go >/dev/null 2>&1; then
    run_cmd go build ./...
  else
    skip_unavailable "Go not installed"
  fi

  current_section="LINT"
  echo ""
  echo "=== Go Vet ==="
  run_cmd go vet ./...

  if command -v golangci-lint >/dev/null 2>&1; then
    echo ""
    echo "=== golangci-lint ==="
    run_cmd golangci-lint run 2>&1
  fi

# ============================================================================
# RUST
# ============================================================================
elif [[ "$LANGUAGE" == "rust" ]]; then
  current_section="BUILD_CHECK"
  echo "=== Rust Build Check ==="
  if command -v cargo >/dev/null 2>&1; then
    run_cmd cargo check 2>&1
  else
    skip_unavailable "Cargo not installed"
  fi

  current_section="LINT"
  echo ""
  echo "=== Clippy Lint ==="
  if cargo clippy --version >/dev/null 2>&1; then
    run_cmd cargo clippy -- -D warnings 2>&1
  else
    skip_unavailable "clippy not installed"
  fi

# ============================================================================
# JAVA
# ============================================================================
elif [[ "$LANGUAGE" == "java" ]]; then
  current_section="BUILD_CHECK"
  echo "=== Java Build Check ==="
  if [[ -f "$repo_root/gradlew" ]]; then
    run_cmd "$repo_root/gradlew" compileJava 2>&1
  elif [[ -f "$repo_root/mvnw" ]]; then
    run_cmd "$repo_root/mvnw" compile 2>&1
  elif command -v gradle >/dev/null 2>&1; then
    run_cmd gradle compileJava 2>&1
  elif command -v mvn >/dev/null 2>&1; then
    run_cmd mvn compile 2>&1
  else
    skip_unavailable "No Java build tool available"
  fi

# ============================================================================
# UNKNOWN
# ============================================================================
else
  echo "[$GATE_NAME] WARN: Unknown language '$LANGUAGE'. Set LANGUAGE env var."
  skip_unavailable "Cannot determine quality checks for unknown language"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[$GATE_NAME] PASS: Code quality validation passed"
