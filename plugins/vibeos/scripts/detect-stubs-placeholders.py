#!/usr/bin/env python3
"""Stub/Placeholder/Fallback Detection Script v1.0.

Scans a codebase for patterns indicating stub, placeholder, or fallback code.
Language-aware: supports Python, TypeScript/JavaScript, Go, Rust, Java.

Usage:
    python scripts/detect-stubs-placeholders.py
    python scripts/detect-stubs-placeholders.py --scan-dirs src/ lib/
    python scripts/detect-stubs-placeholders.py --language typescript
    python scripts/detect-stubs-placeholders.py --critical-only
    python scripts/detect-stubs-placeholders.py --json
    python scripts/detect-stubs-placeholders.py --baseline baselines/stubs.txt
    python scripts/detect-stubs-placeholders.py --summary
    python scripts/detect-stubs-placeholders.py --include-tests

Exit Codes:
- 0: Clean (no critical findings) or warnings only
- 1: Critical findings detected (must fix before merge)
- 2: Configuration / runtime error

Environment:
  SCAN_DIRS  Space-separated directories to scan (alternative to --scan-dirs)
  LANGUAGE   python|typescript|javascript|go|rust|java (alternative to --language)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

FRAMEWORK_VERSION = "1.0.0"

# ============================================================================
# CONFIGURATION
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent

# Language → file extension mapping
LANGUAGE_EXTENSIONS: dict[str, list[str]] = {
    "python": ["*.py"],
    "typescript": ["*.ts", "*.tsx", "*.js", "*.jsx", "*.mjs"],
    "javascript": ["*.js", "*.jsx", "*.mjs", "*.cjs"],
    "go": ["*.go"],
    "rust": ["*.rs"],
    "java": ["*.java", "*.kt", "*.kts"],
}

# Default scan dirs per language (used when no --scan-dirs provided)
DEFAULT_SCAN_DIRS: dict[str, list[str]] = {
    "python": ["src", "lib", "app"],
    "typescript": ["src", "lib", "app"],
    "javascript": ["src", "lib", "app"],
    "go": ["."],
    "rust": ["src"],
    "java": ["src"],
}

# Directories to always exclude
EXCLUDE_DIRS: set[str] = {
    "node_modules",
    "__pycache__",
    ".git",
    "venv",
    ".venv",
    "dist",
    "build",
    ".cache",
    "coverage",
    "htmlcov",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "vendor",
    "target",
    ".next",
    ".nuxt",
    "out",
}

# Governance script patterns (excluded from keyword checks to avoid self-detection)
GOVERNANCE_SCRIPT_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^detect-"),
    re.compile(r"^enforce-"),
    re.compile(r"^validate-"),
    re.compile(r"^verify-"),
    re.compile(r"^scan-"),
    re.compile(r"^audit"),
    re.compile(r"^check-"),
]

# Test file patterns
TEST_FILE_PATTERNS: list[re.Pattern[str]] = [
    # Python
    re.compile(r"test_.*\.py$"),
    re.compile(r".*_test\.py$"),
    re.compile(r"conftest\.py$"),
    # JS/TS
    re.compile(r".*\.test\.[jt]sx?$"),
    re.compile(r".*\.spec\.[jt]sx?$"),
    re.compile(r".*__tests__.*"),
    # Go
    re.compile(r".*_test\.go$"),
    # Rust
    re.compile(r".*tests?\.rs$"),
    # Java
    re.compile(r".*Test\.java$"),
    re.compile(r".*Tests\.java$"),
    re.compile(r".*Spec\.java$"),
]

# ============================================================================
# DATA MODELS
# ============================================================================

Severity = Literal["CRITICAL", "WARNING"]


@dataclass
class Finding:
    """A single detected stub/placeholder/fallback."""
    finding_id: str
    severity: Severity
    file_path: str
    line_number: int
    rule: str
    message: str
    line_content: str

    def display_key(self) -> str:
        """Return a stable key for baseline comparison."""
        return f"{self.rule}:{self.file_path}:{self.line_number}"


@dataclass
class Report:
    """Complete detection report."""
    timestamp: str
    scan_dirs: list[str]
    language: str
    total_files_scanned: int
    critical_count: int
    warning_count: int
    total_count: int
    findings: list[Finding] = field(default_factory=list)
    exit_code: int = 0


# ============================================================================
# LANGUAGE DETECTION
# ============================================================================


def detect_language(project_root: Path) -> str:
    """Auto-detect project language from config files."""
    if (project_root / "pyproject.toml").exists() or (project_root / "setup.py").exists():
        return "python"
    if (project_root / "tsconfig.json").exists():
        return "typescript"
    if (project_root / "package.json").exists():
        return "javascript"
    if (project_root / "go.mod").exists():
        return "go"
    if (project_root / "Cargo.toml").exists():
        return "rust"
    if (project_root / "pom.xml").exists() or (project_root / "build.gradle").exists():
        return "java"
    return "python"  # default


# ============================================================================
# DETECTION HELPERS
# ============================================================================


def _is_governance_script(file_path: str) -> bool:
    """Check if file is a governance script that legitimately discusses stubs."""
    name = Path(file_path).name
    return any(p.search(name) for p in GOVERNANCE_SCRIPT_PATTERNS)


def _is_test_file(path: Path) -> bool:
    """Check if file is a test file."""
    name = path.name
    for part in path.parts:
        if part in ("tests", "test", "__tests__", "test_utils"):
            return True
    return any(p.search(name) for p in TEST_FILE_PATTERNS)


# ============================================================================
# PYTHON-SPECIFIC RULES
# ============================================================================


def _py_pass_only_body(file_path: str, line: str, lines: list[str], idx: int) -> bool:
    """Check if `pass` is the sole body of a function/method/class (Python)."""
    stripped = line.strip()
    if stripped != "pass":
        return False

    search_start = max(0, idx - 15)
    found_def = False
    def_line_idx = -1
    body_lines_between = 0
    in_docstring = False

    for j in range(idx - 1, search_start - 1, -1):
        prev = lines[j].strip()
        if prev.startswith('"""') or prev.startswith("'''"):
            in_docstring = not in_docstring
            continue
        if in_docstring:
            continue
        if not prev or prev.startswith("#"):
            continue
        if re.match(r"^(async\s+)?def\s+\w+|^class\s+\w+", prev):
            found_def = True
            def_line_idx = j
            break
        body_lines_between += 1
        if body_lines_between > 3:
            break

    if not found_def:
        return False

    def_line = lines[def_line_idx].strip()

    # Exception: custom exception classes
    if re.match(r"^class\s+\w+(Error|Exception)\b", def_line):
        return False
    if re.match(r"^class\s+\w+\(.*\b(Error|Exception)\b", def_line):
        return False

    # Exception: NoOp/Null/Sentinel classes
    for j in range(def_line_idx - 1, max(0, def_line_idx - 50) - 1, -1):
        cls_line = lines[j].strip()
        if re.match(r"^class\s+((_?NoOp|Noop|_?Null|_?Dummy|_?Sentinel)\w*)", cls_line):
            return False
        if re.match(r"^class\s+", cls_line):
            break

    # Exception: @abstractmethod
    for j in range(def_line_idx - 1, max(0, def_line_idx - 5) - 1, -1):
        prev = lines[j].strip()
        if not prev or prev.startswith("#"):
            continue
        if prev == "@abstractmethod" or "abstract" in prev.lower():
            return False
        if prev.startswith("@"):
            continue
        break

    return True


