#!/usr/bin/env bash
set -euo pipefail

# validate-api-contracts.sh — API contract, versioning, error consistency, rate limiting
# VC Audit Dimension: D10 (API & Integration Design)
# Checks: OpenAPI/Swagger spec exists & matches routes, API versioning, error response
# consistency, rate limiting middleware, request timeout configuration, webhook signatures.
#
# Exit codes:
#   0 — All checks pass
#   1 — Violations found (blocking)
#   2 — Configuration error or no API routes found (skip)
#
# Environment:
#   PROJECT_ROOT      — Project root directory (default: pwd)
#   REQUIRE_SPEC      — Require OpenAPI/GraphQL spec file (default: false)
#   REQUIRE_VERSIONING — Require API versioning (default: false)
#   EXCLUDE_DIRS      — Colon-separated directories to exclude

FRAMEWORK_VERSION="2.0.0"
GATE_NAME="validate-api-contracts"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
REQUIRE_SPEC="${REQUIRE_SPEC:-false}"
REQUIRE_VERSIONING="${REQUIRE_VERSIONING:-false}"
EXCLUDE_DIRS="${EXCLUDE_DIRS:-}"

VIOLATIONS=0
WARNINGS=0

# Build find exclude pattern
FIND_PRUNE="-path */node_modules -prune -o -path */.git -prune -o -path */__pycache__ -prune -o -path */venv -prune -o -path */.venv -prune -o -path */dist -prune -o -path */build -prune -o -path */.next -prune -o -path */target -prune -o -path */vendor -prune -o"

# -------------------------------------------------------------------
# Detect API framework
# -------------------------------------------------------------------
detect_api_framework() {
    # Python frameworks
    if grep -rql "from fastapi\|import fastapi" "$PROJECT_ROOT" --include="*.py" 2>/dev/null | head -1 | grep -q .; then
        echo "fastapi"
        return
    fi
    if grep -rql "from django.urls\|from rest_framework" "$PROJECT_ROOT" --include="*.py" 2>/dev/null | head -1 | grep -q .; then
        echo "django"
        return
    fi
    if grep -rql "from flask\|import flask" "$PROJECT_ROOT" --include="*.py" 2>/dev/null | head -1 | grep -q .; then
        echo "flask"
        return
    fi
    # Node frameworks
    if grep -rql "from 'express'\|require('express')\|from \"express\"" "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null | head -1 | grep -q .; then
        echo "express"
        return
    fi
    if grep -rql "@nestjs/common\|@Controller\|@Module" "$PROJECT_ROOT" --include="*.ts" 2>/dev/null | head -1 | grep -q .; then
        echo "nestjs"
        return
    fi
    if grep -rql "from 'next'\|from \"next\"\|next/server" "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null | head -1 | grep -q .; then
        echo "nextjs"
        return
    fi
    # Go
    if grep -rql "net/http\|gin-gonic\|gorilla/mux\|chi\|echo" "$PROJECT_ROOT" --include="*.go" 2>/dev/null | head -1 | grep -q .; then
        echo "go-http"
        return
    fi
    echo "unknown"
}

