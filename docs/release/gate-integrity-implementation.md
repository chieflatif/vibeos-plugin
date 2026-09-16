# Gate-result integrity implementation

The release gate runner now distinguishes evidence of executed checks from an
empty or unavailable check set. This closes the reproduced false-green path in
which an enabled `pre_commit` phase with zero resolved gates exited `0` without
reporting a failed result.

## Result policy

- A phase is required unless its own manifest object explicitly sets
  `"enabled": false`. This preserves legacy phase declarations, which have no
  `enabled` field and remain required.
- An enabled phase that resolves to zero gates reports `FAIL`, exits `1`, and
  records one blocking failure in JSON output. It cannot report `PASS`.
- An explicitly disabled phase is not executed. It reports `SKIP`, exits `0`,
  and JSON output has `summary.result` set to `SKIP`, never `PASS`.
- A gate that emits `SKIP:` is still shown as `SKIP`. If its effective blocking
  value is true, the phase records a blocking failure and exits `1`; a skipped
  required check is not evidence of a passing phase.
- Per-gate `blocking` is honored when supplied, including on tier-2 and tier-3
  gates. If absent, the existing tier policy continues to decide blocking.

The runner retains the prior fail-closed handling of missing blocking scripts.
The same final-result accounting now applies to a blocking script that is
present but declares itself unavailable.

## Verification

`python3 -m pytest tests/test_gate_required_results.py -q` passed: seven
spec-driven cases cover enabled-empty failure, disabled-empty `SKIP`, disabled
phase non-execution, blocking marker-skip failure, a gate-level blocking
override, default target-root propagation, and an explicit gate override.

`bash -n plugins/vibeos/scripts/gate-runner.sh` and `git diff --check` passed.

The two legacy marker-skip tests now encode the strengthened contract. The
ordinary marker-skip case exercises tiers 0 through 3: tiers 0 and 1 must fail
the phase, while tiers 2 and 3 retain an allowed `SKIP`. The noisy marker-skip
case remains a tier-0, large-output regression guard for the SIGPIPE-safe
matcher, but now expects the blocking failure and complete summary accounting.

`tests/test_code_quality_project_root.py` adds two target-root fixtures. They
prove that an explicit `PROJECT_ROOT` controls Python compile and lint targets
for both a relative source directory and an absolute source directory. The
code-quality gate now uses the plugin directory only when no target project is
supplied, and only auto-selects `scripts/` when that selected directory is an
actual VibeOS plugin root.

An initial populated pre-commit diagnostic, before the manifest’s framework
source configuration was supplied, exposed a file-size hard breach and a
blocking code-quality skip. Those findings prompted separate manifest and
file-budget work; they are not a final release result.

The dependency manifest entries carry `ONLY_WHEN_DEP_FILES_CHANGE`, but neither
dependency gate reads or verifies that condition. It therefore cannot establish
a verified not-applicable result. The smallest safe follow-up is to define the
changed-file comparison explicitly (for example, the staged diff at pre-commit)
and implement it in the dependency gates before relying on that manifest flag.
A missing audit tool should remain a distinct `SKIP` outcome and fail when the
gate is blocking.

## Portable timeouts and target propagation

`gate_timeout.py` is a bundled Python standard-library helper used for every
gate invocation. It creates a process group, captures combined output, returns
the child exit status on normal completion, and sends `SIGTERM` followed by
`SIGKILL` to the group on a deadline before returning `124`. This removes the
macOS dependency on absent GNU `timeout` or `gtimeout` utilities. The profile
installer includes the helper in its runtime core; legacy bootstraps already
copy the complete scripts directory or all top-level Python scripts.

The helper emits an exact stderr marker only after it has enforced a deadline.
The runner requires both that marker and exit `124` before classifying a gate as
`TIMEOUT`. A gate that naturally exits `124` remains an ordinary `FAIL` with
its captured output preserved.

`tests/test_gate_timeout.py` covers normal output, a non-zero child status, a
natural `124`, a timed-out parent with a sleeping child, runner timeout and
natural-`124` accounting, and profile installation of the helper.

The runner now exports its selected `--project-dir` as `PROJECT_ROOT` to every
gate subprocess, even when called from another working directory. A gate's
manifest environment may explicitly set `PROJECT_ROOT`; that deliberate value
is preserved. The regression fixtures cover both paths.

## Complexity source scopes

`validate-code-complexity.sh` now accepts `SOURCE_DIR` (relative to
`PROJECT_ROOT` or absolute) and `LANGUAGE`. This lets a manifest assess a
controlled package while retaining the actual project root for normal language
detection. A missing source directory or a selected language with no matching
source files reports `ERROR` and exits `2`; it cannot reach the final `PASS`.

The Python AST analysis now collects its emitted summary before updating the
shell counters. This retains violations that the earlier pipeline subshell
discarded. A harmless commented-code search is also guarded against its normal
no-match exit status under `set -e` and `pipefail`, so warning-only evaluations
produce their final summary and `PASS`.

`tests/test_code_complexity_required.py` verifies that a four-line function
over a two-line limit exits `1` with a complexity failure, and that an empty
explicit Python source scope exits `2` without `PASS`. A direct scoped run of
`plugins/vibeos/scripts/controlled_evaluation` with the release thresholds
reported five warnings and exited `0`.