def _py_not_implemented(file_path: str, line: str, lines: list[str], idx: int) -> bool:
    """Validate NotImplementedError, excluding ABC patterns."""
    if _is_governance_script(file_path):
        return False

    search_start = max(0, idx - 10)
    for j in range(idx - 1, search_start - 1, -1):
        prev = lines[j].strip()
        if not prev or prev.startswith("#"):
            continue
        if prev == "@abstractmethod":
            return False
        if re.match(r"^(async\s+)?def\s+\w+", prev):
            break
        if re.match(r"^class\s+\w+.*\b(ABC|Abstract|Base|Protocol|Interface)\b", prev):
            return False

    for j in range(idx - 1, max(0, idx - 50) - 1, -1):
        prev = lines[j].strip()
        if re.match(r"^class\s+\w+.*\b(ABC|Abstract|Base|Protocol|Interface)\b", prev):
            return False
        if re.match(r"^class\s+", prev):
            break

    return True


def _py_empty_except(file_path: str, line: str, lines: list[str], idx: int) -> bool:
    """Detect except: pass patterns."""
    if line.strip() != "pass":
        return False
    for j in range(idx - 1, max(0, idx - 5) - 1, -1):
        prev = lines[j].strip()
        if not prev or prev.startswith("#"):
            continue
        if re.match(r"^except(\s+\w+(\s+as\s+\w+)?)?:\s*(#.*)?$", prev):
            return True
        break
    return False


