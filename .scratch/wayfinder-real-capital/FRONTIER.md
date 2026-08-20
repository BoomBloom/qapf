# Frontier — what is takeable right now

Updated 2026-08-20 after ticket 07's 5-attempt budget ran to completion.

| # | Ticket | Type | Blocked by | Takeable? |
|---|--------|------|-----------|-----------|
| 01 | What risk limits bind this system? | grilling (HITL) | — | CLOSED — 0.20/0.06, set live |
| 02 | What must the strategy prove? | grilling | — | CLOSED |
| 03 | Equity data past 2020 (final holdout) | research | — | YES (off critical path; moot unless a new attempt budget opens) |
| 04 | Which prop firms permit automation? | research | — | CLOSED |
| 05 | Literature on regime factor weighting | research | — | CLOSED |
| 06 | Keep / invert / flatten the weights | grilling | — | CLOSED |
| 07 | Does the strategy clear the bar? | task | — | **CLOSED — budget exhausted, 5/5 attempts. FAILS by 0.0009 (DSR 0.9491).** |
| 08 | Does it survive costs at $1,000? | task | — | YES (07's attempts already preview this via condition 3, which passes every time) |
| 09 | Which broker and platform? | grilling (HITL) | — | CLOSED — Interactive Brokers, own API |
| 10 | Universe survivorship bias | grilling (HITL) | — | CLOSED — fix it properly |
| 11 | Intraday equity vs daily closes | grilling (HITL) | — | CLOSED — Alpaca (live) + Alpha Vantage free (historical) |
| 12 | Wire kill-switch enforcement | task | — | CLOSED — enforced in Agent 1's risk_gate |
| 13 | Build the point-in-time universe | task | — | HALF DONE — membership free/verified, prices need Sharadar |

**The critical path has changed shape.** Ticket 07 is closed, not open — there is no more attempt budget
to spend without a new decision. The full trajectory (DSR: 0.9636 → 0.9615 → 0.9301 → 0.8870 → 0.9491;
Sharpe: 0.564 → 0.726 → 0.738 → 0.718 → **0.897, beating the 0.849 benchmark for the first time**) shows
attempt 5 (dropping the 5-day reversal factor — a specific, checkable point raised by an external AI
review, verified via a cheap diagnostic before being spent as the final formal attempt) came within a
rounding error of clearing the bar while passing every other condition.

**What's actually undecided now, and it's the operator's call, not a default:**
1. **Accept the result as-is** — the strategy is not yet fit for real capital on this exact
   universe/window, full stop. Move to whatever "not yet" means for the operator's own staged plan.
2. **Authorize a fresh attempt budget** aimed specifically at closing 0.0009 — not a blind restart, since
   attempt 5's reversal-drop is already a validated, real finding to build forward from.
3. **Resolve ticket 13's Sharadar signup first** — the one structurally different lever (real delisted-
   name prices, not just membership) that no attempt in the closed budget touched, and the only remaining
   candidate that could move the result by more than a rounding error rather than another marginal
   refinement.

Tickets 03, 08 are AFK and low-priority unless option 2 is chosen. Ticket 13's remaining half (the
Sharadar signup itself) needs the operator directly — same as always, an account/payment step I cannot
do on their behalf.
