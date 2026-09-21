# WO-157 post-blocker full-audit corrections

Parent full audit: `claude-audit-96e0e5ee-a663-4b2d-9a07-70be5112a0b0`  
Tested implementation: `e0710e034e745b16f8eb363309c8b1237b501302`

| Finding | Correction |
|---|---|
| F-001 | Receipt validation now fails on any non-ignored uncommitted path while continuing to tolerate local receipt/session artifacts and ignored bytecode. |
| F-002 | Receipts now record safe mode, project-only setting sources and the exact max-turns preflight path. The pinned CLI help explicitly states that safe mode disables `CLAUDE.md` and the named customizations; no personal configuration is read or copied. |
| F-003 | Audit evidence must name the tested implementation commit and tree. The CLI proves ancestry and rejects executable changes in later evidence-only commits. |
| F-004 | Documentation now states that receipt, report and raw provider output remain local integrity artifacts; committed evidence records IDs and outcomes but is not standalone provider proof. |
| F-005 | Provider output now requires a success subtype, native structured output, the requested canonical model/provider and no nonzero use by another model. |
| F-006 | Validation reparses and compares the current work-order write scope while allowing non-normative status text to advance. |
| F-007 | Nested receipt objects are type-checked and malformed input exits through the controlled failure path. |
| F-008 | Required help flags use option-boundary matching. Advertised `--max-turns` skips the probe; the compatibility path requires the exact isolated authentication stop. |
| F-009 | The close gate now requires the supplied Markdown report to resolve to the report path bound by the registered receipt. |
| F-010 | Tests now cover dirty worktrees, config/write-scope drift, tested-commit drift, provider subtype/extra-model/fallback refusal, malformed receipts and wrong-report refusal. |
| F-011 | Stale packet-size and release-state wording is corrected. The currently redundant scope check is retained and labelled as intentional defense in depth. |
| F-012 | The self-release boundary is explicit: WO-157 runs the same validation manually; installed opt-in projects receive the blocking `wo_exit` gate. |

The focused slice passed 85 tests plus 39 subtests. The full suite passed 395 tests
plus 85 subtests, and the pre-commit bundle passed 9 gates with 1 configured advisory
skip. Exact commands, durations and commit/tree bindings are in `automated-tests.md`.
