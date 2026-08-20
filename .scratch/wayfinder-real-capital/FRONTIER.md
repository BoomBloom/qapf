# Frontier — what is takeable right now

Updated 2026-08-20 after resolving tickets 09 and 11, and ticket 07's attempt 2 (still fails, closer).

| # | Ticket | Type | Blocked by | Takeable? |
|---|--------|------|-----------|-----------|
| 01 | What risk limits bind this system? | grilling (HITL) | — | CLOSED — 0.20/0.06, set live |
| 02 | What must the strategy prove? | grilling | — | CLOSED |
| 03 | Equity data past 2020 (final holdout) | research | — | YES (off critical path) |
| 04 | Which prop firms permit automation? | research | — | CLOSED |
| 05 | Literature on regime factor weighting | research | — | CLOSED |
| 06 | Keep / invert / flatten the weights | grilling | — | CLOSED |
| 07 | Does the strategy clear the bar? | task | — | **OPEN — FAILS, attempt 2/5, closer. 3 attempts left.** |
| 08 | Does it survive costs at $1,000? | task | — | YES (07's attempts already preview this via condition 3, which passes) |
| 09 | Which broker and platform? | grilling (HITL) | — | CLOSED — Interactive Brokers, own API |
| 10 | Universe survivorship bias | grilling (HITL) | — | CLOSED — fix it properly |
| 11 | Intraday equity vs daily closes | grilling (HITL) | — | CLOSED — Alpaca (live) + Alpha Vantage free (historical) |
| 12 | Wire kill-switch enforcement | task | — | CLOSED — enforced in Agent 1's risk_gate |
| 13 | Build the point-in-time universe | task | — | HALF DONE — membership free/verified, prices need Sharadar |

**The critical path is ticket 07 itself now** — every ticket that was blocking it is closed or as far
along as it can go without the operator's own account signups (Sharadar for 13, Alpaca/Alpha Vantage for
11, IBKR for 09). Attempt 2 (volatility-managed exposure) genuinely closed part of the gap: return-per-
unit-drawdown now beats the benchmark; Sharpe is at 85% of the benchmark's, up from 66%. **Recommended
next for attempt 3**: `docs/research/viable-alpha-families.md`'s #2 (OHLC-range volatility estimators —
Yang-Zhang/Parkinson/Garman-Klass) as an enabler to sharpen the same volatility-management signal, using
the O/H/L columns `agents/alpha/factors.py` already downloads and currently ignores. Deliberately not
started yet — flagged as needing more careful design than a quick swap (the estimator would need to
inform a PORTFOLIO-level vol input, not just a per-name one) rather than rushed.

Not yet built, both closed but unimplemented: the Alpaca live-monitoring wire-in and the Alpha Vantage
historical backfill script (ticket 11); IBKR account/API-credential setup (ticket 09).

Everything else is AFK (no operator input needed) or already closed.
