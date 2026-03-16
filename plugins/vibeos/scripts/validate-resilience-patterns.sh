#!/usr/bin/env bash
set -euo pipefail

# validate-resilience-patterns.sh — Circuit breakers, timeouts, retries, graceful shutdown, DLQ
# VC Audit Dimensions: D3 (Architecture) + D10 (API & Integration)
# Validates that external service calls have timeout, retry, and circuit breaker patterns,
# that async processors have dead letter queues, and that the app handles SIGTERM gracefully.
#
# Exit codes:
#   0 — All checks pass
#   1 — Violations found (blocking)
#   2 — Configuration error or not applicable (skip)
#
# Environment:
#   PROJECT_ROOT      — Project root directory (default: pwd)
#   REQUIRE_CIRCUIT_BREAKERS — Require circuit breaker pattern (default: false)
#   EXCLUDE_DIRS      — Colon-separated directories to exclude

FRAMEWORK_VERSION="2.0.0"
GATE_NAME="validate-resilience-patterns"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
REQUIRE_CIRCUIT_BREAKERS="${REQUIRE_CIRCUIT_BREAKERS:-false}"
EXCLUDE_DIRS="${EXCLUDE_DIRS:-}"

VIOLATIONS=0
WARNINGS=0

# -------------------------------------------------------------------
# Check for external HTTP calls without timeouts
# -------------------------------------------------------------------
check_http_timeouts() {
    local no_timeout_count=0

    # Python: requests library without timeout
    local bare_requests
    bare_requests=$(grep -rn 'requests\.\(get\|post\|put\|delete\|patch\|head\)(' \
        "$PROJECT_ROOT" --include="*.py" 2>/dev/null | \
        grep -v 'timeout' | grep -v '#' | grep -v 'test' | grep -v 'mock' || true)
    if [ -n "$bare_requests" ]; then
        local count
        count=$(echo "$bare_requests" | wc -l | tr -d ' ')
        echo "[${GATE_NAME}] WARN: $count requests.* calls without timeout — will hang indefinitely on slow responses:"
        echo "$bare_requests" | head -3 | while IFS= read -r line; do
            echo "  $line"
        done
        no_timeout_count=$((no_timeout_count + count))
        WARNINGS=$((WARNINGS + 1))
    fi

    # Python: httpx without timeout
    local bare_httpx
    bare_httpx=$(grep -rn 'httpx\.\(get\|post\|put\|delete\|patch\|AsyncClient\|Client\)(' \
        "$PROJECT_ROOT" --include="*.py" 2>/dev/null | \
        grep -v 'timeout' | grep -v '#' | grep -v 'test' || true)
    if [ -n "$bare_httpx" ]; then
        local count
        count=$(echo "$bare_httpx" | wc -l | tr -d ' ')
        echo "[${GATE_NAME}] WARN: $count httpx calls without timeout"
        no_timeout_count=$((no_timeout_count + count))
        WARNINGS=$((WARNINGS + 1))
    fi

    # Node: fetch without AbortController/signal
    local bare_fetch
    bare_fetch=$(grep -rn 'fetch(' "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null | \
        grep -v 'signal\|AbortController\|timeout' | grep -v 'test\|spec\|mock\|//' || true)
    if [ -n "$bare_fetch" ]; then
        local count
        count=$(echo "$bare_fetch" | wc -l | tr -d ' ')
        echo "[${GATE_NAME}] WARN: $count fetch() calls without AbortController/signal — no timeout protection"
        no_timeout_count=$((no_timeout_count + count))
        WARNINGS=$((WARNINGS + 1))
    fi

    # Node: axios without timeout
    local bare_axios
    bare_axios=$(grep -rn 'axios\.\(get\|post\|put\|delete\|patch\)(' \
        "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null | \
        grep -v 'timeout' | grep -v 'test\|spec\|mock\|//' || true)
    if [ -n "$bare_axios" ]; then
        local count
        count=$(echo "$bare_axios" | wc -l | tr -d ' ')
        echo "[${GATE_NAME}] WARN: $count axios calls without timeout"
        no_timeout_count=$((no_timeout_count + count))
        WARNINGS=$((WARNINGS + 1))
    fi

    # Go: http.Client without Timeout
    local bare_go_http
    bare_go_http=$(grep -rn 'http\.DefaultClient\|http\.Get(\|http\.Post(' \
        "$PROJECT_ROOT" --include="*.go" 2>/dev/null | \
        grep -v 'test\|//' || true)
    if [ -n "$bare_go_http" ]; then
        local count
        count=$(echo "$bare_go_http" | wc -l | tr -d ' ')
        echo "[${GATE_NAME}] WARN: $count uses of http.DefaultClient or http.Get/Post (no timeout) — use custom client with Timeout"
        no_timeout_count=$((no_timeout_count + count))
        WARNINGS=$((WARNINGS + 1))
    fi

    if [ "$no_timeout_count" -eq 0 ]; then
        echo "[${GATE_NAME}] PASS: External HTTP calls have timeout configuration"
    fi
}

# -------------------------------------------------------------------
# Check for retry logic with backoff
# -------------------------------------------------------------------
check_retry_patterns() {
    local retry_found=false

    # Python: tenacity, backoff, urllib3.Retry
    if grep -rq 'tenacity\|@retry\|backoff\|Retry(\|max_retries\|retry_with_backoff\|retrying' \
        "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Retry with backoff pattern detected (Python)"
        retry_found=true
    fi

    # Node: p-retry, retry, got retry, axios-retry
    if grep -rq 'p-retry\|axios-retry\|retry.*backoff\|exponentialBackoff\|retryDelay\|maxRetries' \
        "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Retry with backoff pattern detected (Node.js)"
        retry_found=true
    fi

    # Go: retry libraries, custom retry loops with sleep
    if grep -rq 'retry\|backoff\|ExponentialBackoff\|time\.Sleep.*retry\|MaxRetries' \
        "$PROJECT_ROOT" --include="*.go" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Retry pattern detected (Go)"
        retry_found=true
    fi

    if [ "$retry_found" = "false" ]; then
        echo "[${GATE_NAME}] WARN: No retry/backoff patterns detected — transient failures in external services will propagate to users"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# -------------------------------------------------------------------
# Check for circuit breaker pattern
# -------------------------------------------------------------------
check_circuit_breakers() {
    local circuit_breaker_found=false

    # Python: pybreaker, circuitbreaker, tenacity circuit breaker
    if grep -rq 'pybreaker\|CircuitBreaker\|circuit_breaker\|circuitbreaker' \
        "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Circuit breaker pattern detected (Python)"
        circuit_breaker_found=true
    fi

    # Node: opossum, cockatiel, circuit-breaker
    if grep -rq 'opossum\|CircuitBreaker\|circuitBreaker\|cockatiel\|circuit-breaker' \
        "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Circuit breaker pattern detected (Node.js)"
        circuit_breaker_found=true
    fi

    # Go: gobreaker, hystrix-go, sony/gobreaker
    if grep -rq 'gobreaker\|hystrix\|CircuitBreaker\|circuit.*breaker' \
        "$PROJECT_ROOT" --include="*.go" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Circuit breaker pattern detected (Go)"
        circuit_breaker_found=true
    fi

    # Infrastructure level (Istio, Envoy)
    if grep -rq 'circuitBreaker\|outlierDetection\|circuit_breaker' \
        "$PROJECT_ROOT" --include="*.yaml" --include="*.yml" --include="*.json" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Circuit breaker configured at infrastructure level"
        circuit_breaker_found=true
    fi

    if [ "$circuit_breaker_found" = "false" ]; then
        if [ "$REQUIRE_CIRCUIT_BREAKERS" = "true" ]; then
            echo "[${GATE_NAME}] FAIL: No circuit breaker pattern — cascading failures will propagate across services"
            VIOLATIONS=$((VIOLATIONS + 1))
        else
            echo "[${GATE_NAME}] WARN: No circuit breaker pattern — cascading failure risk on external service outages"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Check for synchronous external calls in request path
# -------------------------------------------------------------------
check_sync_external_calls() {
    # Detect synchronous external service calls inside request handlers
    # This is a scaling bottleneck — long-running external calls block request threads

    # Python: requests (sync) used in FastAPI/Django/Flask handlers
    local sync_in_handlers
    sync_in_handlers=$(grep -rln 'requests\.\(get\|post\|put\|delete\)' "$PROJECT_ROOT" --include="*.py" 2>/dev/null | while IFS= read -r f; do
        # Check if the file also contains route/view definitions
        if grep -q '@\(app\|router\)\.\(get\|post\|put\|delete\)\|def.*request.*:\|@api_view' "$f" 2>/dev/null; then
            local rel
            rel=$(python3 -c "import os; print(os.path.relpath('$f', '${PROJECT_ROOT}'))" 2>/dev/null || echo "$f")
            echo "$rel"
        fi
    done || true)

    if [ -n "$sync_in_handlers" ]; then
        local count
        count=$(echo "$sync_in_handlers" | wc -l | tr -d ' ')
        echo "[${GATE_NAME}] WARN: $count handler files use synchronous HTTP clients (requests library) — blocks request thread during external calls:"
        echo "$sync_in_handlers" | head -3 | while IFS= read -r f; do
            echo "  $f"
        done
        echo "  Consider httpx (async) or move to background task for long-running calls"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# -------------------------------------------------------------------
# Check for dead letter queue / error queue
# -------------------------------------------------------------------
check_dead_letter_queue() {
    local has_async_processing=false
    local has_dlq=false

    # Detect async processing
    if grep -rq 'celery\|rq\|bull\|BullMQ\|SQS\|RabbitMQ\|Kafka\|redis.*queue\|taskiq\|dramatiq\|huey' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        has_async_processing=true
    fi

    if [ "$has_async_processing" = "true" ]; then
        # Check for DLQ configuration
        if grep -rq 'dead_letter\|deadLetter\|DLQ\|dlq\|failed_queue\|error_queue\|retry_queue\|on_failure\|max_retries.*=\|task_reject_on_worker_lost' \
            "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" --include="*.yaml" --include="*.yml" --include="*.json" 2>/dev/null; then
            echo "[${GATE_NAME}] PASS: Dead letter queue / failure handling detected for async processors"
            has_dlq=true
        fi

        if [ "$has_dlq" = "false" ]; then
            echo "[${GATE_NAME}] WARN: Async processing detected but no dead letter queue — failed messages will be lost silently"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Check for graceful shutdown handling
# -------------------------------------------------------------------
check_graceful_shutdown() {
    local shutdown_found=false

    # Python: signal handlers, atexit, uvicorn shutdown
    if grep -rq 'signal\.signal.*SIGTERM\|signal\.signal.*SIGINT\|atexit\.register\|on_shutdown\|@app\.on_event.*shutdown\|lifespan.*shutdown' \
        "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Graceful shutdown handler detected (Python)"
        shutdown_found=true
    fi

    # Node: process.on SIGTERM/SIGINT
    if grep -rq "process\.on.*SIGTERM\|process\.on.*SIGINT\|server\.close\|onShutdown\|beforeExit\|gracefulShutdown" \
        "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Graceful shutdown handler detected (Node.js)"
        shutdown_found=true
    fi

    # Go: signal.Notify, context cancellation
    if grep -rq 'signal\.Notify.*syscall\.SIGTERM\|signal\.Notify.*os\.Interrupt\|srv\.Shutdown\|GracefulStop' \
        "$PROJECT_ROOT" --include="*.go" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Graceful shutdown handler detected (Go)"
        shutdown_found=true
    fi

    # Docker STOPSIGNAL
    if grep -rq 'STOPSIGNAL' "$PROJECT_ROOT" --include="Dockerfile*" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Docker STOPSIGNAL configured"
        shutdown_found=true
    fi

    if [ "$shutdown_found" = "false" ]; then
        # Only warn if this is a service (not a CLI tool or library)
        if grep -rq 'app\.\(run\|listen\)\|uvicorn\|gunicorn\|http\.ListenAndServe\|createServer' \
            "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
            echo "[${GATE_NAME}] WARN: No graceful shutdown handler — in-flight requests will be terminated on deploy"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Check for connection pool management
# -------------------------------------------------------------------
check_connection_pools() {
    # Check for explicit connection pool configuration
    local pool_found=false

    # Python: SQLAlchemy pool, psycopg pool, redis connection pool
    if grep -rq 'pool_size\|max_overflow\|pool_recycle\|ConnectionPool\|connection_pool\|pool_pre_ping\|NullPool\|AsyncConnectionPool' \
        "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Database connection pool configuration detected (Python)"
        pool_found=true
    fi

    # Node: pool configuration
    if grep -rq 'connectionLimit\|pool.*max\|poolSize\|maxPoolSize\|connection_limit\|pool.*min' \
        "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Connection pool configuration detected (Node.js)"
        pool_found=true
    fi

    # Go: SetMaxOpenConns, SetMaxIdleConns
    if grep -rq 'SetMaxOpenConns\|SetMaxIdleConns\|SetConnMaxLifetime' \
        "$PROJECT_ROOT" --include="*.go" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Connection pool configuration detected (Go)"
        pool_found=true
    fi

    if [ "$pool_found" = "false" ]; then
        # Only warn if database is used
        if grep -rq 'psycopg\|sqlalchemy\|prisma\|typeorm\|mongoose\|pg\|mysql\|gorm' \
            "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
            echo "[${GATE_NAME}] WARN: No explicit connection pool configuration — default pool settings may not handle production load"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
main() {
    echo "[${GATE_NAME}] INFO: Starting resilience pattern validation (v${FRAMEWORK_VERSION})"

    # Check if this is a service (skip for pure libraries/CLI tools)
    local is_service=false
    if grep -rq 'app\.\(run\|listen\)\|uvicorn\|gunicorn\|http\.ListenAndServe\|createServer\|express()\|FastAPI()\|HttpServer' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        is_service=true
    fi

    if [ "$is_service" = "false" ]; then
        echo "[${GATE_NAME}] SKIP: Not a service project — resilience checks not applicable"
        exit 0
    fi

    check_http_timeouts
    check_retry_patterns
    check_circuit_breakers
    check_sync_external_calls
    check_dead_letter_queue
    check_graceful_shutdown
    check_connection_pools

    echo ""
    echo "[${GATE_NAME}] INFO: Resilience pattern validation complete — $VIOLATIONS violations, $WARNINGS warnings"

    if [ "$VIOLATIONS" -gt 0 ]; then
        echo "[${GATE_NAME}] FAIL: $VIOLATIONS resilience violations found"
        exit 1
    fi

    if [ "$WARNINGS" -gt 0 ]; then
        echo "[${GATE_NAME}] WARN: $WARNINGS resilience warnings (non-blocking)"
    fi

    echo "[${GATE_NAME}] PASS: Resilience pattern checks passed"
    exit 0
}

main "$@"
