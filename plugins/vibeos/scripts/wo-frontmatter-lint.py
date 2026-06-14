#!/usr/bin/env python3
"""Lint WO frontmatter and generate the vNext WO-INDEX block."""

import argparse
import importlib.util
import re
import sys
from dataclasses import dataclass
from pathlib import Path


START = "<!-- VIBEOS-GENERATED-START: wo-frontmatter-index -->"
END = "<!-- VIBEOS-GENERATED-END: wo-frontmatter-index -->"
COMPLETE_STATUSES = {"Complete", "Deferred"}
ACTIVE_PHASE_MINIMUM = 35


@dataclass
class WoRecord:
    wo: str
    title: str
    phase: int
    status: str
    source: str
    order: int


def load_contracts_module():
    path = Path(__file__).with_name("wo-contracts.py")
    spec = importlib.util.spec_from_file_location("wo_contracts", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


contracts = load_contracts_module()


def wo_number(wo: str) -> int:
    match = re.search(r"WO-([0-9]+)", wo)
    return int(match.group(1)) if match else 999999


def planning_files(project_dir: Path) -> list[Path]:
    docs = project_dir / "docs/planning"
    return sorted(path for path in docs.glob("WO-*.md") if re.match(r"WO-[0-9]+", path.name))


def has_frontmatter(path: Path) -> bool:
    try:
        return path.read_text(encoding="utf-8").splitlines()[0].strip() == "---"
    except IndexError:
        return False


def body_without_frontmatter(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return text
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[index + 1 :])
    return text


def scope_reflected_in_prose(contract: dict, body: str, rel_path: str) -> bool:
    non_doc_scope = [
        path
        for path in contract["write_scope"]
        if path != rel_path and not path.startswith("docs/planning/") and not path.startswith("docs/evidence/")
    ]
    if not non_doc_scope:
        return True
    lower_body = body.lower()
    for path in non_doc_scope:
        if "*" in path:
            token = path.split("*", 1)[0].rstrip("/").lower()
            if token and token in lower_body:
                return True
            continue
        basename = Path(path).name.lower()
        if path.lower() in lower_body or basename in lower_body:
            return True
    return False


def lint_frontmatter(project_dir: Path, require_from: int, historical: list[str]) -> list[str]:
    findings = []
    files = planning_files(project_dir)
    present = {re.match(r"(WO-[0-9]+)", path.name).group(1): path for path in files}

    for wo in historical:
        path = present.get(wo)
        if path and not has_frontmatter(path):
            findings.append(f"{path}: missing required historical fixture frontmatter")

    for path in files:
        match = re.match(r"(WO-[0-9]+)", path.name)
        if not match:
            continue
        wo_id = match.group(1)
        if wo_number(wo_id) >= require_from and not has_frontmatter(path):
            findings.append(f"{path}: missing required frontmatter for WO-{require_from}+ migration")
            continue
        if not has_frontmatter(path):
            continue
        text = path.read_text(encoding="utf-8")
        try:
            contract = contracts.load_contract(path)
        except Exception as exc:
            findings.append(f"{path}: invalid frontmatter: {exc}")
            continue
        rel_path = str(path.relative_to(project_dir))
        body = body_without_frontmatter(text)
        if contract["wo"] != wo_id:
            findings.append(f"{path}: frontmatter wo {contract['wo']} does not match filename {wo_id}")
        if rel_path not in contract["write_scope"]:
            findings.append(f"{path}: write_scope must include this WO file")
        if contract["status"] not in body:
            findings.append(f"{path}: prose status does not reflect frontmatter status {contract['status']}")
        if not scope_reflected_in_prose(contract, body, rel_path):
            findings.append(f"{path}: write_scope is not reflected in prose scope/impact text")
    return findings


def parse_master_plan(project_dir: Path) -> dict[str, WoRecord]:
    path = project_dir / "docs/planning/VNEXT-UPGRADE-AUDIT-AND-MASTER-PLAN-2026-06-10.md"
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    section = text.split("## 7. Detailed Development Plan", 1)[-1].split("\n## 8.", 1)[0]
    phase = 0
    order = 0
    records = {}
    for line in section.splitlines():
        phase_match = re.match(r"### Phase ([0-9]+)", line)
        if phase_match:
            phase = int(phase_match.group(1))
            continue
        row_match = re.match(r"\|\s*\*\*(WO-[0-9]+)\*\*\s*\|\s*([^|]+?)\s*\|", line)
        if not row_match or not phase:
            continue
        order += 1
        wo, title = row_match.groups()
        records[wo] = WoRecord(wo=wo, title=title.strip(), phase=phase, status="Planned", source="master-plan", order=order)
    return records


def frontmatter_records(project_dir: Path) -> dict[str, WoRecord]:
    records = {}
    for path in planning_files(project_dir):
        if not has_frontmatter(path):
            continue
        contract = contracts.load_contract(path)
        records[contract["wo"]] = WoRecord(
            wo=contract["wo"],
            title=contract["title"],
            phase=int(contract["phase"]),
            status=contract["status"],
            source="frontmatter",
            order=1000 + wo_number(contract["wo"]),
        )
    return records


def combined_records(project_dir: Path) -> list[WoRecord]:
    records = parse_master_plan(project_dir)
    for wo, record in frontmatter_records(project_dir).items():
        existing = records.get(wo)
        if existing:
            record.order = existing.order
        records[wo] = record
    return sorted(records.values(), key=lambda item: (item.phase, item.order, wo_number(item.wo)))


def generated_block(project_dir: Path) -> str:
    records = combined_records(project_dir)
    active = next(
        (record for record in records if record.phase >= ACTIVE_PHASE_MINIMUM and record.status not in COMPLETE_STATUSES),
        None,
    )
    lines = [
        START,
        "## Active",
        "",
        "| WO | Title | Phase | Status | Source |",
        "|---|---|---|---|---|",
    ]
    if active:
        lines.append(f"| {active.wo} | {active.title} | {active.phase} | {active.status} | {active.source} |")
    else:
        lines.append("| — | No active WO | — | Complete | generated |")
    lines.extend(
        [
            "",
            "## vNext Machine-Readable View",
            "",
            "Generated from WO frontmatter plus the vNext master plan. Do not edit this block by hand.",
            "",
            "| WO | Title | Phase | Status | Source |",
            "|---|---|---|---|---|",
        ]
    )
    for record in records:
        if record.phase >= 33:
            lines.append(f"| {record.wo} | {record.title} | {record.phase} | {record.status} | {record.source} |")
    lines.append(END)
    return "\n".join(lines)


def legacy_index_body(path: Path) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    if START in text and END in text:
        return text.split(END, 1)[1].strip()
    backlog = text.find("\n## Backlog")
    legacy = text[backlog + 1 :] if backlog != -1 else ""
    old_vnext = legacy.find("\n### Phases 34")
    if old_vnext != -1:
        legacy = legacy[:old_vnext].rstrip()
    return legacy.strip()


def generate_index(project_dir: Path) -> str:
    index_path = project_dir / "docs/planning/WO-INDEX.md"
    legacy = legacy_index_body(index_path)
    parts = ["# Work Order Index", "", generated_block(project_dir)]
    if legacy:
        parts.extend(["", legacy])
    return "\n".join(parts).rstrip() + "\n"


def run_lint(args) -> int:
    findings = lint_frontmatter(args.project_dir, args.require_from, args.historical_fixture)
    if findings:
        for finding in findings:
            print(f"[wo-frontmatter] FAIL: {finding}", file=sys.stderr)
        return 1
    print("[wo-frontmatter] PASS: frontmatter contracts are valid")
    return 0


def run_generate(args) -> int:
    text = generate_index(args.project_dir)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return 0


def run_validate_index(args) -> int:
    expected = generate_index(args.project_dir)
    actual_path = args.project_dir / "docs/planning/WO-INDEX.md"
    actual = actual_path.read_text(encoding="utf-8") if actual_path.exists() else ""
    if actual != expected:
        print("[wo-frontmatter] FAIL: WO-INDEX.md generated block is stale; run generate-index", file=sys.stderr)
        return 1
    print("[wo-frontmatter] PASS: WO-INDEX.md generated block is current")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in ["lint", "generate-index", "validate-index"]:
        sub = subparsers.add_parser(name)
        sub.add_argument("--project-dir", type=Path, default=Path("."))
        if name == "lint":
            sub.add_argument("--require-from", type=int, default=107)
            sub.add_argument("--historical-fixture", action="append", default=["WO-106"])
        if name == "generate-index":
            sub.add_argument("--out", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    args.project_dir = args.project_dir.resolve()
    if args.command == "lint":
        return run_lint(args)
    if args.command == "generate-index":
        return run_generate(args)
    if args.command == "validate-index":
        return run_validate_index(args)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
