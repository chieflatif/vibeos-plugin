---
name: discover
description: Run product discovery to turn a rough idea into validated product, anchor, and governance documents. Use when a user describes what they want to build, shares a product idea, says "I want to build/create/make...", mentions a "new project/app/product", or needs help defining scope, requirements, architecture, and technical approach. Also use for existing codebases when the user wants to analyze what they have.
argument-hint: "[product idea or description]"
allowed-tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
---

# /vibeos:discover — Product Discovery

Turn a rough product idea into validated product documents before any code is written.

## Communication Contract

Follow the full USER-COMMUNICATION-CONTRACT.md (`docs/USER-COMMUNICATION-CONTRACT.md`). Key rules:
- Lead with outcome, follow with mechanism
- Present decisions with consequences
- Introduce every concept on first use with plain English definition

Skill-specific addenda:
- Never ask the user to choose technologies before they understand the business difference
- Summarize what was learned after each meaningful step
- Explain in plain English first; add technical detail after that only when it helps the user understand the recommendation
- If the user needs to choose, present options with pros, cons, and a recommendation

## Discovery Flow

### Step 0a: First-Run Onboarding

Check if this is the user's first time using VibeOS on this project:

1. Read `.vibeos/config.json` — if it does not exist or `onboarding_complete` is `false`, this is the first run
2. If first run, present the onboarding message:

> **Welcome to VibeOS**
>
> VibeOS turns Claude into an autonomous development engine. Here's how it works:
>
> 1. **You describe what you want to build** — I'll ask questions to understand your vision
> 2. **I create a development plan** — broken into phases and work orders (detailed task specs)
> 3. **I build autonomously** — writing tests first, then code, with quality checks at every step
> 4. **I check in with you** — at natural pause points so you can review, redirect, or continue
>
> **Your role:** You make the decisions — what to build, what quality level to target, when to ship. I handle the implementation, testing, and quality enforcement.
>
> **What to expect:** You'll see progress updates as each piece is built. I'll explain what I'm doing in plain English. When I need your input, I'll present clear options with their implications.
>
> **How to interact:** Just talk to me naturally. Say things like "I want to build a task management app" or "how's progress?" or "continue building." You never need to type commands — I'll figure out what you need.

3. Create `.vibeos/config.json` (or update it) with `"onboarding_complete": true`
4. If existing code is detected (Step 0b below), append to the onboarding: "I see you already have code — I'll start by understanding what's here before we plan anything new."

### Step 0b: Detect Existing Code

Before starting discovery, check if the project has existing source code:

1. Look for source directories: `src/`, `lib/`, `app/`, `pkg/`, `cmd/`, `internal/`, `server/`, `client/`, `api/`, `core/`
2. Look for language indicators: `package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle`, `*.csproj`, `Gemfile`, `composer.json`, `pyproject.toml`, `setup.py`
3. Count source files (excluding test files, node_modules, vendor dirs, and generated files)

**If existing code is found (10+ source files):** Switch to the **Midstream Discovery Flow** below.

**If no existing code (greenfield project):** Continue with Step 1.

---

## Greenfield Discovery Flow

### Step 1: Capture Intent

If `$ARGUMENTS` contains a product description, use it. Otherwise ask the user:

> "Tell me what you want to build. Describe it however feels natural — the problem it solves, who it's for, what the main workflow looks like. I'll ask follow-up questions where I need more clarity."

Capture:
- What they want to build (in their own words)
- Who it's for (primary user/persona)
- The main problem it solves
- The most important workflow
- What would make the experience feel excellent, trustworthy, or delightful
- What would count as an unacceptable shortcut or compromise
- Desired platforms: web, mobile, API, internal tool, or mixed
- Any hard constraints: timeline, integrations, budget, compliance, cloud, team

**Do NOT ask stack/framework questions first.** Focus on business intent.

Write the captured intent to `docs/product/PROJECT-IDEA.md` using the structure from `.vibeos/reference/product/PROJECT-IDEA.md.ref`.

### Step 2: Draft Product Shape

