#!/usr/bin/env bash
set -euo pipefail

# validate-data-integrity.sh — Migration management, DB constraints, transactions, idempotency, PII inventory
# VC Audit Dimension: D7 (Data Model & Persistence)
# Validates that the data layer has proper migrations, enforces constraints at the
# database level, uses transactions for multi-step operations, and handles PII correctly.
#
# Exit codes:
#   0 — All checks pass
#   1 — Violations found (blocking)
#   2 — Configuration error or no database detected (skip)
#
# Environment:
#   PROJECT_ROOT          — Project root directory (default: pwd)
#   REQUIRE_MIGRATIONS    — Require migration framework (default: true for DB projects)
#   REQUIRE_TRANSACTIONS  — Require transaction usage (default: true)
#   EXCLUDE_DIRS          — Colon-separated directories to exclude

FRAMEWORK_VERSION="2.0.0"
GATE_NAME="validate-data-integrity"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
REQUIRE_MIGRATIONS="${REQUIRE_MIGRATIONS:-true}"
REQUIRE_TRANSACTIONS="${REQUIRE_TRANSACTIONS:-true}"
EXCLUDE_DIRS="${EXCLUDE_DIRS:-}"

VIOLATIONS=0
WARNINGS=0

FIND_PRUNE="-path */node_modules -prune -o -path */.git -prune -o -path */__pycache__ -prune -o -path */venv -prune -o -path */.venv -prune -o -path */dist -prune -o -path */build -prune -o -path */.next -prune -o -path */target -prune -o -path */vendor -prune -o"

# -------------------------------------------------------------------
# Detect database usage
# -------------------------------------------------------------------
detect_database() {
    local db_type="none"

    # PostgreSQL
    if grep -rq 'psycopg\|asyncpg\|pg\|postgres\|postgresql\|DATABASE_URL.*postgres\|POSTGRES' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" --include="*.env*" --include="*.yaml" --include="*.yml" 2>/dev/null; then
        db_type="postgresql"
    fi

    # MySQL
    if grep -rq 'mysql\|pymysql\|mysql2\|MariaDB' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        db_type="mysql"
    fi

    # SQLite
    if grep -rq 'sqlite\|SQLite\|sqlite3' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        if [ "$db_type" = "none" ]; then
            db_type="sqlite"
        fi
    fi

    # MongoDB
    if grep -rq 'mongodb\|pymongo\|mongoose\|MongoClient' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        db_type="mongodb"
    fi

    # CosmosDB
    if grep -rq 'cosmos\|CosmosClient\|COSMOS' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.env*" 2>/dev/null; then
        db_type="cosmosdb"
    fi

    echo "$db_type"
}

# -------------------------------------------------------------------
# Detect ORM
# -------------------------------------------------------------------
detect_orm() {
    # SQLAlchemy
    if grep -rq 'sqlalchemy\|SQLAlchemy\|declarative_base\|mapped_column' "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
        echo "sqlalchemy"
        return
    fi
    # Django ORM
    if grep -rq 'from django.db\|models\.Model\|models\.CharField' "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
        echo "django"
        return
    fi
    # Prisma
    if [ -f "$PROJECT_ROOT/prisma/schema.prisma" ] || grep -rq '@prisma/client\|PrismaClient' "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "prisma"
        return
    fi
    # TypeORM
    if grep -rq 'typeorm\|@Entity\|@Column\|@PrimaryGeneratedColumn' "$PROJECT_ROOT" --include="*.ts" 2>/dev/null; then
        echo "typeorm"
        return
    fi
    # Sequelize
    if grep -rq 'sequelize\|Sequelize\|DataTypes' "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "sequelize"
        return
    fi
    # Drizzle
    if grep -rq 'drizzle-orm\|drizzle' "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "drizzle"
        return
    fi
    # GORM
    if grep -rq 'gorm\.io\|gorm\.Model' "$PROJECT_ROOT" --include="*.go" 2>/dev/null; then
        echo "gorm"
        return
    fi
    # Tortoise ORM
    if grep -rq 'tortoise\|Tortoise\|tortoise\.contrib' "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
        echo "tortoise"
        return
    fi
    echo "none"
}