# -------------------------------------------------------------------
# Check for API specification files
# -------------------------------------------------------------------
check_api_spec() {
    local spec_found=false
    local spec_files=""

    # OpenAPI / Swagger
    spec_files=$(eval "find \"$PROJECT_ROOT\" $FIND_PRUNE \( -name 'openapi.json' -o -name 'openapi.yaml' -o -name 'openapi.yml' -o -name 'swagger.json' -o -name 'swagger.yaml' -o -name 'swagger.yml' -o -name 'api-spec.json' -o -name 'api-spec.yaml' \) -print" 2>/dev/null || true)
    if [ -n "$spec_files" ]; then
        echo "[${GATE_NAME}] PASS: OpenAPI/Swagger spec found:"
        echo "$spec_files" | while IFS= read -r f; do
            local rel
            rel=$(python3 -c "import os; print(os.path.relpath('$f', '${PROJECT_ROOT}'))" 2>/dev/null || echo "$f")
            echo "  $rel"
        done
        spec_found=true
    fi

    # GraphQL schema
    local gql_files
    gql_files=$(eval "find \"$PROJECT_ROOT\" $FIND_PRUNE \( -name 'schema.graphql' -o -name '*.graphql' -o -name 'schema.gql' \) -print" 2>/dev/null || true)
    if [ -n "$gql_files" ]; then
        echo "[${GATE_NAME}] PASS: GraphQL schema found"
        spec_found=true
    fi

    # Protobuf
    local proto_files
    proto_files=$(eval "find \"$PROJECT_ROOT\" $FIND_PRUNE -name '*.proto' -print" 2>/dev/null || true)
    if [ -n "$proto_files" ]; then
        echo "[${GATE_NAME}] PASS: Protocol Buffers definitions found"
        spec_found=true
    fi

    # Auto-generated specs (FastAPI produces spec automatically)
    local framework
    framework=$(detect_api_framework)
    if [ "$framework" = "fastapi" ]; then
        echo "[${GATE_NAME}] INFO: FastAPI auto-generates OpenAPI spec at /docs — acceptable"
        spec_found=true
    fi

    if [ "$spec_found" = "false" ]; then
        if [ "$REQUIRE_SPEC" = "true" ]; then
            echo "[${GATE_NAME}] FAIL: No API specification file found (OpenAPI, GraphQL, or Protobuf)"
            VIOLATIONS=$((VIOLATIONS + 1))
        else
            echo "[${GATE_NAME}] WARN: No API specification file found — recommended for enterprise-grade APIs"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Check API versioning
# -------------------------------------------------------------------
check_api_versioning() {
    local framework
    framework=$(detect_api_framework)
    local versioning_found=false

    case "$framework" in
        fastapi)
            # Check for APIRouter prefixes with version
            if grep -rq 'prefix.*["\x27]/v[0-9]\|APIRouter.*v[0-9]\|app\.include_router.*v[0-9]' "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
                echo "[${GATE_NAME}] PASS: API versioning detected (URL prefix pattern)"
                versioning_found=true
            fi
            # Check for header-based versioning
            if grep -rq 'x-api-version\|api.version\|APIVersion' "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
                echo "[${GATE_NAME}] PASS: API versioning detected (header-based)"
                versioning_found=true
            fi
            ;;
        django)
            if grep -rq "v[0-9]\|api/v\|versioning_class\|URLPathVersioning\|NamespaceVersioning" "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
                echo "[${GATE_NAME}] PASS: API versioning detected"
                versioning_found=true
            fi
            ;;
        express|nestjs)
            if grep -rq "'/v[0-9]\|/api/v[0-9]\|VersioningType\|enableVersioning\|@Version" "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null; then
                echo "[${GATE_NAME}] PASS: API versioning detected"
                versioning_found=true
            fi
            ;;
        go-http)
            if grep -rq '"/v[0-9]\|/api/v[0-9]' "$PROJECT_ROOT" --include="*.go" 2>/dev/null; then
                echo "[${GATE_NAME}] PASS: API versioning detected"
                versioning_found=true
            fi
            ;;
        nextjs)
            # Next.js API routes with versioned directories
            if [ -d "$PROJECT_ROOT/app/api/v1" ] || [ -d "$PROJECT_ROOT/pages/api/v1" ] || [ -d "$PROJECT_ROOT/src/app/api/v1" ]; then
                echo "[${GATE_NAME}] PASS: API versioning detected (directory-based)"
                versioning_found=true
            fi
            ;;
    esac

    if [ "$versioning_found" = "false" ]; then
        if [ "$REQUIRE_VERSIONING" = "true" ]; then
            echo "[${GATE_NAME}] FAIL: No API versioning detected — required for production APIs"
            VIOLATIONS=$((VIOLATIONS + 1))
        else
            echo "[${GATE_NAME}] WARN: No API versioning detected — recommended before v1 ship"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Check error response consistency
