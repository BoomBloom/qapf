# 06 — Keep, invert, or flatten Agent 7's regime-conditional factor weights?

**Type:** `wayfinder:grilling`
**Blocked by:** 05 (regime-factor-evidence)
**Status:** open · unclaimed

## Question

Keep, invert, or flatten Agent 7's regime-conditional factor weights?

The decision that ticket 05's evidence feeds. Options, none obviously right:

- **Keep** — the hand-set priors are theoretically motivated and one 3-year sample cannot overturn them.
- **Invert** — Agent 14's measurement is the only actual evidence from this system, and it points the
  other way.
- **Flatten to equal weight** — if the literature says factor timing is unreliable, equal weighting is
  the honest default and removes a source of overfitting.
- **Fit them** — but this is the most dangerous option: fitting regime weights on the same window used to
  validate destroys the validation. Would require the untouched window from ticket 02.

Note that inverting weights because one backtest said so is itself a form of overfitting, on a sample
of one.
