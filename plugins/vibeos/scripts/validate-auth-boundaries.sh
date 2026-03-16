#!/usr/bin/env bash
set -euo pipefail

# validate-auth-boundaries.sh — Auth coverage, IDOR detection, session management, SBOM, git history secrets
# VC Audit Dimension: D2 (Security Posture)
# Validates that all API endpoints have auth, no IDOR vulnerabilities exist,
# session management is secure, and no secrets exist in git history.
#
# Exit codes:
#   0 — All checks pass
#   1 — Violations found (blocking)
#   2 — Configuration error or no API found (skip)
#
# Environment:
#   PROJECT_ROOT        — Project root directory (default: pwd)
#   REQUIRE_SBOM        — Require SBOM generation (default: false)
#   GIT_HISTORY_DEPTH   — Commits to scan for secrets (default: 100)
#   EXCLUDE_DIRS        — Colon-separated directories to exclude

FRAMEWORK_VERSION="2.0.0"
GATE_NAME="validate-auth-boundaries"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
REQUIRE_SBOM="${REQUIRE_SBOM:-false}"
GIT_HISTORY_DEPTH="${GIT_HISTORY_DEPTH:-100}"
EXCLUDE_DIRS="${EXCLUDE_DIRS:-}"

VIOLATIONS=0
WARNINGS=0

