# Controlled evaluation independent test contract

Status: contract frozen before implementation inspection on 2026-09-16. Owner:
Independent Test Design. Scope: the public `prepare`, `evaluate`, and `publish`
CLI in the reusable harness release amendment.

## Boundary

The tests were derived from
`docs/planning/REUSABLE-HARNESS-RELEASE-AMENDMENT-2026-09-16.md` and the public
owner layout supplied by Release Integration. Independent Test Design did not
open the new `controlled_evaluation` implementation or standalone entrypoint
before the test files were written, syntax checked, and run red.

The suite invokes the real standalone CLI against disposable Git repositories.
Its `fake_codex.py` is a deterministic launcher emulator: it accepts the required
Codex sandbox argument vector and executes only the command after `--`. It does
not implement a sandbox, does not prove native Codex enforcement, and must never
be cited as native-runtime qualification. Release Integration separately owns a
real macOS Codex smoke with synthetic files and no credentials or provider work.

## Synthetic owner inputs

`tests/controlled_evaluation_fixtures.py` creates these inputs under a temporary
directory whose path contains spaces:

- `test_owner.py` contains the exact required functions
  `test_candidate_file` and `test_candidate_identity`.
- `project_checks.py` receives candidate root and result directory, writes
  `project.json` with schema `vibeos.project-checks.v1`, exact `PASS` cases
  `project-build` and `project-test`, held check `manual-provider-check`, and
  both qualification booleans false. It also writes identity evidence.
- The owner spec contains only the accepted schema, owner test paths, project
  adapter path, exact sorted required identities, held identities, candidate
  writable paths, explicit absolute tool paths, absolute dependencies, timeout,
  line limit, and complexity limit.
- Each candidate is a committed synthetic Git repository. Two separate tests
  use distinct project identities and directory names containing spaces.

## Acceptance matrix

| Area | Required proof |
|---|---|
| Preparation | New owner only; pinned config; adaptation and result layout; complete clean Git baseline; candidate bytes unchanged |
| Path custody | Owner and candidate distinct, canonical, nonnested directories; reject linked inputs, traversal, absolute writable paths, wrong types, and nonabsolute dependencies |
| Owner preservation | Refuse any preexisting owner content and preserve its bytes exactly |
| Spec strictness | Reject malformed JSON, missing/empty required owner list, duplicates, and unsorted required project cases |
| Positive evaluation | Real public CLI creates current, check, sealed-run, admission, and project-evidence artifacts |
| Exact owner accounting | Reject missing, empty, failed, skipped, duplicate, and malformed owner cases |
| Exact project accounting | Reject missing, duplicate, and malformed project cases and malformed check JSON |
| Process status | Reject subprocess exits 1, 2, 3, 4, 5, and 6 even when a passing XML report exists |
| Drift | Reject candidate source, protected config/profile, tool, dependency, sealed evidence, and current-run drift |
| Process control | Exercise a real elapsed timeout and a real SIGTERM; neither may create admission |
| Concurrency | Hold one real evaluation and require a second writer to fail without a second admission |
| Publication | Publish only exact current PRE_REVIEW evidence; preserve separate acceptance/release state; exact retry is byte-, inode-, and timestamp-idempotent |
| Immutability | Refuse a repeated evaluation for the same run and preserve the original record |

## Initial red evidence

The first run occurred after the suite was frozen and before the entrypoint
existed:

```text
python3 -m py_compile tests/controlled_evaluation_fixtures.py \
  tests/test_controlled_evaluation_prepare.py \
  tests/test_controlled_evaluation_evidence.py \
  tests/test_controlled_evaluation_runtime.py
exit 0

python3 -m pytest -q tests/test_controlled_evaluation_prepare.py \
  tests/test_controlled_evaluation_evidence.py \
  tests/test_controlled_evaluation_runtime.py
31 failed, 9 passed, 9 subtests passed in 4.13s
```

The positive-path failures reported the absent
`plugins/vibeos/scripts/controlled-evaluation.py`. The passing negative cases
were refusals caused by that same absence and are not implementation evidence.
No green result is claimed by this record.

After the initial red run, Release Integration identified that the source
protocol's exact project-case status vocabulary is `PASS` or `FAIL`. The fixture
had used the descriptive word `passed`. Independent Test Design corrected only
those two synthetic status values to exact `PASS`; no acceptance expectation or
negative case was weakened, and the implementation remained uninspected.

The first implementation join also showed that macOS returns a temporary path
through the `/var` alias while the contract requires canonical paths. The
fixture now resolves its temporary root before constructing owner, candidate,
and input paths. This makes the synthetic input comply with the existing
canonical-path requirement; it does not change a production expectation.

Public-interface inspection then confirmed that eligibility is recorded in
`results/current.json`; `admitted.json` and the exact `PRE_REVIEW` status are
created by `publish`. The positive assertion was moved to those protocol-owned
artifacts. The fake launcher also now scans dependency dictionary keys because
the prepared profile correctly represents dependencies as path-to-hash records.
Both changes align the fixture with public output shape and leave all refusal
conditions intact.

The amendment requires a pinned Git revision and a complete byte baseline, but
does not require a clean working tree. The initial test had inferred that dirty
tracked bytes must be refused. It now verifies the narrower contract: a non-Git
candidate is refused, while uncommitted bytes are preserved and pinned in the
baseline. Separate drift tests still require any post-prepare change to fail.

## Join and release evidence

After the red freeze, Independent Test Design may inspect the implementation
only to diagnose a public-interface mismatch or a faulty fixture. Contract
weakening requires a written amendment-based reason in this record. A passing
deterministic suite proves protocol behavior under launcher emulation only.
Release still requires the independently owned native Codex smoke, original
relevant suites, full suite, changed-source review, and fresh-clone release
verification.

## Deterministic green result

After Engineering Controls corrected the production namespace and link-custody
failures found by the frozen suite, and after the recorded public-interface
fixture corrections above, the scoped deterministic run passed:

```text
python3 -m pytest -q tests/test_controlled_evaluation_prepare.py \
  tests/test_controlled_evaluation_evidence.py \
  tests/test_controlled_evaluation_runtime.py
21 passed, 36 subtests passed in 28.79s
```

This is complete deterministic protocol evidence for the cases in the matrix.
It is not evidence that the installed macOS Codex version accepts or enforces
the native sandbox profile.