def _py_empty_return(file_path: str, line: str, lines: list[str], idx: int) -> bool:
    """Detect functions that unconditionally return {}, [], or None."""
    stripped = line.strip()
    if stripped not in ("return {}", "return []", "return None"):
        return False
    indent_level = len(line) - len(line.lstrip())
    for j in range(idx - 1, max(0, idx - 15) - 1, -1):
        prev = lines[j]
        prev_stripped = prev.strip()
        prev_indent = len(prev) - len(prev.lstrip())
        if not prev_stripped:
            continue
        if re.match(r"^(async\s+)?def\s+\w+", prev_stripped) and prev_indent < indent_level:
            body_lines = 0
            for k in range(j + 1, min(len(lines), idx + 1)):
                bl = lines[k].strip()
                if bl and not bl.startswith("#") and not bl.startswith('"""') and not bl.startswith("'''"):
                    body_lines += 1
            return body_lines <= 2
    return False


# ============================================================================
# UNIVERSAL RULES (all languages)
# ============================================================================


def _is_real_placeholder(file_path: str, line: str, lines: list[str], idx: int) -> bool:
    """Validate 'placeholder' keyword, filtering false positives."""
    if _is_governance_script(file_path):
        return False
    lower = line.lower()
    # Template placeholder APIs (legitimate)
    if re.search(r"resolve_placeholder|_placeholder\(|placeholder_pattern|placeholder_regex", lower):
        return False
    if re.search(r"sql\.placeholder|Placeholder\(\)", line):
        return False
    if re.search(r"def\s+\w*placeholder\w*|class\s+\w*placeholder\w*", lower):
        return False
    if re.search(r"\w*_?placeholders?\s*=", lower):
        return False
    return True


def _is_real_stub(file_path: str, line: str, lines: list[str], idx: int) -> bool:
    """Validate 'stub' keyword, filtering false positives."""
    if _is_governance_script(file_path):
        return False
    lower = line.lower()
    if re.search(r"stubborn|stubb", lower):
        return False
    if not re.search(r"\bstub(s|bed|bing)?\b", lower):
        return False
    if re.search(r"replaces?\s+(the\s+)?(\w+[-_])?\w*\s*stub|was\s+a\s+stub|remove[sd]?\s+\w*\s*stub", lower):
        return False
    return True


def _empty_assertion(file_path: str, line: str, lines: list[str], idx: int) -> bool:
    """Check for assert True, assert 1 == 1, etc."""
    stripped = line.strip()
    # Python
    if re.match(r"^assert\s+True\s*(#.*)?$", stripped):
        return True
    if re.match(r"^assert\s+1\s*==\s*1\s*(#.*)?$", stripped):
        return True
    # JS/TS
    if re.match(r"^expect\(true\)\.toBe\(true\)", stripped):
        return True
    if re.match(r"^assert\.ok\(true\)", stripped):
        return True
    # Go
    if re.match(r"^//\s*no assertions", stripped, re.IGNORECASE):
        return True
    return False


# ============================================================================
# JS/TS SPECIFIC RULES
# ============================================================================


def _js_empty_function(file_path: str, line: str, lines: list[str], idx: int) -> bool:
    """Detect empty function bodies in JS/TS: function foo() {} or () => {}."""
    stripped = line.strip()
    # Single-line empty function
    if re.search(r"(function\s+\w+\s*\([^)]*\)\s*\{\s*\}|=>\s*\{\s*\})", stripped):
        return True
    # Multi-line: opening brace followed by closing brace
    if stripped.endswith("{"):
        if idx + 1 < len(lines) and lines[idx + 1].strip() == "}":
            return True
    return False


