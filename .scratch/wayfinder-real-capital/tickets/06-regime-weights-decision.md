# 06 — Keep, invert, or flatten Agent 7's regime-conditional factor weights?

**Type:** `wayfinder:grilling`
**Blocked by:** None — ticket 05 CLOSED 2026-08-19. **This ticket is now takeable.**
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

### Informed by ticket 05's evidence (2026-08-19)

The research recommends **flatten, not invert** — and reframes the question. The issue is not which
direction the weights point but that **the conditioning variable itself is unsupported**: no published
evidence ties factor premia to growth x inflation quadrants, while momentum's crash risk is well
evidenced against *market* state (Daniel & Moskowitz's bear x ex-ante-variance interaction) and
reversal against VIX (Nagel, R^2 = 0.56).

So the live options are now:

- **Flatten to equal weight** — honest default; removes an unsupported conditioner and a source of
  overfitting. Cheapest, and defensible on the evidence.
- **Re-instrument** — keep conditioning, but on what the literature supports: momentum on
  `bear_market x ex_ante_variance`, reversal on VIX, and drop the macro quadrant conditioner entirely.
  More work, better evidenced, and it changes what Agent 6 is FOR (it would still classify regimes, but
  Agent 7 would stop consuming that classification).
- **Keep and fix only stagflation** — the one cell contradicted at t = -4.2. Minimal change, but keeps a
  conditioner the evidence does not support.

Note the interaction with ticket 02's five-attempt budget: each of these is a variant, and trying more
than one counts as more than one attempt.
