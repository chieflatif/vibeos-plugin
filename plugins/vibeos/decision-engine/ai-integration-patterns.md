# AI Integration Patterns Decision Tree

## Purpose

When a project uses AI/LLM capabilities, determine the appropriate gates, WOs, and architecture
patterns to ensure safe, cost-effective, and maintainable AI integration.

## Entry Condition

This tree is evaluated when `project-definition.json` contains:
- `ai_provider` is set (openai, anthropic, azure-openai, google-ai, cohere, huggingface, custom)
- OR `features` or `workflows` mention AI, LLM, ML, chatbot, embedding, vector search, RAG, agent

## Decision 1: AI Integration Depth

Classify the AI integration:

| Signal | Classification | Implications |
|--------|---------------|--------------|
| Single API call to LLM provider, response shown to user | **Surface** | Low risk, low cost control needs |
| Multiple LLM calls chained, RAG pipeline, embedding + retrieval | **Core pipeline** | Medium risk, needs cost control + caching |
| AI agent with tool use, autonomous actions, DB writes from LLM output | **Autonomous** | High risk, needs guardrails + human-in-loop |
| Custom model training, fine-tuning, inference serving | **Model owner** | Highest risk, needs MLOps pipeline |

**Output:** `ai_depth: surface | core_pipeline | autonomous | model_owner`

## Decision 2: Gate Selection

### Always enable when AI detected:
- `validate-ai-integration.sh` (tier 2 — important, non-blocking)
- `validate-security-patterns.sh` with `INCLUDE_AI_PATTERNS=true`

### Enable for `core_pipeline` and above:
- `validate-ai-integration.sh` (upgrade to tier 1 — blocking)
- `REQUIRE_COST_CONTROLS=true` on validate-ai-integration.sh

### Enable for `autonomous`:
- `REQUIRE_COST_CONTROLS=true`
- Add architecture rule: `ai_output_validation` — LLM output must be validated/parsed before database writes or user display
- Add architecture rule: `no_raw_llm_exec` — LLM output must never be passed to `exec()`, `eval()`, `subprocess`, or SQL queries

**Output:**
```json
{
  "ai_gates": [
    {
      "script": "validate-ai-integration.sh",
      "tier": 1,
      "config": {
        "REQUIRE_COST_CONTROLS": true
      }
    }
  ],
  "ai_architecture_rules": [
    {
      "name": "ai-output-validation",
      "type": "forbidden_patterns",
      "description": "LLM output must not be used in DB queries or exec without validation",
      "source_module": "src/",
      "patterns": ["exec.*llm_output", "eval.*ai_response", "cursor.execute.*generated"]
    }
  ]
}
```

## Decision 3: Mandatory WOs for AI Projects

### For all AI projects:
Add to Phase 1 (Foundation):
- **AI Provider Setup** — Configure API client, API key management (env var, not hardcoded), model version pinning, basic error handling and retry logic

### For `core_pipeline` and above:
Add to Development Plan:
- **AI Cost Control** — Token counting, usage tracking, per-user rate limits, spend alerts, response caching strategy
- **AI Safety Guardrails** — Input sanitization before LLM calls, output validation after LLM responses, content moderation for user-facing output

### For `autonomous`:
Add to Development Plan:
- **AI Human-in-the-Loop** — Define which actions require human approval, implement approval workflow, audit log for autonomous decisions
- **AI Fallback Architecture** — Define behavior when AI service unavailable, implement graceful degradation, fallback to non-AI path where possible

### For `model_owner`:
Add to Development Plan:
- **ML Pipeline Setup** — Model versioning, training data management, experiment tracking, inference serving
- **Model Monitoring** — Output quality metrics, drift detection, A/B testing framework

## Decision 4: Architecture Patterns by AI Depth

### Surface
```
User → API Handler → LLM Client (with timeout + retry) → Response Validation → User
```
Requirements: API key in env, timeout on LLM call, basic error handling

### Core Pipeline
```
User → API Handler → Pipeline Orchestrator → [Embedding, Retrieval, LLM, Post-processing] → Response Validation → User
                                           ↓
                                     Cache Layer
```
Requirements: All surface requirements + caching, token tracking, pipeline observability

### Autonomous
```
User → API Handler → Agent Orchestrator → Tool Selection → Action Execution → Result Validation → User
                                        ↓                    ↓
                                   Guardrails         Human Approval (if high-risk)
                                        ↓
                                   Audit Log
```
Requirements: All pipeline requirements + action audit logging, human-in-loop gates, output sandboxing

### Model Owner
All above + MLOps pipeline (training, evaluation, deployment, monitoring, rollback)

## Decision 5: Provider Abstraction

If `ai_depth` >= `core_pipeline`:
- Recommend provider abstraction layer (interface/protocol/trait for LLM client)
- Enables: provider switching, A/B testing between models, cost optimization by routing to cheaper models for simple queries
- Architecture rule: `ai-provider-abstraction` — direct LLM provider imports only in the abstraction module, not in business logic

If `ai_depth` == `surface`:
- Abstraction is optional but flag single-vendor dependency risk

## Output

```json
{
  "ai_depth": "surface | core_pipeline | autonomous | model_owner",
  "ai_providers": ["openai", "anthropic"],
  "gates": {
    "validate-ai-integration": {
      "tier": 2,
      "config": {
        "REQUIRE_COST_CONTROLS": false
      }
    }
  },
  "mandatory_wos": ["AI Provider Setup"],
  "architecture_rules": [],
  "architecture_pattern": "surface",
  "provider_abstraction_recommended": false,
  "notes": []
}
```