Read `.vibeos/decision-engine/product-shaping.md` and apply the decision tree to classify:

- **Product type**: web-saas, mobile-app, api-platform, internal-tool, marketplace, other
- **Platform set**: web, mobile, api, internal
- **Sensitive data categories**: pii, payments, health, financial, confidential-business-data
- **Compliance signals**: gdpr, soc2, owasp
- **Governance intensity**: solo/team, low/medium/high risk

Present the classification to the user:

> "Based on what you've described, here's how I'd classify this project: [classification]. Does this match your intent, or should I adjust anything?"

### Step 3: Adaptive Follow-Ups

Only ask questions when BOTH conditions are true:
1. **Confidence is low** — you're not sure about the answer
2. **Impact is high** — getting it wrong would affect architecture or compliance

High-value follow-up questions:
- Who is the primary user? (if unclear)
- What must exist in v1? (if scope is vague)
- What is explicitly out of scope? (always valuable)
- What should this product never become, even if it would be faster to ship?
- What does "done well" feel like for the user? (speed, trust, clarity, polish, etc.)
- Does it process payments, health data, financial data, PII, or company secrets? (if sensitive data unclear)
- Is it mobile-first, web-first, or API-first? (if platform unclear)
- Are there non-negotiable integrations? (if integrations mentioned)

Tag each inferred field with:
- `source`: user-confirmed | inferred | default
- `confidence`: high | medium | low

### Step 4: Build Canonical Definition

Create `project-definition.json` in the project root with this structure:

```json
{
  "idea": {
    "name": {"value": "", "source": "", "confidence": ""},
    "summary": {"value": "", "source": "", "confidence": ""},
    "product_type": {"value": "", "source": "", "confidence": ""}
  },
  "users": {
    "primary_persona": {"value": "", "source": "", "confidence": ""},
    "secondary_personas": []
  },
  "scope": {
    "core_workflows": [],
    "v1_features": [],
    "non_goals": []
  },
  "anchors": {
    "product_promise": {"value": "", "source": "", "confidence": ""},
    "experience_principles": [],
    "non_negotiables": [],
    "anti_goals": [],
    "engineering_principles": [],
    "research_freshness_policy": {"value": "", "source": "", "confidence": ""}
  },
  "constraints": {
    "platforms": [],
    "integrations": [],
    "sensitive_data": [],
    "compliance_targets": []
  },
  "technical_recommendation": {
    "language": {"value": "", "source": "", "confidence": ""},
    "framework": {"value": "", "source": "", "confidence": ""},
    "database": {"value": "", "source": "", "confidence": ""},
    "deployment_shape": {"value": "", "source": "", "confidence": ""},
    "notes": [],
    "evidence_sources": [],
    "last_verified": {"value": "", "source": "", "confidence": ""}
  },
  "governance_profile": {
    "team_size": {"value": "", "source": "", "confidence": ""},
    "risk_level": {"value": "", "source": "", "confidence": ""},
    "deployment_context": {"value": "", "source": "", "confidence": ""}
  }
}
```

For technical recommendation, read `.vibeos/decision-engine/technical-recommendation.md` and apply the decision tree based on product type and constraints.

### Step 5: Generate Product Artifacts

Generate the core anchor and product documents using the reference templates in `.vibeos/reference/`:

