# 07 — Does the strategy clear the bar on data it has never been tuned on?

**Type:** `wayfinder:task`
**Blocked by:** 02 (validation-bar), 03 (data-past-2020), 06 (regime-weights-decision)
**Status:** open · unclaimed

## Question

Does the strategy clear the bar on data it has never been tuned on?

The moment of truth for this map. Runs the strategy — with whatever weights ticket 06 settles on —
against the untouched window from ticket 02, using the extended data from ticket 03, and reports
whether it clears the bar.

Resolution records the actual numbers, whatever they are. A failure here is a legitimate and likely
outcome, and resolves this ticket just as validly as a pass. What happens next in that case is
deliberately left in the map's fog, because it depends on how it fails.
