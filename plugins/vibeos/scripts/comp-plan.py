#!/usr/bin/env python3
"""Generate a VibOS Comp execution plan and worktree scope manifest."""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


SHARED_PATHS = [
    "MISSION.md",
    "COMP-PLAN.md",
    ".vibeos/worktree-scopes.json",
    "docs/planning/",
    "docs/evidence/",
    "docs/evidence/FLOW-INTEGRITY.md",
    "docs/evidence/SYSTEM-INVARIANTS.md",
    "docs/evidence/DEPENDENCY-INTELLIGENCE.md",
    "docs/evidence/DELIVERY-INFRASTRUCTURE.md",
    "README.md",
    ".env.example",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
]


def slugify(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")[:48] or "mission"


def read_mission(project_dir: Path) -> str:
    mission = project_dir / "MISSION.md"
    if not mission.exists():
        raise FileNotFoundError("MISSION.md is required before generating COMP-PLAN.md")
    return mission.read_text(encoding="utf-8")


def mission_name(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# Mission:"):
            return line.split(":", 1)[1].strip() or "Comp Mission"
    return "Comp Mission"


def existing_source_shape(project_dir: Path):
    frontend_markers = ["frontend", "client", "web", "ui", "components", "pages"]
    backend_markers = ["backend", "server", "api", "services", "app/api"]
    data_markers = ["db", "database", "migrations", "alembic", "prisma"]

    dirs = {str(path.relative_to(project_dir)) for path in project_dir.iterdir() if path.is_dir()}
    nested = {str(path.relative_to(project_dir)) for path in project_dir.glob("*/*") if path.is_dir()}
    all_dirs = dirs | nested

    has_frontend = any(any(marker in item for marker in frontend_markers) for item in all_dirs)
    has_backend = any(any(marker in item for marker in backend_markers) for item in all_dirs)
    has_data = any(any(marker in item for marker in data_markers) for item in all_dirs)
    has_source = any(item in dirs for item in ["src", "app", "lib", "server", "client", "frontend", "backend"])

    return {
        "has_source": has_source,
        "has_frontend": has_frontend,
        "has_backend": has_backend,
        "has_data": has_data,
        "dirs": sorted(all_dirs),
    }


def choose_mode(shape):
    if not shape["has_source"]:
        return "parallel", "Greenfield mission: safe to create explicit frontend, backend, operations, and quality territories."
    if shape["has_frontend"] and shape["has_backend"]:
        return "parallel", "Existing project has separable frontend and backend territories."
    return "sequential", "Existing source layout is ambiguous; safe parallel ownership cannot be proven from directory structure."


def work_packages(name: str, mode: str):
    slug = slugify(name)
    packages = [
        {
            "wo_id": "WO-001",
            "title": "Foundation and integration spine",
            "role": "integration-captain",
            "branch": "",
            "main_only": True,
            "exclusive_paths": [],
            "verification": "architecture notes, environment docs, initial gate manifest, mission alignment, dependency intelligence baseline, delivery infrastructure baseline",
        },
        {
            "wo_id": "WO-002",
            "title": "Backend, data, auth, and API contracts",
            "role": "backend-data-security",
            "branch": f"feat/wo-002-{slug}-backend",
            "main_only": False,
            "exclusive_paths": ["apps/api/", "backend/", "server/", "src/api/", "src/services/", "migrations/"],
            "verification": "unit, integration, contract, auth boundary, data integrity, dependency intelligence, dependency freshness",
        },
        {
            "wo_id": "WO-003",
            "title": "Frontend critical workflow",
            "role": "frontend-experience",
            "branch": f"feat/wo-003-{slug}-frontend",
            "main_only": False,
            "exclusive_paths": ["apps/web/", "frontend/", "client/", "src/ui/", "src/components/", "src/pages/"],
            "verification": "component, accessibility, responsive, loading/empty/error states, critical-path e2e, user-flow handoff proof",
        },
        {
            "wo_id": "WO-004",
            "title": "Observability, deployment, and operations",
            "role": "infra-observability",
            "branch": f"feat/wo-004-{slug}-ops",
            "main_only": False,
            "exclusive_paths": ["infra/", "deploy/", "ops/", "scripts/ops/", "monitoring/", "docs/runbooks/"],
            "verification": "CI/CD pipeline, deployment path, health, logs, metrics or request IDs, smoke test, rollback/runbook evidence, runtime/dependency audit evidence",
        },
        {
            "wo_id": "WO-005",
            "title": "Security, flow integrity, Comp gauntlet, and evidence dossier",
            "role": "quality-security-flow-evidence",
            "branch": f"feat/wo-005-{slug}-quality",
            "main_only": False,
            "exclusive_paths": ["tests/", "e2e/", "docs/evidence/", "docs/security/", "docs/qa/"],
            "verification": "full test suite, critical user-flow audit, system invariant audit, dependency intelligence audit, delivery infrastructure audit, objective fidelity, security audit, comp_gauntlet, scorecard evidence",
        },
    ]
    if mode == "sequential":
        for package in packages:
            package["branch"] = ""
            package["main_only"] = True
            package["exclusive_paths"] = []
    return packages


def scope_manifest(packages):
    branches = {}
    for package in packages:
        if package["main_only"]:
            continue
        branches[package["branch"]] = {
            "wo_ids": [package["wo_id"]],
            "exclusive_paths": package["exclusive_paths"],
            "description": f"{package['title']} ({package['role']})",
        }
    return {"branches": branches, "shared_paths": SHARED_PATHS}


def render_plan(name: str, mode: str, decision: str, packages, scopes):
    lines = [
        f"# COMP-PLAN: {name}",
        "",
        "## Execution Mode",
        "",
        f"`{mode}`",
        "",
        "## Parallelization Decision",
        "",
        decision,
        "",
        "## Work Packages",
        "",
        "| WO | Role | Branch | Exclusive Paths | Verification |",
        "|---|---|---|---|---|",
    ]
    for package in packages:
        branch = package["branch"] or "main-only"
        paths = ", ".join(package["exclusive_paths"]) if package["exclusive_paths"] else "n/a"
        lines.append(f"| {package['wo_id']} | {package['role']} | `{branch}` | {paths} | {package['verification']} |")

    lines.extend([
        "",
        "## Primary Flow Checkpoints",
        "",
        "| Layer | Planning Requirement | Evidence Expected |",
        "|---|---|---|",
        "| User objective | Identify the mission promise and user outcome that proves success | `MISSION.md` objective and acceptance criteria |",
        "| UI or entrypoint | Identify the screen, route, CLI, webhook, job, or public entrypoint the user starts from | route map, screenshot, or command evidence |",
        "| Auth/session | Identify authentication, authorization, role, ownership, or tenant context for the flow | auth tests or route guard evidence |",
        "| Backend/API | Identify the backend endpoint, handler, service, or integration called by the flow | contract or integration test evidence |",
        "| Data or side effect | Identify the durable change, external action, or explicit no-persistence rationale | migration, repository, event, or log evidence |",
        "| Feedback | Identify loading, validation, success, empty, and error states relevant to the primary path | UI test, E2E output, screenshot, or log evidence |",
        "",
        "## System Invariant Checkpoints",
        "",
        "| Invariant Class | Planning Requirement | Evidence Expected |",
        "|---|---|---|",
        "| Identity and ownership | Define what data/actions a user, role, or tenant must never access incorrectly | auth, ownership, or tenant isolation tests |",
        "| State transitions | Define valid states and transitions; reject impossible states | domain tests, schema constraints, or service validation |",
        "| Data integrity | Define uniqueness, deletion/archive, migration, and persistence assumptions | migration, constraint, and data integrity evidence |",
        "| Idempotency and side effects | Define retry, duplicate submit, webhook, job, or external side-effect guarantees | idempotency or retry tests |",
        "| Failure recovery | Define rollback, compensation, error surfacing, and recovery expectations | failure tests, runbook, or logs |",
        "| Auditability | Define sensitive actions that must be explainable later | audit logs, events, request IDs, or dossier links |",
        "",
        "## Dependency Intelligence Checkpoints",
        "",
        "| Dependency Control | Planning Requirement | Evidence Expected |",
        "|---|---|---|",
        "| Runtime and package manager | Define the runtime, package manager, and install command before dependency changes | runtime versions, package-manager version, install command output |",
        "| Current-source evidence | Verify high-impact dependencies against current docs, registries, release notes, or changelogs | dated source links or research registry entries |",
        "| Stack currency packs | Apply detected stack packs for Node/TypeScript, frontend, Python/FastAPI, AI SDK, auth/security, database/ORM, and deployment runtimes | `DEPENDENCY-INTELLIGENCE.md` pack table and command output |",
        "| Version and lockfile policy | Pin or lock dependencies according to ecosystem norms; explain any ranges | manifest and lockfile diff |",
        "| Compatibility | Prove selected versions work with the runtime, framework, bundler, database, or SDK constraints | install/build/test output and compatibility notes |",
        "| Security audit | Run the ecosystem audit or document unavailable tooling with rationale | audit command output or accepted deferral |",
        "| Upgrade path | Name risky dependencies and define who owns updates, breaking changes, and rollback | dependency owner notes and upgrade path |",
        "",
        "## Delivery Infrastructure Checkpoints",
        "",
        "| Delivery Control | Planning Requirement | Evidence Expected |",
        "|---|---|---|",
        "| CI/CD pipeline | Define pipeline or local-proof substitute that runs tests, gates, dependency checks, security checks, and build | workflow file, script, or command output |",
        "| Deployability | Define deployment target, artifact, environment boundary, and deploy command | deployment config, Dockerfile, host config, or runbook |",
        "| Environment and secrets | Define environment variables, secret storage, approval boundary, and secret-free examples | `.env.example`, secret scan, CI secret references |",
        "| Observability | Define health, logs, metrics/traces or request IDs, and error reporting for the core workflow | health output, sample logs, metrics/traces, error evidence |",
        "| Smoke and health checks | Define post-build or post-deploy checks that prove the real path works | smoke command, health command, CI step, or local proof |",
        "| Rollback and runbook | Define rollback, redeploy, recovery, and common failure diagnosis | runbook, rollback command, recovery notes |",
    ])

    lines.extend([
        "",
        "## Shared Paths",
        "",
    ])
    for path in scopes["shared_paths"]:
        lines.append(f"- `{path}`")

    lines.extend([
        "",
        "## Main-Only Work",
        "",
    ])
    for package in packages:
        if package["main_only"]:
            lines.append(f"- {package['wo_id']}: {package['title']}")

    lines.extend([
        "",
        "## Merge Order",
        "",
        "1. Main-only foundation work first.",
        "2. Backend/data/auth before frontend integration when contracts are not stable.",
        "3. Frontend and operations can merge after their contract dependencies are merged or proven by contract tests.",
        "4. Quality/security/flow/invariants/evidence merges last after rebasing on all completed implementation branches.",
        "",
        "## Unsafe Parallelization Notes",
        "",
    ])
    if mode == "sequential":
        lines.append("- Parallel execution downgraded to sequential because safe ownership was unclear.")
    else:
        lines.append("- Shared paths are expected conflict points. Rebase after each merge to main.")

    lines.extend([
        "",
        "## Required Follow-Up",
        "",
        "- Commit `.vibeos/worktree-scopes.json` on the base branch before creating worktrees.",
        "- Create one worktree per `feat/*` branch listed in the scope manifest.",
        "- Do not merge between feature branches.",
        "- Maintain a primary user-flow map from mission through implementation and evidence.",
        "- Maintain a system invariant map from mission through implementation and evidence.",
        "- Maintain dependency intelligence evidence for current-source decisions, compatibility, lockfiles, security audits, and upgrade paths.",
        "- Maintain delivery infrastructure evidence for CI/CD, deployment, observability, smoke checks, rollback, and runbooks.",
        "- Run `comp_gauntlet` before final demo or handoff.",
        "",
        f"_Generated at {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}_",
        "",
    ])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    try:
        mission = read_mission(project_dir)
    except FileNotFoundError as exc:
        print(f"[comp-plan] FAIL: {exc}", file=sys.stderr)
        return 1

    name = mission_name(mission)
    shape = existing_source_shape(project_dir)
    mode, decision = choose_mode(shape)
    packages = work_packages(name, mode)
    scopes = scope_manifest(packages)

    (project_dir / ".vibeos").mkdir(parents=True, exist_ok=True)
    (project_dir / "COMP-PLAN.md").write_text(render_plan(name, mode, decision, packages, scopes), encoding="utf-8")
    (project_dir / ".vibeos/worktree-scopes.json").write_text(json.dumps(scopes, indent=2) + "\n", encoding="utf-8")

    payload = {
        "status": "ok",
        "mode": mode,
        "mission": name,
        "branches": sorted(scopes["branches"].keys()),
        "shared_paths": scopes["shared_paths"],
        "decision": decision,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"[comp-plan] PASS: wrote COMP-PLAN.md and .vibeos/worktree-scopes.json ({mode})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
