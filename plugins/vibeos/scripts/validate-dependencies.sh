#!/usr/bin/env bash
# VibeOS Plugin — Dependency Security Validation Gate
# Runs language-appropriate dependency audit (pip-audit, npm audit, etc.)
#
# Usage:
#   bash scripts/validate-dependencies.sh
#
# Environment:
#   PROJECT_ROOT  — target project root (default: script parent)
#   LANGUAGE      — python|typescript|javascript|go|rust|java (default: auto-detect)
#   PACKAGE_FILE  — path to package manifest (default: auto-detect)
#
# Exit codes:
#   0 = No known vulnerabilities
#   1 = Vulnerabilities found
#   2 = Audit tool not available (skip)
set -euo pipefail

FRAMEWORK_VERSION="2.2.0"
GATE_NAME="validate-dependencies"

usage() {
  cat <<'EOF'
Usage:
  bash scripts/validate-dependencies.sh

Environment:
  PROJECT_ROOT  Target project root (default: script parent)
  LANGUAGE      python|typescript|javascript|go|rust|java (default: auto-detect)
  PACKAGE_FILE  Path to package manifest (default: auto-detect)

Runs:
  Python     → pip-audit
  JS/TS      → npm audit / yarn audit
  Go         → govulncheck
  Rust       → cargo audit
  Java       → (advisory only — use OWASP dependency-check)
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

echo "[$GATE_NAME] Dependency Security Validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

repo_root="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# Auto-detect language
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
  elif [[ -f "$repo_root/pom.xml" ]] || [[ -f "$repo_root/build.gradle" ]]; then
    echo "java"
  else
    echo "unknown"
  fi
}

LANGUAGE="${LANGUAGE:-$(detect_language)}"
echo "Language: $LANGUAGE"

case "$LANGUAGE" in
  python)
    if command -v pip-audit >/dev/null 2>&1; then
      echo "=== pip-audit ==="
      if pip-audit 2>&1; then
        echo "[$GATE_NAME] PASS: No known Python vulnerabilities"
        exit 0
      else
        echo "[$GATE_NAME] FAIL: pip-audit found vulnerabilities"
        exit 1
      fi
    elif python3 -m pip_audit --version >/dev/null 2>&1; then
      echo "=== pip-audit (module) ==="
      if python3 -m pip_audit 2>&1; then
        echo "[$GATE_NAME] PASS: No known Python vulnerabilities"
        exit 0
      else
        echo "[$GATE_NAME] FAIL: pip-audit found vulnerabilities"
        exit 1
      fi
    else
      echo "[$GATE_NAME] WARN: pip-audit not installed. Install with: pip install pip-audit"
      echo "[$GATE_NAME] SKIP: Cannot audit dependencies without pip-audit"
      exit 0
    fi
    ;;

  typescript|javascript)
    if [[ -f "$repo_root/yarn.lock" ]] && command -v yarn >/dev/null 2>&1; then
      echo "=== yarn audit ==="
      if yarn audit --level moderate 2>&1; then
        echo "[$GATE_NAME] PASS: No known JS/TS vulnerabilities"
        exit 0
      else
        echo "[$GATE_NAME] FAIL: yarn audit found vulnerabilities"
        exit 1
      fi
    elif [[ -f "$repo_root/package-lock.json" ]] || [[ -f "$repo_root/package.json" ]]; then
      if ! command -v npm >/dev/null 2>&1; then
        echo "[$GATE_NAME] WARN: npm not installed. Install Node.js/npm to audit JS/TS dependencies"
        echo "[$GATE_NAME] SKIP: Cannot audit JS/TS dependencies without npm"
        exit 0
      fi
      echo "=== npm audit ==="
      if (cd "$repo_root" && npm audit --audit-level=moderate) 2>&1; then
        echo "[$GATE_NAME] PASS: No known JS/TS vulnerabilities"
        exit 0
      else
        echo "[$GATE_NAME] FAIL: npm audit found vulnerabilities"
        exit 1
      fi
    else
      echo "[$GATE_NAME] WARN: No package manager lock file found"
      echo "[$GATE_NAME] SKIP: Cannot audit JS/TS dependencies"
      exit 0
    fi
    ;;

  go)
    if command -v govulncheck >/dev/null 2>&1; then
      echo "=== govulncheck ==="
      if (cd "$repo_root" && govulncheck ./...) 2>&1; then
        echo "[$GATE_NAME] PASS: No known Go vulnerabilities"
        exit 0
      else
        echo "[$GATE_NAME] FAIL: govulncheck found vulnerabilities"
        exit 1
      fi
    else
      echo "[$GATE_NAME] WARN: govulncheck not installed. Install with: go install golang.org/x/vuln/cmd/govulncheck@latest"
      echo "[$GATE_NAME] SKIP: Cannot audit Go dependencies"
      exit 0
    fi
    ;;

  rust)
    if command -v cargo-audit >/dev/null 2>&1; then
      echo "=== cargo audit ==="
      if (cd "$repo_root" && cargo audit) 2>&1; then
        echo "[$GATE_NAME] PASS: No known Rust vulnerabilities"
        exit 0
      else
        echo "[$GATE_NAME] FAIL: cargo audit found vulnerabilities"
        exit 1
      fi
    else
      echo "[$GATE_NAME] WARN: cargo-audit not installed. Install with: cargo install cargo-audit"
      echo "[$GATE_NAME] SKIP: Cannot audit Rust dependencies"
      exit 0
    fi
    ;;

  java)
    echo "[$GATE_NAME] WARN: Java dependency audit requires OWASP dependency-check plugin"
    echo "[$GATE_NAME] WARN: Add to Gradle: id 'org.owasp.dependencycheck' version '9.0.0'"
    echo "[$GATE_NAME] SKIP: No built-in Java audit tool"
    exit 0
    ;;

  *)
    echo "[$GATE_NAME] WARN: Unknown language '$LANGUAGE'"
    echo "[$GATE_NAME] SKIP: Cannot determine dependency audit tool"
    exit 0
    ;;
esac
