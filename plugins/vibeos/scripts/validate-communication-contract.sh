#!/usr/bin/env bash
set -euo pipefail

FRAMEWORK_VERSION="2.0.0"
GATE_NAME="communication-contract"

PLUGIN_DIR="${1:-$(cd "$(dirname "$0")/.." && pwd)}"
REPO_ROOT="$(cd "$PLUGIN_DIR/../.." && pwd 2>/dev/null || true)"
PLUGIN_CONTRACT="$PLUGIN_DIR/docs/USER-COMMUNICATION-CONTRACT.md"
ROOT_CONTRACT="$REPO_ROOT/docs/USER-COMMUNICATION-CONTRACT.md"
PLANNING_DIR="$REPO_ROOT/docs/planning"

FAILURES=0

pass() {
  echo "[$GATE_NAME] PASS: $1"
}

fail() {
  echo "[$GATE_NAME] FAIL: $1"
  FAILURES=$((FAILURES + 1))
}

check_required_phrase() {
  local file="$1"
  local phrase="$2"
  if grep -Fq "$phrase" "$file"; then
    pass "$(basename "$file") contains: $phrase"
  else
    fail "$(basename "$file") missing required phrase: $phrase"
  fi
}

validate_decision_blocks() {
  local file="$1"

  awk '
    BEGIN {
      in_block = 0
      saw_pros = 0
      saw_cons = 0
      saw_recommend = 0
      start_line = 0
      status = 0
    }

    /Your options:/ {
      in_block = 1
      saw_pros = 0
      saw_cons = 0
      saw_recommend = 0
      start_line = NR
      next
    }

    in_block {
      if ($0 ~ /Pros:/) saw_pros = 1
      if ($0 ~ /Cons:/) saw_cons = 1
      if ($0 ~ /I recommend/) {
        saw_recommend = 1
        if (!saw_pros || !saw_cons) {
          printf("%s:%d missing Pros/Cons in decision block\n", FILENAME, start_line)
          status = 1
        }
        in_block = 0
        next
      }

      if (NR - start_line > 30) {
        printf("%s:%d missing recommendation in decision block\n", FILENAME, start_line)
        status = 1
        in_block = 0
      }
    }

    END {
      if (in_block) {
        printf("%s:%d unterminated decision block\n", FILENAME, start_line)
        status = 1
      }
      exit status
    }
  ' "$file"
}

if [[ ! -f "$PLUGIN_CONTRACT" ]]; then
  fail "Plugin communication contract not found at $PLUGIN_CONTRACT"
else
  pass "Plugin communication contract found"
fi

if [[ -f "$ROOT_CONTRACT" ]]; then
  if cmp -s "$PLUGIN_CONTRACT" "$ROOT_CONTRACT"; then
    pass "Root and plugin communication contracts are identical"
  else
    fail "Root and plugin communication contracts differ"
  fi
else
  echo "[$GATE_NAME] SKIP: Root communication contract not found at $ROOT_CONTRACT"
fi

for phrase in \
  "Plain English first" \
  "Technical detail second" \
  "Never present options without recommending one." \
  "INFERRED_DEFAULT_DECISION" \
  "Pros:" \
  "Cons:"
do
  check_required_phrase "$PLUGIN_CONTRACT" "$phrase"
done

BARE_CHOICE_PATTERNS='Options: \(a\)|Would you like to:|What do you want to do\? \[|Keep or change\?'
SEARCH_PATHS=(
  "$PLUGIN_DIR/skills"
  "$PLUGIN_DIR/decision-engine"
)

if [[ -d "$PLANNING_DIR" ]]; then
  SEARCH_PATHS+=("$PLANNING_DIR")
fi

if rg -n "$BARE_CHOICE_PATTERNS" "${SEARCH_PATHS[@]}" > /tmp/vibeos-communication-bare-choices.txt 2>/dev/null; then
  fail "Bare choice patterns found:\n$(cat /tmp/vibeos-communication-bare-choices.txt)"
else
  pass "No bare choice shorthand found in runtime prompts or planning docs"
fi
rm -f /tmp/vibeos-communication-bare-choices.txt

while IFS= read -r file; do
  if validate_decision_blocks "$file" > /tmp/vibeos-communication-block.txt 2>&1; then
    rel_file="${file#$PLUGIN_DIR/}"
    pass "${rel_file:-$file} decision blocks include pros/cons and recommendation"
  else
    fail "$(cat /tmp/vibeos-communication-block.txt)"
  fi
done < <(find "$PLUGIN_DIR/skills" -name "SKILL.md" -type f | sort)
rm -f /tmp/vibeos-communication-block.txt

if [[ "$FAILURES" -gt 0 ]]; then
  echo "[$GATE_NAME] FAIL: $FAILURES communication issue(s) found"
  exit 1
fi

echo "[$GATE_NAME] PASS: Communication contract validation succeeded"
