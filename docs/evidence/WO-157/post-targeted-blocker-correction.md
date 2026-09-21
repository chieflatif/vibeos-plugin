# WO-157 post-targeted blocker correction

Targeted receipt: `claude-audit-909ed4d9-ba46-4776-bef7-0b63ef3e7bd2`

The targeted check closed every original finding and found one new medium blocker in
the close gate. Profile activation was parsed only when `jq` was available. If the
generated companion gate row was also absent, an active companion module or malformed
profile could therefore leave `COMPANION_REQUIRED=false`.

The correction removes that conditional parser path:

- `project-profile.json` is parsed with the same required Python runtime already used
  for the manifest.
- Invalid JSON or a non-string `active_modules` list fails closed.
- Exact active-module membership sets the companion requirement even when the generated
  manifest row and `jq` are both absent.
- A phase runtime other than `claude` fails closed.
- The existing enabled manifest row still requires a matching active profile, preserving
  manifest/profile consistency.

Tests cover an active profile with no manifest and no `jq`, plus a malformed profile
with no manifest. Focused, full-suite, static and quality-gate results are bound to the
corrected implementation in `automated-tests.md`.

Because this was a new material blocker rather than an unclosed original finding, the
next review is one fresh full audit of the exact corrected candidate.

The first local packet build stopped before a provider call because eight lines of
unchanged diff context pushed the complete review 5.9 KB over the separate 300 KB diff
cap. The audit scope was not narrowed. Diff context was reduced to the standard three
lines, retaining every changed line while bringing the complete diff to about 242 KB.