# -------------------------------------------------------------------
# Check for unprotected endpoints
# -------------------------------------------------------------------
check_unprotected_endpoints() {
    local framework=""

    # Detect framework
    if grep -rq 'from fastapi\|import fastapi' "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
        framework="fastapi"
    elif grep -rq 'from django\|django\.urls' "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
        framework="django"
    elif grep -rq 'from flask\|import flask' "$PROJECT_ROOT" --include="*.py" 2>/dev/null; then
        framework="flask"
    elif grep -rq "require('express')\|from 'express'\|from \"express\"" "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null; then
        framework="express"
    elif grep -rq '@nestjs/common\|@Controller' "$PROJECT_ROOT" --include="*.ts" 2>/dev/null; then
        framework="nestjs"
    elif grep -rq 'net/http\|gin-gonic\|gorilla/mux\|echo\|chi' "$PROJECT_ROOT" --include="*.go" 2>/dev/null; then
        framework="go"
    fi

    case "$framework" in
        fastapi)
            # Find route definitions and check for Depends() with auth
            local routes_without_auth
            routes_without_auth=$(grep -rn '@\(app\|router\)\.\(get\|post\|put\|delete\|patch\)' "$PROJECT_ROOT" --include="*.py" 2>/dev/null | \
                grep -v 'test' | grep -v '#' || true)

            if [ -n "$routes_without_auth" ]; then
                local total_routes
                total_routes=$(echo "$routes_without_auth" | wc -l | tr -d ' ')

                # Check which route files have auth dependencies
                local auth_routes=0
                echo "$routes_without_auth" | while IFS= read -r route_line; do
                    local route_file
                    route_file=$(echo "$route_line" | cut -d: -f1)
                    if grep -q 'Depends.*auth\|Depends.*get_current_user\|Depends.*verify_token\|Depends.*require_auth\|Security(' "$route_file" 2>/dev/null; then
                        auth_routes=$((auth_routes + 1))
                    fi
                done

                # Check for explicitly public endpoints (health, docs, login)
                local public_patterns='health\|healthz\|docs\|redoc\|openapi\|login\|register\|signup\|token\|callback\|webhook\|public'
                local public_count
                public_count=$(echo "$routes_without_auth" | grep -ci "$public_patterns" || true)
                public_count="${public_count:-0}"

                # Files with routes but no auth import
                local unprotected_files
                unprotected_files=$(echo "$routes_without_auth" | cut -d: -f1 | sort -u | while IFS= read -r f; do
                    if ! grep -q 'Depends.*auth\|Depends.*get_current\|Security(\|oauth2_scheme\|HTTPBearer\|APIKeyHeader' "$f" 2>/dev/null; then
                        local rel
                        rel=$(python3 -c "import os; print(os.path.relpath('$f', '${PROJECT_ROOT}'))" 2>/dev/null || echo "$f")
                        echo "$rel"
                    fi
                done || true)

                if [ -n "$unprotected_files" ]; then
                    local unprotected_count
                    unprotected_count=$(echo "$unprotected_files" | wc -l | tr -d ' ')
                    echo "[${GATE_NAME}] WARN: $unprotected_count route files without auth dependency injection:"
                    echo "$unprotected_files" | head -5 | while IFS= read -r f; do
                        echo "  $f"
                    done
                    WARNINGS=$((WARNINGS + 1))
                else
                    echo "[${GATE_NAME}] PASS: FastAPI routes have auth dependencies"
                fi
            fi
            ;;

        django)
            # Check for views without permission_classes or login_required
            local undecorated_views
            undecorated_views=$(grep -rln 'def.*request' "$PROJECT_ROOT" --include="*.py" 2>/dev/null | grep -v 'test\|migration' | while IFS= read -r f; do
                if grep -q 'def.*request' "$f" 2>/dev/null; then
                    if ! grep -q 'permission_classes\|login_required\|IsAuthenticated\|@login_required\|@permission_required' "$f" 2>/dev/null; then
                        python3 -c "import os; print(os.path.relpath('$f', '${PROJECT_ROOT}'))" 2>/dev/null || echo "$f"
                    fi
                fi
            done || true)

            if [ -n "$undecorated_views" ]; then
                local count
                count=$(echo "$undecorated_views" | wc -l | tr -d ' ')
                echo "[${GATE_NAME}] WARN: $count view files without explicit permission checks:"
                echo "$undecorated_views" | head -5 | while IFS= read -r f; do
                    echo "  $f"
                done
                WARNINGS=$((WARNINGS + 1))
            else
                echo "[${GATE_NAME}] PASS: Django views have permission checks"
            fi
            ;;

        express|nestjs)
            # Check for routes without auth middleware
            local route_files
            route_files=$(grep -rln 'router\.\|app\.\(get\|post\|put\|delete\|patch\)\|@Get\|@Post\|@Put\|@Delete\|@Patch' \
                "$PROJECT_ROOT" --include="*.ts" --include="*.js" 2>/dev/null | grep -v 'test\|spec\|node_modules' || true)

            if [ -n "$route_files" ]; then
                local unprotected_files
                unprotected_files=$(echo "$route_files" | while IFS= read -r f; do
                    if ! grep -q 'auth\|Auth\|jwt\|JWT\|passport\|guard\|Guard\|@UseGuards\|middleware.*auth\|isAuthenticated\|requireAuth\|verifyToken' "$f" 2>/dev/null; then
                        local rel
                        rel=$(python3 -c "import os; print(os.path.relpath('$f', '${PROJECT_ROOT}'))" 2>/dev/null || echo "$f")
                        echo "$rel"
                    fi
                done || true)

                if [ -n "$unprotected_files" ]; then
                    local count
                    count=$(echo "$unprotected_files" | wc -l | tr -d ' ')
                    echo "[${GATE_NAME}] WARN: $count route files without auth middleware:"
                    echo "$unprotected_files" | head -5 | while IFS= read -r f; do
                        echo "  $f"
                    done
                    WARNINGS=$((WARNINGS + 1))
                else
                    echo "[${GATE_NAME}] PASS: Express/NestJS routes have auth middleware"
                fi
            fi
            ;;

        go)
            # Check for handler functions without auth middleware
            local handler_files
            handler_files=$(grep -rln 'func.*http\.ResponseWriter\|func.*gin\.Context\|func.*echo\.Context' \
                "$PROJECT_ROOT" --include="*.go" 2>/dev/null | grep -v 'test' || true)

            if [ -n "$handler_files" ]; then
                local unprotected_files
                unprotected_files=$(echo "$handler_files" | while IFS= read -r f; do
                    if ! grep -q 'auth\|Auth\|jwt\|JWT\|middleware\|token\|session' "$f" 2>/dev/null; then
                        local rel
                        rel=$(python3 -c "import os; print(os.path.relpath('$f', '${PROJECT_ROOT}'))" 2>/dev/null || echo "$f")
                        echo "$rel"
                    fi
                done || true)

                if [ -n "$unprotected_files" ]; then
                    local count
                    count=$(echo "$unprotected_files" | wc -l | tr -d ' ')
                    echo "[${GATE_NAME}] WARN: $count handler files without auth middleware reference"
                    WARNINGS=$((WARNINGS + 1))
                fi
            fi
            ;;
    esac
}

# -------------------------------------------------------------------
# Check for IDOR (Insecure Direct Object Reference) patterns
# -------------------------------------------------------------------
check_idor() {
    # Pattern: route parameter used directly in DB query without ownership verification
    # e.g., /users/{user_id} → SELECT * FROM users WHERE id = user_id (no check that requester owns this)

    local idor_risks=""

    # Python: path parameter used in direct query without current_user comparison
    idor_risks=$(grep -rn 'def.*\(.*_id.*\)\|def.*\(.*item_id.*\)\|def.*\(.*user_id.*\)' "$PROJECT_ROOT" --include="*.py" 2>/dev/null | \
        grep -v 'test\|#\|current_user\|get_current' || true)

    # Check for direct ID usage in queries
    local direct_id_queries
    direct_id_queries=$(grep -rn 'get(.*_id)\|filter(id=.*_id)\|WHERE.*id.*=.*{.*_id\|findOne.*_id\|findById.*_id\|findUnique.*id.*_id' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null | \
        grep -v 'test\|#\|//\|current_user\|request\.user\|req\.user\|ctx\.user\|session\.user' | head -10 || true)

    if [ -n "$direct_id_queries" ]; then
        local count
        count=$(echo "$direct_id_queries" | wc -l | tr -d ' ')
        echo "[${GATE_NAME}] WARN: $count potential IDOR patterns — object lookup by ID without ownership verification:"
        echo "$direct_id_queries" | head -3 | while IFS= read -r line; do
            echo "  $line"
        done
        echo "  Review these to ensure the requesting user has authorization to access the referenced object"
        WARNINGS=$((WARNINGS + 1))
    else
        echo "[${GATE_NAME}] PASS: No obvious IDOR patterns detected"
    fi
}

