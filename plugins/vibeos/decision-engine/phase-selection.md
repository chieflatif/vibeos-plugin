# Phase Selection Decision Tree

## PURPOSE
Determine which gate phases to enable based on team size and project complexity.

## INPUTS
- `governance.team_size`
- `governance.compliance_targets`
- `governance.production_urls`
- `stack.language` (for component-specific exits)

---

## PHASE DEFINITIONS

```

`wo_exit` is the universal user-facing audit phase. Small and enterprise projects may also expose specialized `wo_exit_*` phases, but `gate-runner.sh wo_exit` must remain valid through an explicit phase or compatibility fallback.
session_start     tier=0  "Run at session start — env checks, drift detection"
wo_entry          tier=1  "Run before starting any WO — prerequisites check"
pre_commit        tier=1  "Run before every commit — fast, blocking gates"
wo_exit_backend   tier=1  "Run after completing backend WO work"
wo_exit_frontend  tier=1  "Run after completing frontend WO work"
wo_exit_crosscutting tier=1  "Run after WO touching both frontend and backend"
wo_exit_governance tier=1  "Run after any WO — governance compliance"
post_deploy       tier=1  "Run after deploying — smoke tests, health checks"
full_audit        tier=2  "Comprehensive audit — all gates"
session_end       tier=0  "Run at session end — summary, uncommitted check"
```

---

## DECISION TREE

### Solo Developer (1 person)
```
IF team_size == "solo":
  ENABLE PHASES:
    session_start        ← light: env check only
    wo_entry             ← required: accepted plan must pass entry audit before coding
    pre_commit           ← always: fast gates on every commit
    wo_exit              ← combined: no backend/frontend split
    full_audit           ← on-demand: comprehensive check

  DISABLE PHASES:
    wo_exit_backend      ← merged into wo_exit
    wo_exit_frontend     ← merged into wo_exit
    wo_exit_crosscutting ← merged into wo_exit
    wo_exit_governance   ← merged into wo_exit
    post_deploy          ← IF production_urls exist: enable, ELSE skip
    session_end          ← skip: solo devs manage their own sessions

  SPECIAL:
    wo_exit combines gates from: wo_exit_backend + wo_exit_governance
    IF compliance != ["none"]:
      ADD wo_exit_governance as separate phase (compliance evidence needs explicit governance)
```

### Small Team (2-5 people)
```
IF team_size == "small":
  ENABLE PHASES:
    session_start        ← standard: env + drift + health
    wo_entry             ← standard: WO validation before work starts
    pre_commit           ← always: fast gates
    wo_exit_backend      ← IF language is backend-capable
    wo_exit_governance   ← always: governance compliance on every WO
    full_audit           ← on-demand
    session_end          ← standard: summary + uncommitted check

  DISABLE PHASES:
    wo_exit_frontend     ← IF project has frontend dirs: enable, ELSE skip
    wo_exit_crosscutting ← IF project has both frontend and backend: enable, ELSE skip
    post_deploy          ← IF production_urls exist: enable, ELSE skip

  SPECIAL:
    IF project has no frontend (source_dirs don't contain typical frontend patterns):
      SKIP wo_exit_frontend and wo_exit_crosscutting
      wo_exit_backend becomes the only component exit
```

### Enterprise (5+ people)
```
IF team_size == "enterprise":
  ENABLE PHASES:
    ALL 10 PHASES

  SPECIAL:
    wo_exit_crosscutting includes gates from both wo_exit_backend and wo_exit_frontend
    post_deploy always enabled (enterprise projects should have production URLs)
    IF production_urls is empty:
      WARN: "Enterprise team with no production URLs? Consider adding them."
      ENABLE post_deploy anyway (placeholder for when URLs are added)
```

---

## PHASE-TO-GATE ASSIGNMENT

Which gates run in which phases:

```
session_start:
  - validate-session-start.sh

wo_entry:
  - validate-work-order.sh (entry mode)
  - validate-infrastructure-manifest.sh

pre_commit:
  - validate-no-secrets.sh
  - validate-security-patterns.sh
  - detect-stubs-placeholders.py
  - validate-code-quality.sh

wo_exit_backend:
  - enforce-architecture.sh
  - validate-logging-patterns.sh
  - validate-documentation-completeness.sh
  - validate-test-integrity.sh
  - validate-code-quality.sh
  - validate-security-patterns.sh

wo_exit_frontend:
  (frontend build + test commands — project-specific, agent generates these)

wo_exit_crosscutting:
  includes: [wo_exit_backend, wo_exit_frontend]

wo_exit_governance:
  - validate-audit-completeness.sh (strict audit-loop enforcement)
  - validate-no-secrets.sh
  - detect-stubs-placeholders.py
  - validate-evidence-bundle.sh (IF compliance includes soc2)
  - validate-dependency-versions.sh
  - validate-dependencies.sh

post_deploy:
  - smoke-test.sh
  - health-check.sh

full_audit:
  includes: [pre_commit, wo_exit_backend, wo_exit_governance]
  additional:
    - validate-owasp-alignment.sh
    - validate-pii-handling.sh
    - validate-tenant-isolation.sh
    - validate-audit-completeness.sh

session_end:
  (session summary generation — agent handles this, no gate script)
```

---

## SOLO "wo_exit" MERGE RULES

When team_size == "solo", the separate exit phases merge into one `wo_exit`:

```
wo_exit (solo) = UNION OF:
  wo_exit_backend gates
  wo_exit_governance gates
  DEDUPLICATED (remove duplicate gate entries)
```

---

## OUTPUT

```json
{
  "selected_phases": ["<list of enabled phase names>"],
  "phase_config": {
    "<phase_name>": {
      "description": "<what this phase does>",
      "gates": ["<list of gate script filenames>"],
      "includes": ["<list of other phases to inherit gates from>"]
    }
  },
  "disabled_phases": [
    { "phase": "<name>", "reason": "<why disabled>" }
  ]
}
```
