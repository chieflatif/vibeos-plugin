# Candidate verification

- Tested implementation commit: `818519f079b3e0fb1f0b49a3601c3b7dbf9fd6f1`
- Tested tree: `5898b5c1e2b5c3199e7e1652b8d2b04f556944f6`

Canonical pre-commit gate command:

```sh
bash plugins/vibeos/scripts/gate-runner.sh pre_commit --continue-on-failure \
  --manifest plugins/vibeos/quality-gate-manifest.json --project-dir . \
  --framework-dir plugins/vibeos --timeout 600
```

Result: PASS, nine gates passed, zero failed, one optional dependency gate skipped.
The test gate collected 415 tests and passed in 136 seconds on system Python3.14
with pytest9.0.2 and Ruff0.15.0. The wrapper summarizes gate status rather than
retaining every successful pytest line; 415 is the collected count, not a claimed
count of independent product-acceptance scenarios.

Focused companion suite: 59 tests plus 23 subtests passed. This includes full review,
targeted corrections, newly found blocker history, minor disposition, unmet
acceptance blocking, v1 compatibility, unrelated-work tolerance, config invariants,
missing target failure, synthetic provider unavailability, approval mismatch refusal,
fresh-context command construction, honest provenance and mixed review chains.
Packaging/installer follow-up: 21 tests plus seven subtests passed. All production
scripts passed Ruff; frontmatter and generated index checks passed. Shell syntax
and scoped Git diff checks passed.

Failure history is retained here rather than hidden:

- Initial non-companion regression slice: 355 tests and70subtests passed, one size
  gate failed. The close-gate script and fallback helper were simplified through
  deduplication to295and299physical lines; the size gate then passed. No new size
  exception was added. The preexisting large companion-core exception remains.
- An initial canonical run selected an existing Python3.13 virtual environment.
  Controlled-evaluation fixtures resolve `sys.executable`, thereby selecting its
  base interpreter, which lacked pytest. The failed fixture passed unchanged on
  the established system interpreter. The complete canonical command above then
  passed there. This does not claim universal virtual-environment compatibility.
- A test-only fixture cap increased from100000to120000bytes for its measured
  103343-byte packet, which includes a copy of the installed validator. Production
  budgets and test assertions were not loosened.

Fake CLI/provider tests are integration-contract evidence, not real provider calls.
No real fallback authorization exists for this candidate. The separate live Claude
source review must still pass before publication; the earlier live design review
does not establish source acceptance. Existing projects have not been upgraded.
