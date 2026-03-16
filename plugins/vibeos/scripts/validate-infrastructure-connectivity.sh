#!/usr/bin/env bash
# VibeOS — Post-Deploy Infrastructure Connectivity Gate
# Validates that the application can reach its declared external dependencies.
#
# Reads project-definition.json or .env.example to identify required services,
# then attempts lightweight connectivity checks for each.
#
# Usage:
#   bash scripts/validate-infrastructure-connectivity.sh
#   bash scripts/validate-infrastructure-connectivity.sh --project-dir /path/to/project
#   bash scripts/validate-infrastructure-connectivity.sh --strict
#
# Environment:
#   PROJECT_ROOT  — project root directory (default: auto-detect)
#
# Exit codes:
#   0 = All connectivity checks passed (or advisory mode)
#   1 = One or more connectivity checks failed in strict mode
#   2 = Configuration error
set -euo pipefail

FRAMEWORK_VERSION="2.0.0"
GATE_NAME="validate-infrastructure-connectivity"

# ─── Defaults ────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$SCRIPT_DIR/.." && pwd)}"
STRICT=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-dir) PROJECT_ROOT="$2"; shift 2 ;;
    --strict) STRICT=true; shift ;;
    -h|--help)
      echo "Usage: bash $0 [--project-dir PATH] [--strict]"
      exit 0
      ;;
    *) shift ;;
  esac
done

echo "[$GATE_NAME] Infrastructure Connectivity Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Project: $PROJECT_ROOT"
echo "Mode: $([ "$STRICT" = true ] && echo 'STRICT (blocking)' || echo 'ADVISORY (non-blocking)')"
echo ""

PASS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

# ─── Service Detection ───────────────────────────────────────────
# Build a list of services to check from project-definition.json and .env patterns

declare -a SERVICES=()

# Method 1: Read from project-definition.json
PROJ_DEF="$PROJECT_ROOT/project-definition.json"
if [[ -f "$PROJ_DEF" ]] && command -v python3 >/dev/null 2>&1; then
  while IFS= read -r svc; do
    SERVICES+=("$svc")
  done < <(python3 - "$PROJ_DEF" <<'PYEOF'
import json, sys
from pathlib import Path

proj = json.loads(Path(sys.argv[1]).read_text())

# Extract database type
db = proj.get("stack", {}).get("database", "")
if db:
    print(f"database:{db}")

# Extract cloud provider
cloud = proj.get("agent", {}).get("cloud_provider", "")
if cloud:
    print(f"cloud:{cloud}")

# Look for known service patterns in the full config
flat = json.dumps(proj).lower()
service_hints = {
    "redis": "redis",
    "cosmos": "cosmosdb",
    "ai_search": "azure-ai-search",
    "openai": "azure-openai",
    "blob": "azure-blob",
    "key_vault": "azure-keyvault",
    "rabbitmq": "rabbitmq",
    "kafka": "kafka",
    "elasticsearch": "elasticsearch",
    "s3": "aws-s3",
    "dynamodb": "aws-dynamodb",
    "sqs": "aws-sqs",
    "sns": "aws-sns",
}
for hint, svc in service_hints.items():
    if hint in flat:
        print(f"service:{svc}")
PYEOF
  )
fi

# Method 2: Read from .env.example or .env.template
for envfile in "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env.template" "$PROJECT_ROOT/.env.sample"; do
  if [[ -f "$envfile" ]]; then
    while IFS= read -r line; do
      # Skip comments and empty lines
      [[ -z "$line" || "$line" =~ ^# ]] && continue
      var_name="${line%%=*}"
      case "$var_name" in
        *DATABASE_URL*|*DB_HOST*|*POSTGRES*|*PG_*)
          SERVICES+=("env:postgresql")
          ;;
        *REDIS_*|*CACHE_URL*)
          SERVICES+=("env:redis")
          ;;
        *COSMOS*|*COSMOSDB*)
          SERVICES+=("env:cosmosdb")
          ;;
        *AZURE_OPENAI*|*OPENAI_*)
          SERVICES+=("env:azure-openai")
          ;;
        *AI_SEARCH*|*SEARCH_*)
          SERVICES+=("env:azure-ai-search")
          ;;
        *BLOB_*|*STORAGE_ACCOUNT*)
          SERVICES+=("env:azure-blob")
          ;;
        *KEY_VAULT*|*KEYVAULT*)
          SERVICES+=("env:azure-keyvault")
          ;;
        *RABBITMQ*|*AMQP_*)
          SERVICES+=("env:rabbitmq")
          ;;
        *KAFKA_*)
          SERVICES+=("env:kafka")
          ;;
        *ELASTICSEARCH*|*ELASTIC_*)
          SERVICES+=("env:elasticsearch")
          ;;
        *AWS_S3*|*S3_BUCKET*)
          SERVICES+=("env:aws-s3")
          ;;
        *DYNAMODB*)
          SERVICES+=("env:aws-dynamodb")
          ;;
      esac
    done < "$envfile"
    break  # Only read the first env file found
  fi
