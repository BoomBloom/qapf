# 11 — Should the CRO evaluate risk on intraday equity rather than daily closes?

**Type:** `wayfinder:grilling`
**Blocked by:** None — can start immediately.
**Status:** CLOSED — Alpaca (live) + Alpha Vantage free tier (historical backfill), 2026-08-20

## Question

Surfaced by ticket 04's research.

Agent 10 and Agent 9 both compute drawdown from **daily closing** returns. Every prop firm — and any
honest risk assessment — evaluates loss limits on **intraday equity including unrealised P&L**. A
position that falls 9% during the session and closes down 4% breaches a 5% daily limit in reality and
looks fine in this system.

Consequences:

- **The -36.68% max drawdown is optimistic.** True intraday drawdown is strictly worse; how much worse
  is unmeasured.
- Any future "passes the prop-firm rule" conclusion from a close-based backtest is measuring the wrong
  quantity.
- More immediately: the risk limits set in ticket 01 mean something different depending on which
  quantity they bind.

The decision: does the CRO move to intraday evaluation, and if so, where does intraday data come from?
Qlib's bundled dataset is daily OHLCV. Intraday high/low gives a cheap conservative bound (worst-case
within the session) without full tick data — that may be enough, and is far cheaper than a tick feed.

## Grilled (2026-08-19)

Offered the cheap Qlib high/low bound as the recommendation; operator chose the bigger option instead:
**get real intraday/tick data now**, not a conservative bound. This is real new scope, not a small
follow-on — it needs an actual data source picked and verified (coverage, cost, licensing) for two
different uses that may need different sources: (a) the live CRO's real-time risk gate, where free
options plausibly exist, and (b) re-scoring ticket 07's historical -36.68% drawdown with true intraday
data, which Qlib's free bundle cannot provide at all. Dispatched as real research rather than guessed —
see the note below. **Any provider requiring a paid subscription needs the operator to actually sign up
and provide a key** — CLAUDE.md's safety rules mean I cannot create accounts or enter payment details on
your behalf, so whatever this research finds, the account/subscription step (if any) is yours to do.

## Research complete (2026-08-19) — `docs/research/intraday-data-providers.md` (389 lines, cited)

Live-verified, not guessed: yfinance's actual interval caps were found by triggering the real failures
(1m caps hard at 8 days, 5m/15m/30m at 60 days, 1h at 730 days — all boundary-tested in this project's
own venv today). Real pricing/coverage pages fetched for Alpaca, Massive (Polygon.io's 2025-10-30
rebrand — same API), Databento, Tiingo, Alpha Vantage, IEX Cloud (confirmed dead since 2024-08-31), and
two flat-fee vendors.

**Two different answers for two different needs, decision still pending:**

1. **Live risk monitoring (the CRO's real-time gate):** Alpaca Markets' free/paper tier — genuinely
   **$0, no card**, just an email+password signup. Real-time IEX websocket (≤30 symbols, comfortably
   covers the current universe). Straightforward to wire in whenever this is picked up.
2. **Historical 2008-2017 intraday backtesting (re-scoring the -36.68% max drawdown for real):**
   **no free option is both fast and complete.** Best paid path: Massive Advanced tier, **$199/mo,
   operator must personally subscribe**. Free-but-slow fallback: Alpha Vantage's free tier genuinely
   covers the window (verified back to Jan 2000) but at 25 req/day would take ~2 months of wall-clock
   backfill for this ticker set. A one-time-purchase alternative (FirstRateData, ~$400) exists but its
   backtest-licensing terms weren't verifiable from the pages checked.

**Still open — needs the operator's call, not decided here:** which of (a) pay $199/mo, (b) accept a
~2-month free backfill, (c) buy FirstRateData's bundle, or (d) defer this and use live Alpaca data only
(no historical re-score) going forward.

## Resolved (2026-08-20)

Operator: $199/mo (Massive) is too much, prefers the cheaper option. **Decision: option (b) — Alpaca
free/paper tier for live intraday risk monitoring ($0, no card), and Alpha Vantage's free tier for the
historical 2008-2017 re-score, accepting the ~2-month backfill timeline at 25 req/day rather than paying.**

Both are genuinely free signups the operator can do without any payment step. Not yet built: the actual
Alpaca websocket wiring into the CRO's live risk gate, and the Alpha Vantage backfill script (should be
designed as a long-running background job per the research doc's own note, not an interactive one-shot —
1,680 ticker-month requests at 25/day is real wall-clock time, not a quick script to run and wait on).
