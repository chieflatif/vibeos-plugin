#!/usr/bin/env bash
set -euo pipefail

# validate-code-complexity.sh — Cyclomatic complexity, function length, god objects
# VC Audit Dimension: D4 (Code Quality & Maintainability)
# Detects functions that are too complex, too long, or have too many parameters.
# Detects god objects (classes with excessive methods/lines).
# Uses language-native tools when available, falls back to heuristic line counting.
#
# Exit codes:
#   0 — All complexity checks pass
#   1 — Complexity violations found (blocking)
#   2 — Configuration error or no source files found (skip)
#
# Environment:
#   PROJECT_ROOT        — Project root directory (default: pwd)
#   MAX_CYCLOMATIC      — Max cyclomatic complexity per function (default: 15)
#   WARN_CYCLOMATIC     — Warn threshold for cyclomatic complexity (default: 10)
#   MAX_FUNCTION_LINES  — Max lines per function (default: 80)
#   WARN_FUNCTION_LINES — Warn threshold for function lines (default: 50)
#   MAX_PARAMS          — Max parameters per function (default: 7)
#   MAX_CLASS_METHODS   — Max methods per class (default: 15)
#   MAX_CLASS_LINES     — Max lines per class (default: 400)
#   EXCLUDE_DIRS        — Colon-separated directories to exclude
#   EXCLUDE_PATTERNS    — Colon-separated file patterns to exclude

FRAMEWORK_VERSION="2.0.0"
GATE_NAME="validate-code-complexity"

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
MAX_CYCLOMATIC="${MAX_CYCLOMATIC:-15}"
WARN_CYCLOMATIC="${WARN_CYCLOMATIC:-10}"
MAX_FUNCTION_LINES="${MAX_FUNCTION_LINES:-80}"
WARN_FUNCTION_LINES="${WARN_FUNCTION_LINES:-50}"
MAX_PARAMS="${MAX_PARAMS:-7}"
MAX_CLASS_METHODS="${MAX_CLASS_METHODS:-15}"
MAX_CLASS_LINES="${MAX_CLASS_LINES:-400}"
EXCLUDE_DIRS="${EXCLUDE_DIRS:-}"
EXCLUDE_PATTERNS="${EXCLUDE_PATTERNS:-}"

VIOLATIONS=0
WARNINGS=0

# Build exclude arguments for find
build_find_excludes() {
    local excludes=""
    # Always exclude common non-source directories
    local default_excludes="node_modules .git __pycache__ .mypy_cache .ruff_cache .pytest_cache venv .venv env .env dist build .next .nuxt target vendor"
    for d in $default_excludes; do
        excludes="$excludes -path */$d -prune -o"
    done
    # User-specified excludes
    if [ -n "$EXCLUDE_DIRS" ]; then
        local IFS=":"
        for d in $EXCLUDE_DIRS; do
            excludes="$excludes -path */$d -prune -o"
        done
    fi
    echo "$excludes"
}

FIND_EXCLUDES=$(build_find_excludes)

# Detect project language
detect_language() {
    if [ -f "$PROJECT_ROOT/pyproject.toml" ] || [ -f "$PROJECT_ROOT/setup.py" ] || [ -f "$PROJECT_ROOT/requirements.txt" ] || [ -f "$PROJECT_ROOT/Pipfile" ]; then
        echo "python"
    elif [ -f "$PROJECT_ROOT/package.json" ]; then
        if [ -f "$PROJECT_ROOT/tsconfig.json" ]; then
            echo "typescript"
        else
            echo "javascript"
        fi
    elif [ -f "$PROJECT_ROOT/go.mod" ]; then
        echo "go"
    elif [ -f "$PROJECT_ROOT/Cargo.toml" ]; then
        echo "rust"
    elif [ -f "$PROJECT_ROOT/pom.xml" ] || [ -f "$PROJECT_ROOT/build.gradle" ] || [ -f "$PROJECT_ROOT/build.gradle.kts" ]; then
        echo "java"
    else
        echo "unknown"
    fi
}

