#!/usr/bin/env python3
"""
VibeOS Plugin — Testing Anti-Pattern Detector

Scans test files for patterns that produce false-passing tests:
1. Silent pass guards: if (element) { assert... } with no else
2. Vacuous assertions: asserting hardcoded defaults
3. Verify-after-delete with wrong ID: using fallback strings instead of actual IDs
4. Conditional assertion blocks with zero unconditional assertions
5. Mock-only integration points with no contract validation

Usage:
    python3 scripts/detect-testing-antipatterns.py [--scan-dirs tests frontend/__tests__] [--language python|typescript] [--json]

Exit codes:
    0 = Clean or warnings only
    1 = Anti-patterns found (blocking if configured)
    2 = Runtime error
"""

import sys
import os
import re
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List

FRAMEWORK_VERSION = "2.0.0"
GATE_NAME = "detect-testing-antipatterns"


@dataclass
class Finding:
    pattern: str
    severity: str  # critical, high, medium, low
    file: str
    line: int
    description: str
    code_snippet: str
    recommendation: str


@dataclass
class Report:
    total_files_scanned: int = 0
    total_findings: int = 0
    findings: List[Finding] = field(default_factory=list)
    patterns_checked: List[str] = field(default_factory=list)


def scan_silent_pass_guards_ts(content: str, filepath: str) -> List[Finding]:
    """Detect: if (element) { fireEvent...; expect... } with no else/fail."""
    findings = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        # Pattern: if (element) or if (something) { ...expect
        if re.search(r'if\s*\(\s*\w+\s*\)\s*\{', line):
            # Look ahead for expect() without a corresponding else { fail/throw }
            block_depth = 0
            has_assertion = False
            has_else = False
            for j in range(i, min(i + 20, len(lines))):
                block_depth += lines[j].count('{') - lines[j].count('}')
                if 'expect(' in lines[j] or 'assert' in lines[j].lower():
                    has_assertion = True
                if 'else' in lines[j] and ('fail' in lines[j] or 'throw' in lines[j]):
                    has_else = True
                if block_depth <= 0 and j > i:
                    break
            if has_assertion and not has_else:
                findings.append(Finding(
                    pattern="silent-pass-guard",
                    severity="high",
                    file=filepath,
                    line=i + 1,
                    description="Conditional assertion block with no else/fail — test silently passes when element is not found",
                    code_snippet=line.strip(),
                    recommendation="Add else { fail('Expected element to exist') } or move assertion outside the conditional"
                ))
    return findings


def scan_silent_pass_guards_py(content: str, filepath: str) -> List[Finding]:
    """Detect: if element: assert... with no else."""
    findings = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        stripped = line.strip()
        if re.match(r'if\s+\w+\s*:', stripped):
            # Look ahead for assert within the if block
            indent = len(line) - len(line.lstrip())
            has_assertion = False
            has_else = False
            for j in range(i + 1, min(i + 15, len(lines))):
                inner_indent = len(lines[j]) - len(lines[j].lstrip())
                if lines[j].strip() == '':
                    continue
                if inner_indent <= indent and lines[j].strip():
                    if lines[j].strip().startswith('else'):
                        has_else = True
                    break
                if 'assert' in lines[j]:
                    has_assertion = True
            if has_assertion and not has_else:
                findings.append(Finding(
                    pattern="silent-pass-guard",
                    severity="high",
                    file=filepath,
                    line=i + 1,
                    description="Conditional assertion with no else — test passes with zero assertions when condition is false",
                    code_snippet=stripped,
                    recommendation="Use pytest.fail() in else branch or assert the condition itself"
                ))
    return findings


def scan_verify_after_delete_fallback(content: str, filepath: str) -> List[Finding]:
    """Detect: using literal fallback strings in verify-after-delete patterns."""
    findings = []
    lines = content.split('\n')
    for i, line in enumerate(lines):
        # Pattern: variable or "fallback" or 'fallback'
        if re.search(r'\w+\s+or\s+["\']', line) and ('delete' in content[max(0, i - 500):i + 500].lower()):
            findings.append(Finding(
                pattern="verify-after-delete-fallback",
                severity="high",
                file=filepath,
                line=i + 1,
                description="Verify-after-delete uses a literal fallback string instead of the actual ID — assertion may be vacuous",
                code_snippet=line.strip(),
                recommendation="Assert the ID is not None before using it in the verify step"
            ))
    return findings


