# Gate Selection Decision Tree

## PURPOSE
Determine which of the 34 gate scripts to enable based on project config. (gate-runner.sh is always included as the orchestrator.)

## INPUTS
- `stack.language`
- `stack.database`
- `governance.compliance_targets`
- `governance.production_urls`
- `governance.deployment_context` (prototype | production | customer-facing | scale)

---

## ALWAYS ENABLED

These gates are enabled for every project regardless of config:

```
PRE-COMMIT (6 gates — always on):
  validate-no-secrets.sh          tier=0  blocking=true
  validate-security-patterns.sh   tier=0  blocking=true
  detect-stubs-placeholders.py    tier=1  blocking=true
  validate-code-quality.sh        tier=1  blocking=true
  validate-tests-required.sh      tier=1  blocking=true   ← TDD: blocks when no test files
  validate-tests-pass.sh          tier=1  blocking=true   ← TDD: blocks when test command fails

CORE (5 gates — always on):
  validate-work-order.sh                  tier=1  blocking=true
  validate-development-plan-alignment.sh  tier=1  blocking=true  (wo_exit, full_audit)
  enforce-architecture.sh                 tier=1  blocking=true
  validate-logging-patterns.sh            tier=3  blocking=false
  validate-documentation-completeness.sh  tier=3  blocking=false

INFRASTRUCTURE (4 gates — always on):
  validate-infrastructure-manifest.sh  tier=2  blocking=false
  validate-dependency-versions.sh      tier=2  blocking=true
  validate-session-start.sh            tier=0  blocking=false
  validate-test-integrity.sh           tier=2  blocking=false  (quality of existing tests; tests-required enforces presence)

DEPENDENCIES (1 gate — always on):
  validate-dependencies.sh             tier=2  blocking=false
```

QUALITY & ARCHITECTURE (3 gates — always on):
  validate-code-complexity.sh        tier=2  blocking=false   ← function length, cyclomatic complexity, god objects
  validate-dev-environment.sh        tier=3  blocking=false   ← README, lockfile, CI config, task runner
  test-quality-gate.sh               tier=2  blocking=false   ← mock density, TDD compliance

VERIFICATION INTEGRITY (4 gates — always on, new in v2.0):
  validate-worktree-freshness.sh     tier=0  blocking=true    ← audit worktree staleness detection
  detect-testing-antipatterns.py     tier=1  blocking=true    ← silent pass guards, vacuous assertions, mock-only integration
  validate-wo-status-integrity.sh    tier=1  blocking=true    ← status inflation prevention (wo_exit only)
  validate-cross-boundary-contracts.sh  tier=1  blocking=true ← frontend-backend contract validation (cross-boundary only)

Total always-on: 20 gates

---

## CONDITIONAL GATES

### VC Audit Enhancement Gates (new — triggered by deployment_context or AI usage)
```
IF deployment_context IN ["production", "customer-facing", "scale"]:
  ENABLE:
    validate-observability.sh          tier=2  blocking=false
      config: REQUIRE_HEALTH=true
    validate-resilience-patterns.sh    tier=2  blocking=false
    validate-data-integrity.sh         tier=2  blocking=false
    validate-api-contracts.sh          tier=2  blocking=false
    validate-auth-boundaries.sh        tier=2  blocking=false

IF deployment_context == "customer-facing" OR deployment_context == "scale":
  MODIFY:
    validate-observability.sh          → REQUIRE_METRICS=true, tier=1
    validate-resilience-patterns.sh    → tier=1 blocking=true
    validate-auth-boundaries.sh        → tier=1 blocking=true

IF deployment_context == "scale":
  MODIFY:
    validate-observability.sh          → REQUIRE_TRACING=true
    validate-resilience-patterns.sh    → REQUIRE_CIRCUIT_BREAKERS=true
    validate-api-contracts.sh          → REQUIRE_SPEC=true REQUIRE_VERSIONING=true tier=1

IF deployment_context == "prototype":
  SKIP: validate-observability.sh, validate-resilience-patterns.sh, validate-api-contracts.sh
  ENABLE (advisory only):
    validate-data-integrity.sh         tier=3  blocking=false
    validate-auth-boundaries.sh        tier=3  blocking=false
```