# -------------------------------------------------------------------
# Check migration framework
# -------------------------------------------------------------------
check_migrations() {
    local migrations_found=false

    # Alembic (SQLAlchemy)
    if [ -d "$PROJECT_ROOT/alembic" ] || [ -f "$PROJECT_ROOT/alembic.ini" ]; then
        local migration_count
        migration_count=$(find "$PROJECT_ROOT/alembic/versions" -name "*.py" 2>/dev/null | wc -l | tr -d ' ')
        migration_count="${migration_count:-0}"
        echo "[${GATE_NAME}] PASS: Alembic migrations found ($migration_count versions)"
        migrations_found=true
    fi

    # Django migrations
    local django_migration_dirs
    django_migration_dirs=$(find "$PROJECT_ROOT" -type d -name "migrations" -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null || true)
    if [ -n "$django_migration_dirs" ]; then
        local total_migrations=0
        echo "$django_migration_dirs" | while IFS= read -r mdir; do
            local count
            count=$(find "$mdir" -name "*.py" -not -name "__init__.py" 2>/dev/null | wc -l | tr -d ' ')
            count="${count:-0}"
            total_migrations=$((total_migrations + count))
        done
        if grep -rq 'from django.db import migrations' "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
            echo "[${GATE_NAME}] PASS: Django migrations found"
            migrations_found=true
        fi
    fi

    # Prisma migrations
    if [ -d "$PROJECT_ROOT/prisma/migrations" ]; then
        local prisma_count
        prisma_count=$(find "$PROJECT_ROOT/prisma/migrations" -type d -mindepth 1 2>/dev/null | wc -l | tr -d ' ')
        prisma_count="${prisma_count:-0}"
        echo "[${GATE_NAME}] PASS: Prisma migrations found ($prisma_count versions)"
        migrations_found=true
    fi

    # Knex migrations
    if [ -d "$PROJECT_ROOT/migrations" ] || [ -d "$PROJECT_ROOT/db/migrations" ]; then
        if grep -rq 'exports\.up\|exports\.down\|knex\.schema' "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null; then
            echo "[${GATE_NAME}] PASS: Knex migrations found"
            migrations_found=true
        fi
    fi

    # TypeORM migrations
    if grep -rq 'MigrationInterface\|QueryRunner' "$PROJECT_ROOT" --include="*.ts" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: TypeORM migrations found"
        migrations_found=true
    fi

    # Drizzle migrations
    if [ -d "$PROJECT_ROOT/drizzle" ]; then
        echo "[${GATE_NAME}] PASS: Drizzle migrations directory found"
        migrations_found=true
    fi

    # Go migrations (golang-migrate, goose)
    if grep -rq 'golang-migrate\|goose\|atlas' "$PROJECT_ROOT" --include="*.go" --include="go.mod" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Go migration framework detected"
        migrations_found=true
    fi
    if find "$PROJECT_ROOT" -name "*.sql" -path "*/migrations/*" 2>/dev/null | head -1 | grep -q .; then
        echo "[${GATE_NAME}] PASS: SQL migration files found"
        migrations_found=true
    fi

    if [ "$migrations_found" = "false" ]; then
        if [ "$REQUIRE_MIGRATIONS" = "true" ]; then
            echo "[${GATE_NAME}] FAIL: No migration framework detected — schema changes must be versioned and reversible"
            VIOLATIONS=$((VIOLATIONS + 1))
        else
            echo "[${GATE_NAME}] WARN: No migration framework detected"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Check for database-level constraints
# -------------------------------------------------------------------
check_constraints() {
    local orm
    orm=$(detect_orm)

    case "$orm" in
        sqlalchemy)
            # Check for models without NOT NULL / unique / foreign key constraints
            local models_without_constraints
            models_without_constraints=$(grep -rn 'Column(' "$PROJECT_ROOT" --include="*.py" 2>/dev/null | grep -v 'nullable\|unique\|ForeignKey\|primary_key\|index\|server_default\|CheckConstraint' | grep -v 'test' | grep -v '#' || true)
            if [ -n "$models_without_constraints" ]; then
                local count
                count=$(echo "$models_without_constraints" | wc -l | tr -d ' ')
                echo "[${GATE_NAME}] WARN: $count Column() definitions without explicit constraints (nullable, unique, FK) — constraints default to nullable=True in SQLAlchemy"
                echo "$models_without_constraints" | head -3 | while IFS= read -r line; do
                    echo "  $line"
                done
                WARNINGS=$((WARNINGS + 1))
            else
                echo "[${GATE_NAME}] PASS: SQLAlchemy models use explicit constraints"
            fi
            ;;
        django)
            # Django fields have sensible defaults but check for blank=True without explicit intent
            local permissive_fields
            permissive_fields=$(grep -rn 'null=True.*blank=True\|blank=True.*null=True' "$PROJECT_ROOT" --include="*.py" 2>/dev/null | grep -v 'test' | grep -v '#' || true)
            if [ -n "$permissive_fields" ]; then
                local count
                count=$(echo "$permissive_fields" | wc -l | tr -d ' ')
                if [ "$count" -gt 10 ]; then
                    echo "[${GATE_NAME}] WARN: $count fields with null=True, blank=True — verify these are intentional, not default laziness"
                    WARNINGS=$((WARNINGS + 1))
                fi
            fi
            echo "[${GATE_NAME}] PASS: Django ORM enforces constraints by default"
            ;;
        prisma)
            # Prisma schema: check for missing @unique, @relation
            if [ -f "$PROJECT_ROOT/prisma/schema.prisma" ]; then
                local optional_count
                optional_count=$(grep -c '?' "$PROJECT_ROOT/prisma/schema.prisma" 2>/dev/null || true)
                optional_count="${optional_count:-0}"
                local total_fields
                total_fields=$(grep -cE '^\s+\w+\s+\w+' "$PROJECT_ROOT/prisma/schema.prisma" 2>/dev/null || true)
                total_fields="${total_fields:-1}"
                if [ "$total_fields" -gt 0 ]; then
                    local optional_pct=$((optional_count * 100 / total_fields))
                    if [ "$optional_pct" -gt 50 ]; then
                        echo "[${GATE_NAME}] WARN: $optional_pct% of Prisma fields are optional — verify this is intentional"
                        WARNINGS=$((WARNINGS + 1))
                    fi
                fi
                echo "[${GATE_NAME}] PASS: Prisma schema analyzed"
            fi
            ;;
        typeorm)
            # Check for entities without explicit nullable settings
            local loose_columns
            loose_columns=$(grep -rn '@Column()' "$PROJECT_ROOT" --include="*.ts" 2>/dev/null | grep -v 'test' || true)
            if [ -n "$loose_columns" ]; then
                local count
                count=$(echo "$loose_columns" | wc -l | tr -d ' ')
                echo "[${GATE_NAME}] WARN: $count @Column() without explicit options — TypeORM defaults to nullable"
                WARNINGS=$((WARNINGS + 1))
            fi
            ;;
    esac
}