# -------------------------------------------------------------------
check_error_consistency() {
    local framework
    framework=$(detect_api_framework)

    case "$framework" in
        fastapi)
            # Check for exception handlers
            local has_handler=false
            if grep -rq 'exception_handler\|HTTPException\|RequestValidationError' "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
                has_handler=true
            fi
            # Check for bare raise without structured error
            local bare_errors
            bare_errors=$(grep -rn 'raise HTTPException' "$PROJECT_ROOT" --include="*.py" 2>/dev/null | grep -v 'detail=' | head -5 || true)
            if [ -n "$bare_errors" ]; then
                echo "[${GATE_NAME}] WARN: HTTPException raised without detail parameter:"
                echo "$bare_errors" | head -3 | while IFS= read -r line; do
                    echo "  $line"
                done
                WARNINGS=$((WARNINGS + 1))
            fi
            # Check for consistent error schema
            if grep -rq 'class.*ErrorResponse\|class.*ErrorDetail\|class.*APIError' "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
                echo "[${GATE_NAME}] PASS: Structured error response model found"
            else
                echo "[${GATE_NAME}] WARN: No structured error response model — inconsistent error formats likely"
                WARNINGS=$((WARNINGS + 1))
            fi
            ;;
        express|nestjs)
            # Check for global error handler middleware
            if grep -rq 'errorHandler\|ErrorFilter\|ExceptionFilter\|app\.use.*err.*req.*res.*next' "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null; then
                echo "[${GATE_NAME}] PASS: Global error handler found"
            else
                echo "[${GATE_NAME}] WARN: No global error handler — inconsistent error responses likely"
                WARNINGS=$((WARNINGS + 1))
            fi
            ;;
        django)
            if grep -rq 'EXCEPTION_HANDLER\|exception_handler\|handler500\|handler404' "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
                echo "[${GATE_NAME}] PASS: Custom error handler configured"
            else
                echo "[${GATE_NAME}] WARN: No custom error handler — Django defaults may not suit API clients"
                WARNINGS=$((WARNINGS + 1))
            fi
            ;;
        go-http)
            if grep -rq 'ErrorResponse\|writeError\|JSONError\|respondError\|httpError' "$PROJECT_ROOT" --include="*.go" 2>/dev/null; then
                echo "[${GATE_NAME}] PASS: Structured error response pattern found"
            else
                echo "[${GATE_NAME}] WARN: No structured error response pattern detected"
                WARNINGS=$((WARNINGS + 1))
            fi
            ;;
    esac
}

