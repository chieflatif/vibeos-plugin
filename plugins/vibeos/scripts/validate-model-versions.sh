#!/usr/bin/env bash
# validate-model-versions.sh — Enforce approved AI model deployment names
#
# Scans project source files for AI model deployment names and fails if any
# forbidden model identifiers are found. Approved and forbidden model lists
# are fully configurable via environment variables.
#
# Configuration via environment variables:
#   APPROVED_MODELS   — space-separated list of approved deployment names
#                       (informational only — logged but not enforced as a pattern)
#   FORBIDDEN_MODELS  — space-separated list of forbidden model name patterns
#                       (default: gpt-4o gpt-4-turbo gpt-4.5 gpt-4-32k "gpt-4")
#   SCAN_DIRS         — colon-separated directories to scan
#                       (default: src:tests:config)
#   PROJECT_ROOT      — project root directory (default: pwd)
#
# Exit codes:
#   0 — All checks pass
#   1 — Forbidden model reference found (blocking)
#   2 — Configuration error
set -euo pipefail

FRAMEWORK_VERSION="2.2.0"
GATE_NAME="validate-model-versions"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"

# Default forbidden patterns — these represent deprecated or unapproved model versions.
# Projects should override via FORBIDDEN_MODELS env var to match their own approved list.
DEFAULT_FORBIDDEN="gpt-4o gpt-4-turbo gpt-4\.5 gpt-4-32k"
FORBIDDEN_MODELS="${FORBIDDEN_MODELS:-${DEFAULT_FORBIDDEN}}"

# Approved models are informational — used in the summary log
APPROVED_MODELS="${APPROVED_MODELS:-}"

# Directories to scan — colon-separated
SCAN_DIRS="${SCAN_DIRS:-src:tests:config}"

VIOLATIONS=0

echo "[${GATE_NAME}] Starting model version validation (v${FRAMEWORK_VERSION})"

if [ -n "${APPROVED_MODELS}" ]; then
    echo "[${GATE_NAME}] INFO: Approved models: ${APPROVED_MODELS}"
fi

echo "[${GATE_NAME}] INFO: Forbidden patterns: ${FORBIDDEN_MODELS}"
echo "[${GATE_NAME}] INFO: Scanning directories: ${SCAN_DIRS}"

# Convert space-separated forbidden models into an array
read -ra FORBIDDEN_ARRAY <<< "${FORBIDDEN_MODELS}"

# Convert colon-separated scan dirs into an array
IFS=':' read -ra SCAN_DIR_ARRAY <<< "${SCAN_DIRS}"

# Scan each directory for each forbidden pattern
for scan_dir in "${SCAN_DIR_ARRAY[@]}"; do
    dir_path="${PROJECT_ROOT}/${scan_dir}"
    if [ ! -d "${dir_path}" ]; then
        echo "[${GATE_NAME}] SKIP: Directory '${scan_dir}' not found — skipping"
        continue
    fi

    echo "[${GATE_NAME}] INFO: Scanning ${scan_dir}/"

    for pattern in "${FORBIDDEN_ARRAY[@]}"; do
        matches=$(grep -rn \
            --include="*.py" \
            --include="*.json" \
            --include="*.yaml" \
            --include="*.yml" \
            --include="*.sh" \
            --exclude-dir=".git" \
            --exclude-dir="__pycache__" \
            --exclude-dir=".mypy_cache" \
            --exclude-dir=".ruff_cache" \
            --exclude-dir=".pytest_cache" \
            -E "${pattern}" "${dir_path}" 2>/dev/null || true)

        if [ -n "${matches}" ]; then
            echo "[${GATE_NAME}] FAIL: Forbidden model pattern '${pattern}' found in ${scan_dir}/:"
            echo "${matches}" | sed 's/^/  /'
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done
done

# Summary
if [ "${VIOLATIONS}" -gt 0 ]; then
    echo "[${GATE_NAME}] FAIL: ${VIOLATIONS} forbidden model reference(s) found."
    if [ -n "${APPROVED_MODELS}" ]; then
        echo "[${GATE_NAME}] INFO: Only these model names are approved: ${APPROVED_MODELS}"
    fi
    echo "[${GATE_NAME}] INFO: Update model references to use approved deployment names."
    exit 1
fi

echo "[${GATE_NAME}] PASS: No forbidden model references found."
exit 0
