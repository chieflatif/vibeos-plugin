# WO-157 new-blocker correction

The second targeted verification closed all 18 original findings and reported one new
medium blocker: exact equality with the recorded `origin/*` commit would invalidate a
receipt after a routine fetch or merge even when the audited ancestry remained intact.

The correction retains the security property without freezing the remote ref:

- At audit time, the supplied base must still equal the candidate's merge base with
  the committed default-branch ref.
- The receipt retains the exact default-branch commit and merge base as historical
  evidence.
- Validation recomputes the historical merge base from the recorded commit and proves
  it descends from the audited base.
- Validation separately recomputes the merge base against the current remote ref and
  requires the audited base to remain its ancestor.
- A normal remote advance or merge therefore remains valid; an unrelated or rewritten
  default-branch history fails closed.
- Tests prove both the safe-advance pass and unrelated-history refusal.

Because this was a new material blocker rather than an original finding correction,
the next provider step is a new full audit of the corrected candidate, as required by
the companion-audit state machine.

The accumulated release diff is rendered with eight context lines so every changed
path fits beneath the 300 KB diff ceiling. The later post-blocker full packet uses the
committed 400 KB prompt ceiling because it also carries the complete correction
evidence; no path is removed from the final audit scope.
