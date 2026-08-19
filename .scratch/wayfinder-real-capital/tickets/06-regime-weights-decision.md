# 06 — Keep, invert, or flatten Agent 7's regime-conditional factor weights?

**Type:** `wayfinder:grilling`
**Blocked by:** None — ticket 05 CLOSED 2026-08-19. **This ticket is now takeable.**
**Status:** CLOSED 2026-08-19 · resolved with the operator

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

---

## Resolution (2026-08-19): FLATTEN to equal weight

Chosen over inverting and over re-instrumenting, as **attempt 1 of the 5-attempt budget** set in ticket 02.

### Why flatten rather than re-instrument first

Re-instrumenting (momentum on Daniel & Moskowitz's `bear x ex-ante-variance`, reversal on VIX) is the
better-evidenced end state, but it is the wrong FIRST move. It adds machinery, so a failure would be
ambiguous — weak factors, or a wrong instrument? Flattening is diagnostic in both directions:

- **If flat equal-weight factors clear the bar**, regime conditioning was never needed. One attempt, and
  a large finding.
- **If they fail**, the problem is the factors themselves, not the conditioning — which is exactly what
  you need to know before spending attempt 2 on a more elaborate conditioner.

Sequencing chosen so each attempt is diagnostic rather than just another roll.

### What changes in the code

`REGIME_FACTOR_WEIGHTS` in `backend/agents/alpha/combiner.py` becomes 0.25 for each of the four factors,
identical across all four macro regimes.

**Keep the mechanism, flatten the values.** Deleting the regime-weight table would make the
re-instrument option (attempt 2, if warranted) expensive to reach; keeping a table whose rows are all
identical is honest as long as a comment says why. Agent 7's `__main__.py` regime-sensitivity test
asserts that switching regimes changes signals — that test must be **inverted** to assert regimes no
longer change factor weighting, or it will fail by design.

### Architectural consequence, stated plainly

**Agent 6's regime output stops driving Agent 7's factor weights.** It still drives Agent 2 (optimizer
choice and gross exposure), so Agent 6 is not disconnected — but its role in the alpha layer becomes
informational. Anyone reading the architecture should not be told the alpha signal is regime-conditional,
because after this change it is not.

### What would reopen this

Attempt 2 re-instruments on market state rather than macro quadrants — but only if flat factors show
promise and fall short. If flat factors fail outright, the honest next step is questioning the factors,
not the conditioner.
