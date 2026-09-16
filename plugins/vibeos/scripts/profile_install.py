#!/usr/bin/env python3
# FILE-SIZE-EXCEPTION: WO-147 — cohesive profile-driven analyze/apply installer with generation, audit, and upgrade-safety logic.
"""Profile-driven VibeOS install planner and applier."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import signal
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

from install_integrity import (
    analysis_input_binding,
    IntegrityError,
    atomic_write,
    contained_path,
    file_state,
    output_inventory,
    plan_payload_hash,
    profile_binding,
    safe_relative,
    sha256_file,
    sha256_json,
    source_binding,
    target_binding,
    verify_profile_binding,
    verify_analysis_input_binding,
    verify_source_binding,
    verify_target_binding,
)
from install_recovery import (
    RecoveryError,
    begin_transaction,
    complete_transaction,
    mark_recovery_required,
    project_lock,
    record_expected_state,
    recover_transaction,
    require_no_active_transaction,
)


FRAMEWORK_VERSION = "2.3.0"

MODE_MODULES = {
    "minimal": [
        "runtime-core",
        "codex-core",
        "claude-core",
        "active-surface-audit",
    ],
    "product-engineering": [
        "runtime-core",
        "codex-core",
        "claude-core",
        "product-engineering-agents",
        "product-engineering-gates",
        "active-surface-audit",
    ],
    "regulated/evidence-heavy": [
        "runtime-core",
        "codex-core",
        "claude-core",
        "product-engineering-agents",
        "product-engineering-gates",
        "evidence-controls",
        "active-surface-audit",
    ],
    "comp": [
        "runtime-core",
        "codex-core",
        "claude-core",
        "product-engineering-agents",
        "product-engineering-gates",
        "comp",
        "active-surface-audit",
    ],
    "autonomy": [
        "runtime-core",
        "codex-core",
        "claude-core",
        "product-engineering-agents",
        "product-engineering-gates",
        "autonomy",
        "active-surface-audit",
    ],
    "full": [
        "runtime-core",
        "codex-core",
        "claude-core",
        "product-engineering-agents",
        "product-engineering-gates",
        "evidence-controls",
        "comp",
        "autonomy",
        "generic-prompt-routing",
        "generic-governance-prompt-scan",
        "commit-msg-enforcement",
        "full-payload",
        "active-surface-audit",
    ],
}

ALL_OPTIONAL_MODULES = [
    "generic-prompt-routing",
    "generic-governance-prompt-scan",
    "commit-msg-enforcement",
    "full-payload",
]

DORMANT_PAYLOAD = [
    ".vibeos/reference",
    ".vibeos/decision-engine",
    ".vibeos/convergence",
    "docs/USER-COMMUNICATION-CONTRACT.md",
]

DEFAULT_AVOID_SURFACES = [
    ".vibeos/reference",
    ".vibeos/decision-engine",
    ".vibeos/convergence",
    "docs/USER-COMMUNICATION-CONTRACT.md",
    "project-definition.json",
]

CANON_CANDIDATES = [
    "AGENTS.md",
    "PROJECT.md",
    "README.md",
    "RULES.md",
    "WORKFLOW.md",
    "ORCHESTRATION.md",
    "STATE_MACHINE.md",
    "pyramid",
    "schemas",
    "templates",
    "tools",
    "agents",
    "runs",
    "receipts",
    "work-orders",
]

TARGET_ANALYSIS_INPUTS = sorted(
    set(
        CANON_CANDIDATES
        + [
            "PROJECT.md",
            "README.md",
            "AGENTS.md",
            "tools/validate_all.py",
            "harness/run.py",
            "pytest.ini",
            "tests",
            "package.json",
        ]
    )
)

RUNTIME_CORE_SCRIPTS = [
    "detect-runtime-capabilities.sh",
    "runtime-capabilities.py",
    "gate-runner.sh",
    "gate_timeout.py",
    "setup-git-hooks.sh",
    "validate-no-secrets.sh",
    "secrets-allowlist.json",
]

PRODUCT_ENGINEERING_SCRIPTS = [
    "detect-stubs-placeholders.py",
    "detect-testing-antipatterns.py",
    "validate-code-quality.sh",
    "validate-file-size.sh",
    "validate-security-patterns.sh",
    "validate-tests-pass.sh",
    "validate-tests-required.sh",
    "validate-code-complexity.sh",
    "validate-dependency-versions.sh",
    "validate-dependencies.sh",
]

EVIDENCE_SCRIPTS = [
    "evidence-recall.py",
    "validate-evidence-bundle.sh",
    "validate-audit-completeness.sh",
    "validate-independent-audit.sh",
]

COMP_SCRIPTS = [
    "comp-plan.py",
    "comp-integration-check.py",
    "comp-scorecard.py",
    "comp-red-team.py",
    "comp-dossier.py",
    "validate-comp-ai-failure-modes.py",
    "validate-flow-integrity.py",
    "validate-system-invariants.py",
    "validate-dependency-intelligence.py",
    "validate-delivery-infrastructure.py",
]

AUTONOMY_SCRIPTS = [
    "autonomy-heartbeat.py",
    "autonomy-loop.py",
    "autonomy-runner.py",
    "autonomy-runtime-adapter.py",
    "autonomy-failure-detector.py",
    "autonomy-recovery-planner.py",
    "autonomy-recovery-resolution.py",
    "autonomy-scheduler-guard.py",
    "autonomy-scheduler-profile.py",
    "autonomy-smoke.py",
    "autonomy-supervisor.py",
    "autonomy_lease.py",
    "limit-aware-scheduler.py",
    "validate-long-run-autonomy.py",
]

MINIMAL_SKILLS = [
    "vibeos-help",
    "vibeos-status",
    "vibeos-gate",
]

PRODUCT_SKILLS = [
    "vibeos-discover",
    "vibeos-plan",
    "vibeos-build",
    "vibeos-audit",
    "vibeos-checkpoint",
    "vibeos-wo",
    "vibeos-project-status",
    "vibeos-session-audit",
]

OPTIONAL_SKILLS = {
    "comp": ["vibeos-comp"],
    "autonomy": ["vibeos-autonomous"],
}

MINIMAL_ROLES = [
    "investigator",
    "plan-auditor",
    "correctness-auditor",
]

PRODUCT_ROLES = [
    "backend",
    "frontend",
    "tester",
    "test-auditor",
    "doc-writer",
    "security-auditor",
    "architecture-auditor",
    "correctness-auditor",
    "product-drift-auditor",
    "flow-auditor",
    "system-invariant-auditor",
    "dependency-intelligence-auditor",
    "delivery-infrastructure-auditor",
    "integration-captain",
    "red-team-auditor",
    "evidence-auditor",
    "contract-validator",
    "prompt-engineer",
]


class InstallError(RuntimeError):
    """Raised for user-correctable install errors."""


def utc_now() -> str:
    return (
        dt.datetime.now(dt.UTC)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def clean_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "project"


def title_case_from_slug(value: str) -> str:
    return (
        " ".join(part.capitalize() for part in re.split(r"[-_\s]+", value) if part)
        or "Project"
    )


def snake(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()


def relative_path(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def resolve_source(source_arg: str) -> Path:
    candidate = Path(source_arg).expanduser().absolute()
    if candidate.is_symlink():
        raise InstallError(f"source may not be a symlink: {candidate}")
    source = candidate.resolve()
    if (source / "plugins/vibeos/scripts").is_dir():
        return (source / "plugins/vibeos").resolve()
    if (source / "scripts").is_dir() and (source / "agents").is_dir():
        return source
    raise InstallError(f"source does not look like a VibeOS source tree: {source}")


def resolve_target(target_arg: str) -> Path:
    candidate = Path(target_arg).expanduser().absolute()
    if candidate.is_symlink():
        raise InstallError(f"target may not be a symlink: {candidate}")
    target = candidate.resolve()
    if not target.is_dir():
        raise InstallError(f"target directory does not exist: {target}")
    return target


def check_source_target_safety(source: Path, target: Path) -> None:
    if source == target:
        raise InstallError("source and target are the same directory")
    if source in target.parents or target in source.parents:
        raise InstallError("source and target must be nonnested canonical directories")
    if (target / "plugins/vibeos").exists() and (target / "vibeos-init.sh").exists():
        raise InstallError(
            "target appears to be the VibeOS source repo; refusing to install into source"
        )
    for child in [".vibeos", ".codex", ".agents", ".claude"]:
        candidate = target / child
        if candidate.is_symlink():
            raise InstallError(f"refusing to write through symlink: {candidate}")


GENERATED_MARKER_PREFIXES = ("<!-- VIBEOS-GENERATED", "# VIBEOS-GENERATED")
GENERATED_SURFACE_HEADING_SUFFIX = " — VibeOS Project Surface"


def is_generated_file(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        with path.open(encoding="utf-8", errors="replace") as handle:
            first_line = handle.readline()
    except OSError:
        return False
    return first_line.lstrip().startswith(GENERATED_MARKER_PREFIXES)


def first_heading(path: Path) -> str | None:
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
    except OSError:
        return None
    return None


def detect_project_name(target: Path) -> str:
    for name in ["PROJECT.md", "README.md", "AGENTS.md"]:
        path = target / name
        if is_generated_file(path):
            continue
        heading = first_heading(path)
        if not heading:
            continue
        # Strip only the exact generated-heading form ("<name> — VibeOS Project
        # Surface") or its degenerate bare variants; anything else without the
        # separator is a legitimate user title.
        if heading.endswith(GENERATED_SURFACE_HEADING_SUFFIX):
            heading = heading[: -len(GENERATED_SURFACE_HEADING_SUFFIX)].strip()
        elif heading in ("— VibeOS Project Surface", "VibeOS Project Surface"):
            heading = ""
        if heading:
            return heading
    return title_case_from_slug(target.name)


def detect_canon(target: Path) -> list[str]:
    canon: list[str] = []
    for path in CANON_CANDIDATES:
        candidate = target / path
        if not candidate.exists():
            continue
        if candidate.is_file() and is_generated_file(candidate):
            continue
        canon.append(path)
    return canon


def detect_validators(target: Path) -> list[dict[str, str]]:
    validators: list[dict[str, str]] = []
    if (target / "tools/validate_all.py").is_file():
        validators.append(
            {"name": "validate-all", "command": "python3 tools/validate_all.py"}
        )
    if (target / "harness/run.py").is_file():
        validators.append(
            {"name": "harness-all", "command": "python3 harness/run.py --stage all"}
        )
    if (target / "pytest.ini").is_file() or (target / "tests").is_dir():
        validators.append({"name": "pytest", "command": "python3 -m pytest"})
    if (target / "package.json").is_file():
        validators.append({"name": "npm-test", "command": "npm test"})
    return validators


def load_profile(profile_path: Path | None, target: Path, mode: str) -> dict[str, Any]:
    profile: dict[str, Any]
    if profile_path:
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
    else:
        profile = {}

    project_name = profile.get("project_name") or detect_project_name(target)
    project_slug = profile.get("project_slug") or clean_slug(project_name)
    canon_paths = profile.get("canon_paths") or detect_canon(target)
    protected_files = profile.get("protected_files") or canon_paths
    avoid_surfaces = list(
        dict.fromkeys(profile.get("avoid_surfaces", []) + DEFAULT_AVOID_SURFACES)
    )
    profile_mode = profile.get("mode") or mode
    if profile_mode not in MODE_MODULES:
        raise InstallError(f"unknown install mode: {profile_mode}")

    normalized = {
        "schema_version": 1,
        "project_name": project_name,
        "project_slug": project_slug,
        "project_type": profile.get(
            "project_type", "project-native software repository"
        ),
        "mode": profile_mode,
        "canon_paths": canon_paths,
        "protected_files": protected_files,
        "avoid_surfaces": avoid_surfaces,
        "lead_runtime": profile.get("lead_runtime", "codex"),
        "phase_audit_runtime": profile.get("phase_audit_runtime", "claude"),
        "governance_level": profile.get(
            "governance_level", "product-risk-proportional"
        ),
        "domain_gates": profile.get("domain_gates", []),
        "enabled_modules": profile.get("enabled_modules", []),
        "disabled_modules": profile.get("disabled_modules", []),
        "primary_gates": profile.get("primary_gates", []),
    }
    return normalized


def modules_for_profile(profile: dict[str, Any]) -> list[str]:
    modules = list(MODE_MODULES[profile["mode"]])
    for module in profile.get("enabled_modules", []):
        if module not in modules:
            modules.append(module)
    disabled = set(profile.get("disabled_modules", []))
    return [module for module in modules if module not in disabled]


def skipped_modules(enabled: list[str], mode: str) -> list[str]:
    skipped = [module for module in ALL_OPTIONAL_MODULES if module not in enabled]
    if "full-payload" not in enabled:
        skipped.extend(
            [
                "dormant-reference-payload",
                "dormant-decision-engine",
                "dormant-convergence",
            ]
        )
    if mode != "full":
        skipped.append("full")
    return list(dict.fromkeys(skipped))


def selected_scripts(source: Path, enabled: list[str]) -> list[str]:
    if "full-payload" in enabled:
        return sorted(
            path.name
            for path in (source / "scripts").iterdir()
            if path.is_file() and "__pycache__" not in path.parts
        )

    scripts = list(RUNTIME_CORE_SCRIPTS)
    if "product-engineering-gates" in enabled:
        scripts.extend(PRODUCT_ENGINEERING_SCRIPTS)
    if "evidence-controls" in enabled:
        scripts.extend(EVIDENCE_SCRIPTS)
    if "comp" in enabled:
        scripts.extend(COMP_SCRIPTS)
    if "autonomy" in enabled:
        scripts.extend(AUTONOMY_SCRIPTS)

    existing = []
    for script in dict.fromkeys(scripts):
        if (source / "scripts" / script).is_file():
            existing.append(script)
    return existing


def selected_skills(enabled: list[str]) -> list[str]:
    skills = list(MINIMAL_SKILLS)
    if "product-engineering-agents" in enabled:
        skills.extend(PRODUCT_SKILLS)
    for module, module_skills in OPTIONAL_SKILLS.items():
        if module in enabled:
            skills.extend(module_skills)
    return list(dict.fromkeys(skills))


def selected_roles(source: Path, enabled: list[str]) -> list[str]:
    roles = list(MINIMAL_ROLES)
    if "product-engineering-agents" in enabled:
        roles.extend(PRODUCT_ROLES)
    available = {path.stem for path in (source / "agents").glob("*.md")}
    return [role for role in dict.fromkeys(roles) if role in available]


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        return {}, text
    raw = parts[1]
    body = parts[2]
    meta: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip().strip('"')
    return meta, body


def role_read_only(role: str, meta: dict[str, str]) -> bool:
    if "tester" == role:
        return False
    if "auditor" in role or role in {"contract-validator", "plan-auditor"}:
        return True
    tools = meta.get("tools", "")
    disallowed = meta.get("disallowedTools", "")
    return (
        "Write" not in tools
        and "Edit" not in tools
        or "Write" in disallowed
        or "Edit" in disallowed
    )


def render_profile_summary(profile: dict[str, Any]) -> str:
    canon = profile.get("canon_paths") or ["No canon paths detected yet"]
    gates = profile.get("primary_gates") or [
        "Use detected validators from the install plan"
    ]
    return "\n".join(
        [
            f"Project: {profile['project_name']}",
            f"Mode: {profile['mode']}",
            f"Lead runtime: {profile['lead_runtime']}",
            f"Phase audit runtime: {profile['phase_audit_runtime']}",
            "Canon paths:",
            *[f"- {path}" for path in canon],
            "Primary gates:",
            *[f"- {gate}" for gate in gates],
        ]
    )


def generated_header(template_id: str, profile_hash: str, source_hash: str) -> str:
    return "\n".join(
        [
            "<!-- VIBEOS-GENERATED: profile-driven-install -->",
            f"<!-- template_id: {template_id} -->",
            f"<!-- profile_hash: {profile_hash} -->",
            f"<!-- source_hash: {source_hash} -->",
            "",
        ]
    )


def render_agents_md(profile: dict[str, Any], profile_hash: str) -> str:
    template_id = "codex.agents-md.v1"
    source_hash = sha256_text(template_id)
    summary = render_profile_summary(profile)
    skill_list = "\n".join(
        f"- `{skill}`: `.agents/skills/{skill}/SKILL.md`"
        for skill in selected_skills(modules_for_profile(profile))
    )
    return (
        generated_header(template_id, profile_hash, source_hash)
        + f"# {profile['project_name']} — VibeOS Project Surface\n\n"
        + "This is a project-native VibeOS surface generated from the local project profile. "
        + f"The operating truth is `{profile['project_name']}` canon, not generic framework material.\n\n"
        + "## Profile\n\n"
        + f"```text\n{summary}\n```\n\n"
        + "## Operating Rules\n\n"
        + "- Read the project canon before planning or implementation.\n"
        + "- Treat VibeOS as a supporting harness for this project.\n"
        + "- Do not replace project-specific validators with generic paperwork.\n"
        + "- Codex TOML agents are active runtime contracts and must stay profile-specific.\n"
        + "- Auditor roles are read-only unless the project profile explicitly says otherwise.\n\n"
        + "## Controlled Evaluation\n\n"
        + "Read `.vibeos/controlled-evaluation-guide.md` when present and run "
        + "`.vibeos/scripts/controlled-evaluation.py --help` before configuring an evaluation. "
        + "Use project-owner specified required test/check identities and a protected evaluation profile. "
        + "Never invent coverage, and never treat `PRE_REVIEW` publication as acceptance.\n\n"
        + "## Skills\n\n"
        + skill_list
        + "\n\n"
        + "## Checks\n\n"
        + "Run the active-surface audit after install or upgrade:\n\n"
        + "```bash\npython3 .vibeos/scripts/vibeos-active-surface-audit.py\n```\n"
    )


def render_claude_md(profile: dict[str, Any], profile_hash: str) -> str:
    template_id = "claude.boot-md.v1"
    source_hash = sha256_text(template_id)
    summary = render_profile_summary(profile)
    return (
        generated_header(template_id, profile_hash, source_hash)
        + f"# {profile['project_name']} — Claude/Cursor VibeOS Surface\n\n"
        + "This surface is generated from the project profile. It should support the "
        + f"{profile['project_name']} delivery model without turning generic VibeOS process into project truth.\n\n"
        + "## Profile\n\n"
        + f"```text\n{summary}\n```\n\n"
        + "## Runtime Split\n\n"
        + f"- Lead runtime: `{profile['lead_runtime']}`\n"
        + f"- Phase audit runtime: `{profile['phase_audit_runtime']}`\n\n"
        + "## Rules\n\n"
        + "- Preserve protected canon unless Latif explicitly approves a diff.\n"
        + "- Keep evidence, tests, and product outcomes ahead of process format.\n"
        + "- For controlled evaluation, read `.vibeos/controlled-evaluation-guide.md` when present, "
        + "then run `.vibeos/scripts/controlled-evaluation.py --help`; use owner-specified identities "
        + "and never treat `PRE_REVIEW` as acceptance.\n"
        + "- Run project validators and the VibeOS active-surface audit after install or upgrade.\n"
    )


def render_skill(skill: str, profile: dict[str, Any], profile_hash: str) -> str:
    template_id = f"skill.{skill}.v1"
    source_hash = sha256_text(template_id)
    summary = render_profile_summary(profile)
    readable = skill.replace("vibeos-", "").replace("-", " ").title()
    return (
        generated_header(template_id, profile_hash, source_hash)
        + "---\n"
        + f"name: {skill}\n"
        + f"description: {readable} workflow for {profile['project_name']} using the project profile.\n"
        + "---\n\n"
        + f"# {readable} — {profile['project_name']}\n\n"
        + "Use this skill only when it advances this target project. The project profile "
        + "and canon paths are the source of operating truth.\n\n"
        + "## Profile\n\n"
        + f"```text\n{summary}\n```\n\n"
        + "## Required Behavior\n\n"
        + "- Start from the project canon and existing validators.\n"
        + "- Keep outputs project-specific and evidence-backed.\n"
        + "- Do not introduce generic governance work unless it protects this project.\n"
        + "- Before an engineering completion claim that uses controlled evaluation, run "
        + "`.vibeos/scripts/controlled-evaluation.py --help`, use project-owner specified required "
        + "test/check identities and the protected evaluation profile, never invent coverage, and "
        + "never treat `PRE_REVIEW` as acceptance.\n"
        + "- Report partial verification honestly.\n"
    )


def render_role_contract(
    role: str, meta: dict[str, str], profile: dict[str, Any], profile_hash: str
) -> str:
    template_id = f"role.{role}.v1"
    meta_hash = sha256_text(json_dumps(meta))
    summary = render_profile_summary(profile)
    name = meta.get("name", role)
    read_only = role_read_only(role, meta)
    authority = "read-only review" if read_only else "workspace implementation"
    return (
        generated_header(template_id, profile_hash, meta_hash)
        + "---\n"
        + f"name: {name}\n"
        + f"description: {role.replace('-', ' ').title()} for {profile['project_name']}.\n"
        + f"authority: {authority}\n"
        + "---\n\n"
        + f"# {role.replace('-', ' ').title()} — {profile['project_name']}\n\n"
        + "This role is generated from the profile-aware VibeOS role template. "
        + f"Its job is to improve `{profile['project_name']}` within the project canon and validators.\n\n"
        + "## Profile\n\n"
        + f"```text\n{summary}\n```\n\n"
        + "## Contract\n\n"
        + f"- Authority: `{authority}`.\n"
        + "- Use the target repo's canon, tests, and validators as evidence.\n"
        + "- Do not promote generic VibeOS process above project outcomes.\n"
        + "- Keep findings and completion claims tied to files, commands, or artifacts.\n"
        + "- If this is an auditor role, inspect and report; do not edit project files.\n"
    )


def render_codex_toml(
    role: str, meta: dict[str, str], profile: dict[str, Any], profile_hash: str
) -> str:
    template_id = f"codex.toml.{role}.v1"
    meta_hash = sha256_text(json_dumps(meta))
    read_only = role_read_only(role, meta)
    sandbox = "read-only" if read_only else "workspace-write"
    model_key = (meta.get("model") or "sonnet").lower()
    model_map = {
        "opus": ("gpt-5.5", "high"),
        "sonnet": ("gpt-5.5", "medium"),
        "haiku": ("gpt-5.4-mini", "low"),
    }
    model, effort = model_map.get(model_key, ("gpt-5.5", "medium"))
    instructions = (
        f"You are the {role.replace('-', ' ')} role for {profile['project_name']}. "
        "This Codex TOML file is an active runtime contract generated from the same "
        "profile-aware role source as the Markdown contract. The target project profile "
        "and canon paths are operating truth. Do not substitute generic VibeOS workflow "
        "for project-specific evidence, tests, validators, or product outcomes. "
        f"Profile hash: {profile_hash}. "
        f"Authority: {'read-only review' if read_only else 'workspace implementation'}."
    )

    # TOML files are UTF-8; render strings without \uXXXX escapes so the
    # active-surface audit's literal project-name check holds for non-ASCII names.
    # DEL must stay escaped: JSON leaves 0x7f raw but TOML rejects it.
    def toml_str(value: str) -> str:
        return json.dumps(value, ensure_ascii=False).replace("\x7f", "\\u007f")

    lines = [
        f"# VIBEOS-GENERATED template_id={template_id} profile_hash={profile_hash} source_hash={meta_hash}",
        f"name = {toml_str('vibeos_' + snake(role))}",
        f"description = {toml_str(f'{role.replace("-", " ").title()} for {profile["project_name"]}.')}",
        f"model = {toml_str(model)}",
        f"model_reasoning_effort = {toml_str(effort)}",
        f"sandbox_mode = {toml_str(sandbox)}",
        f"developer_instructions = {toml_str(instructions)}",
        "",
    ]
    return "\n".join(lines)


def render_codex_config(profile: dict[str, Any], profile_hash: str) -> str:
    template_id = "codex.config.v1"
    source_hash = sha256_text(template_id)
    return (
        f"# VIBEOS-GENERATED template_id={template_id} profile_hash={profile_hash} source_hash={source_hash}\n"
        + f"# VibeOS Codex project config for {profile['project_name']}\n"
        + "[features]\n"
        + "codex_hooks = true\n\n"
        + "[agents]\n"
        + "max_threads = 4\n"
    )


def render_codex_hooks(profile: dict[str, Any], enabled: list[str]) -> str:
    hooks: dict[str, Any] = {
        "hooks": {
            "SessionStart": [
                {
                    "matcher": "startup|resume",
                    "hooks": [
                        {
                            "type": "command",
                            "command": 'bash "$(git rev-parse --show-toplevel)/.vibeos/scripts/detect-runtime-capabilities.sh" --project-dir "$(git rev-parse --show-toplevel)"',
                            "timeout": 30,
                            "statusMessage": f"Detecting VibeOS capabilities for {profile['project_name']}",
                        }
                    ],
                }
            ],
            "PreToolUse": [
                {
                    "matcher": "apply_patch|Edit|Write",
                    "hooks": [
                        {
                            "type": "command",
                            "command": 'bash "$(git rev-parse --show-toplevel)/.codex/hooks/secret-scan-codex.sh"',
                            "timeout": 5,
                            "statusMessage": f"Scanning {profile['project_name']} edit for secrets",
                        }
                    ],
                }
            ],
        }
    }
    if "generic-governance-prompt-scan" in enabled:
        hooks["hooks"]["UserPromptSubmit"] = [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": 'bash "$(git rev-parse --show-toplevel)/.codex/hooks/governance-guard-codex.sh"',
                        "timeout": 10,
                        "statusMessage": f"Checking {profile['project_name']} governance",
                    }
                ]
            }
        ]
    return json_dumps(hooks)


def render_claude_settings(profile: dict[str, Any], enabled: list[str]) -> str:
    hooks: dict[str, Any] = {
        "SessionStart": [
            {
                "matcher": "startup",
                "hooks": [
                    {
                        "type": "command",
                        "command": "./.vibeos/scripts/detect-runtime-capabilities.sh --project-dir .",
                        "timeout": 30,
                    }
                ],
            }
        ],
        "PreToolUse": [
            {
                "matcher": "Edit|Write",
                "hooks": [
                    {
                        "type": "command",
                        "command": "./.claude/hooks/secrets-scan.sh",
                        "timeout": 10,
                    },
                    {
                        "type": "command",
                        "command": "./.claude/hooks/frozen-files.sh",
                        "timeout": 5,
                    },
                ],
            }
        ],
    }
    if "generic-prompt-routing" in enabled:
        hooks["UserPromptSubmit"] = [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "./.claude/hooks/intent-router.sh",
                        "timeout": 10,
                    }
                ]
            }
        ]
    elif "generic-governance-prompt-scan" in enabled:
        hooks["UserPromptSubmit"] = [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "./.claude/hooks/governance-guard.sh",
                        "timeout": 10,
                    }
                ]
            }
        ]
    return json_dumps(
        {
            "generated_for": profile["project_name"],
            "hooks": hooks,
            "respectGitignore": True,
        }
    )


def render_gate_manifest(
    profile: dict[str, Any], validators: list[dict[str, str]]
) -> str:
    gates = [
        {
            "name": "vibeos-active-surface-audit",
            "script": "scripts/vibeos-active-surface-audit.py",
            "tier": 0,
            "blocking": True,
            "phase": "pre_commit",
            "env": {},
        },
        {
            "name": "vibeos-active-surface-audit-full",
            "script": "scripts/vibeos-active-surface-audit.py",
            "tier": 0,
            "blocking": True,
            "phase": "full_audit",
            "env": {},
        },
    ]
    for validator in validators:
        gates.append(
            {
                "name": f"existing-{validator['name']}",
                "script": "scripts/vibeos-active-surface-audit.py",
                "tier": 2,
                "blocking": False,
                "phase": "post_install_documented",
                "env": {"DOCUMENTED_COMMAND": validator["command"]},
            }
        )
    manifest = {
        "version": FRAMEWORK_VERSION,
        "project": profile["project_name"],
        "description": "Profile-generated active gate manifest. Existing project validators are recorded in install-plan post checks.",
        "gates": gates,
        "phases": {
            "pre_commit": {
                "description": "Fast blocking checks before commit",
                "enabled": True,
            },
            "full_audit": {
                "description": "Comprehensive active-surface audit",
                "enabled": True,
            },
        },
    }
    return json_dumps(manifest)


def render_active_surface_audit() -> str:
    return r'''#!/usr/bin/env python3
"""Audit generated VibeOS active surfaces for project-native safety."""

from __future__ import annotations

import json
import sys
from pathlib import Path


FORBIDDEN_GENERIC_PHRASES = [
    "autonomous, self-governing development engine",
    "generic VibeOS operating truth",
    "Decision engine and reference materials in .vibeos",
]


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def main() -> int:
    root = Path.cwd()
    profile = load_json(root / ".vibeos/project-profile.json")
    lock = load_json(root / ".vibeos/install-lock.json")
    project = profile.get("project_name")
    enabled = set(profile.get("active_modules", []))
    avoid = set(profile.get("avoid_surfaces", []))
    failures: list[str] = []

    # TOML/JSON surfaces embed the name string-escaped (quotes, backslashes),
    # so the mention check must accept the escaped form too.
    project_forms = [project] if project else []
    if project:
        escaped = json.dumps(project, ensure_ascii=False)[1:-1]
        if escaped != project:
            project_forms.append(escaped)

    def mentions_project(text: str) -> bool:
        return any(form in text for form in project_forms)

    if not project:
        failures.append("missing project_name in .vibeos/project-profile.json")

    generated_files = lock.get("generated_files", [])
    instruction_files = [
        item
        for item in generated_files
        if item.get("instruction_surface") and (root / item.get("path", "")).is_file()
    ]

    for item in instruction_files:
        path = root / item["path"]
        text = path.read_text(encoding="utf-8", errors="replace")
        if project and not mentions_project(text):
            failures.append(f"{item['path']} does not mention target project {project!r}")
        for phrase in FORBIDDEN_GENERIC_PHRASES:
            if phrase in text:
                failures.append(f"{item['path']} contains generic active-instruction phrase: {phrase}")
        for avoided in avoid:
            if avoided and avoided in text:
                failures.append(f"{item['path']} references rejected generic path: {avoided}")

    if "full-payload" not in enabled:
        for dormant in [".vibeos/reference", ".vibeos/decision-engine", ".vibeos/convergence"]:
            if (root / dormant).exists():
                failures.append(f"dormant payload exists without full-payload opt-in: {dormant}")

    for toml_path in (root / ".codex/agents").glob("*.toml"):
        text = toml_path.read_text(encoding="utf-8", errors="replace")
        stem = toml_path.stem
        if ("auditor" in stem or stem in {"plan-auditor", "contract-validator"}) and 'sandbox_mode = "read-only"' not in text:
            failures.append(f"read-only role is not read-only in Codex TOML: {toml_path.relative_to(root)}")
        if project and not mentions_project(text):
            failures.append(f"Codex TOML does not mention target project {project!r}: {toml_path.relative_to(root)}")

    hooks = load_json(root / ".codex/hooks.json")
    if "UserPromptSubmit" in hooks.get("hooks", {}) and "generic-governance-prompt-scan" not in enabled:
        failures.append("Codex UserPromptSubmit governance scan is active without opt-in")

    claude_settings = load_json(root / ".claude/settings.json")
    if "UserPromptSubmit" in claude_settings.get("hooks", {}) and not (
        {"generic-prompt-routing", "generic-governance-prompt-scan"} & enabled
    ):
        failures.append("Claude prompt routing/governance scan is active without opt-in")

    commit_msg = root / ".git/hooks/commit-msg"
    if commit_msg.is_file() and "commit-msg-enforcement" not in enabled:
        text = commit_msg.read_text(encoding="utf-8", errors="replace")
        if "VibeOS" in text or "validate-commit-msg" in text:
            failures.append("VibeOS commit-msg enforcement is active without opt-in")

    if failures:
        print("[vibeos-active-surface-audit] FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"[vibeos-active-surface-audit] PASS: active surfaces are project-native for {project}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def output(
    path: str,
    content: str | bytes,
    template_id: str,
    *,
    source_hash: str | None = None,
    instruction_surface: bool = False,
    executable: bool = False,
) -> dict[str, Any]:
    if isinstance(content, bytes):
        content_hash = sha256_bytes(content)
        resolved_source_hash = source_hash or content_hash
    else:
        content_hash = sha256_text(content)
        resolved_source_hash = source_hash or sha256_text(template_id)
    return {
        "path": path,
        "content": content,
        "template_id": template_id,
        "source_hash": resolved_source_hash,
        "content_hash": content_hash,
        "instruction_surface": instruction_surface,
        "executable": executable,
    }


def read_source_agent(source: Path, role: str) -> tuple[dict[str, str], str]:
    path = contained_path(source, f"agents/{role}.md", "source agent")
    text = path.read_text(encoding="utf-8", errors="replace")
    return parse_frontmatter(text)


def add_tree_outputs(
    outputs: list[dict[str, Any]], source_dir: Path, target_prefix: str
) -> None:
    if source_dir.is_symlink():
        raise InstallError(f"source tree may not be a symlink: {source_dir}")
    for path in sorted(source_dir.rglob("*")):
        if path.is_symlink():
            raise InstallError(f"source tree may not contain symlinks: {path}")
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(source_dir).as_posix()
        payload = path.read_bytes()
        outputs.append(
            output(
                f"{target_prefix}/{rel}",
                payload,
                f"copy.{target_prefix}.{rel}",
                source_hash=sha256_bytes(payload),
                executable=os.access(path, os.X_OK) or path.suffix in {".sh", ".py"},
            )
        )


def add_python_package_outputs(
    outputs: list[dict[str, Any]], source_dir: Path, target_prefix: str
) -> None:
    if source_dir.is_symlink():
        raise InstallError(
            f"controlled evaluation package may not be a symlink: {source_dir}"
        )
    for path in sorted(source_dir.rglob("*.py")):
        if path.is_symlink():
            raise InstallError(
                f"controlled evaluation package may not contain symlinks: {path}"
            )
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        rel = path.relative_to(source_dir).as_posix()
        payload = path.read_bytes()
        outputs.append(
            output(
                f"{target_prefix}/{rel}",
                payload,
                f"copy.{target_prefix}.{rel}",
                source_hash=sha256_bytes(payload),
                executable=os.access(path, os.X_OK),
            )
        )


def controlled_evaluation_guide(source: Path, repo: Path) -> Path | None:
    candidates = [
        contained_path(
            source,
            "docs/CONTROLLED-EVALUATION.md",
            "controlled evaluation guide",
        ),
        contained_path(
            repo,
            "docs/CONTROLLED-EVALUATION.md",
            "controlled evaluation guide",
        ),
    ]
    return next((path for path in candidates if path.is_file()), None)


def build_outputs(plan: dict[str, Any], source: Path) -> list[dict[str, Any]]:
    profile = plan["profile"]
    profile_hash = plan["profile_hash"]
    enabled = plan["enabled_modules"]
    validators = plan["existing_validators"]
    outputs: list[dict[str, Any]] = []

    profile_for_target = dict(profile)
    profile_for_target["active_modules"] = enabled
    outputs.append(
        output(
            ".vibeos/project-profile.json",
            json_dumps(profile_for_target),
            "profile.project-profile.v1",
            source_hash=profile_hash,
        )
    )

    for script in selected_scripts(source, enabled):
        src = contained_path(source, f"scripts/{script}", "source script")
        payload = src.read_bytes()
        outputs.append(
            output(
                f".vibeos/scripts/{script}",
                payload,
                f"copy.script.{script}",
                source_hash=sha256_bytes(payload),
                executable=script.endswith((".sh", ".py")),
            )
        )

    evaluation_entrypoint = contained_path(
        source, "scripts/controlled-evaluation.py", "controlled evaluation entrypoint"
    )
    evaluation_package = source / "scripts" / "controlled_evaluation"
    if evaluation_entrypoint.is_file() and evaluation_package.is_dir():
        payload = evaluation_entrypoint.read_bytes()
        outputs.append(
            output(
                ".vibeos/scripts/controlled-evaluation.py",
                payload,
                "copy.script.controlled-evaluation.py",
                source_hash=sha256_bytes(payload),
                executable=True,
            )
        )
        add_python_package_outputs(
            outputs,
            evaluation_package,
            ".vibeos/scripts/controlled_evaluation",
        )
        guide = controlled_evaluation_guide(
            source, Path(plan["source_binding"]["repo"])
        )
        if guide is not None:
            guide_payload = guide.read_bytes()
            outputs.append(
                output(
                    ".vibeos/controlled-evaluation-guide.md",
                    guide_payload,
                    "copy.docs.CONTROLLED-EVALUATION",
                    source_hash=sha256_bytes(guide_payload),
                    instruction_surface=False,
                )
            )

    audit_script = render_active_surface_audit()
    outputs.append(
        output(
            ".vibeos/scripts/vibeos-active-surface-audit.py",
            audit_script,
            "script.active-surface-audit.v1",
            executable=True,
        )
    )

    if "full-payload" in enabled:
        for folder in ["reference", "decision-engine", "convergence"]:
            source_dir = source / folder
            if source_dir.is_dir():
                add_tree_outputs(outputs, source_dir, f".vibeos/{folder}")
        docs_source = contained_path(
            source, "docs/USER-COMMUNICATION-CONTRACT.md", "source documentation"
        )
        if docs_source.is_file():
            payload = docs_source.read_bytes()
            outputs.append(
                output(
                    "docs/USER-COMMUNICATION-CONTRACT.md",
                    payload,
                    "copy.docs.USER-COMMUNICATION-CONTRACT",
                    source_hash=sha256_bytes(payload),
                    instruction_surface=True,
                )
            )

    outputs.append(
        output(
            "AGENTS.md",
            render_agents_md(profile, profile_hash),
            "codex.agents-md.v1",
            instruction_surface=True,
        )
    )
    outputs.append(
        output(
            ".claude/CLAUDE.md",
            render_claude_md(profile, profile_hash),
            "claude.boot-md.v1",
            instruction_surface=True,
        )
    )
    outputs.append(
        output(
            ".claude/settings.json",
            render_claude_settings(profile, enabled),
            "claude.settings.v1",
            instruction_surface=False,
        )
    )
    outputs.append(
        output(
            ".codex/config.toml",
            render_codex_config(profile, profile_hash),
            "codex.config.v1",
            instruction_surface=True,
        )
    )
    outputs.append(
        output(
            ".codex/hooks.json",
            render_codex_hooks(profile, enabled),
            "codex.hooks.v1",
        )
    )
    outputs.append(
        output(
            ".claude/quality-gate-manifest.json",
            render_gate_manifest(profile, validators),
            "gate-manifest.v1",
        )
    )

    secret_hook = contained_path(
        source,
        "reference/codex/hooks/secret-scan-codex.sh",
        "Codex hook source",
    )
    if secret_hook.is_file():
        payload = secret_hook.read_bytes()
        outputs.append(
            output(
                ".codex/hooks/secret-scan-codex.sh",
                payload,
                "copy.codex-hook.secret-scan-codex",
                source_hash=sha256_bytes(payload),
                executable=True,
            )
        )
    if "generic-governance-prompt-scan" in enabled:
        governance_hook = contained_path(
            source,
            "reference/codex/hooks/governance-guard-codex.sh",
            "Codex hook source",
        )
        if governance_hook.is_file():
            payload = governance_hook.read_bytes()
            outputs.append(
                output(
                    ".codex/hooks/governance-guard-codex.sh",
                    payload,
                    "copy.codex-hook.governance-guard-codex",
                    source_hash=sha256_bytes(payload),
                    executable=True,
                )
            )

    for hook in ["secrets-scan.sh", "frozen-files.sh"]:
        src = contained_path(source, f"hooks/scripts/{hook}", "Claude hook source")
        if src.is_file():
            payload = src.read_bytes()
            outputs.append(
                output(
                    f".claude/hooks/{hook}",
                    payload,
                    f"copy.claude-hook.{hook}",
                    source_hash=sha256_bytes(payload),
                    executable=True,
                )
            )
    if "generic-prompt-routing" in enabled:
        src = contained_path(
            source, "hooks/scripts/intent-router.sh", "Claude hook source"
        )
        if src.is_file():
            payload = src.read_bytes()
            outputs.append(
                output(
                    ".claude/hooks/intent-router.sh",
                    payload,
                    "copy.claude-hook.intent-router",
                    source_hash=sha256_bytes(payload),
                    executable=True,
                )
            )
    if "generic-governance-prompt-scan" in enabled:
        src = contained_path(
            source, "hooks/scripts/governance-guard.sh", "Claude hook source"
        )
        if src.is_file():
            payload = src.read_bytes()
            outputs.append(
                output(
                    ".claude/hooks/governance-guard.sh",
                    payload,
                    "copy.claude-hook.governance-guard",
                    source_hash=sha256_bytes(payload),
                    executable=True,
                )
            )

    for skill in selected_skills(enabled):
        text = render_skill(skill, profile, profile_hash)
        outputs.append(
            output(
                f".agents/skills/{skill}/SKILL.md",
                text,
                f"skill.{skill}.v1",
                instruction_surface=True,
            )
        )
        outputs.append(
            output(
                f".codex/skills/{skill}/SKILL.md",
                text,
                f"skill.{skill}.v1",
                instruction_surface=True,
            )
        )
        outputs.append(
            output(
                f".claude/skills/{skill}/SKILL.md",
                text,
                f"skill.{skill}.v1",
                instruction_surface=True,
            )
        )

    for role in selected_roles(source, enabled):
        meta, _body = read_source_agent(source, role)
        contract = render_role_contract(role, meta, profile, profile_hash)
        toml = render_codex_toml(role, meta, profile, profile_hash)
        outputs.append(
            output(
                f".codex/agent-contracts/{role}.md",
                contract,
                f"role.{role}.v1",
                source_hash=sha256_text(json_dumps(meta)),
                instruction_surface=True,
            )
        )
        outputs.append(
            output(
                f".claude/agents/{role}.md",
                contract,
                f"role.{role}.v1",
                source_hash=sha256_text(json_dumps(meta)),
                instruction_surface=True,
            )
        )
        outputs.append(
            output(
                f".codex/agents/{role}.toml",
                toml,
                f"codex.toml.{role}.v1",
                source_hash=sha256_text(json_dumps(meta)),
                instruction_surface=True,
            )
        )

    return outputs


def planned_active_gates(
    profile: dict[str, Any], validators: list[dict[str, str]]
) -> list[dict[str, Any]]:
    gates = [
        {
            "name": "vibeos-active-surface-audit",
            "phase": "pre_commit",
            "command": "python3 .vibeos/scripts/vibeos-active-surface-audit.py",
            "blocking": True,
        },
        {
            "name": "vibeos-active-surface-audit",
            "phase": "full_audit",
            "command": "python3 .vibeos/scripts/vibeos-active-surface-audit.py",
            "blocking": True,
        },
    ]
    for gate in profile.get("primary_gates", []):
        gates.append(
            {
                "name": "profile-primary-gate",
                "phase": "post_install",
                "command": gate,
                "blocking": True,
            }
        )
    for validator in validators:
        gates.append(
            {
                "name": validator["name"],
                "phase": "post_install",
                "command": validator["command"],
                "blocking": False,
            }
        )
    return gates


def build_plan(
    source: Path,
    target: Path,
    profile: dict[str, Any],
    *,
    profile_path: Path | None = None,
    plan_path: Path | None = None,
) -> dict[str, Any]:
    check_source_target_safety(source, target)
    enabled = modules_for_profile(profile)
    validators = detect_validators(target)
    profile_hash = sha256_text(json_dumps(profile))
    plan: dict[str, Any] = {
        "schema_version": 2,
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": utc_now(),
        "source": str(source),
        "target": str(target),
        "mode": profile["mode"],
        "profile_hash": profile_hash,
        "profile": profile,
        "detected_canon": detect_canon(target),
        "protected_files": profile.get("protected_files", []),
        "existing_validators": validators,
        "enabled_modules": enabled,
        "skipped_modules": skipped_modules(enabled, profile["mode"]),
        "active_gates": planned_active_gates(profile, validators),
        "dormant_payload": [] if "full-payload" in enabled else DORMANT_PAYLOAD,
        "post_install_checks": [
            "python3 .vibeos/scripts/vibeos-active-surface-audit.py",
            "bash .vibeos/scripts/detect-runtime-capabilities.sh --project-dir .",
        ],
        "source_binding": source_binding(source, FRAMEWORK_VERSION),
        "profile_binding": profile_binding(profile_path, profile_hash),
        "target_analysis_binding": analysis_input_binding(
            target, TARGET_ANALYSIS_INPUTS
        ),
        "plan_path": str(plan_path.resolve()) if plan_path else None,
    }
    outputs = build_outputs(plan, source)
    inventory = output_inventory(outputs)
    plan["analyzed_outputs"] = inventory
    plan["analyzed_outputs_hash"] = sha256_json(inventory)
    plan["source_generated_inventory_sha256"] = sha256_json(
        {
            "relevant_source_files_sha256": plan["source_binding"][
                "relevant_files_sha256"
            ],
            "analyzed_outputs_hash": plan["analyzed_outputs_hash"],
        }
    )
    active_surfaces = [item["path"] for item in outputs]
    active_surfaces.append(".vibeos/install-lock.json")
    plan["active_surfaces"] = sorted(active_surfaces)
    plan["overwrite_plan"] = build_overwrite_plan(target, outputs)
    candidate_paths = [
        row["candidate"]
        for row in plan["overwrite_plan"]
        if isinstance(row.get("candidate"), str)
    ]
    bound_paths = [item["path"] for item in outputs]
    bound_paths.extend(candidate_paths)
    bound_paths.append(".vibeos/install-lock.json")
    plan["target_binding"] = target_binding(target, bound_paths)
    plan["plan_payload_hash"] = plan_payload_hash(plan)
    return plan


def load_existing_lock(target: Path) -> dict[str, Any]:
    lock_path = contained_path(target, ".vibeos/install-lock.json", "install lock")
    if lock_path.is_file():
        try:
            payload = json.loads(lock_path.read_text(encoding="utf-8"))
            return payload if isinstance(payload, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def existing_file_meta(lock: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        item["path"]: item for item in lock.get("generated_files", []) if "path" in item
    }


def build_overwrite_plan(
    target: Path, outputs: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    lock = load_existing_lock(target)
    previous = existing_file_meta(lock)
    result: list[dict[str, Any]] = []
    for item in outputs:
        path = contained_path(target, item["path"], "install output")
        candidate: str | None = None
        if not path.exists():
            action = "create"
            reason = "file does not exist"
        else:
            old = previous.get(item["path"])
            current_hash = sha256_bytes(path.read_bytes())
            if current_hash == item["content_hash"]:
                expected_mode = 0o755 if item.get("executable") else 0o644
                if stat.S_IMODE(path.stat().st_mode) != expected_mode:
                    action = "repair-file-mode"
                    reason = "generated content matches but file mode drifted"
                else:
                    action = "keep-current"
                    reason = "generated content is already current"
            elif old and current_hash == old.get("content_hash"):
                action = "replace-generated"
                reason = "previous generated file has no local changes"
            elif old:
                action = "three-way-merge-required"
                reason = (
                    "local customization detected; write candidate without overwriting"
                )
                candidate = conflict_relative_path(target, item)
            else:
                action = "preserve-existing"
                reason = "unmanaged target file exists"
                candidate = conflict_relative_path(target, item)
        row = {"path": item["path"], "action": action, "reason": reason}
        if candidate:
            row["candidate"] = candidate
        result.append(row)
    return result


def write_plan(plan: dict[str, Any], plan_path: Path) -> None:
    atomic_write(plan_path, json_dumps(plan).encode("utf-8"), 0o644)


def read_plan(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise InstallError("install plan must be a JSON object")
    return payload


def write_output(target: Path, item: dict[str, Any]) -> None:
    path = contained_path(target, item["path"], "install output")
    content = item["content"]
    payload = content if isinstance(content, bytes) else content.encode("utf-8")
    mode = 0o755 if item.get("executable") else 0o644
    atomic_write(path, payload, mode)


def conflict_path(target: Path, rel_path: str) -> Path:
    safe = rel_path.replace("/", "__")
    return contained_path(
        target,
        f".vibeos/merge-conflicts/{safe}.generated",
        "merge candidate",
    )


def conflict_relative_path(target: Path, item: dict[str, Any]) -> str:
    base = relative_path(conflict_path(target, item["path"]), target)
    path = contained_path(target, base, "merge candidate")
    if not path.exists() or (
        path.is_file() and sha256_file(path) == item["content_hash"]
    ):
        return base
    alternative = f"{base}.{item['content_hash'][:12]}"
    alternative_path = contained_path(target, alternative, "merge candidate")
    if not alternative_path.exists() or (
        alternative_path.is_file()
        and sha256_file(alternative_path) == item["content_hash"]
    ):
        return alternative
    raise InstallError(
        f"merge candidate paths are occupied; preserve them and choose a fresh plan: {base}"
    )


def expected_conflicts(plan: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {"path": row["path"], "candidate": row["candidate"]}
        for row in plan.get("overwrite_plan", [])
        if row.get("action") in {"three-way-merge-required", "preserve-existing"}
    ]


def expected_installed_state(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    outputs = {
        row["path"]: row
        for row in plan.get("analyzed_outputs", [])
        if isinstance(row, dict) and isinstance(row.get("path"), str)
    }
    overwrite_rows = plan.get("overwrite_plan")
    if not isinstance(overwrite_rows, list):
        raise InstallError("install plan overwrite inventory is invalid")
    overwrite = {
        row["path"]: row
        for row in overwrite_rows
        if isinstance(row, dict) and isinstance(row.get("path"), str)
    }
    if len(outputs) != len(plan.get("analyzed_outputs", [])) or set(outputs) != set(
        overwrite
    ):
        raise InstallError("install plan output and overwrite inventories differ")
    baseline = {
        row["path"]: row
        for row in plan.get("target_binding", [])
        if isinstance(row, dict) and isinstance(row.get("path"), str)
    }
    expected: dict[str, dict[str, Any]] = {}
    action_names = {
        "create": "created",
        "replace-generated": "replaced-generated",
        "repair-file-mode": "repaired-file-mode",
        "keep-current": "unchanged",
        "three-way-merge-required": "preserved-local-customization",
        "preserve-existing": "preserved-unmanaged-existing",
    }
    for rel, output_row in sorted(outputs.items()):
        overwrite_row = overwrite[rel]
        action = overwrite_row.get("action")
        if action not in action_names:
            raise InstallError(f"install plan has unknown overwrite action: {rel}={action}")
        if action in {"three-way-merge-required", "preserve-existing"}:
            state = baseline.get(rel)
            if not isinstance(state, dict) or state.get("kind") != "file":
                raise InstallError(f"preserved output lacks a file baseline: {rel}")
            expected[rel] = dict(state, action=action_names[action])
            candidate = overwrite_row.get("candidate")
            safe_relative(candidate, "merge candidate")
            expected[candidate] = {
                "path": candidate,
                "kind": "file",
                "sha256": output_row["content_hash"],
                "mode": 0o755 if output_row.get("executable") else 0o644,
                "action": "merge-candidate",
            }
        else:
            expected[rel] = {
                "path": rel,
                "kind": "file",
                "sha256": output_row["content_hash"],
                "mode": 0o755 if output_row.get("executable") else 0o644,
                "action": action_names[action],
            }
    return expected


def verify_installed_state(
    target: Path, plan: dict[str, Any], lock: dict[str, Any]
) -> None:
    status = lock.get("transaction_status")
    if status != "complete":
        raise InstallError(f"installed transaction is not complete: {status}")
    required_bindings = {
        "schema_version": 2,
        "framework_version": FRAMEWORK_VERSION,
        "source": plan["source"],
        "target": plan["target"],
        "mode": plan["mode"],
        "profile_hash": plan["profile_hash"],
        "source_binding": plan["source_binding"],
        "profile_binding": plan["profile_binding"],
        "plan_path": plan["plan_path"],
        "plan_payload_hash": plan["plan_payload_hash"],
        "analyzed_outputs_hash": plan["analyzed_outputs_hash"],
        "source_generated_inventory_sha256": plan[
            "source_generated_inventory_sha256"
        ],
        "generated_files": plan["analyzed_outputs"],
        "conflicts": expected_conflicts(plan),
    }
    for field, expected_value in required_bindings.items():
        if lock.get(field) != expected_value:
            raise InstallError(f"install lock binding mismatch: {field}")
    checks = lock.get("post_install_checks")
    if not isinstance(checks, list) or not checks or any(
        not isinstance(check, dict) or check.get("exit_code") != 0 for check in checks
    ):
        raise InstallError("install lock lacks passing post-install checks")

    expected = expected_installed_state(plan)
    rows = lock.get("installed_state")
    if not isinstance(rows, list):
        raise InstallError("install lock is missing installed state")
    actual_rows: dict[str, dict[str, Any]] = {}
    for row in rows:
        if (
            not isinstance(row, dict)
            or set(row) != {"path", "kind", "sha256", "mode", "action"}
            or not isinstance(row.get("path"), str)
            or row["path"] in actual_rows
        ):
            raise InstallError("install lock has malformed installed state")
        actual_rows[row["path"]] = row
    if actual_rows != expected:
        raise InstallError("install lock installed-state inventory mismatch")
    for rel, expected_row in expected.items():
        actual = file_state(target, rel)
        wanted = {key: expected_row[key] for key in ("path", "kind", "sha256", "mode")}
        if actual != wanted:
            raise InstallError(f"installed target drift: {rel}")
    audit = subprocess.run(
        ["python3", ".vibeos/scripts/vibeos-active-surface-audit.py"],
        cwd=target,
        capture_output=True,
        text=True,
        check=False,
    )
    if audit.returncode:
        detail = audit.stdout.strip() or audit.stderr.strip() or "no diagnostic output"
        raise InstallError(f"installed post-check verification failed: {detail}")


def observed_installed_state(
    target: Path, plan: dict[str, Any]
) -> list[dict[str, Any]]:
    expected = expected_installed_state(plan)
    rows: list[dict[str, Any]] = []
    for rel, expected_row in sorted(expected.items()):
        state = file_state(target, rel)
        wanted = {
            key: expected_row[key] for key in ("path", "kind", "sha256", "mode")
        }
        if state != wanted:
            raise InstallError(f"applied output differs from pinned plan: {rel}")
        state["action"] = expected_row["action"]
        rows.append(state)
    return rows


def build_install_lock(
    plan: dict[str, Any],
    plan_path: Path,
    status: str,
    checks: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": 2,
        "transaction_status": status,
        "framework_version": FRAMEWORK_VERSION,
        "generated_at": utc_now(),
        "source": plan["source"],
        "target": plan["target"],
        "mode": plan["mode"],
        "profile_hash": plan["profile_hash"],
        "source_binding": plan["source_binding"],
        "profile_binding": plan["profile_binding"],
        "plan_path": str(plan_path),
        "plan_payload_hash": plan["plan_payload_hash"],
        "analyzed_outputs_hash": plan["analyzed_outputs_hash"],
        "source_generated_inventory_sha256": plan[
            "source_generated_inventory_sha256"
        ],
        "installed_state": observed_installed_state(Path(plan["target"]), plan),
        "generated_files": plan["analyzed_outputs"],
        "conflicts": expected_conflicts(plan),
        "post_install_checks": checks,
    }


def write_transaction_lock(
    target: Path, lock: dict[str, Any], *, allow_previous: bool = False
) -> None:
    lock_path = contained_path(target, ".vibeos/install-lock.json", "install lock")
    lock_payload = json_dumps(lock).encode("utf-8")
    record_expected_state(
        target,
        ".vibeos/install-lock.json",
        {
            "path": ".vibeos/install-lock.json",
            "kind": "file",
            "sha256": sha256_bytes(lock_payload),
            "mode": 0o644,
        },
        allow_previous=allow_previous,
    )
    if (
        allow_previous
        and os.environ.get("VIBEOS_INSTALL_TEST_INTERRUPT_BEFORE_COMPLETE_LOCK")
    ):
        os.kill(os.getpid(), signal.SIGTERM)
    atomic_write(lock_path, lock_payload, 0o644)


def verify_plan(plan: dict[str, Any], plan_path: Path) -> dict[str, Any]:
    if plan_path.is_symlink() or not plan_path.is_file():
        raise InstallError(
            f"install plan must be a regular non-symlink file: {plan_path}"
        )
    if read_plan(plan_path) != plan:
        raise InstallError("install plan changed while acquiring transaction lock")
    if plan.get("schema_version") != 2:
        raise InstallError("install plan schema drift; run analyze again")
    recorded_hash = plan.get("plan_payload_hash")
    if not isinstance(recorded_hash, str) or plan_payload_hash(plan) != recorded_hash:
        raise InstallError("install plan payload hash mismatch")
    if plan.get("framework_version") != FRAMEWORK_VERSION:
        raise InstallError("framework version drift; run analyze again")
    recorded_plan_path = plan.get("plan_path")
    if recorded_plan_path and Path(recorded_plan_path) != plan_path:
        raise InstallError("install plan path drift")

    source = Path(plan["source"]).resolve()
    target = Path(plan["target"]).resolve()
    check_source_target_safety(source, target)
    require_no_active_transaction(target)
    if str(source) != plan.get("source") or str(target) != plan.get("target"):
        raise InstallError("canonical source or target path drift")
    profile = plan.get("profile")
    if not isinstance(profile, dict):
        raise InstallError("install plan profile is invalid")
    profile_hash = sha256_text(json_dumps(profile))
    if profile_hash != plan.get("profile_hash"):
        raise InstallError("embedded profile hash mismatch")
    verify_profile_binding(plan.get("profile_binding"), profile_hash)
    verify_source_binding(source, FRAMEWORK_VERSION, plan.get("source_binding"))
    if modules_for_profile(profile) != plan.get("enabled_modules"):
        raise InstallError("profile module expansion drift")

    analyzed = plan.get("analyzed_outputs")
    if not isinstance(analyzed, list):
        raise InstallError("analyzed output inventory is missing")
    for row in analyzed:
        if not isinstance(row, dict):
            raise InstallError("analyzed output inventory is malformed")
        safe_relative(row.get("path"), "analyzed output path")
    outputs = build_outputs(plan, source)
    inventory = output_inventory(outputs)
    if inventory != analyzed or sha256_json(inventory) != plan.get(
        "analyzed_outputs_hash"
    ):
        raise InstallError("analyzed output drift after analyze")
    combined_inventory = sha256_json(
        {
            "relevant_source_files_sha256": plan["source_binding"][
                "relevant_files_sha256"
            ],
            "analyzed_outputs_hash": plan["analyzed_outputs_hash"],
        }
    )
    if combined_inventory != plan.get("source_generated_inventory_sha256"):
        raise InstallError("source/generated inventory binding mismatch")
    expected_active = sorted(
        [item["path"] for item in outputs] + [".vibeos/install-lock.json"]
    )
    if expected_active != plan.get("active_surfaces"):
        raise InstallError("active output inventory drift")

    lock = load_existing_lock(target)
    if lock.get("plan_payload_hash") == recorded_hash:
        verify_installed_state(target, plan, lock)
        return {"state": "installed", "plan_payload_hash": recorded_hash}

    verify_analysis_input_binding(target, plan.get("target_analysis_binding"))
    verify_target_binding(target, plan.get("target_binding"))
    if build_overwrite_plan(target, outputs) != plan.get("overwrite_plan"):
        raise InstallError("target overwrite baseline drift after analyze")
    return {"state": "planned", "plan_payload_hash": recorded_hash}


def _candidate_output(item: dict[str, Any], candidate: str) -> dict[str, Any]:
    result = dict(item)
    result["path"] = candidate
    return result


def apply_plan(
    plan: dict[str, Any],
    *,
    plan_path: Path,
    skip_post_checks: bool = False,
) -> dict[str, Any]:
    target = Path(plan["target"]).resolve()
    with project_lock(target, exclusive=True):
        return _apply_plan_locked(
            plan,
            plan_path=plan_path,
            skip_post_checks=skip_post_checks,
        )


def _apply_plan_locked(
    plan: dict[str, Any],
    *,
    plan_path: Path,
    skip_post_checks: bool = False,
) -> dict[str, Any]:
    verification = verify_plan(plan, plan_path)
    if verification["state"] == "installed":
        return {
            "applied": [],
            "conflicts": plan.get("conflicts", []),
            "post_install_checks": [],
            "transaction_status": "complete",
            "already_installed": True,
        }
    source = Path(plan["source"])
    target = Path(plan["target"])
    outputs = build_outputs(plan, source)
    overwrite_by_path = {row["path"]: row for row in plan["overwrite_plan"]}
    mutations: list[dict[str, Any]] = [
        {"path": ".vibeos/install-lock.json", "after": None}
    ]
    for item in outputs:
        row = overwrite_by_path[item["path"]]
        if row["action"] in {"create", "replace-generated", "repair-file-mode"}:
            mutations.append(
                {
                    "path": item["path"],
                    "after": {
                        "path": item["path"],
                        "kind": "file",
                        "sha256": item["content_hash"],
                        "mode": 0o755 if item.get("executable") else 0o644,
                    },
                }
            )
        elif row["action"] in {"three-way-merge-required", "preserve-existing"}:
            mutations.append(
                {
                    "path": row["candidate"],
                    "after": {
                        "path": row["candidate"],
                        "kind": "file",
                        "sha256": item["content_hash"],
                        "mode": 0o755 if item.get("executable") else 0o644,
                    },
                }
            )
    begin_transaction(target, plan_path, plan["plan_payload_hash"], mutations)

    applied: list[dict[str, Any]] = []
    conflicts: list[dict[str, str]] = []
    checks: list[dict[str, Any]] = []
    written = 0
    try:
        for item in outputs:
            row = overwrite_by_path[item["path"]]
            planned_action = row["action"]
            action = {
                "create": "created",
                "replace-generated": "replaced-generated",
                "repair-file-mode": "repaired-file-mode",
                "keep-current": "unchanged",
            }.get(planned_action, planned_action)
            if planned_action in {
                "create",
                "replace-generated",
                "repair-file-mode",
            }:
                write_output(target, item)
                written += 1
            elif planned_action in {"three-way-merge-required", "preserve-existing"}:
                candidate = row["candidate"]
                candidate_item = _candidate_output(item, candidate)
                write_output(target, candidate_item)
                written += 1
                action = (
                    "preserved-local-customization"
                    if planned_action == "three-way-merge-required"
                    else "preserved-unmanaged-existing"
                )
                conflicts.append({"path": item["path"], "candidate": candidate})
            applied.append({"path": item["path"], "action": action})
            interrupt_after = os.environ.get("VIBEOS_INSTALL_TEST_INTERRUPT_AFTER")
            if interrupt_after and written >= int(interrupt_after):
                os.kill(os.getpid(), signal.SIGTERM)

        if conflicts != expected_conflicts(plan):
            raise InstallError("applied merge-candidate inventory differs from pinned plan")
        transaction_status = "applied-unverified" if skip_post_checks else "verifying"
        provisional_lock = build_install_lock(
            plan,
            plan_path,
            transaction_status,
            checks,
        )
        write_transaction_lock(target, provisional_lock)

        if not skip_post_checks:
            result = subprocess.run(
                ["python3", ".vibeos/scripts/vibeos-active-surface-audit.py"],
                cwd=target,
                capture_output=True,
                text=True,
                check=False,
            )
            checks.append(
                {
                    "command": "python3 .vibeos/scripts/vibeos-active-surface-audit.py",
                    "exit_code": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                }
            )
            if result.returncode:
                detail = (
                    result.stdout.strip()
                    or result.stderr.strip()
                    or "no diagnostic output"
                )
                raise InstallError(
                    "post-install check failed; run recover with the same plan before retrying: "
                    + detail
                )
            transaction_status = "complete"
            complete_lock = build_install_lock(
                plan,
                plan_path,
                transaction_status,
                checks,
            )
            write_transaction_lock(target, complete_lock, allow_previous=True)
        complete_transaction(target)
        return {
            "applied": applied,
            "conflicts": conflicts,
            "post_install_checks": checks,
            "transaction_status": transaction_status,
            "already_installed": False,
        }
    except Exception as exc:
        mark_recovery_required(target, str(exc))
        raise


def command_analyze(args: argparse.Namespace) -> int:
    source = resolve_source(args.source)
    target = resolve_target(args.target)
    profile_candidate = (
        Path(args.profile).expanduser().absolute() if args.profile else None
    )
    if profile_candidate and profile_candidate.is_symlink():
        raise InstallError(f"profile may not be a symlink: {profile_candidate}")
    profile_path = profile_candidate.resolve() if profile_candidate else None
    if profile_path and not profile_path.is_file():
        print(f"[vibeos] FAIL: profile not found: {profile_path}")
        print(
            "[vibeos] hint: the installer writes the pinned profile to .vibeos/project-profile.json"
        )
        return 2
    plan_path = (
        Path(args.plan).expanduser().resolve()
        if args.plan
        else target / ".vibeos/install-plan.json"
    )
    with project_lock(target, exclusive=True):
        require_no_active_transaction(target)
        profile = load_profile(profile_path, target, args.mode)
        plan = build_plan(
            source,
            target,
            profile,
            profile_path=profile_path,
            plan_path=plan_path,
        )
        write_plan(plan, plan_path)
    print(f"[vibeos] PASS: install plan written: {plan_path}")
    print(
        f"[vibeos] mode={plan['mode']} enabled_modules={len(plan['enabled_modules'])} active_surfaces={len(plan['active_surfaces'])}"
    )
    return 0


def command_apply(args: argparse.Namespace) -> int:
    plan_candidate = Path(args.plan).expanduser().absolute()
    if plan_candidate.is_symlink():
        raise InstallError(f"install plan may not be a symlink: {plan_candidate}")
    plan_path = plan_candidate.resolve()
    plan = read_plan(plan_path)
    result = apply_plan(
        plan, plan_path=plan_path, skip_post_checks=args.skip_post_checks
    )
    conflicts = result["conflicts"]
    if result["already_installed"]:
        print(f"[vibeos] PASS: install already complete and verified: {plan['target']}")
        return 0
    status = result["transaction_status"]
    marker = "PASS" if status == "complete" else "APPLIED-UNVERIFIED"
    print(f"[vibeos] {marker}: applied profile-driven install plan to {plan['target']}")
    print(f"[vibeos] files={len(result['applied'])} conflicts={len(conflicts)}")
    for conflict in conflicts:
        print(
            f"[vibeos] MERGE: preserved {conflict['path']} candidate={conflict['candidate']}"
        )
    failed_checks = [
        check for check in result["post_install_checks"] if check.get("exit_code")
    ]
    if failed_checks:
        for check in failed_checks:
            print(
                f"[vibeos] FAIL: post-install check failed: {check['command']} exit={check['exit_code']}"
            )
        return 1
    return 0


def command_verify(args: argparse.Namespace) -> int:
    plan_candidate = Path(args.plan).expanduser().absolute()
    if plan_candidate.is_symlink():
        raise InstallError(f"install plan may not be a symlink: {plan_candidate}")
    plan_path = plan_candidate.resolve()
    plan = read_plan(plan_path)
    target = Path(plan["target"]).resolve()
    with project_lock(target, exclusive=False):
        result = verify_plan(plan, plan_path)
    print(f"[vibeos] PASS: install transaction verified: {result['state']}")
    print(f"[vibeos] plan_payload_hash={result['plan_payload_hash']}")
    return 0


def command_recover(args: argparse.Namespace) -> int:
    plan_candidate = Path(args.plan).expanduser().absolute()
    if plan_candidate.is_symlink():
        raise InstallError(f"install plan may not be a symlink: {plan_candidate}")
    plan_path = plan_candidate.resolve()
    plan = read_plan(plan_path)
    recorded_hash = plan.get("plan_payload_hash")
    if not isinstance(recorded_hash, str) or plan_payload_hash(plan) != recorded_hash:
        raise InstallError("install plan payload hash mismatch")
    target = Path(plan["target"]).resolve()
    with project_lock(target, exclusive=True):
        if read_plan(plan_path) != plan:
            raise InstallError("install plan changed while acquiring transaction lock")
        restored = recover_transaction(target, plan_path, recorded_hash)
        verify_target_binding(target, plan.get("target_binding"))
    print(f"[vibeos] PASS: interrupted install rollback verified: {target}")
    print(
        f"[vibeos] restored_paths={len(restored)}; run verify, then apply or re-analyze"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vibeos", description="Profile-driven VibeOS installer"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    analyze = sub.add_parser("analyze", help="write a profile-driven install plan")
    analyze.add_argument("--target", required=True, help="target project directory")
    analyze.add_argument(
        "--source", required=True, help="VibeOS source repo or plugins/vibeos directory"
    )
    analyze.add_argument("--profile", help="project profile JSON")
    analyze.add_argument(
        "--mode",
        default="product-engineering",
        choices=sorted(MODE_MODULES),
        help="install mode",
    )
    analyze.add_argument(
        "--plan", help="output plan path; default target/.vibeos/install-plan.json"
    )
    analyze.set_defaults(func=command_analyze)

    apply = sub.add_parser("apply", help="apply a previously generated install plan")
    apply.add_argument("--plan", required=True, help="install plan path")
    apply.add_argument(
        "--skip-post-checks",
        action="store_true",
        help="write files without running generated post checks",
    )
    apply.set_defaults(func=command_apply)

    verify = sub.add_parser(
        "verify", help="verify pinned plan or completed install without writing"
    )
    verify.add_argument("--plan", required=True, help="install plan path")
    verify.set_defaults(func=command_verify)

    recover = sub.add_parser(
        "recover", help="roll back an interrupted apply transaction"
    )
    recover.add_argument(
        "--plan", required=True, help="the exact plan used by interrupted apply"
    )
    recover.set_defaults(func=command_recover)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (
        InstallError,
        IntegrityError,
        RecoveryError,
        OSError,
        json.JSONDecodeError,
        KeyError,
    ) as exc:
        print(f"[vibeos] FAIL: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
