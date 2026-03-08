---
name: discover
description: Run product discovery to turn a rough idea into validated product documents. Use when a user describes what they want to build and needs help defining scope, requirements, architecture, and technical approach. Generates 7 artifacts.
argument-hint: "[product idea or description]"
allowed-tools: Read, Write, Glob, Grep, Bash, AskUserQuestion
---

# /vibeos:discover — Product Discovery

Turn a rough product idea into validated product documents before any code is written.

## Communication Contract

Throughout this entire flow:
- Explain the purpose of each step in plain English before doing it
- Explain what happened and why it matters after each step
- Use the real technical term and explain it in plain language (e.g., "PRD (product requirements doc)")
- When choices exist: explain each option, state pros/cons, make a recommendation with rationale
- Never ask the user to choose technologies before they understand the business difference
- Summarize what was learned after each meaningful step

## Discovery Flow

### Step 1: Capture Intent

If `$ARGUMENTS` contains a product description, use it. Otherwise ask the user:

> "Tell me what you want to build. Describe it however feels natural — the problem it solves, who it's for, what the main workflow looks like. I'll ask follow-up questions where I need more clarity."

Capture:
- What they want to build (in their own words)
- Who it's for (primary user/persona)
- The main problem it solves
- The most important workflow
- Desired platforms: web, mobile, API, internal tool, or mixed
- Any hard constraints: timeline, integrations, budget, compliance, cloud, team

**Do NOT ask stack/framework questions first.** Focus on business intent.

Write the captured intent to `docs/product/PROJECT-IDEA.md` using the structure from `${CLAUDE_SKILL_DIR}/../../reference/product/PROJECT-IDEA.md.ref`.

### Step 2: Draft Product Shape

Read `${CLAUDE_SKILL_DIR}/../../decision-engine/product-shaping.md` and apply the decision tree to classify:

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
    "deployment_shape": {"value": "", "source": "", "confidence": ""}
  },
  "governance_profile": {
    "team_size": {"value": "", "source": "", "confidence": ""},
    "risk_level": {"value": "", "source": "", "confidence": ""},
    "deployment_context": {"value": "", "source": "", "confidence": ""}
  }
}
```

For technical recommendation, read `${CLAUDE_SKILL_DIR}/../../decision-engine/technical-recommendation.md` and apply the decision tree based on product type and constraints.

### Step 5: Generate Product Artifacts

Generate these 5 documents in the project's `docs/product/` directory, using the reference templates in `${CLAUDE_SKILL_DIR}/../../reference/product/`:

1. **PRODUCT-BRIEF.md** — One-page summary (from `PRODUCT-BRIEF.md.ref`)
2. **PRD.md** — Scope, requirements, user stories, acceptance criteria (from `PRD.md.ref`)
3. **TECHNICAL-SPEC.md** — Stack recommendation, modules, security posture (from `TECHNICAL-SPEC.md.ref`) — write to `docs/TECHNICAL-SPEC.md`
4. **ARCHITECTURE-OUTLINE.md** — Systems, data flow, components (from `ARCHITECTURE-OUTLINE.md.ref`)
5. **ASSUMPTIONS-AND-RISKS.md** — Unresolved questions, risks, compliance concerns (from `ASSUMPTIONS-AND-RISKS.md.ref`)

Replace all `{{PLACEHOLDER}}` values with real content from the discovery conversation. Do not leave any placeholders.

### Step 6: Gate Readiness

Before completing, verify all of these are true:
- [ ] Product summary exists
- [ ] Primary persona is defined
- [ ] At least one core workflow is defined
- [ ] V1 scope is defined
- [ ] Sensitive data posture is defined
- [ ] Technical recommendation exists (or user explicitly deferred it)

Report the gate result to the user:

> "Discovery is complete. Here's what we have: [summary]. All [N] artifacts have been generated in docs/product/. You're ready to run `/vibeos:plan` to generate the development plan and governance setup."

If any gate fails, explain what's missing and ask the user to provide it.

## Output Summary

| Artifact | Path | Purpose |
|---|---|---|
| PROJECT-IDEA.md | docs/product/ | Raw user intent |
| project-definition.json | project root | Machine-readable canonical definition |
| PRODUCT-BRIEF.md | docs/product/ | One-page summary |
| PRD.md | docs/product/ | Requirements and user stories |
| TECHNICAL-SPEC.md | docs/ | Stack and implementation approach |
| ARCHITECTURE-OUTLINE.md | docs/product/ | System components and data flow |
| ASSUMPTIONS-AND-RISKS.md | docs/product/ | Open questions and risks |
