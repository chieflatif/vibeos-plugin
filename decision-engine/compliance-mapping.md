# Compliance Mapping Decision Tree

## PURPOSE
Map compliance targets to specific gates, tiers, evidence requirements, and documentation.

## INPUTS
- `governance.compliance_targets`
- `governance.team_size`

---

## SOC 2 TYPE II

### When Selected
```
IF compliance includes "soc2":
```

### Gates
```
ENABLE (tier 1, blocking):
  validate-evidence-bundle.sh     ← Every WO must produce evidence
  validate-audit-completeness.sh  ← Audit trail must be continuous

ENABLE (tier 2, blocking):
  validate-pii-handling.sh        ← PII must be handled correctly

UPGRADE (if already enabled):
  validate-no-secrets.sh          → tier 1 (already default)
  validate-security-patterns.sh   → tier 1 (already default)
```

### Evidence Requirements
```
EVERY WO must produce an evidence bundle containing:
  - summary.md      ← What was done, why, by whom
  - metadata.json   ← Machine-parseable: WO number, dates, gate results, commit SHA
  - gate-results/   ← Output from gate-runner for each phase run

EVIDENCE_DIR: "docs/evidence/{WO_NUMBER}/"

The validate-evidence-bundle.sh gate checks:
  1. summary.md exists and is non-empty
  2. metadata.json is valid JSON with required fields
  3. gate-results/ contains at least one result file
```

### Documentation
```
REQUIRE in CLAUDE.md / agent config:
  - "Every Work Order must produce an evidence bundle"
  - "Evidence bundles are stored in docs/evidence/{WO_NUMBER}/"
  - "Use validate-evidence-bundle.sh to verify evidence before WO completion"

REQUIRE in WO-TEMPLATE.md:
  - "Evidence Location" field
  - "Audit Notes" section
```

### Governance Docs
```
GENERATE:
  - docs/ADR-TEMPLATE.md (architecture decisions must be documented)
  - docs/planning/WO-INDEX.md with "Evidence" column
```

---

## GDPR

### When Selected
```
IF compliance includes "gdpr":
```

### Gates
```
ENABLE (tier 1, blocking):
  validate-pii-handling.sh        ← PII detection in code and logs
  validate-tenant-isolation.sh    ← Data isolation verification

UPGRADE (if already enabled at lower tier):
  validate-pii-handling.sh        → tier 1
  validate-tenant-isolation.sh    → tier 1
```

### PII Configuration
```
validate-pii-handling.sh CONFIG:
  STRICT_MODE: true
  PII_PATTERNS:
    - email addresses in logs
    - phone numbers in logs
    - names in error messages
    - IP addresses logged without consent
    - user IDs exposed in URLs without necessity
  SCAN_DIRS: {source_dirs} + logs/
```

### Tenant Isolation Configuration
```
validate-tenant-isolation.sh CONFIG:
  TENANT_FIELD: "tenant_id" (default, customizable)
  CHECK:
    - SQL queries without tenant_id in WHERE clause
    - ON CONFLICT without tenant_id
    - Hardcoded tenant IDs
    - SELECT * without tenant scope
    - UPDATE/DELETE without tenant_id filter
```

### Documentation
```
REQUIRE in CLAUDE.md / agent config:
  - "All database queries must include tenant_id"
  - "PII must never appear in log output"
  - "User data access requires consent verification"

GENERATE:
  - docs/INFRASTRUCTURE-MANIFEST.md with "Data Privacy" section:
    - Where PII is stored
    - Data retention policies
    - Erasure support mechanism
    - Consent tracking location
```

---

## OWASP TOP 10

### When Selected
```
IF compliance includes "owasp":
```

### Gates
```
ENABLE (tier 1, blocking):
  validate-owasp-alignment.sh     ← OWASP Top 10 checks

UPGRADE:
  validate-security-patterns.sh   → STRICT_MODE=true
    Additional patterns in strict mode:
    - verify=False (SSL bypass)
    - shell=True (command injection)
    - pickle.loads (deserialization)
    - yaml.load without Loader (unsafe YAML)
    - marshal.loads (code execution)
    - __import__ (dynamic imports)
```

