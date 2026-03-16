#!/usr/bin/env bash
set -euo pipefail

# validate-observability.sh — Health endpoints, metrics, tracing, error tracking, alerting
# VC Audit Dimension: D9 (Observability & Operability)
# Checks that production-targeted apps have the instrumentation needed to diagnose
# issues, measure performance, and detect failures.
#
# Exit codes:
#   0 — All checks pass
#   1 — Violations found (blocking)
#   2 — Configuration error or not applicable (skip)
#
# Environment:
#   PROJECT_ROOT     — Project root directory (default: pwd)
#   REQUIRE_METRICS  — Require metrics instrumentation (default: false)
#   REQUIRE_TRACING  — Require distributed tracing (default: false)
#   REQUIRE_HEALTH   — Require health endpoint (default: true for production)
#   EXCLUDE_DIRS     — Colon-separated directories to exclude

FRAMEWORK_VERSION="2.0.0"
GATE_NAME="validate-observability"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
REQUIRE_METRICS="${REQUIRE_METRICS:-false}"
REQUIRE_TRACING="${REQUIRE_TRACING:-false}"
REQUIRE_HEALTH="${REQUIRE_HEALTH:-true}"
EXCLUDE_DIRS="${EXCLUDE_DIRS:-}"

VIOLATIONS=0
WARNINGS=0
CHECKS_PASSED=0

