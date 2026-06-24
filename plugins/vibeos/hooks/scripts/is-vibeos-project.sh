#!/usr/bin/env bash
# VibeOS Plugin — shared project-scope guard
#
# The VibeOS plugin is installed at USER scope, which means its SessionStart,
# UserPromptSubmit, PreToolUse, Stop, SessionEnd (etc.) hooks fire in EVERY
# project on the machine — not just VibeOS-managed repos. Without a guard the
# plugin injects routing/recovery context into unrelated projects, blocks
# innocent prompts (governance-guard), enforces file budgets and TDD rules on
# non-VibeOS code, and — via state-flush — even creates a stray .vibeos/
# directory in projects that never opted in (which then makes prereq-check
# misclassify them as VibeOS projects on the next session).
#
# This helper centralizes the "is this a VibeOS project?" decision so every
# hook can early-exit and stay inert outside VibeOS-managed projects.
#
# A project is VibeOS-managed iff it has either:
#   - .vibeos/config.json     (canonical marker written by /vibeos:discover|init)
#   - project-definition.json (discovered project, possibly pre-config)
#
# Escape hatch: export VIBEOS_FORCE_HOOKS=1 to force hooks on in any directory.
#
# Usage (from a hook script):
#   __VIBEOS_GUARD_LIB="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/is-vibeos-project.sh"
#   if [ -f "$__VIBEOS_GUARD_LIB" ]; then . "$__VIBEOS_GUARD_LIB"; is_vibeos_project || exit 0; fi

is_vibeos_project() {
  # Allow an explicit root argument; otherwise prefer the Claude-provided
  # project dir, then the current working directory.
  local root="${1:-${CLAUDE_PROJECT_DIR:-$PWD}}"

  # Explicit override always wins.
  if [ "${VIBEOS_FORCE_HOOKS:-}" = "1" ]; then
    return 0
  fi

  if [ -f "$root/.vibeos/config.json" ]; then
    return 0
  fi
  if [ -f "$root/project-definition.json" ]; then
    return 0
  fi

  return 1
}