done

# Deduplicate services by extracting the service name after the colon
# (bash 3.2 compatible — no associative arrays)
declare -a UNIQUE_SERVICES=()
_SEEN_LIST=""
for entry in ${SERVICES[@]+"${SERVICES[@]}"}; do
  svc="${entry#*:}"
  case ",$_SEEN_LIST," in
    *",$svc,"*) ;;  # already seen
    *)
      _SEEN_LIST="${_SEEN_LIST:+$_SEEN_LIST,}$svc"
      UNIQUE_SERVICES+=("$svc")
      ;;
  esac
done

if [[ ${#UNIQUE_SERVICES[@]} -eq 0 ]]; then
  echo "[$GATE_NAME] SKIP: No external services detected in project-definition.json or .env.example"
  echo "[$GATE_NAME] SKIP: Add service configuration to enable connectivity validation"
  exit 0
fi

echo "Detected ${#UNIQUE_SERVICES[@]} service(s) to check:"
for svc in "${UNIQUE_SERVICES[@]}"; do
  echo "  - $svc"
done
echo ""

# ─── Connectivity Checks ────────────────────────────────────────

check_postgresql() {
  local host="${PGHOST:-${DB_HOST:-localhost}}"
  local port="${PGPORT:-${DB_PORT:-5432}}"

  echo -n "  [postgresql] $host:$port ... "

  if command -v pg_isready >/dev/null 2>&1; then
    if pg_isready -h "$host" -p "$port" -t 5 >/dev/null 2>&1; then
      echo "PASS"
      PASS_COUNT=$((PASS_COUNT + 1))
      return
    fi
  fi

  # Fallback: TCP check
  if (echo >/dev/tcp/"$host"/"$port") 2>/dev/null; then
    echo "PASS (TCP only)"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo "FAIL (cannot reach $host:$port)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

check_redis() {
  local host="${REDIS_HOST:-localhost}"
  local port="${REDIS_PORT:-6379}"

  echo -n "  [redis] $host:$port ... "

  if command -v redis-cli >/dev/null 2>&1; then
    if redis-cli -h "$host" -p "$port" ping 2>/dev/null | grep -q PONG; then
      echo "PASS"
      PASS_COUNT=$((PASS_COUNT + 1))
      return
    fi
  fi

  # Fallback: TCP check
  if (echo >/dev/tcp/"$host"/"$port") 2>/dev/null; then
    echo "PASS (TCP only)"
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    echo "FAIL (cannot reach $host:$port)"
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
}

check_url_reachable() {
  local name="$1"
  local url_var="$2"
  local url="${!url_var:-}"

  echo -n "  [$name] "

  if [[ -z "$url" ]]; then
    echo "SKIP (env var $url_var not set)"
    SKIP_COUNT=$((SKIP_COUNT + 1))
    return
  fi

  echo -n "$url ... "

  if command -v curl >/dev/null 2>&1; then
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")
    if [[ "$http_code" != "000" ]]; then
      echo "PASS (HTTP $http_code)"
      PASS_COUNT=$((PASS_COUNT + 1))
    else
      echo "FAIL (connection failed)"
      FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
  else
    echo "SKIP (curl not available)"
    SKIP_COUNT=$((SKIP_COUNT + 1))
  fi
}

check_azure_service() {
  local name="$1"
  local endpoint_var="$2"
  local endpoint="${!endpoint_var:-}"

  echo -n "  [$name] "

  if [[ -z "$endpoint" ]]; then
    echo "SKIP (env var $endpoint_var not set)"
    SKIP_COUNT=$((SKIP_COUNT + 1))
    return
  fi

  echo -n "$endpoint ... "

  if command -v curl >/dev/null 2>&1; then
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$endpoint" 2>/dev/null || echo "000")
    if [[ "$http_code" != "000" ]]; then
      echo "PASS (HTTP $http_code)"
      PASS_COUNT=$((PASS_COUNT + 1))
    else
      echo "FAIL (connection failed)"
      FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
  else
    echo "SKIP (curl not available)"
    SKIP_COUNT=$((SKIP_COUNT + 1))
  fi
}

# ─── Run Checks ─────────────────────────────────────────────────
echo "--- Connectivity Results ---"

for svc in "${UNIQUE_SERVICES[@]}"; do
  case "$svc" in
    postgresql|postgres)
      check_postgresql
      ;;
    redis)
      check_redis
      ;;
    cosmosdb)
      check_azure_service "cosmosdb" "COSMOS_ENDPOINT"
      ;;
    azure-openai)
      check_azure_service "azure-openai" "AZURE_OPENAI_ENDPOINT"
      ;;
    azure-ai-search)
      check_azure_service "azure-ai-search" "AI_SEARCH_ENDPOINT"
      ;;
    azure-blob)
      check_azure_service "azure-blob" "AZURE_STORAGE_ACCOUNT_URL"
      ;;
    azure-keyvault)
      check_azure_service "azure-keyvault" "AZURE_KEY_VAULT_URL"
      ;;
    rabbitmq)
      _rmq_host="${RABBITMQ_HOST:-localhost}"
      _rmq_port="${RABBITMQ_PORT:-5672}"
      echo -n "  [rabbitmq] $_rmq_host:$_rmq_port ... "
      if (echo >/dev/tcp/"$_rmq_host"/"$_rmq_port") 2>/dev/null; then
        echo "PASS"
        PASS_COUNT=$((PASS_COUNT + 1))
      else
        echo "FAIL"
        FAIL_COUNT=$((FAIL_COUNT + 1))
      fi
      ;;
    kafka)
      _kafka_bootstrap="${KAFKA_BOOTSTRAP_SERVERS:-localhost:9092}"
      echo -n "  [kafka] $_kafka_bootstrap ... "
      k_host="${_kafka_bootstrap%%:*}"
      k_port="${_kafka_bootstrap##*:}"
      if (echo >/dev/tcp/"$k_host"/"$k_port") 2>/dev/null; then
        echo "PASS"
        PASS_COUNT=$((PASS_COUNT + 1))
      else
        echo "FAIL"
        FAIL_COUNT=$((FAIL_COUNT + 1))
      fi
      ;;
    elasticsearch)
      check_url_reachable "elasticsearch" "ELASTICSEARCH_URL"
      ;;
    aws-s3|aws-dynamodb|aws-sqs|aws-sns)
      echo -n "  [$svc] "
      if command -v aws >/dev/null 2>&1; then
        if aws sts get-caller-identity >/dev/null 2>&1; then
          echo "PASS (AWS credentials valid)"
          PASS_COUNT=$((PASS_COUNT + 1))
        else
          echo "FAIL (AWS credentials invalid or expired)"
          FAIL_COUNT=$((FAIL_COUNT + 1))
        fi
      else
        echo "SKIP (aws cli not installed)"
        SKIP_COUNT=$((SKIP_COUNT + 1))
      fi
      ;;
    *)
      echo "  [$svc] SKIP (no check implemented)"
      SKIP_COUNT=$((SKIP_COUNT + 1))
      ;;
  esac
done

# ─── Summary ────────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "[$GATE_NAME] Passed: $PASS_COUNT | Failed: $FAIL_COUNT | Skipped: $SKIP_COUNT"

if [[ $FAIL_COUNT -gt 0 ]]; then
  if [[ "$STRICT" == "true" ]]; then
    echo "[$GATE_NAME] FAIL: $FAIL_COUNT service(s) unreachable (strict mode)"
    echo "[$GATE_NAME] NOTE: Ensure services are running and environment variables are set"
    exit 1
  else
    echo "[$GATE_NAME] WARN: $FAIL_COUNT service(s) unreachable (advisory mode)"
    echo "[$GATE_NAME] NOTE: Use --strict to make this gate blocking"
    exit 0
  fi
elif [[ $SKIP_COUNT -gt 0 && $PASS_COUNT -eq 0 ]]; then
  echo "[$GATE_NAME] SKIP: All checks skipped (missing tools or env vars)"
  exit 0
else
  echo "[$GATE_NAME] PASS: All $PASS_COUNT service(s) reachable"
  exit 0
fi