# -------------------------------------------------------------------
# Check for health endpoint
# -------------------------------------------------------------------
check_health_endpoint() {
    local health_found=false

    # Pattern: route definitions containing health/healthz/readyz/livez
    if grep -rq '"/health"\|"/healthz"\|"/readyz"\|"/livez"\|/health\b\|health_check\|healthCheck\|HealthCheck' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" --include="*.java" --include="*.rs" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Health check endpoint detected"
        health_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    # Docker/K8s health probes
    if grep -rq 'healthcheck\|livenessProbe\|readinessProbe\|startupProbe' \
        "$PROJECT_ROOT" --include="Dockerfile*" --include="*.yaml" --include="*.yml" --include="docker-compose*" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Container health probe configured"
        health_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    if [ "$health_found" = "false" ]; then
        if [ "$REQUIRE_HEALTH" = "true" ]; then
            echo "[${GATE_NAME}] FAIL: No health check endpoint — production systems must expose /health or /healthz"
            VIOLATIONS=$((VIOLATIONS + 1))
        else
            echo "[${GATE_NAME}] WARN: No health check endpoint detected"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Check for metrics collection
# -------------------------------------------------------------------
check_metrics() {
    local metrics_found=false

    # Prometheus client libraries
    if grep -rq 'prometheus_client\|prom-client\|prometheus\|PrometheusMetrics\|@PrometheusMetric' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Prometheus metrics integration detected"
        metrics_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    # StatsD / Datadog
    if grep -rq 'statsd\|datadog\|DogStatsD\|dd-trace\|ddtrace' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: StatsD/Datadog metrics detected"
        metrics_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    # OpenTelemetry metrics
    if grep -rq 'opentelemetry.*metrics\|MeterProvider\|meter\.create' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: OpenTelemetry metrics detected"
        metrics_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    # Application Insights (Azure)
    if grep -rq 'applicationinsights\|APPINSIGHTS_INSTRUMENTATIONKEY\|APPLICATION_INSIGHTS' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.env*" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Azure Application Insights detected"
        metrics_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    # CloudWatch
    if grep -rq 'cloudwatch\|CloudWatch\|put_metric_data\|putMetricData' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: AWS CloudWatch metrics detected"
        metrics_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    if [ "$metrics_found" = "false" ]; then
        if [ "$REQUIRE_METRICS" = "true" ]; then
            echo "[${GATE_NAME}] FAIL: No metrics instrumentation detected — required for production observability"
            VIOLATIONS=$((VIOLATIONS + 1))
        else
            echo "[${GATE_NAME}] WARN: No metrics instrumentation — latency, error rates, saturation will be invisible"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Check for distributed tracing
# -------------------------------------------------------------------
check_tracing() {
    local tracing_found=false

    # OpenTelemetry
    if grep -rq 'opentelemetry\|TracerProvider\|tracer\.start_span\|@opentelemetry' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: OpenTelemetry tracing detected"
        tracing_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    # Jaeger
    if grep -rq 'jaeger\|JAEGER_AGENT\|JaegerExporter' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" --include="*.env*" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Jaeger tracing detected"
        tracing_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    # Zipkin
    if grep -rq 'zipkin\|ZipkinExporter' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Zipkin tracing detected"
        tracing_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    # AWS X-Ray
    if grep -rq 'aws-xray\|xray_recorder\|AWSXRayDaemon' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: AWS X-Ray tracing detected"
        tracing_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    # DD-Trace
    if grep -rq 'dd-trace\|ddtrace\|datadog.*trace' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Datadog tracing detected"
        tracing_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    if [ "$tracing_found" = "false" ]; then
        if [ "$REQUIRE_TRACING" = "true" ]; then
            echo "[${GATE_NAME}] FAIL: No distributed tracing detected — required for multi-service debugging"
            VIOLATIONS=$((VIOLATIONS + 1))
        else
            echo "[${GATE_NAME}] WARN: No distributed tracing — cross-service debugging will be manual"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Check for error tracking
# -------------------------------------------------------------------
check_error_tracking() {
    local error_tracking_found=false

    # Sentry
    if grep -rq 'sentry_sdk\|@sentry/node\|@sentry/browser\|sentry\.init\|SENTRY_DSN\|Sentry\.init' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.env*" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Sentry error tracking detected"
        error_tracking_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    # Bugsnag
    if grep -rq 'bugsnag\|Bugsnag\|BUGSNAG_API_KEY' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.env*" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Bugsnag error tracking detected"
        error_tracking_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    # Rollbar
    if grep -rq 'rollbar\|Rollbar\|ROLLBAR_ACCESS_TOKEN' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.env*" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Rollbar error tracking detected"
        error_tracking_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    # Airbrake
    if grep -rq 'airbrake\|Airbrake\|AIRBRAKE_PROJECT' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.env*" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Airbrake error tracking detected"
        error_tracking_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    if [ "$error_tracking_found" = "false" ]; then
        echo "[${GATE_NAME}] WARN: No centralized error tracking — errors will disappear into log files"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# -------------------------------------------------------------------
# Check for request latency instrumentation
# -------------------------------------------------------------------
check_latency_instrumentation() {
    local latency_found=false

    # Middleware-based request timing
    if grep -rq 'process_time\|request_duration\|request_latency\|response_time\|requestDuration\|responseTime\|elapsed\|X-Response-Time' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Request latency instrumentation detected"
        latency_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    # Histogram/Summary metrics (Prometheus pattern)
    if grep -rq 'Histogram\|Summary\|histogram_quantile\|request_seconds' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Latency histogram/summary metrics detected"
        latency_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    if [ "$latency_found" = "false" ]; then
        echo "[${GATE_NAME}] WARN: No request latency instrumentation — p50/p95/p99 latency will be unknown"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# -------------------------------------------------------------------
# Check for alerting configuration
# -------------------------------------------------------------------
check_alerting() {
    local alerting_found=false

    # Alert rule files
    if eval "find \"$PROJECT_ROOT\" -name 'alerts.yml' -o -name 'alerts.yaml' -o -name 'alert_rules*' -o -name 'monitors.json' -o -name 'alarms.json' -o -name '*alert*config*'" 2>/dev/null | head -1 | grep -q .; then
        echo "[${GATE_NAME}] PASS: Alerting configuration files detected"
        alerting_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    # PagerDuty / OpsGenie / VictorOps
    if grep -rq 'pagerduty\|opsgenie\|victorops\|PAGERDUTY\|OPSGENIE' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.yaml" --include="*.yml" --include="*.env*" --include="*.json" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Incident management integration detected"
        alerting_found=true
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    fi

    if [ "$alerting_found" = "false" ]; then
        echo "[${GATE_NAME}] WARN: No alerting configuration — failures will go unnoticed until users report them"
        WARNINGS=$((WARNINGS + 1))
    fi
}

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
main() {
    echo "[${GATE_NAME}] INFO: Starting observability validation (v${FRAMEWORK_VERSION})"

    # Check if this is an API/service project (skip for pure libraries/CLI tools)
    local is_service=false
    if grep -rq 'app\.\(run\|listen\)\|uvicorn\|gunicorn\|http\.ListenAndServe\|createServer\|express()\|FastAPI()\|Django\|flask\|HttpServer' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        is_service=true
    fi
    if [ -f "$PROJECT_ROOT/Dockerfile" ] || [ -f "$PROJECT_ROOT/docker-compose.yml" ] || [ -f "$PROJECT_ROOT/docker-compose.yaml" ]; then
        is_service=true
    fi

    if [ "$is_service" = "false" ]; then
        echo "[${GATE_NAME}] SKIP: Not a service/API project — observability checks not applicable"
        exit 0
    fi

    check_health_endpoint
    check_metrics
    check_tracing
    check_error_tracking
    check_latency_instrumentation
    check_alerting

    echo ""
    echo "[${GATE_NAME}] INFO: Observability validation complete — $CHECKS_PASSED checks passed, $VIOLATIONS violations, $WARNINGS warnings"

    if [ "$VIOLATIONS" -gt 0 ]; then
        echo "[${GATE_NAME}] FAIL: $VIOLATIONS observability violations found"
        exit 1
    fi

    if [ "$WARNINGS" -gt 0 ]; then
        echo "[${GATE_NAME}] WARN: $WARNINGS observability gaps (non-blocking but recommended)"
    fi

    echo "[${GATE_NAME}] PASS: Observability checks passed"
    exit 0
}

main "$@"