1. **PRODUCT-BRIEF.md** — One-page summary (from `PRODUCT-BRIEF.md.ref`)
2. **PRD.md** — Scope, requirements, user stories, acceptance criteria (from `PRD.md.ref`)
3. **TECHNICAL-SPEC.md** — Stack recommendation, modules, security posture (from `TECHNICAL-SPEC.md.ref`) — write to `docs/TECHNICAL-SPEC.md`
4. **ARCHITECTURE-OUTLINE.md** — Systems, data flow, components (from `ARCHITECTURE-OUTLINE.md.ref`)
5. **ASSUMPTIONS-AND-RISKS.md** — Unresolved questions, risks, compliance concerns (from `ASSUMPTIONS-AND-RISKS.md.ref`)
6. **PRODUCT-ANCHOR.md** — Core promise, experience principles, non-negotiables, anti-goals (from `reference/product/PRODUCT-ANCHOR.md.ref`) — write to `docs/product/PRODUCT-ANCHOR.md`
7. **QUALITY-ANCHOR.md** — Frozen, human-authored alignment target defining what "Complete" means, forbidden testing patterns, verification integrity requirements, and anti-corruption detection rules. Generate a project-appropriate draft from `reference/governance/QUALITY-ANCHOR-TEMPLATE.md`; the human reviews and freezes it. Write to `docs/QUALITY-ANCHOR.md`. Add `docs/QUALITY-ANCHOR.md` to the frozen files list in `.vibeos/frozen-files.json` so that no agent can modify it after the human approves it.
8. **ENGINEERING-PRINCIPLES.md** — Build philosophy, anti-shortcut rules, freshness policy (from `reference/governance/ENGINEERING-PRINCIPLES.md.ref`) — write to `docs/ENGINEERING-PRINCIPLES.md`
9. **RESEARCH-REGISTRY.md** — Active evidence for high-impact technical decisions (from `reference/governance/RESEARCH-REGISTRY.md.ref`) — write to `docs/research/RESEARCH-REGISTRY.md`
10. **DEVIATIONS.md** — Explicit compromise log (from `reference/governance/DEVIATIONS.md.ref`) — write to `docs/decisions/DEVIATIONS.md`

Replace all `{{PLACEHOLDER}}` values with real content from the discovery conversation. Do not leave any placeholders.

When generating the anchors:
- `PRODUCT-ANCHOR.md` should be written in plain English for non-technical users
- `ENGINEERING-PRINCIPLES.md` should state the quality bar clearly, including that current evidence is required for high-impact external decisions
- `RESEARCH-REGISTRY.md` should be seeded with any stack or integration decisions already made during discovery, including source type and verification date when known
- `DEVIATIONS.md` should start with no open deviations unless the user explicitly accepted a trade-off during discovery

### Step 6: Gate Readiness

Before completing, verify all of these are true:
- [ ] Product summary exists
- [ ] Primary persona is defined
- [ ] At least one core workflow is defined
- [ ] V1 scope is defined
- [ ] Product promise and experience principles are defined
- [ ] Engineering principles are defined
- [ ] Sensitive data posture is defined
- [ ] Technical recommendation exists (or user explicitly deferred it)

Report the gate result to the user:

> "Discovery is complete. Here's what we have: [summary]. The product documents, anchor documents, and governance docs are in place.
>
> **Next step: `/vibeos:plan`** — I'll ask about your technical preferences (framework, database, deployment), configure quality gates for your project, and generate a phased development plan with specific work orders. This usually takes 5-10 minutes of your input."

If any gate fails, explain what's missing and ask the user to provide it.

---

## Midstream Discovery Flow

This flow runs when existing source code is detected (Step 0). It reverse-engineers the architecture from the codebase and produces draft product documents for user validation.

### Step M1: Announce Midstream Mode

Tell the user:

> "I see existing code in this project — [N] source files across [directories]. Instead of starting from scratch, I'll analyze your codebase to understand its architecture, then ask you to validate what I find."

### Step M2: Analyze Codebase

Perform systematic code analysis:

1. **Directory structure** — Map source dirs, test dirs, config files, documentation, scripts, CI/CD
2. **Language and framework detection** — Identify from indicators (package.json → Node.js, requirements.txt → Python, go.mod → Go, etc.). Detect framework from imports/config (Express, FastAPI, Django, Next.js, Spring Boot, etc.)
3. **Import graph** — Analyze imports to build a module dependency map. Identify which modules depend on which.
4. **Architectural pattern detection** — Classify: layered, modular, monolith, microservice, MVC, service-repository, hexagonal, etc. Evidence is based on directory structure and import patterns.
5. **Database layer** — Detect ORM (SQLAlchemy, Prisma, TypeORM, GORM, etc.), raw SQL, migration framework, connection configuration
6. **Auth layer** — Detect middleware, decorators, session management, JWT usage, OAuth integrations
7. **API surface** — Map routes, endpoints, controllers, GraphQL schemas, gRPC definitions
8. **Test infrastructure** — Detect test framework (pytest, jest, go test, etc.), test directory, naming conventions, approximate coverage

