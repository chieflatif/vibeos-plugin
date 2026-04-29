#!/usr/bin/env python3
"""Validate VibOS Comp dependency intelligence artifacts."""

import argparse
import json
import re
import sys
from pathlib import Path


REQUIRED_MISSION_SECTIONS = [
    "## Mission Promise",
    "## Enterprise Foundation Baseline",
    "## Dependency Intelligence",
    "## Acceptance Criteria",
]

MISSION_TERMS = ["dependency", "version", "lockfile", "compatibility", "security", "verified"]

MANIFEST_LOCKFILES = {
    "package.json": ["package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"],
    "pyproject.toml": ["poetry.lock", "pdm.lock", "uv.lock", "requirements.txt", "requirements.lock", "pylock.toml"],
    "requirements.txt": ["requirements.txt"],
    "go.mod": ["go.sum"],
    "Cargo.toml": ["Cargo.lock"],
    "pom.xml": ["pom.xml"],
    "build.gradle": ["gradle.lockfile", "gradle/dependency-locks"],
}

EVIDENCE_TERMS = ["source", "verified", "compatibility", "audit", "lockfile"]
CURRENCY_PACK_PATH = ".vibeos/reference/comp/stack-dependency-currency.json"


def read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore")


def find_manifests(project_dir: Path):
    found = []
    for manifest in MANIFEST_LOCKFILES:
        path = project_dir / manifest
        if path.exists():
            found.append(manifest)
    return found


def load_currency_packs(project_dir: Path):
    path = project_dir / CURRENCY_PACK_PATH
    if not path.exists():
        return []
    try:
        data = json.loads(read(path))
    except json.JSONDecodeError:
        return []
    return data.get("packs", [])


def package_json_dependencies(project_dir: Path):
    path = project_dir / "package.json"
    if not path.exists():
        return set()
    try:
        data = json.loads(read(path))
    except json.JSONDecodeError:
        return set()
    names = set()
    for key in ["dependencies", "devDependencies", "peerDependencies", "optionalDependencies"]:
        value = data.get(key, {})
        if isinstance(value, dict):
            names.update(name.lower() for name in value)
    return names


def text_dependency_names(project_dir: Path):
    names = set()
    for rel in ["requirements.txt", "pyproject.toml"]:
        text = read(project_dir / rel).lower()
        if not text:
            continue
        for line in text.splitlines():
            match = re.match(r"\s*([a-z0-9_.-]+)", line)
            if match and not match.group(1).startswith(("[", "#")):
                names.add(match.group(1))
        names.update(re.findall(r"['\"]([a-z0-9_.-]+)['\"]", text))
    return names


def dependency_surface(project_dir: Path):
    return package_json_dependencies(project_dir) | text_dependency_names(project_dir)


def pack_file_present(project_dir: Path, rel: str) -> bool:
    path = project_dir / rel
    if path.exists():
        return True
    if rel == "terraform" and any(project_dir.rglob("*.tf")):
        return True
    return False


def detected_currency_packs(project_dir: Path):
    packs = load_currency_packs(project_dir)
    dependencies = dependency_surface(project_dir)
    detected = []
    for pack in packs:
        applies = pack.get("applies_when", {})
        files = applies.get("files", [])
        dep_names = {name.lower() for name in applies.get("dependency_names", [])}
        file_match = any(pack_file_present(project_dir, rel) for rel in files)
        dep_match = bool(dependencies & dep_names)
        pack_id = pack.get("id", "")
        if pack_id in {"typescript_node", "deployment_runtime"} and file_match:
            detected.append(pack)
        elif dep_match:
            detected.append(pack)
    return detected


def lockfile_present(project_dir: Path, manifest: str) -> bool:
    for rel in MANIFEST_LOCKFILES[manifest]:
        if (project_dir / rel).exists():
            return True
    return False


def section_item_count(text: str, section: str) -> int:
    match = re.search(rf"{re.escape(section)}(?P<body>.*?)(?:\n## |\Z)", text, re.S)
    if not match:
        return 0
    body = match.group("body")
    return len(re.findall(r"(?m)^\s*(?:-|\d+\.|\|)\s*\S+", body))


