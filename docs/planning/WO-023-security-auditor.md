# WO-023: Security Auditor Agent

## Status

`Draft`

## Phase

Phase 4: Fresh-Context Audit Agents

## Objective

Create a security auditor agent that performs OWASP Top 10 and general security analysis in an isolated, read-only context.

## Scope

### In Scope
- [ ] Create `agents/security-auditor.md` with strict isolation
- [ ] Agent config: isolation: worktree, disallowedTools: Write, Edit, Agent, model: sonnet
- [ ] OWASP Top 10 coverage: injection, broken auth, sensitive data exposure, XXE, broken access control, security misconfiguration, XSS, insecure deserialization, known vulnerabilities, insufficient logging
- [ ] Secrets detection: hardcoded API keys, passwords, tokens, connection strings
- [ ] SQL injection patterns
- [ ] XSS patterns (stored, reflected, DOM-based)
- [ ] CSRF vulnerability detection
- [ ] Authentication bypass patterns
- [ ] PII exposure (unencrypted, logged, returned in APIs)
- [ ] Structured findings with severity (critical, high, medium, low, info)

### Out of Scope
- Architecture analysis (WO-024)
- Correctness analysis (WO-025)
- Fixing found issues (separate WO created from findings)

## Dependencies

| Dependency | Type | Status |
|---|---|---|
| Phase 3 complete | Must complete first | Draft |

## Impact Analysis

- **Files created:** agents/security-auditor.md
- **Systems affected:** Audit pipeline, security enforcement

## Acceptance Criteria

- [ ] AC-1: Agent runs in isolated worktree (cannot affect main working tree)
- [ ] AC-2: Agent cannot use Write, Edit, or Agent tools
- [ ] AC-3: All OWASP Top 10 categories checked
- [ ] AC-4: Hardcoded secrets detected with file path and line number
- [ ] AC-5: Each finding includes: category, severity, file, line, description, recommendation
- [ ] AC-6: Findings returned as structured, parseable output
- [ ] AC-7: False positive rate acceptable (findings include confidence level)

## Test Strategy

- **Integration:** Dispatch against code with known security issues, verify detection
- **False positives:** Dispatch against clean code, verify minimal false positives
- **Coverage:** Verify all OWASP categories represented in checklist

## Implementation Plan

### Step 1: Create Agent File
- YAML frontmatter: model (sonnet), isolation (worktree), disallowedTools (Write, Edit, Agent), maxTurns
- Instructions: systematic security audit protocol
- OWASP checklist embedded in agent instructions

### Step 2: Implement Audit Protocol
- Phase 1: Secrets scan (grep for patterns: API_KEY, password, token, secret)
- Phase 2: Input handling (find all user input entry points, check for validation)
- Phase 3: Auth/authz (check authentication and authorization patterns)
- Phase 4: Data handling (check encryption, PII, logging)
- Phase 5: Configuration (check for debug mode, permissive CORS, missing headers)

### Step 3: Implement Finding Structure
- Each finding: { category, severity, confidence, file, line, description, recommendation }
- Summary: total findings by severity, top risks

## Audit Checkpoints

### Planning Audit
- Status: `pending`
- Test status: Integration test — dispatch against code with planted vulnerabilities
- Risk: Security audit quality depends on agent's security knowledge; may miss novel patterns

## Evidence

- [ ] Agent file created with correct isolation config
- [ ] Known vulnerabilities detected in test code
- [ ] Structured findings returned
- [ ] Tool restrictions enforced
- [ ] All OWASP categories checked