For each inference, track confidence:
- **high** — strong indicator (e.g., `package.json` with `"express"` in dependencies)
- **medium** — indirect indicator (e.g., directory named `controllers/` suggests MVC)
- **low** — weak signal (e.g., few files, ambiguous structure)

### Step M3: Generate Draft Documents

From the code analysis, generate draft documents in the project's `docs/product/` directory:

#### M3a. ARCHITECTURE-OUTLINE.md

Generate `docs/product/ARCHITECTURE-OUTLINE.md` using the reference template at `.vibeos/reference/product/ARCHITECTURE-OUTLINE.md.ref`. Include:
- Detected layers and their boundaries
- Module map with dependencies
- Database schema overview (from migrations or models)
- API surface map
- Auth flow
- Test infrastructure summary

Mark inferred sections with confidence levels.

#### M3b. TECHNICAL-SPEC.md

Generate `docs/TECHNICAL-SPEC.md` using the reference template at `.vibeos/reference/product/TECHNICAL-SPEC.md.ref`. Include:
- Detected language, framework, and runtime version
- Database and ORM
- Key dependencies and their purposes
- Build and deployment configuration
- Test framework and patterns
- Any decisions that should later be backed by current evidence in `docs/research/RESEARCH-REGISTRY.md`

#### M3c. PRODUCT-ANCHOR.md

Generate `docs/product/PRODUCT-ANCHOR.md` using the reference template at `.vibeos/reference/product/PRODUCT-ANCHOR.md.ref`.

Base it on:
- README or existing product docs
- visible user-facing workflows in the codebase
- what the system appears to optimize for today

Mark inferred sections with confidence levels and explicitly ask the user to correct anything that feels off.

#### M3d. PRD.md (with collision handling)

**If `docs/product/PRD.md` does not exist:** Generate a skeleton `docs/product/PRD.md` from the reference template at `.vibeos/reference/product/PRD.md.ref`. Populate with inferred product scope based on code structure, README content (if present), and API surface. Tag each section with source metadata:
```markdown
<!-- source: inferred, updated: 2024-01-15T10:30:00Z -->
## Section Title
```

**If `docs/product/PRD.md` already exists** (from a prior `/vibeos:discover` run): apply section-level merge:

**Section identification:** Each `##` heading is a merge unit. Sections are identified by their metadata comment tag.

**Merge rules:**
1. Section exists with `source: user` → **KEEP** user version unchanged
2. Section exists with `source: inferred` → **REPLACE** with new inference, update timestamp
3. Section is new (not in old PRD) → **ADD** with `source: inferred`
4. Section exists in old PRD but not in new analysis → **KEEP** (user may have added it)

**Conflict handling:** If both user and inference touch the same section (user edited an `inferred` section — detected by comparing content):
- Keep user version
- Add note: `<!-- Note: VibeOS inferred updated content for this section but preserved your edits. Re-run /vibeos:discover to see the new inference in a separate diff. -->`

**Detecting user edits:** A section originally tagged `source: inferred` is considered user-edited if its content differs from what the inference would produce. When a user edits an inferred section, update its tag to `source: user`.

#### M3e. Governance Anchors

Generate:
- `docs/ENGINEERING-PRINCIPLES.md` from `.vibeos/reference/governance/ENGINEERING-PRINCIPLES.md.ref`
- `docs/research/RESEARCH-REGISTRY.md` from `.vibeos/reference/governance/RESEARCH-REGISTRY.md.ref`
- `docs/decisions/DEVIATIONS.md` from `.vibeos/reference/governance/DEVIATIONS.md.ref`

For existing projects, infer the current engineering style from the codebase, but flag low-confidence sections for user confirmation.

#### M3f. project-definition.json

