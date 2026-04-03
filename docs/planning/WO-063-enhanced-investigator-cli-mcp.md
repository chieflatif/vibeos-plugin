# WO-063: Enhanced Investigator & CLI-vs-MCP Reference

## Status

`Complete`

## Phase

Phase 11: Advanced Governance (v2.1)

## Objective

Enhance the investigator agent with two new analysis steps from Joan: MCP vs CLI integration pattern evaluation and infrastructure cost risk assessment. Add a CLI-vs-MCP decision matrix reference document.

## Context

Joan's investigator agent includes two additional pre-flight steps that catch architectural issues before implementation begins:
1. **MCP vs CLI evaluation** — Scans for MCP server dependencies and recommends migration to CLI equivalents where available. CLIs are composable, human-debuggable, and don't require background processes.
2. **Infrastructure cost risk** — Flags architectural choices that scale cost super-linearly, missing connection pools, missing caching layers, and compute-heavy operations in request paths.

## Joan Sources

- `/Users/latifhorst/Joan/.claude/agents/investigator.md` (Steps 10-11)
- `/Users/latifhorst/Joan/.vibeos/reference/cli-vs-mcp.md`

## Scope

### In Scope

1. **Enhanced investigator agent** — Add two new steps:
   - **Step: Assess Integration Pattern Risks (CLI vs MCP)**
     - Scan `.claude/settings.json` for mcpServers
     - For each MCP server: check whether CLI equivalent exists
     - If CLI exists and MCP used anyway: flag as recommendation
     - If WO proposes new MCP: require DEVIATIONS.md justification
   - **Step: Assess Infrastructure Cost Risks**
     - Flag choices scaling cost super-linearly
     - Flag services without connection pool configuration
     - Flag missing caching layers
     - Flag compute-heavy operations in request path

2. **CLI vs MCP reference document** — `reference/cli-vs-mcp.md`:
   - Decision matrix: when CLI wins vs when MCP is justified
   - Common traps (false claims about "AI-first" requiring MCP)
   - Audit questions for existing projects
   - Default recommendation: CLI unless MCP provides clear value

### Out of Scope

- Joan-specific integration references (Graph API, Cosmos DB)
- Modifying how MCP servers are configured

## Acceptance Criteria

1. Investigator agent has MCP/CLI evaluation step
2. Investigator agent has infrastructure cost risk step
3. CLI vs MCP reference document covers decision matrix, traps, and audit questions
4. Reference document is framework-agnostic (no Joan-specific services)
5. No Joan-specific references in investigator additions

## Dependencies

- WO-056 — session state infrastructure

## Files Modified

- `plugins/vibeos/agents/investigator.md` — add Steps 10-11

## Files Created

- `plugins/vibeos/reference/cli-vs-mcp.md`
