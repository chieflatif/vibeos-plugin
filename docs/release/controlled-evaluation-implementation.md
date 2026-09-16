# Controlled evaluation implementation

Status: implementation complete; independent release acceptance remains with the
release owner. This record covers only
`plugins/vibeos/scripts/controlled_evaluation/` and
`plugins/vibeos/scripts/controlled-evaluation.py`.

## Result

The September 13 six-module harness was adapted from fixed Joan paths and
project-specific schemas into a prepared, byte-pinned owner workspace. The CLI
has three fixed actions:

```text
controlled-evaluation.py prepare --owner PATH --candidate PATH --spec FILE
controlled-evaluation.py evaluate --owner PATH --run run-N
controlled-evaluation.py publish --owner PATH --run run-N
```

`prepare` refuses existing owner content, noncanonical or nested roots, symlinked
inputs, malformed or duplicate JSON fields, missing declared test identities,
and non-Git candidates. It validates the current Git `HEAD`, supports both a
fresh-clone `.git` directory and a worktree `.git` pointer, and pins the complete
candidate file inventory as it exists at preparation time. Dirty or untracked
bytes are allowed only because they are included in that complete baseline;
later candidate drift is refused. Preparation does not run project tests.

Owner tests and the Python project adapter are copied into `protected-owner/`.
The six runtime modules are copied into `harness-adaptation/`. Owner evaluation
loads that copied package, pins its bytes and the configured tool/dependency
targets, and uses only the configured identities. No test discovery substitutes
for `required_owner_tests`, and there is no arbitrary-command field.

## Exact spec shape

All keys are required; unknown keys are refused. Lists shown as sorted must also
be unique. Every path is absolute. Path values must name canonical regular files,
not symlinks.

```json
{
  "schema": "vibeos.controlled-evaluation.spec.v1",
  "owner_tests": ["/absolute/owner-inputs/test_owner.py"],
  "project_adapter": "/absolute/owner-inputs/project_adapter.py",
  "required_owner_tests": ["test_build", "test_contract"],
  "required_project_cases": ["build", "test"],
  "held_project_checks": ["manual-provider-check"],
  "writable_files": ["generated/result.json"],
  "tools": {
    "python": "/canonical/path/to/python",
    "ruff": "/canonical/path/to/ruff",
    "codex": "/canonical/path/to/codex"
  },
  "dependencies": ["/absolute/owner-inputs/adapter-policy.json"],
  "timeout_seconds": 30,
  "max_lines": 300,
  "max_complexity": 10
}
```

The adapter is invoked as:

```text
python -I -B PROJECT_ADAPTER CANDIDATE_ROOT RESULT_DIRECTORY
```

It must create `project.json` and `project-evidence/`. `project.json` has this
exact schema and must contain the exact sorted required case inventory:

```json
{
  "schema": "vibeos.project-checks.v1",
  "cases": [{"id": "build", "status": "PASS"}],
  "held": ["manual-provider-check"],
  "project_qualified": false,
  "runtime_qualified": false
}
```

Only uppercase `PASS` and `FAIL` are valid status values. Any missing, failed,
skipped, duplicate, stale, malformed, wrong-type, symlinked, or extra result is
ineligible. A zero adapter exit cannot override incomplete evidence. A nonzero
pytest or outer evaluator exit, including pytest exit codes 1 through 6, cannot
be hidden by passing XML.

## Sandbox and publication controls

The only evaluation route is the native Codex sandbox command:

```text
codex sandbox --sandbox-state-disable-network -P evaluator \
  -c 'permissions.evaluator={extends=":read-only",filesystem={"RESULT_DIR"="write"}}' \
  -C OWNER -- python -I -B OWNER/harness-adaptation/checks.py CONFIG run-N
```

There is no unsandboxed fallback. An unavailable or rejected native profile
produces an ineligible run with a clear launch error. The controller starts the
sandbox in a new process session, kills and reaps the process group on timeout,
completion, SIGTERM, or SIGINT, and records that state. The configured timeout
gets one second of controller cleanup allowance; each inner check retains the
declared timeout.

Evaluation holds a nonblocking single-writer `flock`. It pins inputs before and
after the run and requires them to be identical. Publication revalidates the
current run and all live and sealed artifacts, writes only `PRE_REVIEW`, never
overwrites differing content, and returns the same inode and bytes for an exact
idempotent retry. `PRE_REVIEW` does not claim project, runtime, release, or owner
acceptance.

## Source review and local proof

Fixed-layout assumptions found in the archived source were: two hard-coded Joan
roots; `joan.project27.*` schemas; one fixed `test_owner.py`; one fixed
`project_checks.py`; worktree-pointer-only Git parsing; a project-specific
adapter schema; and a native sandbox command without the current explicit
network-disable flag. Those assumptions were removed while retaining strict
evidence reduction, process cleanup, lock custody, and immutable publication.

The version-specific check used local Codex CLI 0.147.0 help and a disposable
macOS native probe on 2026-09-16. The exact probe was:

```text
/opt/homebrew/bin/codex sandbox --sandbox-state-disable-network -P evaluator \
  -c 'permissions.evaluator={extends=":read-only",filesystem={"/private/tmp/vibeos-native-sandbox-proof/output"="write"}}' \
  -C /private/tmp/vibeos-native-sandbox-proof -- /bin/sh -c \
  'printf allowed > output/result.txt; printf denied > blocked/result.txt'
```

Observed result: `output/result.txt` contained `allowed`; the adjacent write was
denied with `Operation not permitted`; no blocked result file existed. This
proves the command syntax and write boundary on this macOS/Codex version. It does
not attest that a configured `codex` path is an authentic vendor binary; tool
paths and their pinned bytes are owner-trusted inputs. It also does not establish
same-user hostile-author isolation or cross-OS support.

Scoped frozen tests:

```text
python3 -m pytest -q tests/test_controlled_evaluation_prepare.py \
  tests/test_controlled_evaluation_runtime.py \
  tests/test_controlled_evaluation_evidence.py
21 passed, 36 subtests passed
```

The archived source candidate tests and this implementation suite are engineering
evidence only. The release owner separately controls integration, independent
review, fresh-clone install proof, tag/source verification, and release acceptance.