Generate `project-definition.json` in the project root with the same structure as the greenfield flow (Step 4), but with all values marked as `"source": "inferred"` and appropriate confidence levels.

### Step M4: User Validation

Present the inferred architecture to the user for validation:

> "I've analyzed your codebase and here's what I found:
>
> **Architecture:** [pattern] with [N] modules across [M] layers
> **Stack:** [language] [version] + [framework] + [database]
> **Module map:**
> - [module]: [purpose] ([N] files, depends on [deps])
> - [module]: [purpose] ([N] files, depends on [deps])
> - ...
>
> **What I'm confident about:** [high-confidence inferences]
> **What I'm less sure about:** [low-confidence inferences, with specific questions]
>
> Is this accurate? What should I add or correct?"

After user validates or corrects:
1. Update the draft documents with corrections
2. Finalize the architecture document

### Step M5: Midstream Gate Readiness

Before completing, verify all outputs exist:
- [ ] Directory structure mapped
- [ ] Language, framework, and database detected
- [ ] `docs/product/ARCHITECTURE-OUTLINE.md` generated with module map
- [ ] `docs/TECHNICAL-SPEC.md` generated with detected stack
- [ ] `docs/product/PRODUCT-ANCHOR.md` generated and user-reviewed
- [ ] `docs/ENGINEERING-PRINCIPLES.md` generated
- [ ] `docs/research/RESEARCH-REGISTRY.md` generated
- [ ] `docs/decisions/DEVIATIONS.md` generated
- [ ] `docs/product/PRD.md` generated or merged
- [ ] `project-definition.json` generated with inferred values and confidence levels
- [ ] User validated and corrected the architecture

Report the result:

> "Midstream discovery is complete. Here's what we established:
> - Architecture: [pattern] with [N] modules
> - Stack: [language] + [framework] + [database]
> - Product and engineering anchors created so future work can be checked for drift
>
> Your architecture and anchor documents are now the baseline for later audits.
>
> **Next step: `/vibeos:plan`** — I'll run a guided audit of your codebase, walk you through any issues I find (you'll decide what to fix now vs later), then generate a development plan. The audit covers security, architecture, code quality, dependencies, and test coverage."

---

## Output Summary

### Greenfield Artifacts

| Artifact | Path | Purpose |
|---|---|---|
| PROJECT-IDEA.md | docs/product/ | Raw user intent |
| project-definition.json | project root | Machine-readable canonical definition |
| PRODUCT-BRIEF.md | docs/product/ | One-page summary |
| PRD.md | docs/product/ | Requirements and user stories |
| PRODUCT-ANCHOR.md | docs/product/ | Core promise and experience guardrails |
| QUALITY-ANCHOR.md | docs/ | Frozen quality standard — what "Complete" means, forbidden patterns |
| TECHNICAL-SPEC.md | docs/ | Stack and implementation approach |
| ENGINEERING-PRINCIPLES.md | docs/ | Build philosophy and freshness rules |
| RESEARCH-REGISTRY.md | docs/research/ | Current evidence for high-impact decisions |
| DEVIATIONS.md | docs/decisions/ | Explicit compromise log |
| ARCHITECTURE-OUTLINE.md | docs/product/ | System components and data flow |
| ASSUMPTIONS-AND-RISKS.md | docs/product/ | Open questions and risks |

### Midstream Artifacts

| Artifact | Path | Purpose |
|---|---|---|
| project-definition.json | project root | Inferred canonical definition with confidence levels |
| ARCHITECTURE-OUTLINE.md | docs/product/ | Inferred architecture, validated by user |
| PRODUCT-ANCHOR.md | docs/product/ | Inferred product promise and experience guardrails |
| TECHNICAL-SPEC.md | docs/ | Detected stack and implementation details |
| ENGINEERING-PRINCIPLES.md | docs/ | Inferred build standards and freshness rules |
| RESEARCH-REGISTRY.md | docs/research/ | Evidence log for current technical decisions |
| DEVIATIONS.md | docs/decisions/ | Compromise log for explicit trade-offs |
| PRD.md | docs/product/ | Inferred scope (or merged with existing) |
