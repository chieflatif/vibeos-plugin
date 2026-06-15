#!/usr/bin/env python3
# FILE-SIZE-EXCEPTION: WO-124 - cohesive evidence builder for workflow static checks, live output, baseline comparison, and adoption verdict.
"""Build evidence for the VibeOS audit fan-out workflow."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.2.0"
DEFAULT_WORKFLOW = Path(".claude/workflows/vibeos-audit-sweep")
DEFAULT_TARGET = "plugins/vibeos/scripts/runtime-capabilities.py"
REQUIRED_NO_WRITE = [
    "docs/planning/**",
    ".vibeos/**",
    ".claude/settings*.json",
    ".claude/workflows/**",
]
DIRECT_ACCESS_PATTERNS = [
    r"require\s*\(\s*['\"]fs['\"]",
    r"from\s+['\"]fs['\"]",
    r"\bprocess\.",
    r"\bBun\.",
    r"\bDeno\.",
    r"child_process",
]


def extract_int(pattern: str, text: str) -> int | None:
    match = re.search(pattern, text, flags=re.I)
    return int(match.group(1)) if match else None


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def rel(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def find_key(value: Any, key: str) -> Any:
    if isinstance(value, dict):
        if key in value:
            return value[key]
        for child in value.values():
            found = find_key(child, key)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_key(child, key)
            if found is not None:
                return found
    return None


def parse_json_or_jsonl(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        objects = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                objects.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        if not objects:
            raise ValueError(f"{path} is not valid JSON or JSONL")
        for item in reversed(objects):
            if find_key(item, "total_cost_usd") is not None:
                return item
        return objects[-1]


def marker_map(text: str) -> dict[str, str]:
    markers: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"\s*//\s*(VIBEOS_[A-Z0-9_]+):\s*(.+?)\s*$", line)
        if match:
            markers[match.group(1)] = match.group(2)
    return markers


def csv_marker(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_int_constant(text: str, name: str) -> int | None:
    match = re.search(rf"\b{name}\b\s*=\s*(\d+)", text)
    return int(match.group(1)) if match else None


def direct_access_findings(text: str) -> list[str]:
    findings = []
    for pattern in DIRECT_ACCESS_PATTERNS:
        if re.search(pattern, text):
            findings.append(pattern)
    return findings


def static_workflow_checks(root: Path, workflow_path: Path, target: str) -> dict[str, Any]:
    exists = workflow_path.exists()
    text = workflow_path.read_text(encoding="utf-8") if exists else ""
    markers = marker_map(text)
    auditors = csv_marker(markers.get("VIBEOS_WORKFLOW_AUDITORS"))
    no_write = csv_marker(markers.get("VIBEOS_WORKFLOW_GOVERNANCE_NO_WRITE"))
    cost_controls = csv_marker(markers.get("VIBEOS_WORKFLOW_COST_CONTROLS"))
    max_concurrency = parse_int_constant(text, "MAX_CONCURRENT_AGENTS")
    direct_access = direct_access_findings(text)
    meta_first_statement_ok = text.lstrip().startswith("export const meta =")

    checks = {
        "workflow_exists": exists,
        "workflow_path": rel(workflow_path, root),
        "workflow_id": markers.get("VIBEOS_WORKFLOW_ID"),
        "workflow_status_marker": markers.get("VIBEOS_WORKFLOW_STATUS"),
        "meta_first_statement_ok": meta_first_statement_ok,
        "target": target,
        "default_target": markers.get("VIBEOS_WORKFLOW_DEFAULT_TARGET"),
        "auditors": auditors,
        "auditor_count": len(auditors),
        "expected_auditor_count": 12,
        "auditor_count_ok": len(auditors) == 12,
        "governance_no_write": no_write,
        "governance_no_write_ok": all(item in no_write for item in REQUIRED_NO_WRITE),
        "cost_controls": cost_controls,
        "cost_controls_ok": all(
            item in cost_controls
            for item in ["mode=canary", "auditorLimit", "maxConcurrentAuditors"]
        ),
        "uses_args_global": re.search(r"\bargs\b", text) is not None,
        "direct_filesystem_or_shell_access_patterns": direct_access,
        "direct_filesystem_or_shell_access_ok": not direct_access,
        "agent_launch_candidates": [
            name
            for name in ["agent", "runAgent", "Agent.run"]
            if name in text
        ],
        "max_concurrent_agents_declared": max_concurrency,
        "max_concurrent_agents_ok": max_concurrency is None or max_concurrency <= 16,
    }
    checks["status"] = "pass" if all(
        [
            checks["workflow_exists"],
            checks["meta_first_statement_ok"],
            checks["auditor_count_ok"],
            checks["governance_no_write_ok"],
            checks["cost_controls_ok"],
            checks["uses_args_global"],
            checks["direct_filesystem_or_shell_access_ok"],
            checks["max_concurrent_agents_ok"],
        ]
    ) else "fail"
    return checks


def baseline_from_skill(root: Path, target: str) -> dict[str, Any]:
    skill_path = root / "plugins/vibeos/skills/audit/SKILL.md"
    auditors: list[str] = []
    if skill_path.exists():
        text = skill_path.read_text(encoding="utf-8")
        for match in re.finditer(r"\|\s*[^|]+\s*\|\s*`agents/([^`]+?)(?:-same-tree)?\.md`\s*\|", text):
            agent = match.group(1)
            if agent != "plan-auditor":
                auditors.append(agent)
    return {
        "schema_version": "1.0",
        "baseline_id": "vibeos-audit-subagent-path-source-derived",
        "source": rel(skill_path, root),
        "target": target,
        "execution_status": "source_derived_not_live",
        "auditors": auditors,
        "auditor_count": len(auditors),
        "findings": {
            "status": "not_captured",
            "count": None,
        },
        "tokens": {
            "status": "not_captured",
            "total": None,
        },
        "cost": {
            "status": "not_captured",
            "total_cost_usd": None,
        },
        "limitations": [
            "This baseline is derived from the existing audit skill dispatch list.",
            "It is not live subagent execution evidence and cannot satisfy the WO-124 live comparison by itself.",
        ],
    }


def normalize_baseline(root: Path, target: str, baseline_path: Path | None) -> dict[str, Any]:
    if baseline_path:
        payload = load_json(baseline_path)
        payload.setdefault("source", rel(baseline_path, root))
        return payload
    return baseline_from_skill(root, target)


def live_output_summary(root: Path, live_output: Path | None, live_stderr: Path | None) -> dict[str, Any]:
    if not live_output:
        return {
            "status": "not_run",
            "output_path": None,
            "stderr_path": rel(live_stderr, root) if live_stderr else None,
            "total_cost_usd": None,
            "num_turns": None,
            "error": None,
        }
    summary: dict[str, Any] = {
        "status": "captured",
        "output_path": rel(live_output, root),
        "stderr_path": rel(live_stderr, root) if live_stderr else None,
        "total_cost_usd": None,
        "num_turns": None,
        "error": None,
    }
    try:
        payload = parse_json_or_jsonl(live_output)
    except ValueError as exc:
        summary["status"] = "unparseable"
        summary["error"] = str(exc)
        return summary
    summary["total_cost_usd"] = find_key(payload, "total_cost_usd")
    summary["num_turns"] = find_key(payload, "num_turns") or find_key(payload, "turn_count")
    summary["result_type"] = find_key(payload, "subtype") or find_key(payload, "type")
    summary["is_error"] = find_key(payload, "is_error")
    errors = payload.get("errors") if isinstance(payload, dict) else None
    summary["errors"] = errors if isinstance(errors, list) else []
    permission_denials = payload.get("permission_denials") if isinstance(payload, dict) else None
    if isinstance(permission_denials, list):
        summary["permission_denials_count"] = len(permission_denials)
        summary["workflow_permission_denied"] = any(
            isinstance(item, dict) and item.get("tool_name") == "Workflow"
            for item in permission_denials
        )
    else:
        summary["permission_denials_count"] = None
        summary["workflow_permission_denied"] = False
    result = find_key(payload, "result")
    if isinstance(result, str):
        lowered = result.lower()
        summary["auditor_count"] = extract_int(r"\bAgents:\*\*\s*(\d+)", result)
        summary["finding_count"] = extract_int(r"\bConsensus:\*\*\s*(\d+)\s+actionable finding", result)
        mode_match = re.search(r"\bMode:\*\*\s*([a-z0-9_-]+)", result, flags=re.I)
        if mode_match:
            summary["mode"] = mode_match.group(1)
        if (
            "unknown command" in lowered
            or "not found" in lowered
            or "failed to launch" in lowered
            or "rejected at parse time" in lowered
            or "blocked by review gate" in lowered
            or "review dynamic workflow before running" in lowered
            or "did not launch" in lowered
            or "never ran" in lowered
            or "signature mismatch" in lowered
            or "[object object]" in lowered
            or "prompt-serialization bug" in lowered
            or "zero valid findings" in lowered
            or ("workflow" in lowered and "error" in lowered)
        ):
            if "signature mismatch" in lowered or "[object object]" in lowered or "prompt-serialization bug" in lowered:
                summary["status"] = "agent_signature_failed"
            else:
                summary["status"] = "blocked_review_gate" if summary["workflow_permission_denied"] else "failed"
        else:
            summary["status"] = "completed_or_returned"
    if summary["workflow_permission_denied"]:
        summary["status"] = "blocked_review_gate"
    if summary["result_type"] == "error_max_budget_usd" or any(
        "budget" in str(item).lower() for item in summary["errors"]
    ):
        summary["status"] = "budget_limited"
    return summary


def comparison(static_checks: dict[str, Any], baseline: dict[str, Any], live: dict[str, Any]) -> dict[str, Any]:
    baseline_auditors = baseline.get("auditors") or []
    baseline_cost = (baseline.get("cost") or {}).get("total_cost_usd")
    workflow_cost = live.get("total_cost_usd")
    baseline_findings = (baseline.get("findings") or {}).get("count")
    workflow_auditor_count = live.get("auditor_count")
    workflow_finding_count = live.get("finding_count")
    baseline_auditor_count = baseline.get("auditor_count") or len(baseline_auditors)
    return {
        "auditor_count_delta": (
            workflow_auditor_count - baseline_auditor_count
            if workflow_auditor_count is not None
            else static_checks["auditor_count"] - baseline_auditor_count
        ),
        "auditor_list_matches_baseline": (
            workflow_auditor_count == baseline_auditor_count
            if workflow_auditor_count is not None
            else static_checks["auditors"] == baseline_auditors
        ),
        "findings_comparison_status": (
            "pending_live_subagent_and_workflow_findings"
            if baseline_findings is None
            or workflow_finding_count is None
            or live.get("status") in {"not_run", "unparseable", "failed"}
            else "available"
        ),
        "baseline_finding_count": baseline_findings,
        "workflow_finding_count": workflow_finding_count,
        "token_or_cost_comparison_status": (
            "available"
            if baseline_cost is not None and workflow_cost is not None
            else "pending_baseline_or_workflow_token_evidence"
        ),
        "baseline_total_cost_usd": baseline_cost,
        "workflow_total_cost_usd": workflow_cost,
    }


def verdict(static_checks: dict[str, Any], live: dict[str, Any], compare: dict[str, Any]) -> str:
    if static_checks["status"] != "pass":
        return "NO_GO_STATIC_WORKFLOW_CHECK_FAILED"
    if live.get("status") == "not_run":
        return "DEFER_LIVE_WORKFLOW_NOT_RUN"
    if live.get("status") == "blocked_review_gate":
        return "DEFER_WORKFLOW_REVIEW_GATE_NOT_APPROVED"
    if live.get("status") == "budget_limited":
        return "DEFER_LIVE_WORKFLOW_BUDGET_LIMIT"
    if live.get("status") == "agent_signature_failed":
        return "DEFER_WORKFLOW_AGENT_SIGNATURE_FIX_REQUIRED"
    if live.get("status") in {"failed", "unparseable"}:
        return "DEFER_LIVE_WORKFLOW_NOT_PROVEN"
    if compare["token_or_cost_comparison_status"] != "available":
        return "PARTIAL_UNLOCK_CANDIDATE_BASELINE_COST_PENDING"
    return "PARTIAL_UNLOCK_CANDIDATE_REVIEW_BEFORE_DEFAULT"


def build_report(
    root: Path,
    workflow_path: Path,
    target: str,
    baseline_path: Path | None,
    live_output: Path | None,
    live_stderr: Path | None,
    generated_at: str,
) -> dict[str, Any]:
    static_checks = static_workflow_checks(root, workflow_path, target)
    baseline = normalize_baseline(root, target, baseline_path)
    live = live_output_summary(root, live_output, live_stderr)
    compare = comparison(static_checks, baseline, live)
    adoption = verdict(static_checks, live, compare)
    return {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": generated_at,
        "wo": "WO-124",
        "objective": "Bounded first use of the VibeOS audit fan-out dynamic workflow.",
        "static_workflow_checks": static_checks,
        "subagent_path_baseline": baseline,
        "live_workflow_run": live,
        "comparison": compare,
        "adoption_verdict": adoption,
        "summary": {
            "status": "pass" if static_checks["status"] == "pass" else "fail",
            "readiness": (
                "implemented_locally_live_comparison_pending"
                if adoption == "DEFER_LIVE_WORKFLOW_NOT_RUN"
                else adoption.lower()
            ),
        },
        "limitations": [
            "This report does not claim Claude/Codex parity.",
            "This report does not claim automatic write-time enforcement.",
            "A live workflow result cannot be treated as whole-repo audit proof unless the target covers the whole repo.",
            "Cost values parsed from Claude output remain estimates and must be reconciled against provider billing before public cost claims.",
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", default=".", help="Repository root.")
    parser.add_argument("--workflow", default=str(DEFAULT_WORKFLOW), help="Workflow path.")
    parser.add_argument("--target", default=DEFAULT_TARGET, help="Bounded target audited by the probe.")
    parser.add_argument("--baseline", default="", help="Optional subagent-path baseline JSON.")
    parser.add_argument("--live-output", default="", help="Optional Claude headless output JSON/JSONL.")
    parser.add_argument("--live-stderr", default="", help="Optional Claude headless stderr text.")
    parser.add_argument("--out", default="", help="Output JSON path.")
    parser.add_argument("--generated-at", default="", help="Deterministic timestamp override.")
    parser.add_argument("--stdout", action="store_true", help="Print JSON to stdout.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = Path(args.project_dir).resolve()
    workflow_path = Path(args.workflow)
    if not workflow_path.is_absolute():
        workflow_path = root / workflow_path
    baseline_path = Path(args.baseline) if args.baseline else None
    if baseline_path and not baseline_path.is_absolute():
        baseline_path = root / baseline_path
    live_output = Path(args.live_output) if args.live_output else None
    if live_output and not live_output.is_absolute():
        live_output = root / live_output
    live_stderr = Path(args.live_stderr) if args.live_stderr else None
    if live_stderr and not live_stderr.is_absolute():
        live_stderr = root / live_stderr

    report = build_report(
        root=root,
        workflow_path=workflow_path,
        target=args.target,
        baseline_path=baseline_path,
        live_output=live_output,
        live_stderr=live_stderr,
        generated_at=args.generated_at or iso_now(),
    )
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"

    if args.stdout:
        print(payload, end="")
    if args.out:
        out = Path(args.out)
        if not out.is_absolute():
            out = root / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
        print(f"[workflow-audit-sweep-evidence] PASS: wrote {out}")
    if not args.stdout and not args.out:
        print(payload, end="")
    return 0 if report["summary"]["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
