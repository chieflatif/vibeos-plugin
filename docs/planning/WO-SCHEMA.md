# Work Order Frontmatter Schema

VibeOS vNext treats each Work Order as a machine-readable contract. The frontmatter is the source for future generators: scope guards, lane-readiness checks, auditor-artifact gates, model policy checks, loop ceilings, and generated status views.

The authoritative JSON Schema lives at:

`plugins/vibeos/reference/wo-frontmatter.schema.json`

## Contract Block

Every new WO starts with YAML frontmatter:

```yaml
---
wo: WO-111
title: WO Frontmatter Schema + Template
status: In Progress
phase: 35
phase_name: Machine-Readable WO Contracts
wo_class: harness
write_scope:
  - docs/planning/WO-SCHEMA.md
  - plugins/vibeos/reference/wo-frontmatter.schema.json
no_touch:
  - /Users/latifhorst/latifhorstweb/**
required_auditors:
  - correctness-auditor
  - evidence-auditor
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: null
  cost_ceiling_usd: null
---
```

Optional loop fields are allowed only when the WO is eligible for bounded loop execution:

```yaml
loop_goal: "Run until wo_exit passes or ceiling is reached"
loop_ceiling_turns: 8
loop_ceiling_cost_usd: 3.0
```

## Required Fields

| Field | Purpose |
|---|---|
| `wo` | Canonical `WO-NNN` identifier. |
| `title` | Human-readable title without the WO prefix. |
| `status` | Truthful lifecycle state. `Complete` requires relevant tests, gates, evidence, and a recoverable state. |
| `phase` | Numeric development-plan phase. |
| `phase_name` | Human-readable phase name. |
| `wo_class` | Governance class that controls audit depth and evidence expectations. |
| `write_scope` | Path globs this WO may edit. Future generators use this for worktree-scope manifests and lane readiness. |
| `no_touch` | Path globs explicitly forbidden for this WO. Use an empty list when there are no extra no-touch paths. |
| `required_auditors` | Auditor roles required before completion. Future gates consume this field. |
| `model_policy` | Model/effort tier name. This is not a provider model id. |
| `budget_posture` | Token, turn, and cost ceilings. Use `null` only when no explicit ceiling has been approved yet. |

## Work Order Classes

Built-in classes are portable VibeOS policy. Project-specific classes must use a `custom-*` prefix so generators can distinguish local policy from framework policy.

| Class | Governance tier | Minimum auditor intent | Differential audit |
|---|---|---|---|
| `docs-only` | light | evidence | allowed |
| `planning` | light | plan + evidence | allowed |
| `harness` | standard | correctness + evidence | allowed |
| `test-only` | standard | test + evidence | allowed |
| `logic-change` | standard | correctness + test + evidence | allowed |
| `mutation-path` | deep | correctness + security + test + evidence | not allowed |
| `auth-security` | deep | security + correctness + test + evidence | not allowed |
| `dependency` | deep | dependency intelligence + security + evidence | not allowed |
| `delivery-infrastructure` | deep | delivery infrastructure + security + evidence | not allowed |
| `prompt-agent` | standard | prompt engineer + evidence | allowed |
| `release-proof` | deep | evidence + security + correctness | not allowed |

## Model Policy Names

Allowed portable model policies:

- `drafting`
- `implementation`
- `frontier-audit`
- `dependency-research`
- `cost-sensitive`

Project-specific policies must use `custom-*`. Future model policy work resolves these names against the live runtime instead of hardcoding provider model ids.

## Generator Rules

WO-111 defines the contract only. Later WOs consume it:

- WO-112 generates scope, agent, and auditor-gate material from the frontmatter.
- WO-113 migrates active vNext WOs and turns `WO-INDEX.md` into a generated view.
- WO-115 validates lane return packets against `write_scope`.
- WO-118 and WO-119 enforce `model_policy`.
- WO-120 through WO-122 use loop fields and `budget_posture`.
- WO-127 enforces `required_auditors`.

Until WO-113 completes, legacy WOs may remain prose-only. New vNext WOs should use the contract block immediately.
