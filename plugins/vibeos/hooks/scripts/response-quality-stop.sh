#!/usr/bin/env bash
# VibeOS Plugin — Response Quality Stop Review
# Reviews only the most recent assistant response and blocks session stop
# only when concrete code-quality markers are present.
#
# Hook type: Stop
# Output format when blocking: JSON with decision = block
# Framework version: 2.2.0
# Note: No set -euo pipefail — hook reads stdin and uses || fallbacks
# intentionally. This is per hook convention for VibeOS hooks.
FRAMEWORK_VERSION="2.2.0"

INPUT=$(cat)
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // ""' 2>/dev/null || echo "")

if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
  exit 0
fi

LAST_RESPONSE=$(
  jq -rs '
    [
      .[]
      | select(.type == "assistant" and (.message.role? == "assistant"))
      | (.message.content // [])
      | if type == "array" then .[] else empty end
      | select(.type == "text")
      | .text
    ]
    | last // ""
  ' "$TRANSCRIPT_PATH" 2>/dev/null || echo ""
)

if [ -z "$LAST_RESPONSE" ]; then
  exit 0
fi

export LAST_RESPONSE
FINDINGS=$(
  python3 - <<'PY'
import os
import re

text = os.environ.get("LAST_RESPONSE", "")

code_context = bool(
    re.search(
        "\\x60\\x60\\x60|^\\s*(def|class|function|const|let|var|import|from|fn|func|public\\s+class|interface|type|except|throw\\s+new\\s+Error|panic\\s*\\()",
        text,
        re.MULTILINE,
    )
)

if not code_context:
    raise SystemExit(0)

patterns = [
    ("NotImplementedError", re.compile(r"\bNotImplementedError\b")),
    ("TODO/FIXME/HACK/XXX comment", re.compile(r"(?im)^\s*(#|//|/\*|\*)\s*(TODO|FIXME|HACK|XXX)\b")),
    ("commented placeholder marker", re.compile(r"(?im)^\s*(#|//|/\*|\*)\s*.*\bplaceholder\b")),
    ("commented incomplete-code marker", re.compile(r"(?im)^\s*(#|//|/\*|\*)\s*(implement later|add here)\b")),
    (
        "pass-only Python function",
        re.compile(r"(?ms)^\s*def\s+\w+\s*\([^)]*\)\s*:\s*\n\s+pass\b|^\s*def\s+\w+\s*\([^)]*\)\s*:\s*pass\b"),
    ),
    (
        "ellipsis-only Python function",
        re.compile(r"(?ms)^\s*def\s+\w+\s*\([^)]*\)\s*:\s*\n\s*\.\.\.\s*$|^\s*def\s+\w+\s*\([^)]*\)\s*:\s*\.\.\.\s*$"),
    ),
    (
        "swallowed Python exception",
        re.compile(r"(?ms)^\s*except(?:\s+[\w\., ()]+)?\s*:\s*\n\s+pass\b|^\s*except(?:\s+[\w\., ()]+)?\s*:\s*pass\b"),
    ),
    ("empty JS/TS function body", re.compile(r"function\s+\w+\s*\([^)]*\)\s*\{\s*\}|=>\s*\{\s*\}")),
    (
        "throw new Error('not implemented')",
        re.compile(r"throw\s+new\s+Error\s*\(\s*['\"][^'\"]*not\s+implemented[^'\"]*['\"]", re.IGNORECASE),
    ),
    (
        "panic('not implemented')",
        re.compile(r"panic\s*\(\s*['\"][^'\"]*not\s+implemented[^'\"]*['\"]", re.IGNORECASE),
    ),
    ("todo!()/unimplemented!() macro", re.compile(r"\b(todo|unimplemented)!\s*\(", re.IGNORECASE)),
    ("UnsupportedOperationException", re.compile(r"UnsupportedOperationException")),
]

findings = [name for name, pattern in patterns if pattern.search(text)]
if findings:
    print("\n".join(findings))
PY
)

if [ -z "$FINDINGS" ]; then
  exit 0
fi

SUMMARY=$(printf '%s\n' "$FINDINGS" | paste -sd '; ' - | cut -c1-500)

jq -n \
  --arg reason "VibeOS stop review found code-quality markers in the last assistant response: $SUMMARY. Flag them to the user and fix them before ending the turn." \
  '{
    "decision": "block",
    "reason": $reason
  }'
