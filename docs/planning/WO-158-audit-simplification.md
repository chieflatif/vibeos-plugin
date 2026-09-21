---
wo: WO-158
title: "Simplify independent review and approved fallback"
status: In Progress
phase: 50
phase_name: Proportionate Independent Review
wo_class: logic-change
write_scope:
  - .claude-plugin/marketplace.json
  - plugins/vibeos/.claude-plugin/plugin.json
  - plugins/vibeos/quality-gate-manifest.json
  - plugins/vibeos/hook-manifest.json
  - plugins/vibeos/scripts/generate-inventory.py
  - plugins/vibeos/scripts/gate-runner.sh
  - pyproject.toml
  - vibeos-init.sh
  - vibeos-init-codex.sh
  - README.md
  - docs/release/2.4.1.md
  - docs/evidence/vnext/generated-inventory.json
  - plugins/vibeos/scripts/claude-companion-audit.py
  - plugins/vibeos/scripts/approved-codex-review.py
  - plugins/vibeos/scripts/validate-independent-audit.sh
  - plugins/vibeos/scripts/profile_install.py
  - plugins/vibeos/skills/**
  - plugins/vibeos/reference/**
  - tests/test_claude_companion_audit.py
  - tests/test_companion_simplification.py
  - tests/test_approved_codex_review.py
  - tests/test_companion_fallback_integration.py
  - tests/test_profile_install.py
  - docs/CLAUDE-COMPANION-AUDIT.md
  - docs/planning/WO-158-audit-simplification.md
  - docs/planning/WO-INDEX.md
  - docs/evidence/WO-158/**
no_touch:
  - external-projects/**
required_auditors:
  - claude-companion-review
model_policy: implementation
budget_posture:
  token_ceiling: null
  turn_ceiling: 20
  cost_ceiling_usd: 20
---

# Simplify independent review

Status: In Progress. Scope: adapt `claude-companion-audit.py`, its existing gate,
profile installer and generated instructions; add the bounded fallback helper and
regression evidence, then prepare the 2.4.1 package metadata.

Authority: Latif approved the documented engineering routing and VibeOS
simplification sequence on September 20. This is its internal implementation
record; project adoption follows package proof and compatibility checks.

Findings: the 2.4.0 companion gate can skip before checking module activation;
provider failure has no authorized fallback; minor findings and unrelated work
can block completion; correction review resets too broadly; duplicated review
instructions add overhead.

Acceptance:

- An enabled companion gate fails when the review target is missing or invalid.
- Structured receipt validation is sufficient without redundant prose heuristics.
- Claude remains preferred; unavailable-provider evidence plus explicit Latif
  authorization permits a fresh context of the implementing model, honestly
  recorded. Tests and material findings remain authoritative.
- Critical/high or unmet requirements block; minor findings have dispositions.
- Corrections receive affected-area verification; a full rerun needs a material
  coverage reason. Reviewed inputs remain bound while unrelated work proceeds.
- Reuse existing change and test records; generate supporting review inputs.
- Opted-in instructions replace overlapping generic review fanout, retaining
  specialists for named risks. Default-off behavior remains.

Validation: targeted regression cases for changed behaviors, then a disposable
end-to-end workflow and independent review. Existing release evidence remains
historical; this candidate is not released or installed.
