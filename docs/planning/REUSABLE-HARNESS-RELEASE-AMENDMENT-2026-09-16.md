# Reusable harness release amendment — 2026-09-16

Status: Implementation and independent review complete; distribution proof follows. Owner: VibeOS Engineering. Latif authorized
implementation and release by “ok proceed”, and expressly requested smaller-model
subagents with the primary task governing delivery. Target: macOS with Codex.
This is a bounded amendment of existing WO-114/115,127/128,129–133,135–138;
it does not mark their unrelated vNext scope complete.

Outcome: a pinned GitHub release that includes the six generic unpublished fixes,
common September 13 kernel enforcement improvements, and a verified project-profile
install/upgrade route, preserving existing Codex/Claude/Cursor project files.

Base: local generic main 082a011f5804b7d656a75cfa0b5f8d9bd07b2ddc. Inspect newer
Team Board source for reusable fixes but do not transplant its defaults or policy.
Work in the isolated release checkout on codex/vibeos-2.3-release.
Original plugin checkout, contributed archive, and source project remain read-only.

## Controlled evaluation interface and acceptance contract

Reuse/adapt the six reviewed modules from the September 13 source archive under
plugins/vibeos/scripts/controlled_evaluation/ (keep each normally formatted module
at most 300 lines). The standalone entrypoint is
plugins/vibeos/scripts/controlled-evaluation.py. Profile installs carry the entire
package into .vibeos/scripts/controlled_evaluation/ and its entrypoint into
.vibeos/scripts/controlled-evaluation.py. Legacy bootstraps must also carry it.
The installer must not auto-run evaluations or invent project tests.

CLI contract:
- `controlled-evaluation.py prepare --owner PATH --candidate PATH --spec FILE`:
  create a new owner workspace with its pinned protected-owner/config.json,
  harness-adaptation package, results directories/writer.lock. Refuse preexisting
  owner content; preserve candidate bytes. Spec supplies paths to owner tests and
  project adapter, required_owner_tests (test function names test_*), exact sorted
  required_project_cases, held_project_checks, writable_files (relative paths),
  explicit tools python/ruff/codex paths, dependencies (absolute path list), and
  timeout_seconds/max_lines/max_complexity. Native Codex sandbox is required for
  real evaluations. No arbitrary-command engine and no automatic test discovery
  standing in for owner-specified required identities. Report unsupported runtime
  clearly; do not silently execute unsandboxed. Validate source Git revision and
  complete candidate baseline. Owner and candidate must be distinct, nonnested,
  canonical directories; owner may be absent before preparation.
- `controlled-evaluation.py evaluate --owner PATH --run run-N` and
  `... publish --owner PATH --run run-N`: forward to adapted publication protocol.
  Zero only for eligible evaluation or exact PRE_REVIEW publication/idempotent retry.
  Acceptance/release remain a separate owner decision.
- Owner adapter schema: `vibeos.project-checks.v1`, fields cases [{id,status}],
  held list, project_qualified:false, runtime_qualified:false. It receives candidate
  root and result directory, creates project.json and project-evidence directory.
  Python wrapper is an integration adapter; candidate can be any project language.
- Strict duplicate/malformed JSON rejection, exact test case/exit-code accounting,
  required missing/empty/failed/skipped/duplicate/stale result refusal, no passing
  XML hiding nonzero pytest exit (1–6), source/profile/tool drift refusal,
  unchanged input binding before/after, symlink/type custody, actual timeouts and
  SIGTERM invalidation, current-run binding, single-writer lock and immutable
  repeat-safe PRE_REVIEW publication. Reuse source behavior and limitations.
- Runtime reality: native sandbox route is version-dependent. Test available
  macOS Codex syntax using synthetic disposable files and no credentials/provider.
  Supervised evidence controls are not same-user hostile-author isolation.

## Installer and gate contract

Extend the existing profile installer rather than add another installer. Pin
analyzed source/output/profile/target bytes; reject stale/tampered plans, path
traversal and symlinks. Preserve customized/unmanaged files and write separate
merge candidates. Make interrupted application recoverable by exact rollback or
explicit verified replan; prove partial state never claims completed install.
Add verify and recovery CLI commands where needed. Reuse later transaction code
only where product-neutral and simpler than small adaptation. Record real source
commit in install provenance. New module files are included through the above
stable interface. Gate runner must fail empty mandatory phases; intentional
optional empty phases return an explicit non-PASS state. Never zero-check PASS.
No script may treat skipped/missing blocking checks as completed success.

## Test and review plan

Tests derive from this contract before changed implementation is inspected by the
independent test owner. Prove positive install and evidence path plus negatives;
use two different project fixtures, path with spaces, customization upgrade,
source drift, actual interruption/recovery, runner exit failures, duplicate IDs,
lock contention and stale evidence. Run original relevant suites plus full suite,
separate preexisting failures, and independently review exact changed source.
Fresh clone the published GitHub commit and rerun actual install smoke. Verify
metadata/tag/source SHA and locally installed files. Do not claim cross-OS support.

Research reused: prior contribution/source proof and feature-retention map.
Primary refresh 2026-09-16: https://docs.pytest.org/en/stable/reference/exit-codes.html
(nonzero statuses include new6; reject any nonzero); Python subprocess docs for
process groups/timeouts and os docs for atomic rename. No new dependency selected.

Routine internal coordination stays in repository custody; no visible messages to
other Codex tasks. Role names, bounded scope, smaller models. Primary owner alone
integrates, commits, publishes and reports acceptance. Agents do not publish.
