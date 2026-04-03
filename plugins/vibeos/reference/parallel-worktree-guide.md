# Parallel Worktree Guide

**How to set up parallel WO execution, configure territory enforcement, and understand the safety guarantees of VibeOS worktree isolation.**

---

## Overview

Parallel worktrees let you run multiple Work Orders simultaneously in isolated git worktrees. Each WO gets its own branch, its own Claude Code session, and its own exclusive file territory. The two worktree guard hooks enforce isolation automatically — no agent can accidentally overwrite another WO's work.

Use parallel worktrees when:
- A phase has 3 or more independent WOs with no shared migration chains
- Sequential execution would take more than 2 days
- WOs touch clearly separable modules or directories

Do not parallelize WOs that:
- Share an Alembic migration chain (same head)
- Both modify the same router, schema registration, or configuration file exclusively
- Have explicit ordering dependencies in the development plan

---

## Step-by-Step Setup

### 1. Create worktree-scopes.json

Before branching, create `.vibeos/worktree-scopes.json` in the project root on `main`. This file is the single source of truth for which branch owns which files.

```bash
mkdir -p .vibeos
# Create .vibeos/worktree-scopes.json — see schema below
```

### 2. Create the git worktrees

From the project root (main branch):

```bash
git worktree add ../project-feat-wo-042 feat/wo-042-auth-module
git worktree add ../project-feat-wo-043 feat/wo-043-reporting
git worktree add ../project-feat-wo-044 feat/wo-044-notifications
```

Each command creates a new directory with the branch checked out.

### 3. Open one Claude Code session per worktree

Open each worktree directory as its own Claude Code session. Sessions are fully isolated — each sees its own branch, its own uncommitted changes, and its own read of worktree-scopes.json.

### 4. Work normally — hooks enforce the rules

Both `worktree-bash-guard.sh` and `worktree-scope-guard.sh` activate automatically on any `feat/*` branch. You do not need to configure them per-session.

### 5. Merge via PR, in dependency order

When a WO is complete:
1. Open a PR from the feat branch to main
2. Pass CI
3. Merge to main
4. All remaining open worktrees rebase: `git fetch origin && git rebase origin/main`

Never merge feat branches directly into each other.

---

## worktree-scopes.json Schema

```json
{
  "branches": {
    "feat/wo-042-auth-module": {
      "wo_ids": ["WO-042"],
      "exclusive_paths": [
        "src/auth/",
        "src/api/auth_router.py"
      ],
      "alembic_versions": ["042_wo_042_add_auth_tables"],
      "description": "Authentication module — JWT, session management, RBAC"
    },
    "feat/wo-043-reporting": {
      "wo_ids": ["WO-043", "WO-044"],
      "exclusive_paths": [
        "src/reporting/",
        "src/api/reports_router.py"
      ],
      "alembic_versions": [],
      "description": "Reporting module — aggregation jobs and PDF export"
    }
  },
  "shared_paths": [
    "src/config/settings.py",
    "src/api/router.py",
    "src/database/base.py",
    "tests/conftest.py",
    "alembic/versions/",
    "pyproject.toml",
    "docs/planning/",
    "docs/evidence/"
  ]
}
```

### Field Reference

| Field | Required | Description |
|---|---|---|
| `branches` | Yes | Map of branch name to scope definition. Keys must be `feat/*` branch names. |
| `branches[*].wo_ids` | Yes | Work order IDs owned by this branch. Used in deny messages — not enforcement logic. |
| `branches[*].exclusive_paths` | Yes | File paths or path prefixes that ONLY this branch may edit. Other branches are blocked by the scope guard. |
| `branches[*].alembic_versions` | No | Alembic migration filename prefixes owned by this branch. Informational — not enforced by the guard. |
| `branches[*].description` | No | Human-readable summary of this branch's scope and purpose. |
| `shared_paths` | Yes | File paths or path prefixes that any branch may edit. Expect merge conflicts here — resolve via rebase. |

### Path Matching Rules

Both `exclusive_paths` and `shared_paths` use substring matching. A path entry of `src/auth/` will match any file whose absolute path contains `src/auth/`. Entries should be specific enough to avoid false positives — use trailing slashes for directories and full relative paths for individual files.

---

## Safety Guarantees

### What the hooks enforce