def validate(project_dir: Path):
    findings = []
    mission = read(project_dir / "MISSION.md")
    if not mission:
        return [
            {
                "id": "DEP-MISSION-MISSING",
                "severity": "critical",
                "file": "MISSION.md",
                "message": "MISSION.md is required to validate dependency intelligence.",
            }
        ]

    for section in REQUIRED_MISSION_SECTIONS:
        if section not in mission:
            findings.append(
                {
                    "id": "DEP-MISSION-SECTION",
                    "severity": "high",
                    "file": "MISSION.md",
                    "message": f"Missing required dependency section: {section}",
                }
            )

    if "## Dependency Intelligence" in mission and section_item_count(mission, "## Dependency Intelligence") < 3:
        findings.append(
            {
                "id": "DEP-MISSION-ITEMS",
                "severity": "high",
                "file": "MISSION.md",
                "message": "Dependency Intelligence must list at least three concrete dependency controls.",
            }
        )

    lower = mission.lower()
    missing_terms = [term for term in MISSION_TERMS if term not in lower]
    if missing_terms:
        findings.append(
            {
                "id": "DEP-CONTEXT-TERMS",
                "severity": "medium",
                "file": "MISSION.md",
                "message": "Mission does not explicitly describe dependency context: " + ", ".join(missing_terms),
            }
        )

    manifests = find_manifests(project_dir)
    for manifest in manifests:
        if not lockfile_present(project_dir, manifest):
            findings.append(
                {
                    "id": "DEP-LOCKFILE-MISSING",
                    "severity": "high",
                    "file": manifest,
                    "message": f"Dependency manifest {manifest} exists without expected lockfile evidence.",
                }
            )

    evidence_path = project_dir / "docs/evidence/DEPENDENCY-INTELLIGENCE.md"
    evidence = read(evidence_path)
    if manifests and not evidence:
        findings.append(
            {
                "id": "DEP-EVIDENCE-MISSING",
                "severity": "high",
                "file": "docs/evidence/DEPENDENCY-INTELLIGENCE.md",
                "message": "Dependency manifests exist but dependency intelligence evidence is missing.",
            }
        )
    elif evidence:
        evidence_lower = evidence.lower()
        missing_evidence_terms = [term for term in EVIDENCE_TERMS if term not in evidence_lower]
        if missing_evidence_terms:
            findings.append(
                {
                    "id": "DEP-EVIDENCE-CONTEXT",
                    "severity": "medium",
                    "file": "docs/evidence/DEPENDENCY-INTELLIGENCE.md",
                    "message": "Dependency evidence is missing context: " + ", ".join(missing_evidence_terms),
                }
            )

        for pack in detected_currency_packs(project_dir):
            missing_pack_terms = [
                term for term in pack.get("required_evidence_terms", []) if term.lower() not in evidence_lower
            ]
            if missing_pack_terms:
                findings.append(
                    {
                        "id": "DEP-STACK-EVIDENCE",
                        "severity": "high",
                        "file": "docs/evidence/DEPENDENCY-INTELLIGENCE.md",
                        "message": f"{pack.get('label', pack.get('id', 'stack'))} evidence is missing stack currency context: " + ", ".join(missing_pack_terms),
                    }
                )

    scorecard = read(project_dir / "SCORECARD.md")
    if scorecard and "Dependency Intelligence" not in scorecard:
        findings.append(
            {
                "id": "DEP-SCORECARD-MISSING",
                "severity": "medium",
                "file": "SCORECARD.md",
                "message": "SCORECARD.md should include a Dependency Intelligence dimension.",
            }
        )

    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    findings = validate(project_dir)
    blocking = any(f["severity"] in {"critical", "high"} for f in findings)
    status = "fail" if blocking else "warn" if findings else "pass"
    payload = {
        "status": status,
        "findings": findings,
        "detected_currency_packs": [pack.get("id") for pack in detected_currency_packs(project_dir)],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    elif findings:
        label = "FAIL" if blocking else "WARN"
        print(f"[validate-dependency-intelligence] {label}: dependency intelligence findings detected")
        for finding in findings:
            print(f"- {finding['id']} [{finding['severity']}]: {finding['file']} - {finding['message']}")
    else:
        print("[validate-dependency-intelligence] PASS: dependency intelligence looks explicit")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