# -------------------------------------------------------------------
# Check session management security
# -------------------------------------------------------------------
check_session_security() {
    local session_issues=0

    # Token expiry
    if grep -rq 'jwt\|JWT\|jsonwebtoken\|PyJWT\|jose\|token' "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        # Check for token expiry configuration
        if grep -rq 'exp\|expires\|expiresIn\|ACCESS_TOKEN_EXPIRE\|TOKEN_LIFETIME\|max_age\|ttl' \
            "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" --include="*.env*" 2>/dev/null; then
            echo "[${GATE_NAME}] PASS: Token expiry configuration detected"
        else
            echo "[${GATE_NAME}] WARN: JWT/token usage without expiry configuration — tokens may never expire"
            WARNINGS=$((WARNINGS + 1))
            session_issues=$((session_issues + 1))
        fi

        # Check for token in URL (insecure)
        local token_in_url
        token_in_url=$(grep -rn 'token=.*\?.*token\|access_token=.*query\|jwt=.*params\|apikey=.*query' \
            "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null | \
            grep -v 'test\|#\|//' || true)
        if [ -n "$token_in_url" ]; then
            echo "[${GATE_NAME}] FAIL: Token/API key passed in URL query parameters — visible in logs, browser history, referrer headers:"
            echo "$token_in_url" | head -3 | while IFS= read -r line; do
                echo "  $line"
            done
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    fi

    # Cookie security flags
    if grep -rq 'Set-Cookie\|cookie\|Cookie\|session' "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        # Check for httponly, secure, samesite flags
        local insecure_cookies
        insecure_cookies=$(grep -rn 'set_cookie\|cookie(' "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null | \
            grep -v 'httponly\|HttpOnly\|http_only\|secure\|Secure\|samesite\|SameSite' | \
            grep -v 'test\|#\|//' || true)
        if [ -n "$insecure_cookies" ]; then
            local count
            count=$(echo "$insecure_cookies" | wc -l | tr -d ' ')
            echo "[${GATE_NAME}] WARN: $count cookie operations without explicit security flags (httponly, secure, samesite)"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Scan git history for leaked secrets
# -------------------------------------------------------------------
check_git_history_secrets() {
    if ! git -C "$PROJECT_ROOT" rev-parse --git-dir >/dev/null 2>&1; then
        echo "[${GATE_NAME}] SKIP: Not a git repository — cannot scan history"
        return 0
    fi

    echo "[${GATE_NAME}] INFO: Scanning last $GIT_HISTORY_DEPTH commits for secrets..."

    local secret_patterns='AKIA[0-9A-Z]\{16\}\|ASIA[0-9A-Z]\{16\}\|ghp_[a-zA-Z0-9]\{36\}\|gho_[a-zA-Z0-9]\{36\}\|ghs_[a-zA-Z0-9]\{36\}\|sk-[a-zA-Z0-9]\{32,}\|-----BEGIN.*PRIVATE KEY\|password[[:space:]]*=[[:space:]]*["\x27][^"\x27]\{8,\}\|PRIVATE.KEY.*=.*[A-Za-z0-9+/=]\{40,\}'

    local found_secrets
    found_secrets=$(git -C "$PROJECT_ROOT" log --all -p -n "$GIT_HISTORY_DEPTH" 2>/dev/null | \
        grep -n "$secret_patterns" 2>/dev/null | \
        grep -v 'XXXX\|xxxx\|\[REDACTED\]\|example\|placeholder\|test\|mock\|fake\|dummy\|sample' | \
        head -10 || true)

    if [ -n "$found_secrets" ]; then
        local count
        count=$(echo "$found_secrets" | wc -l | tr -d ' ')
        echo "[${GATE_NAME}] FAIL: $count potential secrets found in git history:"
        echo "$found_secrets" | head -5 | while IFS= read -r line; do
            # Truncate the actual secret value
            local truncated
            truncated=$(echo "$line" | cut -c1-100)
            echo "  ${truncated}..."
        done
        echo "  Run 'git filter-repo' or 'BFG Repo Cleaner' to remove from history"
        VIOLATIONS=$((VIOLATIONS + 1))
    else
        echo "[${GATE_NAME}] PASS: No secrets detected in recent git history"
    fi
}

# -------------------------------------------------------------------
# Check for SBOM generation
# -------------------------------------------------------------------
check_sbom() {
    local sbom_found=false

    # Check for SBOM tools in CI/scripts
    if grep -rq 'cyclonedx\|syft\|sbom\|SBOM\|spdx\|SPDX\|software-bill-of-materials' \
        "$PROJECT_ROOT" --include="*.yaml" --include="*.yml" --include="*.json" --include="*.sh" --include="Makefile" --include="*.toml" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: SBOM generation tooling detected"
        sbom_found=true
    fi

    # Check for SBOM output files
    if eval "find \"$PROJECT_ROOT\" -name '*sbom*' -o -name '*cyclonedx*' -o -name '*spdx*'" 2>/dev/null | head -1 | grep -q .; then
        echo "[${GATE_NAME}] PASS: SBOM output files found"
        sbom_found=true
    fi

    if [ "$sbom_found" = "false" ]; then
        if [ "$REQUIRE_SBOM" = "true" ]; then
            echo "[${GATE_NAME}] FAIL: No SBOM generation — required for supply chain security compliance"
            VIOLATIONS=$((VIOLATIONS + 1))
        else
            echo "[${GATE_NAME}] WARN: No SBOM generation — recommended for enterprise supply chain security"
            WARNINGS=$((WARNINGS + 1))
        fi
    fi
}

# -------------------------------------------------------------------
# Check for password hashing strength
# -------------------------------------------------------------------
check_password_hashing() {
    # Detect password hashing in use
    local strong_hash=false
    local weak_hash=false

    # Strong hashing
    if grep -rq 'bcrypt\|argon2\|scrypt\|pbkdf2\|Bcrypt\|Argon2\|PBKDF2' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null; then
        echo "[${GATE_NAME}] PASS: Strong password hashing detected (bcrypt/argon2/scrypt/pbkdf2)"
        strong_hash=true
    fi

    # Weak hashing used for passwords
    local weak_password_hash
    weak_password_hash=$(grep -rn 'md5.*password\|sha1.*password\|sha256.*password\|password.*md5\|password.*sha1\|hashlib\.md5\|hashlib\.sha1\|crypto\.createHash.*md5\|crypto\.createHash.*sha1' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" --include="*.go" 2>/dev/null | \
        grep -v 'test\|#\|//' || true)

    if [ -n "$weak_password_hash" ]; then
        echo "[${GATE_NAME}] FAIL: Weak hash algorithm used for passwords (MD5/SHA1/SHA256 without stretching):"
        echo "$weak_password_hash" | head -3 | while IFS= read -r line; do
            echo "  $line"
        done
        VIOLATIONS=$((VIOLATIONS + 1))
        weak_hash=true
    fi

    # Plain text password storage
    local plaintext_password
    plaintext_password=$(grep -rn 'password.*=.*password\|user\.password.*=.*request\|password.*CharField\|password.*String(' \
        "$PROJECT_ROOT" --include="*.py" --include="*.ts" --include="*.js" 2>/dev/null | \
        grep -v 'test\|#\|//\|hash\|Hash\|bcrypt\|encrypt\|Encrypt\|set_password\|make_password' | head -5 || true)

    if [ -n "$plaintext_password" ]; then
        local count
        count=$(echo "$plaintext_password" | wc -l | tr -d ' ')
        echo "[${GATE_NAME}] WARN: $count potential plaintext password storage patterns — verify these use hashing:"
        echo "$plaintext_password" | head -3 | while IFS= read -r line; do
            echo "  $line"
        done
        WARNINGS=$((WARNINGS + 1))
    fi
}

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
main() {
    echo "[${GATE_NAME}] INFO: Starting auth boundary validation (v${FRAMEWORK_VERSION})"

    check_unprotected_endpoints
    check_idor
    check_session_security
    check_git_history_secrets
    check_sbom
    check_password_hashing

    echo ""
    echo "[${GATE_NAME}] INFO: Auth boundary validation complete — $VIOLATIONS violations, $WARNINGS warnings"

    if [ "$VIOLATIONS" -gt 0 ]; then
        echo "[${GATE_NAME}] FAIL: $VIOLATIONS auth boundary violations found"
        exit 1
    fi

    if [ "$WARNINGS" -gt 0 ]; then
        echo "[${GATE_NAME}] WARN: $WARNINGS auth boundary warnings (non-blocking)"
    fi

    echo "[${GATE_NAME}] PASS: Auth boundary checks passed"
    exit 0
}

main "$@"