| Hook | Trigger | Blocks |
|---|---|---|
| `worktree-bash-guard.sh` | PreToolUse: Bash | Alembic commands, checkout of main/master/develop, merge from base branches, cross-feat merges, direct push to main, destructive DB ops (DROP, TRUNCATE, DELETE WHERE 1=1) |
| `worktree-scope-guard.sh` | PreToolUse: Edit or Write | Edits to any file in another branch's `exclusive_paths` |

### What the hooks do not enforce

- **Alembic version ownership** — `alembic_versions` in the scopes file is documentation only. The Alembic runtime enforces ordering; the guard does not inspect migration file names.
- **Read operations** — hooks only block writes and destructive commands. An agent can still read files from another WO's territory.
- **Main branch** — both hooks are completely silent on `main` and any non-`feat/*` branch.
- **File creation in exclusive paths** — if a branch creates a new file inside another branch's exclusive directory, the scope guard will block it on the next write attempt, but the initial file existence check happens at write time.

### Fail-open behavior

If `.vibeos/worktree-scopes.json` does not exist, both hooks allow all operations. The guards degrade gracefully on projects that have not configured parallel worktrees. This means a missing scopes file is silent — no error, no warning.

---

## Known Conflict Hotspots

These files are touched by nearly every WO. Always list them in `shared_paths`:

| File | Why it conflicts |
|---|---|
| `src/config/settings.py` | Every module adds environment variables |
| `src/api/router.py` | Every module registers routes |
| `tests/conftest.py` | Every module adds fixtures |
| `alembic/versions/` | Every module adds a migration |
| `pyproject.toml` | Every module adds dependencies |
| `docs/planning/` | WO status updates from multiple agents |

Whoever merges last resolves these conflicts. Call them out explicitly in each WO's Parallel Execution Contract section.

---

## Parallel Execution Contract (WO Template)

Every WO that runs in a parallel worktree must include a `Parallel Execution Contract` section in the WO file. Agents read this at session start.

```markdown
## Parallel Execution Contract

| Field | Value |
|---|---|
| **Branch** | `feat/wo-NNN-description` |
| **Worktree path** | `../project-feat-wo-NNN` |
| **Owning WO** | WO-NNN |
| **Exclusive territory** | `src/my_module/` |
| **Shared files** | `src/config/settings.py`, `src/api/router.py` (expect conflicts — rebase last) |

Hard rules (enforced by hooks — violations are blocked):
- Do NOT run `alembic upgrade`, `alembic downgrade`, or `alembic revision`
- Do NOT `git checkout main`, `git checkout master`, or `git checkout develop`
- Do NOT `git merge origin/main` — use `git rebase origin/main`
- Do NOT merge from any other `feat/*` branch
- Do NOT run `DROP DATABASE`, `DROP TABLE`, `TRUNCATE TABLE`, or full-table DELETE
- Do NOT edit files under another branch's exclusive territory

When done: open a PR from `feat/wo-NNN-description` to `main`. Do not merge without passing CI.
```

---

## Merge Order Strategy

1. Identify the dependency graph — which WOs can merge independently, which must sequence.
2. Merge independent WOs first, in the order they finish CI. Each merge to main is a new baseline.
3. After each merge, all remaining open worktrees rebase: `git fetch origin && git rebase origin/main`.
4. Whoever merges last resolves shared-path conflicts. These are expected — not errors.
5. Never cross-merge between `feat/*` branches. The bash guard enforces this.

---

## Troubleshooting

**"BLOCKED: File is exclusive territory of branch..."**
You are on the wrong branch for this file. Either switch to the correct worktree, or — if the file is genuinely shared — add it to `shared_paths[]` in `.vibeos/worktree-scopes.json` and commit that change on `main` before both branches need it.

**"BLOCKED: Alembic migrations must run on main only"**
Complete your WO, merge to main via PR, then run `alembic upgrade head` from the main working tree.

**"BLOCKED: Cannot merge between parallel feature worktrees"**
Your WO depends on another feat branch. Wait for that branch to merge to main via PR, then rebase: `git fetch origin && git rebase origin/main`.

**"BLOCKED: Destructive database operations are blocked"**
Parallel worktrees share the development database. If you need a clean database state, ask the user to provision a separate test database for this worktree and update the database connection string in that session's environment.

**Scope guard is not activating**
Check that your branch name starts with `feat/`. The guard is silent on all other branches. Also verify that `.vibeos/worktree-scopes.json` exists in the project root — the guard fails open if the file is missing.