# -------------------------------------------------------------------
# Python complexity analysis
# -------------------------------------------------------------------
check_python_complexity() {
    local py_files
    py_files=$(eval "find \"$PROJECT_ROOT\" $FIND_EXCLUDES -name '*.py' -print" 2>/dev/null || true)
    if [ -z "$py_files" ]; then
        echo "[${GATE_NAME}] SKIP: No Python files found"
        return 0
    fi

    local file_count
    file_count=$(echo "$py_files" | wc -l | tr -d ' ')
    echo "[${GATE_NAME}] INFO: Analyzing $file_count Python files"

    # Try radon for cyclomatic complexity (most accurate)
    if command -v radon >/dev/null 2>&1; then
        echo "[${GATE_NAME}] INFO: Using radon for cyclomatic complexity analysis"
        local radon_output
        radon_output=$(echo "$py_files" | xargs radon cc -s -n "${WARN_CYCLOMATIC}" 2>/dev/null || true)
        if [ -n "$radon_output" ]; then
            # Parse radon output: lines like "    F 10:0 function_name - C (12)"
            echo "$radon_output" | while IFS= read -r line; do
                # File header lines don't start with spaces
                case "$line" in
                    "    "*)
                        # Extract complexity score from parentheses at end
                        local score
                        score=$(echo "$line" | grep -oE '\([0-9]+\)' | tr -d '()' || true)
                        if [ -n "$score" ]; then
                            if [ "$score" -gt "$MAX_CYCLOMATIC" ]; then
                                echo "[${GATE_NAME}] FAIL: $line — complexity $score exceeds max $MAX_CYCLOMATIC"
                                VIOLATIONS=$((VIOLATIONS + 1))
                            elif [ "$score" -gt "$WARN_CYCLOMATIC" ]; then
                                echo "[${GATE_NAME}] WARN: $line — complexity $score exceeds warn threshold $WARN_CYCLOMATIC"
                                WARNINGS=$((WARNINGS + 1))
                            fi
                        fi
                        ;;
                esac
            done
        fi
    else
        echo "[${GATE_NAME}] WARN: radon not installed — skipping cyclomatic complexity (pip install radon)"
        WARNINGS=$((WARNINGS + 1))
    fi

    # Function length and parameter count analysis via embedded Python
    python3 -c "
import ast
import sys
import os

max_func_lines = int('${MAX_FUNCTION_LINES}')
warn_func_lines = int('${WARN_FUNCTION_LINES}')
max_params = int('${MAX_PARAMS}')
max_class_methods = int('${MAX_CLASS_METHODS}')
max_class_lines = int('${MAX_CLASS_LINES}')
violations = 0
warnings = 0

for fpath in sys.stdin.read().strip().split('\n'):
    if not fpath.strip():
        continue
    try:
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
        tree = ast.parse(source, filename=fpath)
    except (SyntaxError, ValueError):
        continue

    rel = os.path.relpath(fpath, '${PROJECT_ROOT}')
    lines = source.split('\n')

    for node in ast.walk(tree):
        # Function/method length and parameter count
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if hasattr(node, 'end_lineno') and node.end_lineno:
                func_len = node.end_lineno - node.lineno + 1
            else:
                func_len = 0
            param_count = len(node.args.args) + len(node.args.posonlyargs) + len(node.args.kwonlyargs)
            # Exclude 'self' and 'cls'
            if param_count > 0 and node.args.args:
                first = node.args.args[0].arg
                if first in ('self', 'cls'):
                    param_count -= 1

            if func_len > max_func_lines:
                print(f'FAIL:{rel}:{node.lineno}: function \"{node.name}\" is {func_len} lines (max {max_func_lines})')
                violations += 1
            elif func_len > warn_func_lines:
                print(f'WARN:{rel}:{node.lineno}: function \"{node.name}\" is {func_len} lines (warn at {warn_func_lines})')
                warnings += 1

            if param_count > max_params:
                print(f'FAIL:{rel}:{node.lineno}: function \"{node.name}\" has {param_count} parameters (max {max_params})')
                violations += 1

        # God class detection
        if isinstance(node, ast.ClassDef):
            methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            if hasattr(node, 'end_lineno') and node.end_lineno:
                class_len = node.end_lineno - node.lineno + 1
            else:
                class_len = 0

            if len(methods) > max_class_methods:
                print(f'FAIL:{rel}:{node.lineno}: class \"{node.name}\" has {len(methods)} methods (max {max_class_methods})')
                violations += 1

            if class_len > max_class_lines:
                print(f'FAIL:{rel}:{node.lineno}: class \"{node.name}\" is {class_len} lines (max {max_class_lines})')
                violations += 1