# -------------------------------------------------------------------
# Check for transaction usage
# -------------------------------------------------------------------
check_transactions() {
    local transaction_found=false

    # Python: SQLAlchemy session, Django transaction.atomic, async context managers
    if grep -rq 'session\.begin\|session\.commit\|transaction\.atomic\|async with.*session\|begin_nested\|SAVEPOINT' \
        "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Transaction usage detected (Python)"
        transaction_found=true
    fi

    # Node: Prisma $transaction, TypeORM QueryRunner, Knex transaction
    if grep -rq '\$transaction\|queryRunner\|\.transaction(\|startTransaction\|knex\.transaction' \
        "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Transaction usage detected (Node.js)"
        transaction_found=true
    fi

    # Go: sql.Tx, BeginTx, gorm Transaction
    if grep -rq 'BeginTx\|sql\.Tx\|\.Transaction(\|\.Begin()' \
        "$PROJECT_ROOT" --include="*.go" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Transaction usage detected (Go)"
        transaction_found=true
    fi

    # Check for multi-step DB operations WITHOUT transactions (potential data corruption)
    local multi_step_no_tx=0

    # Pattern: multiple create/update/delete in same function without transaction wrapper
    # Python: multiple session.add / session.execute without begin
    local suspicious_python
    suspicious_python=$(grep -rln 'session\.\(add\|execute\|delete\)' "$PROJECT_ROOT" --include="*.py" 2>/dev/null | while IFS= read -r f; do
        local op_count
        op_count=$(grep -c 'session\.\(add\|execute\|delete\)' "$f" 2>/dev/null || true)
        op_count="${op_count:-0}"
        if [ "$op_count" -gt 2 ]; then
            local has_tx
            has_tx=$(grep -c 'begin\|commit\|atomic\|transaction' "$f" 2>/dev/null || true)
            has_tx="${has_tx:-0}"
            if [ "$has_tx" -eq 0 ]; then
                echo "$f"
            fi
        fi
    done || true)

    if [ -n "$suspicious_python" ]; then
        multi_step_no_tx=$(echo "$suspicious_python" | wc -l | tr -d ' ')
        echo "[${GATE_NAME}] WARN: $multi_step_no_tx files with multiple DB operations but no explicit transaction"
        WARNINGS=$((WARNINGS + 1))
    fi

    if [ "$transaction_found" = "false" ]; then
        if [ "$REQUIRE_TRANSACTIONS" = "true" ]; then
            echo "[${GATE_NAME}] FAIL: No transaction usage detected — multi-step operations risk partial writes"
            VIOLATIONS=$((VIOLATIONS + 1))
        else
            echo "[${GATE_NAME}] WARN: No explicit transaction usage detected"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Check for idempotency in webhook/queue handlers
# -------------------------------------------------------------------
check_idempotency() {
    local has_webhooks=false
    local has_queue_consumers=false

    # Detect webhook handlers
    if grep -rq 'webhook\|Webhook\|/webhook\|/hooks\|stripe.*event\|payload.*event' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        has_webhooks=true
    fi

    # Detect queue consumers
    if grep -rq 'celery\|rq\|bull\|BullMQ\|SQS.*receive\|consume\|subscriber\|on_message\|message_handler' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        has_queue_consumers=true
    fi

    if [ "$has_webhooks" = "true" ] || [ "$has_queue_consumers" = "true" ]; then
        # Check for idempotency patterns
        local idempotency_found=false
        if grep -rq 'idempotency_key\|idempotent\|dedup\|deduplicate\|already_processed\|event_id.*processed\|processed_events' \
            "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
            echo "[${GATE_NAME}] PASS: Idempotency pattern detected for webhook/queue handlers"
            idempotency_found=true
        fi

        if [ "$idempotency_found" = "false" ]; then
            echo "[${GATE_NAME}] WARN: Webhook/queue handlers detected but no idempotency pattern — duplicate processing risk"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Check PII field inventory
# -------------------------------------------------------------------
check_pii_inventory() {
    # Look for PII-like field names in models
    local pii_fields
    pii_fields=$(grep -rnE '(email|phone|ssn|social_security|date_of_birth|dob|address|passport|credit_card|bank_account|salary|medical|diagnosis|ip_address|full_name|first_name|last_name|birth)' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" --include="*.prisma" 2>/dev/null | \
        grep -iE '(Column|Field|field|model|schema|@Column|mapped_column|String|Int|Text|Varchar)' | \
        grep -v 'test' | grep -v '#.*email\|//.*email' | head -20 || true)

    if [ -n "$pii_fields" ]; then
        local pii_count
        pii_count=$(echo "$pii_fields" | wc -l | tr -d ' ')
        echo "[${GATE_NAME}] INFO: $pii_count PII-like fields detected in data models"

        # Check if PII fields have encryption/hashing
        local encrypted_pii=0
        if grep -rq 'encrypt\|Encrypted\|hash\|Hash\|EncryptedType\|pgcrypto\|aes_encrypt\|fernet' \
            "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
            encrypted_pii=1
            echo "[${GATE_NAME}] PASS: Encryption/hashing patterns found for data at rest"
        fi

        if [ "$encrypted_pii" -eq 0 ] && [ "$pii_count" -gt 3 ]; then
            echo "[${GATE_NAME}] WARN: $pii_count PII fields but no encryption/hashing pattern — data at rest may be unprotected"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Check for read-modify-write race conditions
# -------------------------------------------------------------------
check_race_conditions() {
    # Detect read-then-write patterns without locking
    # Python: get() then save()/update() without select_for_update or optimistic locking
    local rmw_risk
    rmw_risk=$(grep -rln 'select_for_update\|FOR UPDATE\|optimistic\|version_id\|row_version\|etag\|IF_MATCH' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null || true)

    if [ -n "$rmw_risk" ]; then
        echo "[${GATE_NAME}] PASS: Locking/optimistic concurrency pattern detected"
    else
        # Check if there are update operations that might need it
        local has_updates
        has_updates=$(grep -rq 'update\|UPDATE\|save()\|\.put\|\.patch' \
            "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null && echo "yes" || echo "no")
        if [ "$has_updates" = "yes" ]; then
            echo "[${GATE_NAME}] WARN: Update operations found but no locking/optimistic concurrency — race condition risk on concurrent writes"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
main() {
    echo "[${GATE_NAME}] INFO: Starting data integrity validation (v${FRAMEWORK_VERSION})"

    local db_type
    db_type=$(detect_database)
    echo "[${GATE_NAME}] INFO: Detected database: $db_type"

    if [ "$db_type" = "none" ]; then
        echo "[${GATE_NAME}] SKIP: No database usage detected"
        exit 0
    fi

    local orm
    orm=$(detect_orm)
    echo "[${GATE_NAME}] INFO: Detected ORM: $orm"

    check_migrations
    check_constraints
    check_transactions
    check_idempotency
    check_pii_inventory
    check_race_conditions

    echo ""
    echo "[${GATE_NAME}] INFO: Data integrity validation complete — $VIOLATIONS violations, $WARNINGS warnings"

    if [ "$VIOLATIONS" -gt 0 ]; then
        echo "[${GATE_NAME}] FAIL: $VIOLATIONS data integrity violations found"
        exit 1
    fi

    if [ "$WARNINGS" -gt 0 ]; then
        echo "[${GATE_NAME}] WARN: $WARNINGS data integrity warnings (non-blocking)"
    fi

    echo "[${GATE_NAME}] PASS: Data integrity checks passed"
    exit 0
}

main "$@"
