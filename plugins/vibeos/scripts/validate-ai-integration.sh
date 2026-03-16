#!/usr/bin/env bash
set -euo pipefail

# validate-ai-integration.sh — LLM safety, prompt injection, cost control, hallucination handling
# VC Audit Dimension: D11 (AI/ML & Generated Code Assessment)
# Validates that AI/LLM integrations have input sanitization, cost controls,
# output validation, model version pinning, and fallback behavior.
#
# Exit codes:
#   0 — All checks pass (or no AI integration detected)
#   1 — Violations found (blocking)
#   2 — Configuration error (skip)
#
# Environment:
#   PROJECT_ROOT      — Project root directory (default: pwd)
#   REQUIRE_COST_CONTROLS — Require cost monitoring (default: false)
#   EXCLUDE_DIRS      — Colon-separated directories to exclude

FRAMEWORK_VERSION="2.0.0"
GATE_NAME="validate-ai-integration"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
REQUIRE_COST_CONTROLS="${REQUIRE_COST_CONTROLS:-false}"
EXCLUDE_DIRS="${EXCLUDE_DIRS:-}"

VIOLATIONS=0
WARNINGS=0

# -------------------------------------------------------------------
# Detect AI/LLM usage
# -------------------------------------------------------------------
detect_ai_usage() {
    local ai_found=false
    local ai_providers=""

    # OpenAI
    if grep -rq 'openai\|OpenAI\|OPENAI_API_KEY\|gpt-4\|gpt-3\.5\|o1-\|o3-\|chatgpt' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" --include="*.env*" 2>/dev/null; then
        ai_found=true
        ai_providers="${ai_providers}openai,"
    fi

    # Anthropic
    if grep -rq 'anthropic\|Anthropic\|ANTHROPIC_API_KEY\|claude-\|claude_' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" --include="*.env*" 2>/dev/null; then
        ai_found=true
        ai_providers="${ai_providers}anthropic,"
    fi

    # Azure OpenAI
    if grep -rq 'AZURE_OPENAI\|azure.*openai\|AzureOpenAI\|azure_endpoint' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.env*" 2>/dev/null; then
        ai_found=true
        ai_providers="${ai_providers}azure-openai,"
    fi

    # LangChain
    if grep -rq 'langchain\|LangChain\|ChatOpenAI\|ChatAnthropic\|LLMChain\|AgentExecutor' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null; then
        ai_found=true
        ai_providers="${ai_providers}langchain,"
    fi

    # LlamaIndex
    if grep -rq 'llama_index\|llama-index\|LlamaIndex\|VectorStoreIndex\|ServiceContext' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null; then
        ai_found=true
        ai_providers="${ai_providers}llamaindex,"
    fi

    # Hugging Face
    if grep -rq 'transformers\|huggingface\|HuggingFace\|AutoModel\|pipeline(' \
        "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
        ai_found=true
        ai_providers="${ai_providers}huggingface,"
    fi

    # Google AI
    if grep -rq 'google.*generativeai\|gemini\|GOOGLE_AI_KEY\|vertex_ai\|vertexai' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.env*" 2>/dev/null; then
        ai_found=true
        ai_providers="${ai_providers}google-ai,"
    fi

    # Cohere
    if grep -rq 'cohere\|Cohere\|COHERE_API_KEY' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.env*" 2>/dev/null; then
        ai_found=true
        ai_providers="${ai_providers}cohere,"
    fi

    if [ "$ai_found" = "true" ]; then
        # Remove trailing comma
        ai_providers="${ai_providers%,}"
        echo "$ai_providers"
    else
        echo "none"
    fi
}

