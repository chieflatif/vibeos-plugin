---
name: vibeos-discover
description: Discovery, project shaping, and codebase understanding for VibeOS in Codex. Use when the user describes what they want to build, wants help understanding an existing codebase, needs initial governance artifacts, or wants product and architecture context created before planning.
---

# VibeOS Discover

Use this skill when the project needs discovery, anchor documents, or a codebase-first understanding pass.

## Workflow

1. Read `docs/USER-COMMUNICATION-CONTRACT.md` if it exists.
2. Inspect the repo to determine whether this is greenfield or midstream.
3. Create or refresh the foundational discovery artifacts:
   - `.vibeos/config.json`
   - `project-definition.json`
   - `docs/product/PROJECT-IDEA.md` when starting from a new idea
   - `docs/product/PRODUCT-BRIEF.md`
   - `docs/product/PRD.md`
   - `docs/product/PRODUCT-ANCHOR.md`
   - `docs/product/ARCHITECTURE-OUTLINE.md`
   - `docs/TECHNICAL-SPEC.md`
   - `docs/ENGINEERING-PRINCIPLES.md`
   - `docs/research/RESEARCH-REGISTRY.md`
   - `docs/decisions/DEVIATIONS.md`
4. Keep discovery evidence-backed. Mark assumptions and confidence explicitly.
5. If code already exists, anchor discovery in what is actually present before proposing new structure.
6. Hand off to `vibeos-plan` when the project is ready to be sequenced into work orders.

## Rules

- Ask only the smallest number of questions needed.
- Translate technical choices into user outcomes first.
- When both Codex and Claude/Cursor assets are present, keep them compatible.
