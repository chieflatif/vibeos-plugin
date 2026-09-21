# WO-157 final full-audit corrections

- Parent audit: `claude-audit-892a4340-f578-4cd2-863a-ef7fb410ca31`
- Parent candidate: `54c0080fdbd557ab31d0b7e71ed8b0aa6bba357b`
- Corrected implementation: `ebcbf4c5ce57aabed5540f2fc6b3a067fb4ccfe0`

This correction round is limited to the 17 findings from the final full audit. It does
not change the acceptance contract or expand the original review roots.

| Finding | Correction and evidence |
|---|---|
| F-001 | Verification and later validation now reload the parent provider payload, verify both artifact hashes, compare the stored result/model/provider and recompute closure. A pruning test fails before another provider call. Legacy schema-1 fallback was removed. |
| F-002 | Receipt validation now requires current `HEAD` to descend from the audited candidate and rejects every post-audit path outside recorded review and administrative roots. A new out-of-scope commit test proves refusal. |
| F-003 | Gate activation reads an enabled manifest gate and exact `.active_modules` membership. A disabled gate/profile mention passes normal independent-audit validation without demanding a companion receipt. |
| F-004 | Tests now prove active-module failure for no receipt, no report, and a registered but open receipt. |
| F-005 | Global skills and protocol references use targeted verification only when `claude-companion-audit` is active; all other projects retain their existing convergence behavior. |
| F-006 | `automated-tests.md` binds focused, full-suite, static, inventory, and gate results to implementation commit `ebcbf4c5ce57aabed5540f2fc6b3a067fb4ccfe0` and its tree. |
| F-007 | Git review snapshots hash raw blobs without the 160 KB packet-material ceiling; a tracked 170 KB binary is audited and revalidated. |
| F-008 | Git path discovery uses NUL-delimited output consistently; a non-ASCII tracked filename is audited and revalidated. |
| F-009 | The committed audit configuration bytes are included in both full and correction packets. |
| F-010 | The real CLI help output is checked for every pinned flag before provider invocation and its digest is recorded. A missing-flag fixture fails before the provider call. |
| F-011 | The redundant `--base-ref` option was removed. Full audits compute the merge base from committed `default_branch_ref`; docs and tests use that contract. |
| F-012 | Authentication documentation now states the exact accepted `claude.ai` account-store path and the deliberate rejection of API-key/OAuth environment credentials. |
| F-013 | Auditor execution is restricted to project setting sources from an empty temporary directory, excluding user settings, hooks, plugins, and repository instructions while retaining the account store. |
| F-014 | Public claims now describe provider-reported, provider-bound integrity evidence and retain the explicit same-user trust limitation. |
| F-015 | Installation no longer names an unpublished tag. Operators must select and verify a tag already visible on GitHub; inventory freshness is checked against source. |
| F-016 | The former multi-mode runner was separated into full preparation, correction preparation, provider execution, receipt construction, persistence, branch validation, material validation, post-audit scope validation, and mode/closure validation functions. The single-file exception remains only for portable stdlib installation. |
| F-017 | User-supplied refs reject option-like values and pass through Git's `--end-of-options` boundary. |

The exact commands, counts, commit and tree are in `automated-tests.md`. The next step
is targeted verification of F-001 through F-017 against the unchanged acceptance
contract; only a new material blocker would require another full audit.
