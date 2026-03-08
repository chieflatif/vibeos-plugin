# WO-000: Technical Spike Results

**Date:** 2026-03-07
**Method:** Direct review of official Claude Code documentation at code.claude.com
**Sources verified:**
- https://code.claude.com/docs/en/plugins (Create plugins)
- https://code.claude.com/docs/en/skills (Extend Claude with skills)
- https://code.claude.com/docs/en/sub-agents (Create custom subagents)
- https://code.claude.com/docs/en/hooks (Hooks reference — full page)

---

## Spike 1: Plugin Manifest Schema

**Status: VALIDATED**

Plugin manifest is `.claude-plugin/plugin.json`. Only `name` is required.

**Manifest fields (from official quickstart):**

| Field | Required | Purpose |
|---|---|---|
| `name` | Yes | Unique identifier, used for skill namespace (`/name:skill`) |
| `description` | No | Shown in plugin manager |
| `version` | No | Semantic versioning |
| `author` | No | `{name, email, url}` |
| `homepage` | No | Documentation URL |
| `repository` | No | Source code URL |
| `license` | No | License identifier |

**Plugin directory structure (from official docs):**

| Directory | Location | Purpose |
|---|---|---|
| `.claude-plugin/` | Plugin root | Contains `plugin.json` manifest only |
| `commands/` | Plugin root | Skills as Markdown files (legacy, still works) |
| `agents/` | Plugin root | Custom agent definitions |
| `skills/` | Plugin root | Agent Skills with SKILL.md files |
| `hooks/` | Plugin root | Event handlers in `hooks.json` |
| `.mcp.json` | Plugin root | MCP server configurations |
| `.lsp.json` | Plugin root | LSP server configurations |
| `settings.json` | Plugin root | Default settings (currently only `agent` key supported) |

**Key finding:** Directories at plugin root are auto-discovered. The manifest does NOT need to list them explicitly — if `skills/` exists, skills are loaded. If `agents/` exists, agents are loaded. The manifest is primarily for metadata.

**Common mistake from docs:** "Don't put commands/, agents/, skills/, or hooks/ inside the .claude-plugin/ directory. Only plugin.json goes inside .claude-plugin/."

---

## Spike 2: Skills vs Commands

**Status: VALIDATED — Skills is correct**

From official docs: "Custom commands have been merged into skills. A file at `.claude/commands/review.md` and a skill at `.claude/skills/review/SKILL.md` both create `/review` and work the same way."

- **Skills** (`skills/<name>/SKILL.md`): Modern approach. Directory-based. Supports supporting files, frontmatter, model control, subagent execution.
- **Commands** (`commands/<name>.md`): Legacy. Still works. Single markdown files.

**Skill frontmatter fields (complete list from docs):**

| Field | Required | Description |
|---|---|---|
| `name` | No | Display name. If omitted, uses directory name |
| `description` | Recommended | What the skill does. Claude uses this for auto-invocation |
| `argument-hint` | No | Hint for autocomplete (e.g., `[issue-number]`) |
| `disable-model-invocation` | No | `true` = only manual `/invoke`. Default: `false` |
| `user-invocable` | No | `false` = hidden from `/` menu. Default: `true` |
| `allowed-tools` | No | Tools Claude can use without permission when skill active |
| `model` | No | Model to use when skill active |
| `context` | No | Set to `fork` to run in forked subagent context |
| `agent` | No | Which subagent type when `context: fork` (e.g., `Explore`, `Plan`, custom) |
| `hooks` | No | Hooks scoped to this skill's lifecycle |

**Available string substitutions in skills:**

| Variable | Description |
|---|---|
| `$ARGUMENTS` | All arguments passed when invoking |
| `$ARGUMENTS[N]` / `$N` | Specific argument by 0-based index |
| `${CLAUDE_SESSION_ID}` | Current session ID |
| `${CLAUDE_SKILL_DIR}` | Directory containing the SKILL.md file |

**Note:** `${CLAUDE_SKILL_DIR}` is per-skill, not plugin-wide. For plugin-root scripts, use `${CLAUDE_PLUGIN_ROOT}` in hooks (see Spike 4).

---

## Spike 3: Agent Dispatch

