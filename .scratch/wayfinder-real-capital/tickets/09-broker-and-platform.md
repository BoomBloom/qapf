# 09 — Which broker and platform for the paper and $1,000 live stages?

**Type:** `wayfinder:grilling`
**Blocked by:** 04 (prop-firm-rules)
**Status:** CLOSED — Interactive Brokers, via its own API (not TradingView), 2026-08-20

## Question

Which broker and platform for the paper and $1,000 live stages?

The operator has no broker account yet, has previously used MT4/MT5 and TradingView, and is considering
Interactive Brokers.

The tension: IBKR fits systematic US equity trading and has a genuine API, but prop-firm funding
programmes overwhelmingly require MT4/MT5/cTrader/DXtrade. Choosing IBKR optimises stages 2-3 and may
mean re-platforming for stage 4; choosing an MT5 broker optimises for a stage that ticket 04 may show is
unavailable for equities anyway.

Needs ticket 04's findings before it can be answered without guessing.

## Grilled, not resolved (2026-08-19)

Presented with a recommendation (IBKR direct, given ticket 04 already ruled out prop-firm funding for
this equities strategy so the MT4/MT5 pull no longer applies, and ticket 07 already verified IBKR Lite's
real $0-commission cost model). Operator's answer: **not yet — still deciding.** Left open on purpose,
not closed with a default. Reasonable to revisit once ticket 07 either clears the bar or the reason it
keeps failing is well understood — a broker choice matters less while the strategy itself is unvalidated.

## Resolved (2026-08-20)

Operator's actual constraint, once stated plainly: IBKR vs. "a broker that uses TradingView or has good
trading software" — not IBKR vs. a specific named alternative. Researched rather than assumed: **IBKR
is not an alternative to a TradingView broker, it IS one.** IBKR has a native TradingView charting +
manual one-click order panel, confirmed via TradingView's own broker documentation.

Real nuance worth recording, not glossed over: that panel is **manual-only** — TradingView cannot route
fully automated orders to IBKR by itself. Automating from TradingView needs a third-party webhook bridge
(TradersPost, PickMyTrade, and similar). **This doesn't matter for QAPF's actual architecture**: Agent 11
(`backend/agents/execution/planner.py`) already computes real orders in Python — the system needs IBKR's
own API (TWS or the Client Portal Web API) to place them directly, not TradingView's charting layer as
an intermediary. Routing through a TradingView webhook bridge would be an unnecessary extra hop for a
system that already generates its own orders programmatically.

**Decision: Interactive Brokers**, connected via its own API (TWS/Client Portal), not through TradingView.
The operator still gets TradingView's charts and manual panel for free as a side benefit if they ever
want to eyeball positions or intervene by hand alongside the automated system.

**Not yet done:** actually opening the IBKR account and generating API credentials — that's the
operator's own action, same category as the Sharadar/data-provider signups in tickets 11/13.
