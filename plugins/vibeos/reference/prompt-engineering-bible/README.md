# Prompt Engineering Bible Integration

This folder is a curated local snapshot of the upstream Prompt Engineering Bible
repository so VibeOS can use it without requiring live network access at
runtime.

## Upstream Source

- Repository: `https://github.com/chieflatif/prompt-engineering-bible`
- Snapshot commit: `409b78c96d0231673cad911d8a1a03036dc19da0`
- License: MIT (included locally in `LICENSE`)

## What Is Included

The snapshot intentionally focuses on the books VibeOS can use operationally:

- universal first principles
- core prompt contract and governance books
- agent-type books relevant to VibeOS workers
- generic profile defaults
- canonical prompt and registry templates

## How VibeOS Uses This

The `prompt-engineer` agent reads `registry.yaml` in this folder to:

1. determine which Bible books apply to a target agent or prompt artifact
2. load the required core guidance plus the relevant agent-type guidance
3. create or refine prompt artifacts as governed system assets
4. preserve prompt registry and lifecycle discipline instead of treating prompts as disposable prose

## Local Policy

- This bundle is a canonical local reference for prompt work inside VibeOS.
- Upstream remains the original source of authorship and evolution.
- If the upstream repo changes materially, refresh this snapshot intentionally and record the new commit.