**Status: VALIDATED — all features confirmed**

Agents go in `agents/` directory as .md files with YAML frontmatter.

**Subagent frontmatter fields (complete list from official docs):**

| Field | Required | Description |
|---|---|---|
| `name` | Yes | Unique identifier, lowercase letters and hyphens |
| `description` | Yes | When Claude should delegate to this subagent |
| `tools` | No | Allowlist of tools. Inherits all tools if omitted |
| `disallowedTools` | No | **CONFIRMED EXISTS.** Denylist, removed from inherited/specified list |
| `model` | No | `sonnet`, `opus`, `haiku`, or `inherit`. Default: `inherit` |
| `permissionMode` | No | `default`, `acceptEdits`, `dontAsk`, `bypassPermissions`, `plan` |
| `maxTurns` | No | **CONFIRMED EXISTS.** Maximum agentic turns before stop |
| `skills` | No | Skills preloaded into subagent context at startup |
| `mcpServers` | No | MCP servers available to this subagent |
| `hooks` | No | Lifecycle hooks scoped to this subagent |
| `memory` | No | Persistent memory: `user`, `project`, or `local` |
| `background` | No | `true` to always run as background task |
| `isolation` | No | **CONFIRMED: `worktree`** — runs in temporary git worktree |

**Critical constraint confirmed:** "Subagents cannot spawn other subagents."

**Agent invocation:**
- Agents appear in `/agents` interface
- Claude auto-delegates based on `description` field
- Explicit: "Use the X subagent to..."
- Namespaced as `plugin-name:agent-name` for plugin agents
- Returns results to main conversation (freeform text)

**Key clarification on `tools` vs `disallowedTools`:**
Both fields exist. Use `tools` for allowlist, `disallowedTools` for denylist. From docs example:
```yaml
tools: Read, Grep, Glob, Bash
disallowedTools: Write, Edit
```

**Impact on plan:** Our original audit agent design was correct:
- `disallowedTools: Write, Edit, Agent` — confirmed valid
- `isolation: worktree` — confirmed valid
- `maxTurns` — confirmed valid
- `memory: project` — confirmed valid (useful for auditors tracking patterns)

---

## Spike 4: Hook Exit Codes

**Status: VALIDATED**

**Exit codes (from official hooks reference):**

| Exit Code | Meaning |
|---|---|
| **0** | Success — action proceeds. Stdout parsed for JSON. For UserPromptSubmit/SessionStart, stdout added as context |
| **2** | Blocking error — stderr fed to Claude as error. PreToolUse blocks tool call, UserPromptSubmit rejects prompt |
| **Any other** | Non-blocking error — stderr shown in verbose mode, execution continues |

**JSON output option (exit 0 + JSON on stdout):**
For PreToolUse: `hookSpecificOutput.permissionDecision` = `"allow"` / `"deny"` / `"ask"`
For other events: `decision` = `"block"`, `reason` = explanation

**Hook event types (17 events from official docs):**

| Event | When it fires | Matcher |
|---|---|---|
| `SessionStart` | Session begins or resumes | How started: startup, resume, clear, compact |
| `UserPromptSubmit` | Prompt submitted, before Claude processes | No matcher support |
| `PreToolUse` | Before tool call. Can block it | Tool name |
| `PermissionRequest` | Permission dialog appears | Tool name |
| `PostToolUse` | After tool call succeeds | Tool name |
| `PostToolUseFailure` | After tool call fails | Tool name |
| `Notification` | Claude Code sends notification | Notification type |
| `SubagentStart` | Subagent spawned | Agent type name |
| `SubagentStop` | Subagent finishes | Agent type name |
| `Stop` | Claude finishes responding | No matcher support |
| `TeammateIdle` | Agent team teammate going idle | No matcher support |
| `TaskCompleted` | Task marked as completed | No matcher support |
| `InstructionsLoaded` | CLAUDE.md or rules loaded | No matcher support |
| `ConfigChange` | Config file changes during session | Config source |
| `WorktreeCreate` | Worktree being created | No matcher support |
| `WorktreeRemove` | Worktree being removed | No matcher support |
| `PreCompact` | Before context compaction | Trigger: manual, auto |
| `SessionEnd` | Session terminates | Why ended |

