# Controlled evaluation

This package brings reusable engineering checks into a project without copying
another product's test identities, filesystem paths or acceptance policy. It
binds a candidate to protected owner inputs, runs configured checks through the
native Codex sandbox, verifies complete evidence and publishes an immutable
`PRE_REVIEW` result. Independent review and owner acceptance remain separate.

The supported target for this release is supervised macOS/Codex engineering.
The controls detect the documented forms of stale or incomplete evidence. They
do not provide confidentiality or a security boundary against a hostile process
running as the same macOS user, and do not authorize deployment or provider actions.

## Prepare project-owned checks

Keep the evaluation owner directory separate from the candidate repository.
The owner directory must be new, and neither directory may contain the other.
Preparation pins the current complete candidate baseline. `writable_files`
records owner-selected candidate paths for binding and Python lint inventory; it
does not grant write access. The native evaluator can write only inside the
current run's result directory. A candidate should be a disposable Git checkout
of the project revision under evaluation. Dirty or untracked bytes are accepted
only when preparation includes them in the complete pinned baseline.

Provide two Python files:

- An owner test module containing the required `test_*` functions. These tests
  express acceptance criteria independently of the implementation.
- A project adapter accepting candidate-root and result-directory arguments. It
  runs the project's own checks, captures their real exit codes, creates a
  `project-evidence` directory, and writes `project.json` with the exact schema
  below. The adapter can invoke the target project's language-specific tooling;
  a Python wrapper does not limit the candidate to Python.

```json
{
  "schema": "vibeos.project-checks.v1",
  "cases": [{"id": "required-example", "status": "PASS"}],
  "held": [],
  "project_qualified": false,
  "runtime_qualified": false
}
```

List all required case identities explicitly and in sorted order. Never create
a PASS row solely because an output file exists or a wrapper returned zero.
The adapter must derive it from the corresponding real check. Retain failed
outputs. A fake, skipped or missing required check is a failure.

Create an evaluation specification with absolute canonical file paths. Resolve
tool symlinks on the destination machine first; for example,
`python3 -c 'import pathlib,sys; print(pathlib.Path(sys.executable).resolve())'`
prints the running Python executable's canonical path. Supply the actual installed
Codex and Ruff executables in the same way. Preparation hashes their bytes.

```json
{
  "schema": "vibeos.controlled-evaluation.spec.v1",
  "owner_tests": ["/absolute/evaluation-inputs/test_owner.py"],
  "project_adapter": "/absolute/evaluation-inputs/project_checks.py",
  "required_owner_tests": ["test_candidate_file", "test_candidate_identity"],
  "required_project_cases": ["project-build", "project-test"],
  "held_project_checks": ["manual-provider-check"],
  "writable_files": ["artifact.txt"],
  "tools": {
    "python": "/absolute/bin/python3",
    "ruff": "/absolute/bin/ruff",
    "codex": "/absolute/bin/codex"
  },
  "dependencies": ["/absolute/evaluation-inputs/requirements.lock"],
  "timeout_seconds": 120,
  "max_lines": 300,
  "max_complexity": 10
}
```

Replace the example paths and identities with the owner's actual files and checks.
Identity lists are unique and sorted; writable paths are relative to the candidate.
Pin dependency files that affect evaluation, including lockfiles and relevant
configuration. Limits are explicit, with current maximums 300 seconds, 300 lines
and complexity 10. `timeout_seconds` is one total work budget for the sandboxed
evaluation and the lint, pytest and adapter phases together. A later phase gets
only the time remaining; no phase is promised a fresh or full timeout window.
Bounded termination and reaping after that deadline can extend wall-clock return
by up to two seconds. Tool and dependency paths are local inputs, not credentials.
Recreate the specification and its hashes on the other Mac.

This release's largest harness module is 289 lines, so `max_lines` below 289
makes every evaluation ineligible even though the schema accepts lower positive
values. Pytest runs isolated with `-I`, plugin autoload disabled, no ancestor
configuration and no `conftest.py` loading. Owner tests must work within those
limits. The complete candidate inventory refuses symlinks, special entries and
empty directories; checkouts that materialize linked `node_modules`, `.venv` or
similar trees are unsupported without a separate clean candidate checkout.

```bash
python3 .vibeos/scripts/controlled-evaluation.py prepare \
  --owner /absolute/path/to/new-evaluation-owner \
  --candidate /absolute/path/to/disposable-candidate \
  --spec /absolute/path/to/evaluation-spec.json
python3 .vibeos/scripts/controlled-evaluation.py evaluate \
  --owner /absolute/path/to/new-evaluation-owner --run run-1
python3 .vibeos/scripts/controlled-evaluation.py publish \
  --owner /absolute/path/to/new-evaluation-owner --run run-1
```

Inspect `results/current.json`, the run's sealed evidence, and the published
record. Only an eligible current run may publish. A repeated identical publish
is idempotent; conflicting evidence is refused. Evaluation exit zero and a
`PRE_REVIEW` artifact do not establish owner acceptance.

## What is checked

- Exact configuration, source, tool and dependency bindings before and after work.
- Required owner tests and project case identities; no omissions or duplicates.
- Actual child exits, including nonzero pytest exits even when XML looks successful.
- Test report structure, skip/failure/error markers and evidence hashes.
- Declared file inventory, regular-file types, symlink refusal and protected inputs.
- Owner-configured source-size and Ruff complexity limits for the copied owner
  Python, the six harness modules and declared writable candidate Python files.
- Single-writer ownership, current-run identity and immutable output publication.
- One total timeout budget, interruption invalidation and nested process-group
  cleanup with SIGTERM followed by a bounded SIGKILL fallback.

The result directory has a strict top-level inventory: `owner-report.xml`,
`checks.json`, `project.json` and `project-evidence/`. The three documents must
be regular files. `project-evidence/` must be a real directory and its complete
nested inventory may contain only regular files and directories; symlinks and
special files are refused. Missing or additional top-level outputs are refused.
These structural checks do not turn adapter-authored evidence into independent
acceptance; required identities and exits still have to match the owner profile.
The native Codex wrapper must also be silent: any stdout or stderr byte from the
outer sandbox command makes the run ineligible. Individual lint, pytest and
adapter streams remain captured inside `checks.json` and are validated there.

If the native sandbox is unavailable or its syntax differs, evaluation fails
clearly. It never falls back to unsandboxed execution. Update runtime evidence
and review the compatible invocation before retrying. Model selection, account
sessions and global Codex configuration are not changed by this package.

After an interrupted or failed run, retain its evidence and use a new run ID once
the cause is resolved. Old success cannot stand for a new candidate or changed
owner policy. Changing the protected baseline requires a new reviewed preparation.
The cleanup guarantee covers the Codex group and pytest/adapter descendants that
remain in the new process group created for their check. A descendant that
deliberately creates another session, daemonizes through an external supervisor,
or is controlled by a hostile same-user process can escape this measured
boundary. Whole-host compromise remains outside the supported isolation model.
