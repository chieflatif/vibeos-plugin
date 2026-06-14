#!/usr/bin/env bash
# VibeOS Plugin — Work Order Frontmatter Validator

set -euo pipefail

PROJECT_DIR="${PROJECT_DIR:-.}"

while [ $# -gt 0 ]; do
  case "$1" in
    --project-dir)
      PROJECT_DIR="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/wo-frontmatter-lint.py" lint --project-dir "$PROJECT_DIR"
python3 "$SCRIPT_DIR/wo-frontmatter-lint.py" validate-index --project-dir "$PROJECT_DIR"