# -------------------------------------------------------------------
# Check for prompt injection protection
# -------------------------------------------------------------------
check_prompt_injection() {
    # Look for user input being concatenated directly into prompts
    local unsafe_prompt_patterns

    # Python: f-string or .format() with user input in prompt
    unsafe_prompt_patterns=$(grep -rn 'f".*{.*user.*}.*prompt\|f".*{.*input.*}.*system\|f".*{.*message.*}.*role.*system\|\.format(.*user_input\|\.format(.*request\.' \
        "$PROJECT_ROOT" --include="*.py" 2>/dev/null | grep -v 'test\|#' || true)

    # JS/TS: template literals with user input in prompt
    local unsafe_js_prompts
    unsafe_js_prompts=$(grep -rn '`.*\${.*user.*}.*prompt\|`.*\${.*input.*}.*system\|`.*\${.*message.*}.*role.*system' \
        "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null | grep -v 'test\|//' || true)

    if [ -n "$unsafe_prompt_patterns" ] || [ -n "$unsafe_js_prompts" ]; then
        local combined=""
        if [ -n "$unsafe_prompt_patterns" ]; then combined="$unsafe_prompt_patterns"; fi
        if [ -n "$unsafe_js_prompts" ]; then
            if [ -n "$combined" ]; then
                combined="$combined
$unsafe_js_prompts"
            else
                combined="$unsafe_js_prompts"
            fi
        fi
        local count
        count=$(echo "$combined" | wc -l | tr -d ' ')
        echo "[${GATE_NAME}] WARN: $count potential prompt injection vectors — user input interpolated directly into LLM prompts:"
        echo "$combined" | head -3 | while IFS= read -r line; do
            echo "  $line"
        done
        WARNINGS=$((WARNINGS + 1))
    else
        echo "[${GATE_NAME}] PASS: No obvious prompt injection patterns detected"
    fi

    # Check for input sanitization before LLM calls
    if grep -rq 'sanitize.*prompt\|clean.*input.*llm\|validate.*prompt\|strip.*injection\|prompt.*guard\|guardrail' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Prompt input sanitization/guardrails detected"
    else
        echo "[${GATE_NAME}] WARN: No prompt sanitization or guardrail patterns detected"
        WARNINGS=$((WARNINGS + 1))
    fi

    # Check for system prompt extraction protection
    if grep -rq 'system.*prompt.*secret\|do not reveal.*system\|ignore.*previous.*instructions\|jailbreak' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] INFO: System prompt protection instructions detected"
    fi
}

# -------------------------------------------------------------------
# Check for LLM output validation
# -------------------------------------------------------------------
check_output_validation() {
    # Check if LLM output is validated before use
    local output_validation_found=false

    # Structured output parsing (JSON mode, Pydantic, Zod)
    if grep -rq 'response_format.*json\|json_mode\|\.parse(\|Pydantic.*model\|BaseModel.*response\|zod.*parse\|z\.object\|json\.loads.*response\|JSON\.parse.*response' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: LLM output validation/parsing detected"
        output_validation_found=true
    fi

    # Content filtering
    if grep -rq 'content.*filter\|moderation\|safety.*check\|toxic\|harmful\|ContentFilter\|ModerationModel' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Content filtering/moderation detected"
        output_validation_found=true
    fi

    if [ "$output_validation_found" = "false" ]; then
        echo "[${GATE_NAME}] WARN: No LLM output validation — raw model output may reach users or database without checks"
        WARNINGS=$((WARNINGS + 1))
    fi

    # Check if LLM output is written directly to database or executed
    local dangerous_output_usage
    dangerous_output_usage=$(grep -rn 'exec.*response\|eval.*completion\|execute.*llm_output\|\.execute(.*ai_response\|db\.run(.*generated\|cursor\.execute(.*llm' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null | grep -v 'test\|#\|//' || true)

    if [ -n "$dangerous_output_usage" ]; then
        echo "[${GATE_NAME}] FAIL: LLM output executed as code or used in raw DB queries — critical injection risk:"
        echo "$dangerous_output_usage" | head -3 | while IFS= read -r line; do
            echo "  $line"
        done
        VIOLATIONS=$((VIOLATIONS + 1))
    fi
}