def _js_todo_throw(file_path: str, line: str, lines: list[str], idx: int) -> bool:
    """Detect throw new Error('Not implemented') in JS/TS."""
    if _is_governance_script(file_path):
        return False
    stripped = line.strip()
    return bool(re.search(r"throw\s+new\s+Error\s*\(\s*['\"].*(?:not\s+implemented|todo|fixme)", stripped, re.IGNORECASE))


# ============================================================================
# GO SPECIFIC RULES
# ============================================================================


def _go_panic_not_implemented(file_path: str, line: str, lines: list[str], idx: int) -> bool:
    """Detect panic('not implemented') in Go."""
    if _is_governance_script(file_path):
        return False
    return bool(re.search(r'panic\s*\(\s*".*not\s+implemented', line, re.IGNORECASE))


# ============================================================================
# RUST SPECIFIC RULES
# ============================================================================


def _rust_todo_unimplemented(file_path: str, line: str, lines: list[str], idx: int) -> bool:
    """Detect todo!() and unimplemented!() in Rust."""
    if _is_governance_script(file_path):
        return False
    return bool(re.search(r"\b(todo|unimplemented)!\s*\(", line))


# ============================================================================
# RULE DEFINITIONS
# ============================================================================

# Format: (name, severity, pattern, description, extensions, skip_tests, validator)
from typing import Optional, Tuple, Set, Callable
RuleType = Tuple[str, Severity, "re.Pattern[str]", str, Optional[Set[str]], bool, Optional[object]]

# Universal rules (all languages)
UNIVERSAL_RULES: list[RuleType] = [
    (
        "todo-comment",
        "CRITICAL",
        re.compile(r"(#|//|/\*|\*)\s*\b(TODO|FIXME|HACK|XXX)\b", re.IGNORECASE),
        "TODO/FIXME/HACK/XXX comment",
        None,
        True,
        lambda fp, line, lines, idx: not _is_governance_script(fp),
    ),
    (
        "placeholder-keyword",
        "CRITICAL",
        re.compile(r"\bplaceholder\b", re.IGNORECASE),
        "placeholder keyword in code",
        None,
        True,
        _is_real_placeholder,
    ),
    (
        "stub-keyword",
        "CRITICAL",
        re.compile(r"\bstub\b", re.IGNORECASE),
        "stub keyword in code",
        None,
        True,
        _is_real_stub,
    ),
    (
        "empty-assertion",
        "CRITICAL",
        re.compile(r"assert\s+True|assert\s+1\s*==\s*1|expect\(true\)\.toBe\(true\)|assert\.ok\(true\)"),
        "Empty/always-passing test assertion",
        None,
        False,
        _empty_assertion,
    ),
    (
        "temp-comment",
        "CRITICAL",
        re.compile(r"(#|//|/\*)\s*(temporary|temp fix|workaround)\b", re.IGNORECASE),
        "Temporary/workaround comment",
        None,
        True,
        lambda fp, line, lines, idx: not _is_governance_script(fp),
    ),
]

# Python-specific rules
PYTHON_RULES: list[RuleType] = [
    (
        "not-implemented",
        "CRITICAL",
        re.compile(r"\bNotImplementedError\b"),
        "NotImplementedError raised",
        {".py"},
        False,
        _py_not_implemented,
    ),
    (
        "pass-only-body",
        "CRITICAL",
        re.compile(r"^\s+pass\s*(#.*)?$"),
        "pass-only function/method body (stub)",
        {".py"},
        True,
        _py_pass_only_body,
    ),
    (
        "hardcoded-mock-return",
        "CRITICAL",
        re.compile(r"\breturn\b.*\b(fake_|mock_|dummy_|\"fake\"|'fake'|\"mock\"|'mock'|\"dummy\"|'dummy'|sample_data|test_data)", re.IGNORECASE),
        "Hardcoded mock/fake return in production code",
        {".py"},
        True,
        lambda fp, line, lines, idx: not _is_governance_script(fp) and line.strip().startswith("return"),
    ),
    (
        "empty-except",
        "WARNING",
        re.compile(r"^\s+pass\s*(#.*)?$"),
        "Empty except block (except: pass)",
        {".py"},
        False,
        _py_empty_except,
    ),
    (
        "unconditional-empty-return",
        "WARNING",
        re.compile(r"^\s+return\s+(\{\}|\[\]|None)\s*(#.*)?$"),
        "Function unconditionally returns empty dict/list/None (possible stub)",
        {".py"},
        True,
        _py_empty_return,
    ),
    (
        "print-in-prod",
        "WARNING",
        re.compile(r"^\s*print\("),
        "print() in production code (use logging instead)",
        {".py"},
        True,
        lambda fp, line, lines, idx: not _is_governance_script(fp) and not fp.startswith("scripts/"),
    ),
]