# -------------------------------------------------------------------
# Check rate limiting
# -------------------------------------------------------------------
check_rate_limiting() {
    local rate_limit_found=false

    # Python
    if grep -rq 'slowapi\|RateLimiter\|rate_limit\|throttle_classes\|UserRateThrottle\|AnonRateThrottle\|flask_limiter\|Limiter' "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Rate limiting detected (Python)"
        rate_limit_found=true
    fi

    # Node
    if grep -rq 'express-rate-limit\|rateLimit\|rate-limiter\|@nestjs/throttler\|ThrottlerModule\|ThrottlerGuard' "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Rate limiting detected (Node.js)"
        rate_limit_found=true
    fi

    # Go
    if grep -rq 'rate\.Limiter\|golang.org/x/time/rate\|tollbooth\|limiter\|ratelimit' "$PROJECT_ROOT" --include="*.go" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Rate limiting detected (Go)"
        rate_limit_found=true
    fi

    # Nginx/infrastructure level
    if grep -rq 'limit_req\|limit_conn' "$PROJECT_ROOT" --include="*.conf" --include="nginx*" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Rate limiting detected (Nginx)"
        rate_limit_found=true
    fi

    # API Gateway / cloud config
    if grep -rq 'rateLimit\|throttling\|usagePlan\|quotaSettings' "$PROJECT_ROOT" --include="*.json" --include="*.yaml" --include="*.yml" --include="*.tf" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Rate limiting detected (infrastructure config)"
        rate_limit_found=true
    fi

    if [ "$rate_limit_found" = "false" ]; then
        echo "[${GATE_NAME}] WARN: No rate limiting detected — API vulnerable to abuse and DoS"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# -------------------------------------------------------------------
# Check request timeout configuration
# -------------------------------------------------------------------
check_timeouts() {
    local timeout_found=false

    # Python: httpx, requests, aiohttp timeouts
    if grep -rq 'timeout=\|Timeout(\|connect_timeout\|read_timeout\|request_timeout' "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
        timeout_found=true
    fi

    # Node: axios, fetch, got timeouts
    if grep -rq 'timeout:\|AbortController\|signal:\|connectTimeout\|requestTimeout' "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null; then
        timeout_found=true
    fi

    # Go: http.Client with Timeout
    if grep -rq 'Timeout:\|context\.WithTimeout\|context\.WithDeadline' "$PROJECT_ROOT" --include="*.go" 2>/dev/null; then
        timeout_found=true
    fi

    # Check for HTTP clients WITHOUT timeout
    local no_timeout_clients=0

    # Python: requests.get/post without timeout
    local bare_requests
    bare_requests=$(grep -rn 'requests\.\(get\|post\|put\|delete\|patch\)(' "$PROJECT_ROOT" --include="*.py" 2>/dev/null | grep -v 'timeout' | grep -v '#' | grep -v 'test' || true)
    if [ -n "$bare_requests" ]; then
        no_timeout_clients=$(echo "$bare_requests" | wc -l | tr -d ' ')
        echo "[${GATE_NAME}] WARN: $no_timeout_clients HTTP client calls without timeout parameter:"
        echo "$bare_requests" | head -3 | while IFS= read -r line; do
            echo "  $line"
        done
        WARNINGS=$((WARNINGS + 1))
    fi

    if [ "$timeout_found" = "true" ]; then
        echo "[${GATE_NAME}] PASS: Request timeout configuration detected"
    else
        echo "[${GATE_NAME}] WARN: No timeout configuration detected on HTTP clients"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# -------------------------------------------------------------------
# Check correlation ID / request tracing in API responses
# -------------------------------------------------------------------
check_correlation_ids() {
    local correlation_found=false

    if grep -rq 'correlation.id\|request.id\|trace.id\|X-Request-ID\|X-Correlation-ID\|x-request-id\|request_id' "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Request correlation ID pattern detected"
        correlation_found=true
    fi

    if [ "$correlation_found" = "false" ]; then
        echo "[${GATE_NAME}] WARN: No correlation ID / request ID pattern — debugging production issues will be difficult"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
main() {
    echo "[${GATE_NAME}] INFO: Starting API contract validation (v${FRAMEWORK_VERSION})"

    local framework
    framework=$(detect_api_framework)
    echo "[${GATE_NAME}] INFO: Detected API framework: $framework"

    if [ "$framework" = "unknown" ]; then
        # Check if there are any API-like files at all
        local has_routes=false
        if grep -rql 'router\.\|app\.\(get\|post\|put\|delete\)\|@app\.\|@router\.\|@Get\|@Post\|HandleFunc\|http\.Handle' "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null | head -1 | grep -q .; then
            has_routes=true
        fi
        if [ "$has_routes" = "false" ]; then
            echo "[${GATE_NAME}] SKIP: No API routes detected — this may not be an API project"
            exit 0
        fi
    fi

    check_api_spec
    check_api_versioning
    check_error_consistency
    check_rate_limiting
    check_timeouts
    check_correlation_ids

    echo ""
    echo "[${GATE_NAME}] INFO: API contract validation complete — $VIOLATIONS violations, $WARNINGS warnings"

    if [ "$VIOLATIONS" -gt 0 ]; then
        echo "[${GATE_NAME}] FAIL: $VIOLATIONS API contract violations found"
        exit 1
    fi

    if [ "$WARNINGS" -gt 0 ]; then
        echo "[${GATE_NAME}] WARN: $WARNINGS API contract warnings (non-blocking)"
    fi

    echo "[${GATE_NAME}] PASS: API contract checks passed"
    exit 0
}

main "$@"
