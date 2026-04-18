---
name: vibeos-plan
description: VibeOS planning and work-order generation for Codex. Use when the user says make a plan, break the work down, organize the roadmap, create work orders, or wants governance and sequencing created after discovery.
---

# VibeOS Plan

Use this skill when discovery is done and the project needs a real development plan.

## Workflow

1. Read:
   - `project-definition.json`
   - `docs/product/PRD.md`
   - `docs/product/PRODUCT-ANCHOR.md`
   - `docs/product/ARCHITECTURE-OUTLINE.md`
   - `docs/ENGINEERING-PRINCIPLES.md`
   - `docs/research/RESEARCH-REGISTRY.md`
   - `docs/decisions/DEVIATIONS.md`
2. Generate or refresh:
   - `docs/planning/DEVELOPMENT-PLAN.md`
   - `docs/planning/WO-INDEX.md`
   - `docs/planning/AUDIT-PROTOCOL.md`
   - `docs/planning/AGENT-WORKFLOW.md`
   - `docs/planning/WO-*.md`
   - `.claude/quality-gate-manifest.json`
   - `scripts/architecture-rules.json` when architecture enforcement is needed
3. If the project is a git repo and `.claude/quality-gate-manifest.json` now exists, install or refresh commit-boundary hooks:
   - `bash ".vibeos/scripts/setup-git-hooks.sh" --project-dir "."`
4. For midstream projects, create or refresh:
   - `.vibeos/findings-registry.json`
   - `.vibeos/baselines/midstream-baseline.json`
   - `.vibeos/midstream-report.md`
   - remediation work orders in Phase 0
5. Use outcome language first, then technical detail.
6. Make phase sequencing, dependencies, and acceptance criteria explicit enough for truthful build execution.

## Rules

- Do not start implementation inside planning.
- Do not create a WO without evidence or a concrete objective.
- Preserve shared `.vibeos/` state so Claude/Cursor and Codex can resume from the same planning base.
- Codex does not get Claude runtime hooks; Git hooks are the commit-boundary substitute once planning creates the shared gate manifest.
