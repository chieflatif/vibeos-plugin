# WO-006: Basic hooks.json (Layer 0)

## Status

`Complete`

## Phase

Phase 1: Plugin Foundation

## Objective

Create the hooks.json with real-time enforcement hooks: session start prerequisite check, secrets scan on file writes, frozen file protection, and stub/placeholder detection on Stop events.

## Scope

### In Scope
- [x] Create `hooks/hooks.json` with 4 hook entries
- [x] `SessionStart` command hook: check bash, python3, jq, git are available (warn if missing)
- [x] `PreToolUse` command hook (Write|Edit): secrets scan — block if hardcoded API keys detected
- [x] `PreToolUse` command hook (Write|Edit): frozen files — block writes to protected files
- [x] `Stop` prompt hook: check response for stubs/placeholders/shortcuts
- [x] Convert relevant hook .ref files from VibeOS-2 to executable scripts

### Out of Scope
- Test file protection hook (WO-015)
- Advanced hook configurations (later phases)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| WO-001 | Must complete first | Complete |
| VibeOS-2 reference/hooks/ | Source .ref files | Available |

## Acceptance Criteria

- [x] AC-1: Secrets scan detects AWS keys (AKIA...), OpenAI (sk-...), Anthropic (sk-ant-...), GitHub (ghp_...), Stripe (sk_live_...), generic assignments
- [x] AC-2: Stop prompt hook checks for NotImplementedError, TODO, FIXME, except: pass
- [x] AC-3: SessionStart checks for bash, python3, jq, git
- [x] AC-4: hooks.json is valid JSON (`jq . hooks/hooks.json` succeeds)
- [x] AC-5: All hook scripts pass `bash -n` syntax check

## Implementation Notes

**Hook architecture:**
- All hooks use `${CLAUDE_PLUGIN_ROOT}` for path resolution
- Secrets scan and frozen files both use JSON permissionDecision format (deny/allow)
- Frozen files reads project-specific list from `$CLAUDE_PROJECT_DIR/.claude/frozen-files.json` if it exists
- Stop hook uses `prompt` type (single-turn LLM check) not `command` type
- .env file protection included in both secrets-scan and frozen-files hooks

## Evidence

- [x] hooks.json valid JSON
- [x] All hook scripts pass `bash -n` syntax check
- [x] All hook scripts are executable (chmod +x)
- [x] hooks.json references scripts via `${CLAUDE_PLUGIN_ROOT}`