### OWASP Gate Checks
```
validate-owasp-alignment.sh scans for:

A01 Broken Access Control:
  - Missing auth decorators on endpoints
  - Direct object references without ownership check

A02 Cryptographic Failures:
  - Hardcoded secrets
  - Weak hashing (MD5, SHA1 for passwords)
  - HTTP URLs (not HTTPS)

A03 Injection:
  - SQL string formatting
  - OS command construction from user input
  - LDAP injection patterns

A04 Insecure Design:
  - Missing rate limiting indicators
  - No input validation on endpoints

A05 Security Misconfiguration:
  - DEBUG=True in non-test files
  - CORS allow-all (*) in non-dev config
  - Default credentials

A06 Vulnerable Components:
  (handled by validate-dependencies.sh)

A07 Auth Failures:
  - Credential comparison without constant-time
  - Session tokens in URLs

A08 Data Integrity:
  - Unsigned data in security contexts
  - Missing CSRF tokens

A09 Logging Failures:
  - Security events not logged
  - PII in logs

A10 SSRF:
  - User-controlled URLs in server requests
  - DNS rebinding patterns
```

### Documentation
```
REQUIRE in CLAUDE.md / agent config:
  - "All endpoints must validate input"
  - "Use parameterized queries — never string formatting for SQL"
  - "Never use eval(), exec(), or pickle.loads() with untrusted input"
  - Security section with OWASP reference

GENERATE:
  - Architecture rules for injection prevention
  - Security patterns in .cursorrules / AGENTS.md (if not Claude Code)
```

---

## NO COMPLIANCE TARGETS

### When Selected
```
IF compliance == ["none"]:
```

### Gates
```
ALL compliance gates set to tier 3 (advisory only):
  validate-evidence-bundle.sh      tier=3  blocking=false
  validate-audit-completeness.sh   tier=3  blocking=false
  validate-pii-handling.sh         tier=3  blocking=false
  validate-owasp-alignment.sh      tier=3  blocking=false
  validate-tenant-isolation.sh     tier=3  blocking=false

These gates still RUN but never block. This gives visibility without overhead.
```

### Documentation
```
NOTE in setup summary:
  "Compliance gates are set to advisory mode. They will report issues but won't block."
  "To enable compliance enforcement later, update tier values in quality-gate-manifest.json."
```

---

## COMBINED COMPLIANCE

When multiple standards are selected, rules COMBINE (union, not override):

```
IF compliance includes ["soc2", "gdpr"]:
  validate-pii-handling.sh → tier 1 (highest of both)
  validate-evidence-bundle.sh → tier 1 (SOC 2)
  validate-tenant-isolation.sh → tier 1 (GDPR)
  validate-audit-completeness.sh → tier 1 (SOC 2)
  PII_PATTERNS: GDPR strict mode patterns
  Evidence bundles: SOC 2 format

IF compliance includes ["soc2", "owasp"]:
  validate-security-patterns.sh → tier 1, STRICT_MODE=true (OWASP)
  validate-owasp-alignment.sh → tier 1 (OWASP)
  validate-evidence-bundle.sh → tier 1 (SOC 2)
  Evidence bundles must include security scan results

IF compliance includes ["soc2", "gdpr", "owasp"]:
  ALL compliance gates → tier 1
  ALL strict modes → enabled
  FULL evidence requirements
  FULL PII scanning
  FULL OWASP scanning
```

---

## SOLO DEVELOPER COMPLIANCE WARNING

```
IF team_size == "solo" AND compliance != ["none"]:
  WARN to user:
    "Running full compliance governance as a solo developer adds significant overhead.
     Recommendation: Start with compliance gates at tier 2 (important but non-blocking).
     You can upgrade to tier 1 (blocking) when your team grows.

     Would you like to:
     a) Keep compliance at tier 1 (full enforcement)
     b) Set compliance gates to tier 2 (important but non-blocking) — RECOMMENDED
     c) Set compliance gates to tier 3 (advisory only)"

  IF user chooses b:
    Downgrade all compliance-specific gates to tier 2, blocking=false
  IF user chooses c:
    Downgrade all compliance-specific gates to tier 3, blocking=false
```

---

## OUTPUT

```json
{
  "compliance_config": {
    "soc2": {
      "enabled": true/false,
      "gates": [...],
      "evidence_required": true/false,
      "evidence_dir": "path"
    },
    "gdpr": {
      "enabled": true/false,
      "gates": [...],
      "pii_strict": true/false,
      "tenant_field": "string"
    },
    "owasp": {
      "enabled": true/false,
      "gates": [...],
      "strict_mode": true/false
    }
  },
  "tier_overrides": {
    "<gate_name>": { "tier": 1-3, "blocking": true/false, "reason": "compliance requirement" }
  }
}
```