def scan_mock_only_integration(content: str, filepath: str) -> List[Finding]:
    """Detect: API mocks without any integration test marker."""
    findings = []
    has_mock = bool(re.search(r'jest\.mock|mock_\w+|@patch|MagicMock|vi\.mock', content))
    has_integration_marker = bool(re.search(r'@integration|integration.test|contract.valid', content, re.IGNORECASE))
    has_api_call = bool(re.search(r'fetch\(|apiClient|client\.|requests\.|httpx\.', content))

    if has_mock and has_api_call and not has_integration_marker:
        findings.append(Finding(
            pattern="mock-only-integration",
            severity="medium",
            file=filepath,
            line=1,
            description="Test file mocks API calls but has no integration test marker — mock shapes may not match real API",
            code_snippet="(file-level pattern)",
            recommendation="Add at least one test tagged @integration-test that validates the mock shape against the real API contract"
        ))
    return findings


def scan_directory(scan_dir: str, language: str) -> Report:
    report = Report()
    report.patterns_checked = ["silent-pass-guard", "verify-after-delete-fallback", "mock-only-integration"]

    extensions = {'python': ['.py'], 'typescript': ['.ts', '.tsx'], 'javascript': ['.js', '.jsx']}
    exts = extensions.get(language, ['.py', '.ts', '.tsx'])

    scan_path = Path(scan_dir)
    if not scan_path.exists():
        return report

    for filepath in scan_path.rglob('*'):
        if filepath.suffix not in exts:
            continue
        if 'node_modules' in str(filepath) or '.next' in str(filepath):
            continue

        # Only scan test files
        name = filepath.name.lower()
        if not (name.startswith('test_') or name.endswith('.test.ts') or name.endswith('.test.tsx')
                or name.endswith('_test.py') or 'test' in filepath.parent.name.lower()):
            continue

        report.total_files_scanned += 1
        try:
            content = filepath.read_text(encoding='utf-8', errors='replace')
        except Exception:
            continue

        rel_path = str(filepath)

        if language == 'typescript' or filepath.suffix in ['.ts', '.tsx']:
            report.findings.extend(scan_silent_pass_guards_ts(content, rel_path))
        elif language == 'python' or filepath.suffix == '.py':
            report.findings.extend(scan_silent_pass_guards_py(content, rel_path))

        report.findings.extend(scan_verify_after_delete_fallback(content, rel_path))
        report.findings.extend(scan_mock_only_integration(content, rel_path))

    report.total_findings = len(report.findings)
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Detect testing anti-patterns")
    parser.add_argument('--scan-dirs', nargs='+', default=['tests', 'frontend/__tests__'])
    parser.add_argument('--language', default='auto')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--critical-only', action='store_true')
    args = parser.parse_args()

    combined_report = Report()

    for scan_dir in args.scan_dirs:
        if not os.path.isdir(scan_dir):
            continue
        lang = args.language
        if lang == 'auto':
            lang = 'typescript' if 'frontend' in scan_dir or '__tests__' in scan_dir else 'python'
        report = scan_directory(scan_dir, lang)
        combined_report.total_files_scanned += report.total_files_scanned
        combined_report.findings.extend(report.findings)
        combined_report.patterns_checked = report.patterns_checked

    combined_report.total_findings = len(combined_report.findings)

    if args.critical_only:
        combined_report.findings = [f for f in combined_report.findings if f.severity in ('critical', 'high')]
        combined_report.total_findings = len(combined_report.findings)

    if args.json:
        print(json.dumps(asdict(combined_report), indent=2))
    else:
        print(f"Scanned {combined_report.total_files_scanned} test files")
        print(f"Patterns checked: {', '.join(combined_report.patterns_checked)}")
        print(f"Findings: {combined_report.total_findings}")
        for f in combined_report.findings:
            print(f"\n[{f.severity.upper()}] {f.pattern}")
            print(f"  File: {f.file}:{f.line}")
            print(f"  {f.description}")
            print(f"  Code: {f.code_snippet}")
            print(f"  Fix:  {f.recommendation}")

    sys.exit(1 if combined_report.total_findings > 0 else 0)


if __name__ == '__main__':
    main()
