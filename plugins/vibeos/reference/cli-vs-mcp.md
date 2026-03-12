# CLI vs MCP — Integration Pattern Reference

Use this reference when recommending how an application should integrate with external services or when auditing an existing project that uses MCP servers.

## The Core Question

When an AI agent (or a VibeOS-built app) needs to interact with an external service, there are two main approaches:

1. **CLI approach** — use the service's existing command-line tool (`gh`, `aws`, `kubectl`, `stripe`, etc.)
2. **MCP approach** — build or consume an MCP server that exposes the service via the Model Context Protocol

Both are valid. The question is which to prefer, and when.

---

## Decision Criteria

### Prefer CLI when...

| Signal | Reason |
|---|---|
| The service has a mature, well-documented CLI | LLMs are trained on man pages, GitHub repos, and Stack Overflow. They use CLIs reliably without additional tooling. |
| Composability matters | CLIs pipe through `jq`, `grep`, `awk`. MCP doesn't. For filtering large outputs, shell composition is often the only practical approach. |
| Debugging matters | When the CLI does something unexpected, the human can run the same command and see the same output. MCP failures require JSON transport log spelunking. |
| Auth is already handled | `gh auth login`, `aws sso login`, `kubectl` with kubeconfig — these are battle-tested flows. MCP re-authentication is per-server and often flaky. |
| No background process is desirable | CLI tools are binaries on disk. MCP servers are running processes that must start, stay alive, and not silently hang. |
| You want fine-grained permission control | Claude Code can allowlist specific CLI commands (e.g., allow `gh pr view`, require approval for `gh pr merge`). MCP permissions are all-or-nothing per tool. |
| The team needs to run the same commands | CLIs work for humans and agents alike. MCP tools only exist inside the agent conversation. |

### Prefer MCP when...

| Signal | Reason |
|---|---|
| No CLI exists for the service | Some services (Slack, Notion, custom internal APIs) have no CLI. MCP may be the only agent-accessible interface. |
| The service has a rich programmatic API but no stable CLI | A well-implemented MCP server can be faster and safer than constructing raw HTTP calls. |
| The integration is internal and the team controls the MCP server | Custom internal MCP servers can expose exactly the operations the agent needs with appropriate scoping. |
| Structured tool inputs are genuinely better than shell arguments | If the operation has many optional parameters that are hard to express in a shell command, MCP's JSON input model can be cleaner. |

---

## Common Traps

**"We need MCP because our product is AI-first."**
AI-first means the product uses AI well, not that it uses every AI-specific protocol. Adopting MCP where a CLI already exists adds maintenance overhead with no user benefit.

**"MCP gives us a standardized interface."**
CLIs are also standardized — they've had decades of iteration. POSIX conventions, help flags, exit codes, piping, and man pages are a de facto standard that both humans and LLMs understand.

**"Our CLI is hard to use."**
Fix the CLI. A hard-to-use CLI is a usability problem, not an argument for MCP.

**"MCP is more secure."**
Auth is orthogonal to transport. CLI tools support the same SSO, token, and profile systems that MCP servers use, without an additional protocol layer.

---

## Audit Questions for Existing Projects

When investigating an existing project that uses MCP servers, ask:

1. Does the service already have a CLI? If yes, is there a concrete reason not to use it?
2. Is the MCP server maintained? Is it blocking the team when it fails to start?
3. Are team members able to run the same commands the agent runs? Or is the MCP path invisible to humans?
4. Has MCP re-auth caused lost sessions or development friction?
5. Are there composability requirements (filtering large outputs, piping to other tools) that MCP cannot satisfy?

If the answer to any of 1–5 is yes, recommend migrating that integration to CLI and removing the MCP dependency.

---

## Practical Guidance for New Projects

When VibeOS is recommending integrations for a new project:

- Default to CLI for any service with a documented CLI
- Only introduce MCP when there is no CLI alternative or when the team explicitly owns the MCP server
- If MCP is chosen, document the reason in `docs/decisions/DEVIATIONS.md` under "Integration Pattern Decisions"
- Flag all MCP server dependencies in the architecture doc so they are visible as infrastructure risks

---

## Reference

Based on: "MCP is dead. Long live the CLI" — February 28, 2026
Key takeaway: CLIs are composable, human-debuggable, auth-compatible, and process-free. MCP adds value only when no CLI alternative exists.
