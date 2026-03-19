# Parallel Worktree Execution

**When to use, how to set up, how to stay safe.**

---

## When To Use Parallel Worktrees

Use parallel worktrees when a phase has **3 or more independent work orders** that share no implementation dependencies and would take more than 2 days sequentially. Each WO runs in its own `git worktree` on its own `feat/*` branch. All branches merge back to `main` via PR — never directly to each other.

Do not parallelize WOs that:
- Share a migration chain (same Alembic head)
- Modify the same router or schema registration file exclusively
- Have explicit ordering dependencies in the development plan

---

## How To Set Up Worktrees

```bash
# From the project root (main branch)
git worktree add ../project-feat-wo-042 feat/wo-042-module-name
git worktree add ../project-feat-wo-043 feat/wo-043-module-name
git worktree add ../project-feat-wo-044 feat/wo-044-module-name
```

Open each worktree directory as its own Claude Code session. Each session sees its own branch, its own uncommitted changes, and its own scope definition from `.vibeos/worktree-scopes.json`.

---

## worktree-scopes.json

Create `.vibeos/worktree-scopes.json` in the project root (on `main`) before branching. This file defines what each branch owns and what is shared. Both worktree guard hooks read it at runtime.

**Schema:**

```json
{
  "branches": {
    "feat/wo-042-module-name": {
      "wo_ids": ["WO-042"],
      "exclusive_paths": ["src/my_module/"],
      "alembic_versions": ["042_wo_042_description"],
      "description": "human-readable description of this branch's scope"
    },
    "feat/wo-043-other-module": {
      "wo_ids": ["WO-043"],
      "exclusive_paths": ["src/other_module/"],
      "alembic_versions": ["043_wo_043_description"],
      "description": "human-readable description"
    }
  },
  "shared_paths": [
    "src/config/settings.py",
    "src/orchestrator/engine.py",
    "src/api/router.py",
    "alembic/versions/",
    "tests/conftest.py"
  ]
}
```

**Rules:**
- `exclusive_paths` — only the owning branch may edit these. The scope guard blocks all other branches.
- `shared_paths` — any branch may edit these. Expect merge conflicts here; resolve via rebase.
- `alembic_versions` — migration file name prefixes owned by this branch. Used for documentation; Alembic itself enforces ordering at run time.

---

## The Parallel Execution Contract (WO Section)

Every WO that runs in a parallel worktree must include a `## ⚠️ Parallel Execution Contract` section immediately after the WO header. Agents read this at session start — it cannot be missed.

**Template for a parallel WO:**

```markdown
## ⚠️ Parallel Execution Contract

| Field | Value |
|---|---|
| **Branch** | `feat/wo-NNN-description` |
| **Worktree path** | `../project-feat-wo-NNN` |
| **Owning WO** | WO-NNN |
| **Exclusive territory** | `src/my_module/` |
| **Shared files** | `src/config/settings.py`, `src/api/router.py` (expect conflicts — rebase last) |

**Hard rules (enforced by hooks — violations are BLOCKED):**
- Do NOT run `alembic upgrade`, `alembic downgrade`, or `alembic revision` — migrations run on main after all branches merge
- Do NOT `git checkout main` or `git push origin main` — open a PR
- Do NOT `git merge origin/main` — use `git rebase origin/main`
- Do NOT merge from any other `feat/*` branch — wait for main, then rebase
- Do NOT run `DROP DATABASE` or `TRUNCATE TABLE`
- Do NOT edit files under `src/other_module/` — that is WO-NNN's exclusive territory

**When done:** Open a PR from `feat/wo-NNN-description` → `main`. Do not merge without passing CI.
```

**Template for a main-only (blocking) WO:**

```markdown
## ⚠️ Parallel Execution Contract

This WO runs on `main`. All parallel feature branches wait for this WO to merge before rebasing.
Do not start dependent WOs until this WO's PR is merged and `main` is updated.
```

---

## Merge Order Strategy

1. **Identify the dependency graph** — which WOs can merge independently, which must sequence.
2. **Merge independent WOs first** in the order they finish CI. Each merge to main is a new baseline for the remaining branches.
3. **After each merge**, all remaining open worktrees rebase: `git fetch origin && git rebase origin/main`
4. **Conflict hotspots** — router files, settings, conftest.py, shared base models. Call these out explicitly in the WO's Parallel Execution Contract. Whoever merges last resolves the conflict.
5. **Never cross-merge** between `feat/*` branches. The scope guard enforces this but the rule exists regardless.

---

## Known Conflict Hotspots

These files are touched by nearly every WO. List them in `shared_paths` and note them in each WO's contract:

| File | Why it conflicts |
|---|---|
| `src/config/settings.py` | Every module adds env vars |
| `src/api/router.py` | Every module registers routes |
| `tests/conftest.py` | Every module adds fixtures |
| `alembic/versions/` | Every module adds a migration |
| `pyproject.toml` | Dependency additions from multiple WOs |

---

## Hooks That Enforce This

Both hooks activate **only on `feat/*` branches**. They are silent on `main`.

| Hook | Trigger | Blocks |
|---|---|---|
| `worktree-bash-guard.sh` | PreToolUse:Bash | Alembic commands, `git checkout main`, cross-branch merges, `git push origin main`, destructive DB ops |
| `worktree-scope-guard.sh` | PreToolUse:Edit\|Write | Edits to another branch's `exclusive_paths` |

Both hooks pass silently if `.vibeos/worktree-scopes.json` does not exist — they degrade gracefully on projects that do not use parallel worktrees.