print(f'SUMMARY:violations={violations},warnings={warnings}')
" <<< "$py_files" | while IFS= read -r line; do
        case "$line" in
            FAIL:*)
                echo "[${GATE_NAME}] FAIL: ${line#FAIL:}"
                VIOLATIONS=$((VIOLATIONS + 1))
                ;;
            WARN:*)
                echo "[${GATE_NAME}] WARN: ${line#WARN:}"
                WARNINGS=$((WARNINGS + 1))
                ;;
            SUMMARY:*)
                # Parse summary for accurate counts
                local v w
                v=$(echo "$line" | grep -oE 'violations=[0-9]+' | cut -d= -f2)
                w=$(echo "$line" | grep -oE 'warnings=[0-9]+' | cut -d= -f2)
                VIOLATIONS=$((VIOLATIONS + ${v:-0}))
                WARNINGS=$((WARNINGS + ${w:-0}))
                ;;
        esac
    done
}

# -------------------------------------------------------------------
# JavaScript/TypeScript complexity analysis
# -------------------------------------------------------------------
check_js_complexity() {
    local extensions
    if [ "$1" = "typescript" ]; then
        extensions="-name '*.ts' -o -name '*.tsx'"
    else
        extensions="-name '*.js' -o -name '*.jsx'"
    fi

    local js_files
    js_files=$(eval "find \"$PROJECT_ROOT\" $FIND_EXCLUDES \( $extensions \) -print" 2>/dev/null || true)
    if [ -z "$js_files" ]; then
        echo "[${GATE_NAME}] SKIP: No JS/TS files found"
        return 0
    fi

    local file_count
    file_count=$(echo "$js_files" | wc -l | tr -d ' ')
    echo "[${GATE_NAME}] INFO: Analyzing $file_count JS/TS files"

    # Function length heuristic: count lines between function/method declarations
    echo "$js_files" | while IFS= read -r fpath; do
        [ -z "$fpath" ] && continue
        local rel
        rel=$(python3 -c "import os; print(os.path.relpath('$fpath', '${PROJECT_ROOT}'))" 2>/dev/null || echo "$fpath")

        # Use awk to detect function boundaries and count lines
        awk -v max_lines="$MAX_FUNCTION_LINES" -v warn_lines="$WARN_FUNCTION_LINES" \
            -v max_params="$MAX_PARAMS" -v rel="$rel" -v gate="$GATE_NAME" '
        /^[[:space:]]*(export[[:space:]]+)?(async[[:space:]]+)?function[[:space:]]+[a-zA-Z_]/ ||
        /^[[:space:]]*[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*\(/ ||
        /^[[:space:]]*(public|private|protected|static|async|readonly)?[[:space:]]*(async[[:space:]]+)?[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*\(/ {
            if (func_name != "" && func_start > 0) {
                func_len = NR - func_start
                if (func_len > max_lines) {
                    printf "[%s] FAIL: %s:%d: function \"%s\" is ~%d lines (max %d)\n", gate, rel, func_start, func_name, func_len, max_lines
                } else if (func_len > warn_lines) {
                    printf "[%s] WARN: %s:%d: function \"%s\" is ~%d lines (warn at %d)\n", gate, rel, func_start, func_name, func_len, warn_lines
                }
            }
            # Extract function name
            func_name = $0
            gsub(/^[[:space:]]*(export[[:space:]]+)?(async[[:space:]]+)?function[[:space:]]+/, "", func_name)
            gsub(/^[[:space:]]*(public|private|protected|static|async|readonly)?[[:space:]]*(async[[:space:]]+)?/, "", func_name)
            gsub(/[[:space:]]*\(.*/, "", func_name)
            func_start = NR

            # Count parameters
            params = $0
            match(params, /\(([^)]*)\)/, arr)
            if (arr[1] != "") {
                n = split(arr[1], p, ",")
                if (n > max_params) {
                    printf "[%s] FAIL: %s:%d: function \"%s\" has %d parameters (max %d)\n", gate, rel, NR, func_name, n, max_params
                }
            }
        }
        END {
            if (func_name != "" && func_start > 0) {
                func_len = NR - func_start
                if (func_len > max_lines) {
                    printf "[%s] FAIL: %s:%d: function \"%s\" is ~%d lines (max %d)\n", gate, rel, func_start, func_name, func_len, max_lines
                } else if (func_len > warn_lines) {
                    printf "[%s] WARN: %s:%d: function \"%s\" is ~%d lines (warn at %d)\n", gate, rel, func_start, func_name, func_len, warn_lines
                }
            }
        }
        ' "$fpath"

        # God class detection: count class methods
        local class_info
        class_info=$(awk -v max_methods="$MAX_CLASS_METHODS" -v max_lines="$MAX_CLASS_LINES" \
            -v rel="$rel" -v gate="$GATE_NAME" '
        /^[[:space:]]*(export[[:space:]]+)?(abstract[[:space:]]+)?class[[:space:]]+[a-zA-Z_]/ {
            if (class_name != "" && class_start > 0) {
                class_len = NR - class_start
                if (method_count > max_methods) {
                    printf "[%s] FAIL: %s:%d: class \"%s\" has %d methods (max %d)\n", gate, rel, class_start, class_name, method_count, max_methods
                }
                if (class_len > max_lines) {
                    printf "[%s] FAIL: %s:%d: class \"%s\" is %d lines (max %d)\n", gate, rel, class_start, class_name, class_len, max_lines
                }
            }
            class_name = $0
            gsub(/^[[:space:]]*(export[[:space:]]+)?(abstract[[:space:]]+)?class[[:space:]]+/, "", class_name)
            gsub(/[[:space:]+{].*/, "", class_name)
            class_start = NR
            method_count = 0
        }
        /^[[:space:]]+(public|private|protected|static|async|readonly)?[[:space:]]*(async[[:space:]]+)?[a-zA-Z_][a-zA-Z0-9_]*[[:space:]]*\(/ {
            if (class_name != "") method_count++
        }
        END {
            if (class_name != "" && class_start > 0) {
                class_len = NR - class_start
                if (method_count > max_methods) {
                    printf "[%s] FAIL: %s:%d: class \"%s\" has %d methods (max %d)\n", gate, rel, class_start, class_name, method_count, max_methods
                }
                if (class_len > max_lines) {
                    printf "[%s] FAIL: %s:%d: class \"%s\" is %d lines (max %d)\n", gate, rel, class_start, class_name, class_len, max_lines
                }
            }
        }' "$fpath" 2>/dev/null || true)
        if [ -n "$class_info" ]; then
            echo "$class_info"
        fi
    done
}

# -------------------------------------------------------------------
# Go complexity analysis
# -------------------------------------------------------------------
check_go_complexity() {
    local go_files
    go_files=$(eval "find \"$PROJECT_ROOT\" $FIND_EXCLUDES -name '*.go' -print" 2>/dev/null || true)
    if [ -z "$go_files" ]; then
        echo "[${GATE_NAME}] SKIP: No Go files found"
        return 0
    fi

    local file_count
    file_count=$(echo "$go_files" | wc -l | tr -d ' ')
    echo "[${GATE_NAME}] INFO: Analyzing $file_count Go files"

    # Try gocyclo for cyclomatic complexity
    if command -v gocyclo >/dev/null 2>&1; then
        echo "[${GATE_NAME}] INFO: Using gocyclo for cyclomatic complexity"
        local gocyclo_output
        gocyclo_output=$(gocyclo -over "$WARN_CYCLOMATIC" "$PROJECT_ROOT" 2>/dev/null || true)
        if [ -n "$gocyclo_output" ]; then
            echo "$gocyclo_output" | while IFS= read -r line; do
                local score
                score=$(echo "$line" | awk '{print $1}')
                if [ -n "$score" ] && [ "$score" -gt "$MAX_CYCLOMATIC" ] 2>/dev/null; then
                    echo "[${GATE_NAME}] FAIL: $line — complexity $score exceeds max $MAX_CYCLOMATIC"
                    VIOLATIONS=$((VIOLATIONS + 1))
                elif [ -n "$score" ] && [ "$score" -gt "$WARN_CYCLOMATIC" ] 2>/dev/null; then
                    echo "[${GATE_NAME}] WARN: $line — complexity $score exceeds warn threshold $WARN_CYCLOMATIC"
                    WARNINGS=$((WARNINGS + 1))
                fi
            done
        fi
    else
        echo "[${GATE_NAME}] WARN: gocyclo not installed — skipping cyclomatic complexity (go install github.com/fzipp/gocyclo/cmd/gocyclo@latest)"
        WARNINGS=$((WARNINGS + 1))
    fi

    # Function length via awk
    echo "$go_files" | while IFS= read -r fpath; do
        [ -z "$fpath" ] && continue
        local rel
        rel=$(python3 -c "import os; print(os.path.relpath('$fpath', '${PROJECT_ROOT}'))" 2>/dev/null || echo "$fpath")

        awk -v max_lines="$MAX_FUNCTION_LINES" -v warn_lines="$WARN_FUNCTION_LINES" \
            -v max_params="$MAX_PARAMS" -v rel="$rel" -v gate="$GATE_NAME" '
        /^func[[:space:]]/ {
            if (func_name != "" && func_start > 0) {
                func_len = NR - func_start
                if (func_len > max_lines) {
                    printf "[%s] FAIL: %s:%d: function \"%s\" is %d lines (max %d)\n", gate, rel, func_start, func_name, func_len, max_lines
                } else if (func_len > warn_lines) {
                    printf "[%s] WARN: %s:%d: function \"%s\" is %d lines (warn at %d)\n", gate, rel, func_start, func_name, func_len, warn_lines
                }
            }
            func_name = $0
            gsub(/^func[[:space:]]+(\([^)]*\)[[:space:]]+)?/, "", func_name)
            gsub(/[[:space:]]*\(.*/, "", func_name)
            func_start = NR

            # Count parameters
            params = $0
            n = gsub(/,/, ",", params)
            n = n + 1
            if (params ~ /\(\)/) n = 0
            if (n > max_params) {
                printf "[%s] FAIL: %s:%d: function \"%s\" has ~%d parameters (max %d)\n", gate, rel, NR, func_name, n, max_params
            }
        }
        END {
            if (func_name != "" && func_start > 0) {
                func_len = NR - func_start
                if (func_len > max_lines) {
                    printf "[%s] FAIL: %s:%d: function \"%s\" is %d lines (max %d)\n", gate, rel, func_start, func_name, func_len, max_lines
                } else if (func_len > warn_lines) {
                    printf "[%s] WARN: %s:%d: function \"%s\" is %d lines (warn at %d)\n", gate, rel, func_start, func_name, func_len, warn_lines
                }
            }
        }
        ' "$fpath"
    done
}

# -------------------------------------------------------------------
# Generic fallback for Rust, Java, and unknown languages
# -------------------------------------------------------------------
check_generic_complexity() {
    local lang="$1"
    local extensions=""

    case "$lang" in
        rust)    extensions="-name '*.rs'" ;;
        java)    extensions="-name '*.java'" ;;
        *)       extensions="-name '*.py' -o -name '*.js' -o -name '*.ts' -o -name '*.go' -o -name '*.rs' -o -name '*.java'" ;;
    esac

    local src_files
    src_files=$(eval "find \"$PROJECT_ROOT\" $FIND_EXCLUDES \( $extensions \) -print" 2>/dev/null || true)
    if [ -z "$src_files" ]; then
        echo "[${GATE_NAME}] SKIP: No source files found for $lang"
        return 0
    fi

    local file_count
    file_count=$(echo "$src_files" | wc -l | tr -d ' ')
    echo "[${GATE_NAME}] INFO: Analyzing $file_count $lang files (generic heuristic)"

    # Simple line-counting heuristic for function length
    echo "$src_files" | while IFS= read -r fpath; do
        [ -z "$fpath" ] && continue
        local total_lines
        total_lines=$(wc -l < "$fpath" | tr -d ' ')

        # Flag files over 500 lines as potential god objects
        if [ "$total_lines" -gt 500 ]; then
            local rel
            rel=$(python3 -c "import os; print(os.path.relpath('$fpath', '${PROJECT_ROOT}'))" 2>/dev/null || echo "$fpath")
            echo "[${GATE_NAME}] WARN: $rel is $total_lines lines — potential god object, manual review recommended"
            WARNINGS=$((WARNINGS + 1))
        fi
    done
}

# -------------------------------------------------------------------
# Dead code estimation
# -------------------------------------------------------------------
check_dead_code() {
    local lang="$1"
    local dead_code_warnings=0

    case "$lang" in
        python)
            # Check for unused imports via Python AST
            if command -v ruff >/dev/null 2>&1; then
                local unused
                unused=$(ruff check --select F401 --no-fix "$PROJECT_ROOT" 2>/dev/null | grep -c "F401" || true)
                unused="${unused:-0}"
                if [ "$unused" -gt 0 ]; then
                    echo "[${GATE_NAME}] WARN: $unused unused imports detected (ruff F401)"
                    dead_code_warnings=$((dead_code_warnings + unused))
                fi
            fi
            ;;
        typescript|javascript)
            # Check for eslint unused vars
            if command -v eslint >/dev/null 2>&1; then
                local unused
                unused=$(cd "$PROJECT_ROOT" && eslint --rule '{"no-unused-vars": "warn"}' --format json . 2>/dev/null | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    count = sum(1 for f in data for m in f.get('messages', []) if m.get('ruleId') == 'no-unused-vars')
    print(count)
except: print(0)
" 2>/dev/null || echo "0")
                unused="${unused:-0}"
                if [ "$unused" -gt 0 ]; then
                    echo "[${GATE_NAME}] WARN: $unused unused variables detected (eslint no-unused-vars)"
                    dead_code_warnings=$((dead_code_warnings + unused))
                fi
            fi
            ;;
    esac

    # Commented-out code blocks (all languages)
    local commented_blocks=0
    local src_extensions=""
    case "$lang" in
        python)              src_extensions="*.py" ;;
        typescript)          src_extensions="*.ts" ;;
        javascript)          src_extensions="*.js" ;;
        go)                  src_extensions="*.go" ;;
        rust)                src_extensions="*.rs" ;;
        java)                src_extensions="*.java" ;;
        *)                   src_extensions="*.py" ;;
    esac

    # Count large blocks of commented-out code (3+ consecutive comment lines that look like code)
    local src_files
    src_files=$(eval "find \"$PROJECT_ROOT\" $FIND_EXCLUDES -name '$src_extensions' -print" 2>/dev/null || true)
    if [ -n "$src_files" ]; then
        commented_blocks=$(echo "$src_files" | xargs grep -l '^\s*#.*=\|^\s*//.*=\|^\s*#.*def \|^\s*//.*function\|^\s*#.*class \|^\s*//.*class ' 2>/dev/null | wc -l | tr -d ' ')
        commented_blocks="${commented_blocks:-0}"
        if [ "$commented_blocks" -gt 5 ]; then
            echo "[${GATE_NAME}] WARN: $commented_blocks files contain commented-out code blocks"
            WARNINGS=$((WARNINGS + commented_blocks))
        fi
    fi
}

