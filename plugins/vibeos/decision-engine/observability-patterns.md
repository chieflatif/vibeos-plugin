# Observability Patterns Decision Tree

## Purpose

When a project targets production deployment or customer-facing use, determine the appropriate
observability stack, monitoring WOs, and operational readiness requirements.

## Entry Condition

This tree is evaluated when `project-definition.json` contains:
- `deployment_context` is `production`, `customer-facing`, or `scale`
- OR `compliance` includes `soc2` (SOC 2 requires operational monitoring)

## Decision 1: Observability Depth

Classify the observability needs:

| Deployment Context | Classification | Minimum Requirements |
|-------------------|---------------|---------------------|
| Prototype / internal-only | **Minimal** | Structured logging only |
| Production (single service) | **Standard** | Logging + health endpoint + error tracking + basic metrics |
| Customer-facing | **Full** | Standard + distributed tracing + alerting + runbook |
| Scale / multi-service | **Enterprise** | Full + SLO dashboards + on-call rotation + incident management |

**Output:** `observability_depth: minimal | standard | full | enterprise`

## Decision 2: Gate Selection

### Always enable:
- `validate-logging-patterns.sh` (existing gate, already enabled)

### Enable for `standard` and above:
- `validate-observability.sh` with `REQUIRE_HEALTH=true`
- `validate-resilience-patterns.sh` (tier 2)

### Enable for `full` and above:
- `validate-observability.sh` with `REQUIRE_METRICS=true`
- `validate-resilience-patterns.sh` (upgrade to tier 1)
- `REQUIRE_TRACING=true` on validate-observability.sh (if multi-service)

### Enable for `enterprise`:
- All `full` gates at tier 1 (blocking)
- `REQUIRE_CIRCUIT_BREAKERS=true` on validate-resilience-patterns.sh

**Output:**
```json
{
  "observability_gates": [
    {
      "script": "validate-observability.sh",
      "tier": 2,
      "config": {
        "REQUIRE_HEALTH": true,
        "REQUIRE_METRICS": false,
        "REQUIRE_TRACING": false
      }
    },
    {
      "script": "validate-resilience-patterns.sh",
      "tier": 2,
      "config": {
        "REQUIRE_CIRCUIT_BREAKERS": false
      }
    }
  ]
}
```

## Decision 3: Stack Recommendation by Language

### Python (FastAPI / Django / Flask)

| Component | Recommended | Alternative |
|-----------|------------|-------------|
| Structured logging | `structlog` | `python-json-logger` |
| Metrics | `prometheus-client` | OpenTelemetry metrics |
| Tracing | `opentelemetry-sdk` | `ddtrace` (Datadog) |
| Error tracking | `sentry-sdk` | Rollbar, Bugsnag |
| Health endpoint | FastAPI: built-in route; Django: `django-health-check` | Custom `/healthz` |
| Request ID | `asgi-correlation-id` or middleware | Custom middleware |

### TypeScript/JavaScript (Express / NestJS / Next.js)

| Component | Recommended | Alternative |
|-----------|------------|-------------|
| Structured logging | `pino` | `winston` |
| Metrics | `prom-client` | OpenTelemetry metrics |
| Tracing | `@opentelemetry/sdk-node` | `dd-trace` (Datadog) |
| Error tracking | `@sentry/node` | Bugsnag |
| Health endpoint | NestJS: `@nestjs/terminus`; Express: custom route | `/health` route |
| Request ID | `cls-hooked` + middleware | `express-request-id` |

### Go

| Component | Recommended | Alternative |
|-----------|------------|-------------|
| Structured logging | `slog` (stdlib) | `zap`, `zerolog` |
| Metrics | `prometheus/client_golang` | OpenTelemetry |
| Tracing | `go.opentelemetry.io/otel` | Jaeger client |
| Error tracking | Sentry Go SDK | Custom with structured logging |
| Health endpoint | Custom `/healthz` handler | `alexliesenfeld/health` |
| Request ID | Middleware with `X-Request-ID` | `chi` middleware |

## Decision 4: Mandatory WOs for Observable Systems

### For `standard`:
Add to Development Plan (in Foundation or as cross-cutting phase):
- **Observability Foundation** — Structured logging with correlation IDs, health endpoint with dependency checks, error tracking integration (Sentry/equivalent)

### For `full`:
Add all `standard` WOs plus:
- **Metrics & Monitoring** — Request latency histograms, error rate counters, resource saturation gauges, basic alerting thresholds
- **Runbook Creation** — Document top 5 expected failure modes, their symptoms, and resolution steps

### For `enterprise`:
Add all `full` WOs plus:
- **Distributed Tracing** — Cross-service trace propagation, trace sampling configuration, trace-to-log correlation
- **SLO Dashboard** — Define SLIs (latency p99, error rate, availability), set SLO targets, create dashboard, configure alerts on SLO burn rate
- **Incident Response Setup** — PagerDuty/OpsGenie integration, escalation policy, on-call rotation, post-incident review template

## Decision 5: Health Endpoint Design

The health endpoint is critical for container orchestrators, load balancers, and monitoring.

### Required health endpoint responses:

```json
// GET /health or /healthz
{
  "status": "healthy | degraded | unhealthy",
  "version": "1.2.3",
  "timestamp": "2024-01-01T00:00:00Z",
  "checks": {
    "database": { "status": "healthy", "latency_ms": 5 },
    "cache": { "status": "healthy", "latency_ms": 1 },
    "external_api": { "status": "degraded", "latency_ms": 2500 }
  }
}
```

Rules:
- `/health` — shallow check (app is running), used by load balancers, must respond <100ms
- `/health/ready` or `/readyz` — deep check (all dependencies reachable), used by orchestrators
- Never expose sensitive data in health responses (no connection strings, no internal IPs)
- Return HTTP 200 for healthy/degraded, HTTP 503 for unhealthy

## Output

```json
{
  "observability_depth": "standard | full | enterprise",
  "gates": {
    "validate-observability": { "tier": 2, "config": {} },
    "validate-resilience-patterns": { "tier": 2, "config": {} }
  },
  "stack": {
    "logging": "structlog",
    "metrics": "prometheus-client",
    "tracing": "opentelemetry-sdk",
    "error_tracking": "sentry-sdk",
    "health": "custom /healthz route"
  },
  "mandatory_wos": ["Observability Foundation"],
  "notes": []
}
```
