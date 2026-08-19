# 05 — Does the published literature support regime-conditional factor weighting?

**Type:** `wayfinder:research`
**Blocked by:** None — in progress.
**Status:** CLOSED 2026-08-19 · research complete

## Question

Does the published literature support regime-conditional factor weighting?

FIRED 2026-08-19 — a research subagent is investigating against primary sources; findings land in
`docs/research/regime-factor-evidence.md`.

Agent 7 weights momentum heavily (0.45-0.50) in expansion regimes and shifts to low-volatility (0.45) in
contraction. These are hand-set priors, never fitted. Agent 14 measured the opposite of what they assume:
Sharpe +1.16 in deflationary contraction, -0.32 in disinflationary growth.

The question is whether the priors are backwards or whether one small sample over an unusual period
(2018-2020, spanning COVID) simply cannot support either conclusion. The literature is also genuinely
divided on whether factor timing works at all, and that disagreement should be reported honestly rather
than resolved by picking the convenient side.

---

## Resolution (2026-08-19) — findings in `docs/research/regime-factor-evidence.md` (594 lines, cited)

**The headline: the literature supports conditioning momentum on MARKET state, and specifically fails to
support conditioning any factor on growth x inflation quadrants.** Agent 7 conflates the two.

1. **Momentum crashes are real, but the instrument is wrong.** Daniel & Moskowitz (2016, JFE) define
   their bear indicator as *trailing 24-month market return < 0* — no GDP, no CPI, no NBER dates. Only
   the bear x ex-ante-variance INTERACTION survives; both standalone terms collapse (t = 0.0, -0.8).
   Cooper, Gutierrez & Hameed (2004, JF) tested macro variables head-on and found they "do not capture
   the asymmetry in momentum profits."
2. **The best-powered direct test of the quadrant idea finds nothing.** Ilmanen et al.'s century study
   builds a four-quadrant growth regime almost identical to QAPF's: "For momentum, nothing is
   significant", and coefficients "change sign across asset classes for a given factor."
3. **One weight-table cell is contradicted with real force.** Neville et al. (2021, JPM): low-vol/BAB
   earns -3% real in inflationary regimes vs +8% otherwise (t = -4.2), while momentum is the BEST equity
   factor there. QAPF's stagflation row does exactly the opposite — momentum 0.15, low-vol 0.45.
4. **The four-quadrant framework is being used inside-out.** Bridgewater's own writing defines the boxes
   by growth/inflation *relative to what is discounted* (surprises), maps them to ASSET CLASSES, and
   argues for EQUAL risk across quadrants precisely because you cannot forecast which one you're in.
   QAPF classifies realised, backward-looking levels and then concentrates into its guess.
5. **Reversal is the exception, and the best-evidenced relationship found:** Nagel (2012, RFS) predicts
   reversal returns from VIX with monthly adjusted R^2 = 0.56.

### It also corrected this project's own Agent 14 finding

Agent 14 measured Sharpe +1.16 in contraction vs -0.32 in growth and that was read here as evidence the
priors are backwards. The research argues it is **not**, for four reasons: a sub-1-year regime segment
has SE(Sharpe) ~ 1.0 under Lo (2002), so the 1.48 gap carries t < 1; the measurement is confounded by
market beta because Agent 2 is long-only, so regime Sharpe is mostly the market's; each bucket contains
one idiosyncratic event (the Sept 2019 momentum unwind, COVID); and it is equally consistent with the
contraction prior being right and only the momentum prior wrong.

**Recommendation: FLATTEN, do not invert.** Inverting would put maximum momentum weight exactly where
Daniel & Moskowitz measure the premium ~59pp/yr lower.

Caveat flagged by the researcher: Polk, Haghbin & de Longis (2020, JOIM) is the main pro-rotation
counterweight and its hosted PDF now 404s, so it is cited as existing rather than as verified evidence.