# JavaScript/TypeScript-specific rules
JS_TS_RULES: list[RuleType] = [
    (
        "empty-function",
        "CRITICAL",
        re.compile(r"(function\s+\w+\s*\([^)]*\)\s*\{\s*\}|=>\s*\{\s*\})"),
        "Empty function body",
        {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"},
        True,
        _js_empty_function,
    ),
    (
        "throw-not-implemented",
        "CRITICAL",
        re.compile(r"throw\s+new\s+Error\s*\(", re.IGNORECASE),
        "throw new Error('Not implemented')",
        {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"},
        True,
        _js_todo_throw,
    ),
    (
        "console-log-in-prod",
        "WARNING",
        re.compile(r"^\s*console\.(log|warn|error|info)\s*\("),
        "console.log in production code",
        {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"},
        True,
        lambda fp, line, lines, idx: not _is_governance_script(fp),
    ),
]

# Go-specific rules
GO_RULES: list[RuleType] = [
    (
        "panic-not-implemented",
        "CRITICAL",
        re.compile(r'panic\s*\(\s*"', re.IGNORECASE),
        "panic('not implemented')",
        {".go"},
        True,
        _go_panic_not_implemented,
    ),
]

# Rust-specific rules
RUST_RULES: list[RuleType] = [
    (
        "todo-unimplemented-macro",
        "CRITICAL",
        re.compile(r"\b(todo|unimplemented)!\s*\("),
        "todo!() or unimplemented!() macro",
        {".rs"},
        True,
        _rust_todo_unimplemented,
    ),
]

# Java-specific rules
JAVA_RULES: list[RuleType] = [
    (
        "throw-unsupported",
        "CRITICAL",
        re.compile(r"throw\s+new\s+UnsupportedOperationException"),
        "throw new UnsupportedOperationException",
        {".java", ".kt"},
        True,
        lambda fp, line, lines, idx: not _is_governance_script(fp),
    ),
]

LANGUAGE_RULES: dict[str, list[RuleType]] = {
    "python": PYTHON_RULES,
    "typescript": JS_TS_RULES,
    "javascript": JS_TS_RULES,
    "go": GO_RULES,
    "rust": RUST_RULES,
    "java": JAVA_RULES,
}


# ============================================================================
# FILE SCANNING
# ============================================================================


def _is_excluded_dir(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    return False


def _collect_files(project_root: Path, scan_dirs: list[str], extensions: list[str]) -> list[Path]:
    """Collect files to scan."""
    files: list[Path] = []
    seen: set[Path] = set()

    for rel_dir in scan_dirs:
        scan_dir = project_root / rel_dir
        if not scan_dir.exists():
            continue
        for glob_pattern in extensions:
            for file_path in scan_dir.rglob(glob_pattern):
                if file_path in seen or not file_path.is_file():
                    continue
                if _is_excluded_dir(file_path.relative_to(project_root)):
                    continue
                seen.add(file_path)
                files.append(file_path)

    # Also scan scripts/ and tests/ if they exist
    for extra in ["scripts", "tests"]:
        extra_dir = project_root / extra
        if not extra_dir.exists():
            continue
        for glob_pattern in extensions:
            for file_path in extra_dir.rglob(glob_pattern):
                if file_path in seen or not file_path.is_file():
                    continue
                if _is_excluded_dir(file_path.relative_to(project_root)):
                    continue
                seen.add(file_path)
                files.append(file_path)

    return sorted(files)


def _scan_file(
    file_path: Path,
    project_root: Path,
    rules: list[RuleType],
    include_tests: bool,
) -> list[Finding]:
    """Scan a single file against all rules."""
    findings: list[Finding] = []
    rel_path = str(file_path.relative_to(project_root))
    suffix = file_path.suffix
    is_test = _is_test_file(file_path)

    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return findings

    lines = content.splitlines()

    # Skip this script itself
    if file_path.name == "detect-stubs-placeholders.py":
        return findings

    for rule_name, severity, pattern, description, extensions, skip_tests, validator in rules:
        if extensions is not None and suffix not in extensions:
            continue
        if skip_tests and is_test and not include_tests:
            continue
        # empty-assertion: only scan test files
        if rule_name == "empty-assertion" and not is_test:
            continue

        for idx, line in enumerate(lines):
            if not pattern.search(line):
                continue
            if validator is not None:
                try:
                    if not validator(rel_path, line, lines, idx):
                        continue
                except Exception:
                    continue

            trimmed = line.strip()
            if len(trimmed) > 200:
                trimmed = trimmed[:197] + "..."

            findings.append(Finding(
                finding_id="",
                severity=severity,
                file_path=rel_path,
                line_number=idx + 1,
                rule=rule_name,
                message=f"{description}: {trimmed}",
                line_content=trimmed,
            ))

    return findings


# ============================================================================
# BASELINE HANDLING
# ============================================================================


def _load_baseline(baseline_path: Path) -> set[str]:
    if not baseline_path.exists():
        print(f"WARNING: Baseline file not found: {baseline_path}", file=sys.stderr)
        return set()
    baseline: set[str] = set()
    for line in baseline_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            baseline.add(line)
    return baseline


def _filter_baseline(findings: list[Finding], baseline: set[str]) -> list[Finding]:
    return [f for f in findings if f.display_key() not in baseline and f.finding_id not in baseline]


# ============================================================================
# REPORT
# ============================================================================


def _assign_ids(findings: list[Finding]) -> None:
    critical_counter = 0
    warning_counter = 0
    for f in findings:
        if f.severity == "CRITICAL":
            critical_counter += 1
            f.finding_id = f"C{critical_counter:03d}"
        else:
            warning_counter += 1
            f.finding_id = f"W{warning_counter:03d}"


def _build_report(findings: list[Finding], total_files: int, scan_dirs: list[str], language: str) -> Report:
    critical = sum(1 for f in findings if f.severity == "CRITICAL")
    warning = sum(1 for f in findings if f.severity == "WARNING")
    return Report(
        timestamp=datetime.now(timezone.utc).isoformat(),
        scan_dirs=scan_dirs,
        language=language,
        total_files_scanned=total_files,
        critical_count=critical,
        warning_count=warning,
        total_count=critical + warning,
        findings=findings,
        exit_code=1 if critical > 0 else 0,
    )


# ============================================================================
# OUTPUT
# ============================================================================

_RED = "\033[0;31m"
_YELLOW = "\033[1;33m"
_GREEN = "\033[0;32m"
_BOLD = "\033[1m"
_NC = "\033[0m"


def _print_human(report: Report, summary_only: bool = False, critical_only: bool = False) -> None:
    print()
    print(f"{_BOLD}=== STUB/PLACEHOLDER DETECTION REPORT ==={_NC}")
    print(f"Timestamp: {report.timestamp}")
    print(f"Language: {report.language}")
    print(f"Files scanned: {report.total_files_scanned}")
    print(f"Scan scope: {', '.join(report.scan_dirs)}")
    print()

    if not summary_only:
        critical_findings = [f for f in report.findings if f.severity == "CRITICAL"]
        if critical_findings:
            print(f"{_RED}{_BOLD}CRITICAL FINDINGS (must fix):{_NC}")
            for f in critical_findings:
                print(f"  {_RED}[{f.finding_id}]{_NC} {f.file_path}:{f.line_number} "
                      f"-- {f.rule}: {f.line_content}")
            print()

        if not critical_only:
            warning_findings = [f for f in report.findings if f.severity == "WARNING"]
            if warning_findings:
                print(f"{_YELLOW}{_BOLD}WARNING FINDINGS (review):{_NC}")
                for f in warning_findings:
                    print(f"  {_YELLOW}[{f.finding_id}]{_NC} {f.file_path}:{f.line_number} "
                          f"-- {f.rule}: {f.line_content}")
                print()

    print(f"{_BOLD}SUMMARY:{_NC}")
    print(f"  Critical: {report.critical_count}")
    if not critical_only:
        print(f"  Warning:  {report.warning_count}")
    print(f"  Total:    {report.total_count}")
    print()

    if report.exit_code == 0:
        if report.warning_count > 0:
            print(f"{_YELLOW}EXIT CODE: 0 (warnings only, non-blocking){_NC}")
        else:
            print(f"{_GREEN}EXIT CODE: 0 (clean){_NC}")
    else:
        print(f"{_RED}EXIT CODE: 1 (critical findings found -- must fix before merge){_NC}")
    print()


def _print_json(report: Report, critical_only: bool = False) -> None:
    data = asdict(report)
    if critical_only:
        data["findings"] = [f for f in data["findings"] if f["severity"] == "CRITICAL"]
        data["warning_count"] = 0
        data["total_count"] = data["critical_count"]
    print(json.dumps(data, indent=2))


# ============================================================================
# MAIN
# ============================================================================


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect stubs, placeholders, and fallback code.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--scan-dirs", nargs="+", default=None, help="Directories to scan")
    parser.add_argument("--language", type=str, default=None, help="Project language (python|typescript|javascript|go|rust|java)")
    parser.add_argument("--critical-only", action="store_true", help="Only report critical findings")
    parser.add_argument("--json", action="store_true", dest="json_output", help="JSON output")
    parser.add_argument("--baseline", type=str, default=None, help="Baseline file path")
    parser.add_argument("--summary", action="store_true", help="Summary only")
    parser.add_argument("--include-tests", action="store_true", help="Also scan test files")

    args = parser.parse_args()

    try:
        # Resolve language
        language = args.language or os.environ.get("LANGUAGE") or detect_language(PROJECT_ROOT)

        # Resolve scan dirs
        scan_dirs = args.scan_dirs
        if not scan_dirs:
            env_dirs = os.environ.get("SCAN_DIRS", "").strip()
            if env_dirs:
                scan_dirs = env_dirs.split()
            else:
                # Use defaults and auto-detect which exist
                candidates = DEFAULT_SCAN_DIRS.get(language, ["src", "lib", "app"])
                scan_dirs = [d for d in candidates if (PROJECT_ROOT / d).exists()]
                if not scan_dirs:
                    # Fallback: scan current directory
                    scan_dirs = ["."]

        # Resolve file extensions
        extensions = LANGUAGE_EXTENSIONS.get(language, ["*.py", "*.js", "*.ts", "*.go", "*.rs", "*.java"])
        # Also include shell scripts for universal rules
        if "*.sh" not in extensions:
            extensions = extensions + ["*.sh"]

        files = _collect_files(PROJECT_ROOT, scan_dirs, extensions)
        if not files:
            print("WARNING: No files found to scan.", file=sys.stderr)
            return 2

        # Build rule set: universal + language-specific
        rules = UNIVERSAL_RULES + LANGUAGE_RULES.get(language, [])

        all_findings: list[Finding] = []
        for file_path in files:
            findings = _scan_file(file_path, PROJECT_ROOT, rules, include_tests=args.include_tests)
            all_findings.extend(findings)

        all_findings.sort(key=lambda f: (0 if f.severity == "CRITICAL" else 1, f.file_path, f.line_number))
        _assign_ids(all_findings)

        if args.baseline:
            baseline = _load_baseline(Path(args.baseline))
            all_findings = _filter_baseline(all_findings, baseline)
            _assign_ids(all_findings)

        report = _build_report(all_findings, len(files), scan_dirs, language)

        if args.json_output:
            _print_json(report, critical_only=args.critical_only)
        else:
            _print_human(report, summary_only=args.summary, critical_only=args.critical_only)

        return report.exit_code

    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 2
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