# -------------------------------------------------------------------
# Main
# -------------------------------------------------------------------
main() {
    echo "[${GATE_NAME}] INFO: Starting code complexity analysis (v${FRAMEWORK_VERSION})"
    echo "[${GATE_NAME}] INFO: Thresholds — cyclomatic: warn=$WARN_CYCLOMATIC fail=$MAX_CYCLOMATIC, function-lines: warn=$WARN_FUNCTION_LINES fail=$MAX_FUNCTION_LINES, params: $MAX_PARAMS, class-methods: $MAX_CLASS_METHODS, class-lines: $MAX_CLASS_LINES"

    local lang
    lang=$(detect_language)
    echo "[${GATE_NAME}] INFO: Detected language: $lang"

    case "$lang" in
        python)
            check_python_complexity
            ;;
        typescript|javascript)
            check_js_complexity "$lang"
            ;;
        go)
            check_go_complexity
            ;;
        rust|java)
            check_generic_complexity "$lang"
            ;;
        unknown)
            # Try all known patterns
            check_generic_complexity "unknown"
            ;;
    esac

    # Dead code estimation
    check_dead_code "$lang"

    echo ""
    echo "[${GATE_NAME}] INFO: Complexity analysis complete — $VIOLATIONS violations, $WARNINGS warnings"

    if [ "$VIOLATIONS" -gt 0 ]; then
        echo "[${GATE_NAME}] FAIL: $VIOLATIONS complexity violations found"
        exit 1
    fi

    if [ "$WARNINGS" -gt 0 ]; then
        echo "[${GATE_NAME}] WARN: $WARNINGS complexity warnings (non-blocking)"
    fi

    echo "[${GATE_NAME}] PASS: Code complexity within acceptable limits"
    exit 0
}

main "$@"
