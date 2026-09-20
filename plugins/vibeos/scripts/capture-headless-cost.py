#!/usr/bin/env python3
"""Capture Claude headless JSON cost output into a VibeOS evidence report."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FRAMEWORK_VERSION = "2.4.0"
LABEL = "estimate; reconcile against billing"


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_text(input_path: str) -> tuple[str, str]:
    if input_path == "-":
        return sys.stdin.read(), "stdin"
    path = Path(input_path)
    return path.read_text(encoding="utf-8"), path.as_posix()


def parse_payload(text: str) -> Any:
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
            raise ValueError("input is not valid JSON or JSONL")
        for item in reversed(objects):
            if find_key(item, "total_cost_usd") is not None:
                return item
        return objects[-1]


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


def pick_first(payload: Any, keys: list[str]) -> Any:
    for key in keys:
        value = find_key(payload, key)
        if value is not None:
            return value
    return None


def build_report(payload: Any, source_path: str, generated_at: str) -> dict[str, Any]:
    total = find_key(payload, "total_cost_usd")
    if total is None:
        raise ValueError("headless JSON does not contain total_cost_usd")
    if not isinstance(total, (int, float)):
        try:
            total = float(total)
        except (TypeError, ValueError) as exc:
            raise ValueError("total_cost_usd must be numeric") from exc

    model_costs = pick_first(payload, ["model_costs", "cost_by_model", "costs_by_model"])
    report: dict[str, Any] = {
        "schema_version": "1.0",
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": generated_at,
        "source": {
            "input_format": "claude_headless_json",
            "source_path": source_path,
        },
        "cost": {
            "label": LABEL,
            "total_cost_usd": total,
        },
        "run": {
            "session_id": pick_first(payload, ["session_id", "sessionId"]),
            "model": pick_first(payload, ["model", "resolved_model"]),
            "num_turns": pick_first(payload, ["num_turns", "turn_count"]),
            "duration_ms": pick_first(payload, ["duration_ms", "durationMs"]),
        },
        "limitations": [
            "This report is parsed from local headless command output.",
            "Treat values as estimates and reconcile against provider billing before public cost claims.",
        ],
    }
    if model_costs is not None:
        report["cost"]["model_costs"] = model_costs
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="-", help="Claude headless JSON output path, or '-' for stdin.")
    parser.add_argument("--evidence-dir", default="docs/evidence/vnext", help="Evidence bundle directory.")
    parser.add_argument("--out", default="", help="Explicit output path. Defaults to <evidence-dir>/cost-report.json.")
    parser.add_argument("--generated-at", default="", help="Override generated_at for deterministic tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    text, source_path = load_text(args.input)
    try:
        payload = parse_payload(text)
        report = build_report(payload, source_path, args.generated_at or iso_now())
    except ValueError as exc:
        print(f"[capture-headless-cost] FAIL: {exc}", file=sys.stderr)
        return 1

    out = Path(args.out) if args.out else Path(args.evidence_dir) / "cost-report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[capture-headless-cost] PASS: wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
