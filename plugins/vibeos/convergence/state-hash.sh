#!/usr/bin/env bash
set -euo pipefail

# state-hash.sh — Deterministic hash of source file state
# Used by convergence controls to detect code changes between fix cycles.
# Exit 0 with hash on stdout; exit 1 on error.

FRAMEWORK_VERSION="2.0.0"

usage() {
  echo "Usage: $0 --project-dir <path> [--exclude <pattern>]..."
  echo ""
  echo "Produces a deterministic SHA-256 hash of all source files in the project."
  echo "Excludes .git, node_modules, .vibeos, and other non-source directories by default."
  echo ""
  echo "Options:"
  echo "  --project-dir    Root directory of the project to hash"
  echo "  --exclude        Additional directory/file patterns to exclude (can be repeated)"
  exit 1
}

PROJECT_DIR=""
EXTRA_EXCLUDES=()

while [ $# -gt 0 ]; do
  case "$1" in
    --project-dir)
      PROJECT_DIR="$2"
      shift 2
      ;;
    --exclude)
      EXTRA_EXCLUDES+=("$2")
      shift 2
      ;;
    --help|-h)
      usage
      ;;
    *)
      echo "[state-hash] ERROR: Unknown argument: $1" >&2
      usage
      ;;
  esac
done

if [ -z "$PROJECT_DIR" ]; then
  echo "[state-hash] ERROR: --project-dir is required" >&2
  exit 1
fi

if [ ! -d "$PROJECT_DIR" ]; then
  echo "[state-hash] ERROR: Directory not found: $PROJECT_DIR" >&2
  exit 1
fi

# Default exclusions: non-source directories
DEFAULT_EXCLUDES=(
  ".git"
  "node_modules"
  ".vibeos"
  "__pycache__"
  ".mypy_cache"
  ".pytest_cache"
  ".ruff_cache"
  "dist"
  "build"
  ".next"
  "coverage"
  ".tox"
  "venv"
  ".venv"
  "env"
)

# Build find exclusion arguments
FIND_EXCLUDES=()
for pattern in "${DEFAULT_EXCLUDES[@]}" ${EXTRA_EXCLUDES[@]+"${EXTRA_EXCLUDES[@]}"}; do
  FIND_EXCLUDES+=(-path "*/${pattern}" -prune -o)
done

# Detect hash command (macOS vs Linux)
if command -v shasum >/dev/null 2>&1; then
  HASH_CMD="shasum -a 256"
elif command -v sha256sum >/dev/null 2>&1; then
  HASH_CMD="sha256sum"
else
  echo "[state-hash] ERROR: No SHA-256 hash command found (need shasum or sha256sum)" >&2
  exit 1
fi

# Find all files, sort deterministically, hash contents
# Sort by path to ensure deterministic ordering regardless of filesystem
FILE_HASHES=$(
  cd "$PROJECT_DIR" && \
  find . "${FIND_EXCLUDES[@]}" -type f -print 2>/dev/null | \
  sort | \
  while IFS= read -r file; do
    $HASH_CMD "$file" 2>/dev/null || true
  done
)

if [ -z "$FILE_HASHES" ]; then
  echo "[state-hash] WARN: No files found to hash" >&2
  # Hash empty string for consistency
  echo "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  exit 0
fi

# Hash all individual file hashes to produce single state hash
STATE_HASH=$(echo "$FILE_HASHES" | $HASH_CMD | awk '{print $1}')

echo "$STATE_HASH"