# -------------------------------------------------------------------
# Check for cost controls
# -------------------------------------------------------------------
check_cost_controls() {
    local cost_controls_found=false

    # Token counting / usage tracking
    if grep -rq 'token.*count\|usage.*tokens\|total_tokens\|prompt_tokens\|completion_tokens\|token_usage\|track.*usage\|usage.*track\|cost.*track\|track.*cost' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Token/usage tracking detected"
        cost_controls_found=true
    fi

    # Rate limiting on AI endpoints
    if grep -rq 'rate.*limit.*ai\|rate.*limit.*llm\|ai.*rate.*limit\|max.*requests.*ai\|quota.*ai\|usage.*limit' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: AI-specific rate limiting detected"
        cost_controls_found=true
    fi

    # Spend caps / budget alerts
    if grep -rq 'max.*spend\|budget.*alert\|cost.*threshold\|spend.*limit\|billing.*alert\|USAGE_CAP\|MAX_TOKENS_PER' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.env*" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Cost/spend controls detected"
        cost_controls_found=true
    fi

    # Caching of AI responses
    if grep -rq 'cache.*llm\|cache.*ai\|cache.*embed\|cache.*completion\|semantic.*cache\|embedding.*cache\|prompt.*cache' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: AI response caching detected — reduces cost at scale"
        cost_controls_found=true
    fi

    if [ "$cost_controls_found" = "false" ]; then
        if [ "$REQUIRE_COST_CONTROLS" = "true" ]; then
            echo "[${GATE_NAME}] FAIL: No AI cost controls detected — uncontrolled LLM spend risk"
            VIOLATIONS=$((VIOLATIONS + 1))
        else
            echo "[${GATE_NAME}] WARN: No AI cost controls (token tracking, rate limits, spend caps, caching) — costs will scale linearly with usage"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Check for model version pinning
# -------------------------------------------------------------------
check_model_versioning() {
    # Look for model references that use "latest" or unversioned
    local unpinned_models
    unpinned_models=$(grep -rn 'model.*=.*"gpt-4"\|model.*=.*"gpt-3.5-turbo"\|model.*=.*"claude-3"\|model.*=.*"claude-2"\|model.*"latest"\|model.*"stable"' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.env*" 2>/dev/null | \
        grep -v 'test\|#\|//' || true)

    if [ -n "$unpinned_models" ]; then
        local count
        count=$(echo "$unpinned_models" | wc -l | tr -d ' ')
        echo "[${GATE_NAME}] WARN: $count model references without version pin (e.g., 'gpt-4' instead of 'gpt-4-0613'):"
        echo "$unpinned_models" | head -3 | while IFS= read -r line; do
            echo "  $line"
        done
        echo "  Unpinned models change behavior without code changes — pin to dated versions"
        WARNINGS=$((WARNINGS + 1))
    else
        echo "[${GATE_NAME}] PASS: Model references appear version-pinned"
    fi
}

# -------------------------------------------------------------------
# Check for AI fallback behavior
# -------------------------------------------------------------------
check_ai_fallback() {
    local fallback_found=false

    # Retry logic
    if grep -rq 'retry.*openai\|retry.*anthropic\|retry.*llm\|tenacity.*retry\|backoff.*retry\|max_retries.*ai\|RateLimitError' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: AI API retry logic detected"
        fallback_found=true
    fi

    # Fallback behavior
    if grep -rq 'fallback.*model\|fallback.*provider\|except.*OpenAI\|except.*Anthropic\|catch.*rate.*limit\|if.*ai.*unavailable\|ai.*timeout\|llm.*fallback' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: AI service fallback behavior detected"
        fallback_found=true
    fi

    # Timeout on AI calls
    if grep -rq 'timeout.*openai\|timeout.*anthropic\|timeout.*llm\|ai.*timeout\|request_timeout.*=\|max_tokens.*=' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Timeout configuration on AI calls detected"
        fallback_found=true
    fi

    if [ "$fallback_found" = "false" ]; then
        echo "[${GATE_NAME}] WARN: No AI fallback, retry, or timeout patterns — service outage will cascade to users"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# -------------------------------------------------------------------
# Check for single AI vendor dependency
# -------------------------------------------------------------------
check_vendor_lock() {
    local providers
    providers=$(detect_ai_usage)

    local provider_count
    provider_count=$(echo "$providers" | tr ',' '\n' | wc -l | tr -d ' ')

    if [ "$provider_count" -eq 1 ] && [ "$providers" != "none" ]; then
        echo "[${GATE_NAME}] WARN: Single AI vendor dependency ($providers) — consider abstraction layer for provider switching"
        WARNINGS=$((WARNINGS + 1))
    elif [ "$provider_count" -gt 1 ]; then
        echo "[${GATE_NAME}] PASS: Multiple AI providers detected ($providers) — reduced vendor lock-in"
    fi

    # Check for abstraction layer
    if grep -rq 'class.*LLM\|class.*AIProvider\|class.*ModelProvider\|interface.*LLM\|interface.*AIProvider\|BaseLLM\|BaseModel.*provider' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: AI provider abstraction layer detected"
    fi
}

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
main() {
    echo "[${GATE_NAME}] INFO: Starting AI integration validation (v${FRAMEWORK_VERSION})"

    local providers
    providers=$(detect_ai_usage)

    if [ "$providers" = "none" ]; then
        echo "[${GATE_NAME}] SKIP: No AI/LLM integration detected — dimension not applicable"
        exit 0
    fi

    echo "[${GATE_NAME}] INFO: AI providers detected: $providers"

    check_prompt_injection
    check_output_validation
    check_cost_controls
    check_model_versioning
    check_ai_fallback
    check_vendor_lock

    echo ""
    echo "[${GATE_NAME}] INFO: AI integration validation complete — $VIOLATIONS violations, $WARNINGS warnings"

    if [ "$VIOLATIONS" -gt 0 ]; then
        echo "[${GATE_NAME}] FAIL: $VIOLATIONS AI integration violations found"
        exit 1
    fi

    if [ "$WARNINGS" -gt 0 ]; then
        echo "[${GATE_NAME}] WARN: $WARNINGS AI integration warnings (non-blocking)"
    fi

    echo "[${GATE_NAME}] PASS: AI integration checks passed"
    exit 0
}

main "$@"