**Hook types (4):**
- `command`: Shell script execution
- `prompt`: Single-turn LLM evaluation
- `agent`: Multi-turn subagent verification with tool access
- `http`: POST to HTTP endpoint

**Plugin hooks:** Defined in `hooks/hooks.json` at plugin root. Format identical to settings.json hooks but wrapped in optional `description` + `hooks` object.

**Critical finding — `${CLAUDE_PLUGIN_ROOT}` EXISTS:**
From official hooks reference, section "Reference scripts by path":
> `${CLAUDE_PLUGIN_ROOT}`: the plugin's root directory, for scripts bundled with a plugin.

Example from docs:
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "hooks": [{
        "type": "command",
        "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh"
      }]
    }]
  }
}
```

Also available: `$CLAUDE_PROJECT_DIR` for project root.

---

## Plugin Installation

**From official docs:**
- **Development:** `claude --plugin-dir ./my-plugin` (loads plugin without installation)
- **In-session:** `/plugin install` (from marketplace or path)
- **NO `claude plugin install` CLI command** — use `--plugin-dir` for dev

Multiple plugins: `claude --plugin-dir ./plugin-one --plugin-dir ./plugin-two`

---

## Summary: What's Confirmed vs. Original Plan

| Item | Original Plan | Official Docs | Status |
|---|---|---|---|
| Plugin system exists | Yes | **Yes** — `.claude-plugin/plugin.json` | Confirmed |
| Skills directory | `skills/` | `skills/` with SKILL.md | Confirmed |
| Agent directory | `agents/` | `agents/` with .md frontmatter | Confirmed |
| Hooks in plugin | `hooks/hooks.json` | `hooks/hooks.json` | Confirmed |
| `disallowedTools` for agents | Used in plan | **Confirmed exists** | Confirmed |
| `maxTurns` for agents | Used in plan | **Confirmed exists** | Confirmed |
| `isolation: worktree` | Used in plan | **Confirmed exists** | Confirmed |
| `memory` for agents | Not in original plan | **Exists** — user/project/local | New capability |
| Hook exit codes | 0=allow, 2=block | 0=allow, 2=block | Confirmed |
| `${CLAUDE_PLUGIN_ROOT}` | Originally `VIBEOS_PLUGIN_ROOT` | **Confirmed exists** in hooks | Confirmed (renamed) |
| `${CLAUDE_SKILL_DIR}` | Not in plan | **Exists** for skill scripts | New capability |
| `$CLAUDE_PROJECT_DIR` | Not in plan | **Exists** for project root | New capability |
| Plugin install CLI | `claude plugin install` | **Does NOT exist** — use `--plugin-dir` | Corrected |
| Subagents can't spawn subagents | In plan | **Confirmed** | Confirmed |
| `context: fork` for skills | Not in plan | **Exists** — run skill in isolated subagent | New capability |
| `background` field for agents | Not in plan | **Exists** — run as background task | New capability |
| `agent` hook type | Not in plan | **Exists** — multi-turn verification subagent | New capability |

## Corrections Applied to Plan

1. ~~`VIBEOS_PLUGIN_ROOT`~~ → `${CLAUDE_PLUGIN_ROOT}` (already renamed in WO files)
2. ~~`claude plugin install`~~ → `claude --plugin-dir ./vibeos-plugin` for development
3. Audit agents: `disallowedTools: Write, Edit, Agent` is valid (original plan was correct, interim "correction" to allowlist was wrong)
4. Plugin manifest is minimal — directories auto-discovered, no need to list them explicitly

## New Capabilities Discovered

These don't change Phase 1 but unlock options for later phases:
- **`memory: project`** for agents — auditors can build persistent knowledge base across sessions
- **`context: fork`** for skills — `/vibeos:build` could run in forked context naturally
- **`agent` hook type** — hooks can spawn verification subagents, not just run shell scripts
- **`background` agents** — audit agents could run in background while build continues
- **`settings.json` at plugin root** — can set a default agent as main thread

## Conclusion

**All 4 core assumptions are validated against official documentation.** The architecture is sound. Minor naming corrections applied. Several new capabilities discovered that enhance later phases.

No architecture revision required. Proceed to Phase 1.