### AI Integration Gates
```
IF ai_provider is set OR features mention AI/LLM/ML:
  ENABLE:
    validate-ai-integration.sh         tier=2  blocking=false
  SEE: decision-engine/ai-integration-patterns.md for tier upgrades based on ai_depth

IF ai_depth IN ["core_pipeline", "autonomous", "model_owner"]:
  MODIFY:
    validate-ai-integration.sh         → REQUIRE_COST_CONTROLS=true  tier=1  blocking=true
```

### Database Gates
```
IF database IN [postgresql, mysql, sqlite]:
  ENABLE: validate-tenant-isolation.sh
    tier = IF compliance includes "gdpr" THEN 1 ELSE 2
    blocking = IF compliance includes "gdpr" THEN true ELSE false

IF database == "none" OR database == "redis-only" OR database == "mongodb":
  SKIP: validate-tenant-isolation.sh
```

### Compliance Gates
```
IF compliance includes "soc2":
  ENABLE:
    validate-evidence-bundle.sh      tier=1  blocking=true
    validate-audit-completeness.sh   tier=1  blocking=true
    validate-pii-handling.sh         tier=2  blocking=false

IF compliance includes "gdpr":
  ENABLE:
    validate-pii-handling.sh         tier=1  blocking=true   (upgrade tier if already enabled)
    validate-tenant-isolation.sh     tier=1  blocking=true   (upgrade tier if already enabled)

IF compliance includes "owasp":
  ENABLE:
    validate-owasp-alignment.sh      tier=1  blocking=true
  MODIFY:
    validate-security-patterns.sh    → set STRICT_MODE=true

IF compliance == ["none"]:
  ENABLE (advisory only):
    validate-evidence-bundle.sh      tier=3  blocking=false
    validate-audit-completeness.sh   tier=3  blocking=false
    validate-pii-handling.sh         tier=3  blocking=false
    validate-owasp-alignment.sh      tier=3  blocking=false
```

### Cross-Boundary Validation
```
IF stack.language contains both a backend language AND a frontend framework (e.g., Python + TypeScript)
OR IF directories matching both backend (src/, app/, server/) and frontend (frontend/, client/, web/) exist
THEN enable:
  validate-cross-boundary-contracts.sh  tier=1  blocking=true  (wo_exit and full_audit)
```

### Post-Deploy Gates
```
IF production_urls is not empty AND production_urls != ["none"]:
  ENABLE:
    smoke-test.sh                    tier=1  blocking=true
    health-check.sh                  tier=1  blocking=true

IF production_urls is empty OR production_urls == ["none"]:
  SKIP: smoke-test.sh, health-check.sh
```

### Deployment Context Gates (Production Readiness)
```
IF deployment_context IN ["production", "customer-facing", "scale"]:
  ENABLE: validate-production-readiness.sh   tier=1  blocking=true
  ENV: PROJECT_DEFINITION=project-definition.json  (or path from project root)

IF deployment_context == "prototype":
  SKIP: validate-production-readiness.sh  (gate skips when prototype — safe to copy script regardless)
```

---

## LANGUAGE-SPECIFIC CONFIG

These don't enable/disable gates but configure how they run:

```
IF language == "python":
  detect-stubs-placeholders.py  → --language python
  validate-code-quality.sh      → LINTER=ruff
  validate-dependencies.sh      → PACKAGE_FILE=pyproject.toml or requirements.txt

IF language == "typescript" OR language == "javascript":
  detect-stubs-placeholders.py  → --language javascript
  validate-code-quality.sh      → LINTER=eslint
  validate-dependencies.sh      → PACKAGE_FILE=package.json

IF language == "go":
  detect-stubs-placeholders.py  → --language go
  validate-code-quality.sh      → LINTER=golangci-lint
  validate-dependencies.sh      → PACKAGE_FILE=go.mod

IF language == "rust":
  detect-stubs-placeholders.py  → --language rust
  validate-code-quality.sh      → LINTER=clippy
  validate-dependencies.sh      → PACKAGE_FILE=Cargo.toml

IF language == "java":
  detect-stubs-placeholders.py  → --language java
  validate-code-quality.sh      → LINTER=checkstyle
  validate-dependencies.sh      → PACKAGE_FILE=pom.xml or build.gradle
```

---

## OUTPUT

```json
{
  "selected_gates": [
    {
      "script": "<filename>",
      "tier": 0-3,
      "blocking": true/false,
      "config": { "<env_var>": "<value>" }
    }
  ],
  "total_enabled": <count>,
  "conditional_enabled": ["<list of conditionally enabled gates>"],
  "skipped": ["<list of skipped gates with reason>"]
}
```
