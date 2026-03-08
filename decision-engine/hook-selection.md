# Hook Selection Decision Tree

## PURPOSE
Determine which hooks to enable based on agent type and project config.

## INPUTS
- `agent_type` (from Phase 1)
- `governance.production_urls`
- `governance.frozen_files`
- `governance.compliance_targets`

---

## HOOK INVENTORY

| Hook | Event Type | Purpose | LOC |
|---|---|---|---|
| secrets-scan.sh | pre-tool | Block writes containing secrets/credentials | ~80 |
| frozen-files.sh | pre-tool | Block edits to protected files | ~40 |
| staging-target.sh | pre-tool | Block commands targeting production URLs | ~50 |
| governance-guard.sh | user-prompt | Block governance-violating prompts | ~50 |
| validate-audit-result.sh | subagent | Validate audit subagent output quality | ~80 |
| session-start.sh | session | Env setup, drift detection, health probe | ~60 |
| session-resume.sh | session | Warn about uncommitted changes | ~30 |
| capture-failure.sh | post-tool | Capture evidence on tool failures | ~25 |

---

## DECISION TREE BY AGENT TYPE

### Claude Code
```
IF agent_type == "claude-code":

  ALWAYS ENABLE:
    secrets-scan.sh        ← pre-tool: catches secrets before they're written
    session-start.sh       ← session: environment validation on every session
    session-resume.sh      ← session: uncommitted change warnings
    capture-failure.sh     ← post-tool: evidence capture on failures

  CONDITIONAL:
    IF frozen_files is not empty AND frozen_files != ["none"]:
      ENABLE: frozen-files.sh
      CONFIG: FROZEN_FILES="{comma-separated list from Q14}"

    IF production_urls is not empty AND production_urls != ["none"]:
      ENABLE: staging-target.sh
      CONFIG: PRODUCTION_URLS="{comma-separated list from Q15}"

    IF compliance_targets != ["none"]:
      ENABLE: governance-guard.sh
      CONFIG: BLOCKED_PATTERNS based on compliance level

    IF project uses subagents:
      ENABLE: validate-audit-result.sh
      REASON: validate subagent audit output before allowing the workflow to proceed
```

### Cursor
```
IF agent_type == "cursor":

  HOOKS: NONE
  REASON: Cursor does not support hook scripts.

  ALTERNATIVE: Embed governance rules directly in .cursorrules:
    - Secrets patterns → "NEVER include these patterns in code: AWS keys (AKIA...), ..."
    - Frozen files → "NEVER edit these files: {list}"
    - Production URLs → "NEVER run commands targeting: {list}"
    - Governance rules → inline in .cursorrules text

  The .cursorrules file acts as the entire governance surface for Cursor.
```

### Codex
```
IF agent_type == "codex":

  HOOKS: NONE
  REASON: Codex CLI does not support hook scripts.

  ALTERNATIVE: Embed governance rules in AGENTS.md:
    - Secrets patterns → "Before writing any file, verify it contains no credentials"
    - Frozen files → "These files are read-only: {list}"
    - Production URLs → "Never target production: {list}"
    - Governance rules → structured sections in AGENTS.md

  The AGENTS.md file acts as the entire governance surface for Codex.
```

---

## HOOK CONFIGURATION

### secrets-scan.sh
```
CONFIG:
  SCAN_PATTERNS:
    ALWAYS: AWS keys (AKIA), API tokens, JWTs, private keys, connection strings
    IF cloud_provider == "azure": Azure connection strings, SAS tokens
    IF cloud_provider == "aws": AWS secret keys, session tokens
    IF cloud_provider == "gcp": GCP service account keys
  TOOL_MATCHER: Write, Edit, Bash
  TIMEOUT: 5000ms
```

### frozen-files.sh
```
CONFIG:
  FROZEN_FILES: from Q14
  TOOL_MATCHER: Write, Edit
  TIMEOUT: 2000ms
```

### staging-target.sh
```
CONFIG:
  PRODUCTION_URLS: from Q15
  TOOL_MATCHER: Bash
  TIMEOUT: 2000ms
```

### governance-guard.sh
```
CONFIG:
  BLOCKED_PATTERNS:
    ALWAYS: "skip.*gate", "ignore.*test", "disable.*hook", "bypass.*check"
    IF compliance != ["none"]: "skip.*audit", "no.*evidence", "force.*deploy"
  TOOL_MATCHER: (user prompt event — no tool matcher needed)
  TIMEOUT: 3000ms
```

### validate-audit-result.sh
```
CONFIG:
  REQUIRED_SECTIONS: ["summary", "gates_run", "pass_count", "fail_count"]
  MIN_GATES_RUN: 3
  TOOL_MATCHER: subagent result event
  TIMEOUT: 5000ms
```

### session-start.sh
```
CONFIG:
  REQUIRED_DOCS:
    ALWAYS: CLAUDE.md (or .cursorrules or AGENTS.md)
    IF wo_dir exists: WO-INDEX.md
  HEALTH_URL: from production_urls (first URL + /health) or "none"
  CHECK_GIT_STATE: true
  CHECK_ENV_FILE: true
  TIMEOUT: 10000ms
```

### session-resume.sh
```
CONFIG:
  CHECK_UNCOMMITTED: true
  CHECK_STASH: true
  TIMEOUT: 5000ms
```

### capture-failure.sh
```
CONFIG:
  EVIDENCE_DIR: ".claude/evidence/" (Claude Code) or "evidence/" (other)
  CAPTURE_STDERR: true
  CAPTURE_EXIT_CODE: true
  TIMEOUT: 3000ms
```

---

## SETTINGS.JSON HOOK WIRING (Claude Code only)

The agent must generate `.claude/settings.json` with hook configuration.
Reference: `reference/claude/settings.json.ref`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "bash .claude/hooks/pre-tool/secrets-scan.sh" }
        ]
      }
    ],
    "PostToolUseFailure": [...],
    "UserPromptSubmit": [...],
    "SubagentStop": [...],
    "SessionStart": [...]
  }
}
```

See `reference/claude/settings.json.ref` for the complete wiring pattern.

---

## OUTPUT

```json
{
  "selected_hooks": [
    {
      "name": "<hook name>",
      "event_type": "<pre-tool|post-tool|user-prompt|subagent|session>",
      "config": { "<config_key>": "<value>" }
    }
  ],
  "embedded_governance": {
    "in_cursorrules": true/false,
    "in_agents_md": true/false
  },
  "settings_json_required": true/false
}
```
