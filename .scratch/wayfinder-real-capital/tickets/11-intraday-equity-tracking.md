# 11 — Should the CRO evaluate risk on intraday equity rather than daily closes?

**Type:** `wayfinder:grilling`
**Blocked by:** None — can start immediately.
**Status:** open · unclaimed

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
